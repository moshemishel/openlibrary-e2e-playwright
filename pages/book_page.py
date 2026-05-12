"""Page Object for OpenLibrary's book/work page.

Implements `add_books_to_reading_list` (function 2 from the spec):
opens each book page and clicks either "Want to Read" or "Already
Read" at random. A screenshot and a log line are saved for every
added book.
"""

import logging
import random
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import Page

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://openlibrary.org"

# How long to wait for the primary button to reflect the new state
# after submitting the add/remove form. The submit triggers a JSON
# roundtrip and the DOM is rewritten in place. If 8s is not enough,
# something deeper is wrong (network, page changed, captcha).
SHELF_ACTION_TIMEOUT_MS = 8_000

# Screenshots from add_books_to_reading_list go here. Created on
# first use, gitignored.
SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"

# Shelves we pick from randomly, per the spec.
RANDOM_SHELVES = ("want_to_read", "already_read")

# Internal snake_case key -> the accessible name visible on the page.
SHELF_LABELS = {
    "want_to_read": "Want to Read",
    "already_read": "Already Read",
    "currently_reading": "Currently Reading",
}

_WORK_ID_REGEX = re.compile(r"/works/(OL[0-9]+W)")


def _work_id_from_url(url: str) -> str:
    """Pull the OL work id out of a OpenLibrary URL.

    `/works/OL893415W/Dune` -> `"OL893415W"`. Returns `"unknown"` if
    the URL does not match -- kept defensive so the screenshot
    filename never crashes the run.
    """
    match = _WORK_ID_REGEX.search(url)
    return match.group(1) if match else "unknown"


def _screenshot_timestamp() -> str:
    """UTC timestamp used to keep screenshots from different runs distinct."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


class BookPage:
    """OpenLibrary book/work page.

    Holds the Playwright `page` and the `base_url` as state, so the
    public function signature does not need to receive them (matches
    the spec).
    """

    DROPPER = ".my-books-dropper"
    PRIMARY_FORM = "form.primary-action"
    DROPDOWN = ".read-statuses"
    DROPDOWN_TRIGGER = ".generic-dropper__dropclick"
    PRIMARY_BTN = ".book-progress-btn"
    PRIMARY_BTN_TEXT = ".btn-text"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    # ----- navigation -----

    async def goto(self, book_url: str) -> None:
        """Open a book page. Accepts a full URL or a relative path."""
        if book_url.startswith("http"):
            await self.page.goto(book_url)
        else:
            await self.page.goto(urljoin(self.base_url, book_url))

    # ----- state -----

    async def current_shelf(self) -> str | None:
        """Return the shelf the book is on, or None if not on any shelf.

        The primary button's class is the state signal:
          * `.unactivated` -> book is on no shelf (None).
          * otherwise -> shelf identified by the primary's `.btn-text`.
        """
        primary = self.page.locator(f"{self.DROPPER} {self.PRIMARY_BTN}")
        classes = (await primary.get_attribute("class")) or ""
        # Check "unactivated" first -- "activated" is a substring of it,
        # so a naive `"activated" in classes` would false-positive here.
        if "unactivated" in classes:
            return None
        text = (await primary.locator(self.PRIMARY_BTN_TEXT).inner_text()).strip()
        for key, label in SHELF_LABELS.items():
            if text == label:
                return key
        return None

    # ----- actions -----

    async def add_to_shelf(self, shelf: str) -> None:
        """Add the book to `shelf`. Idempotent.

        We must check the primary button before falling back to the
        dropdown: in the unshelfed state, the dropdown's "Want to
        Read" button is `hidden` in the DOM and a click on it would
        fail. The primary in that state already shows "Want to Read"
        so we click it directly.
        """
        if shelf not in SHELF_LABELS:
            raise ValueError(f"unknown shelf: {shelf!r}")

        if await self.current_shelf() == shelf:
            logger.info("already on shelf %r, no-op", shelf)
            return

        target_label = SHELF_LABELS[shelf]
        dropper = self.page.locator(self.DROPPER)
        primary_match = dropper.locator(self.PRIMARY_FORM).get_by_role("button", name=target_label)

        if await primary_match.count() == 1:
            await primary_match.click()
        else:
            await dropper.locator(self.DROPDOWN_TRIGGER).click()
            await dropper.locator(self.DROPDOWN).get_by_role("button", name=target_label).click()

        await self._wait_for_primary_activated(target_label)

    async def remove_from_shelf(self) -> None:
        """Remove the book from whatever shelf it is on. Idempotent."""
        if await self.current_shelf() is None:
            return
        dropper = self.page.locator(self.DROPPER)
        await dropper.locator(self.DROPDOWN_TRIGGER).click()
        await dropper.locator(self.DROPDOWN).get_by_role("button", name="Remove From Shelf").click()
        await self._wait_for_primary_unactivated()

    async def _wait_for_primary_activated(self, expected_label: str) -> None:
        """Wait until the primary button is `.activated` with the expected label."""
        await self.page.locator(
            f"{self.DROPPER} {self.PRIMARY_BTN}.activated",
            has_text=expected_label,
        ).wait_for(timeout=SHELF_ACTION_TIMEOUT_MS)

    async def _wait_for_primary_unactivated(self) -> None:
        """Wait until the primary button is `.unactivated` (book on no shelf)."""
        await self.page.locator(f"{self.DROPPER} {self.PRIMARY_BTN}.unactivated").wait_for(
            timeout=SHELF_ACTION_TIMEOUT_MS
        )

    # ----- spec function 2 -----

    async def add_books_to_reading_list(self, urls: list[str]) -> None:
        """For each URL, open the page and add it to a random shelf.

        Each book is added to either "Want to Read" or "Already Read",
        chosen at random per the spec. A screenshot is saved as
        `screenshots/<timestamp>_<idx>_<work_id>_<shelf>.png` and a log line is
        written for every book. Tests can call `random.seed(...)`
        before this function for deterministic shelf choices.
        """
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        for idx, url in enumerate(urls):
            shelf = random.choice(RANDOM_SHELVES)
            await self.goto(url)
            await self.add_to_shelf(shelf)
            work_id = _work_id_from_url(url)
            path = SCREENSHOT_DIR / f"{_screenshot_timestamp()}_{idx:02d}_{work_id}_{shelf}.png"
            await self.page.screenshot(path=str(path))
            logger.info("added %s to %s [shot=%s]", url, shelf, path)


async def add_books_to_reading_list(
    page: Page,
    urls: list[str],
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    """Standalone wrapper for function 2 from the assignment spec."""
    await BookPage(page, base_url).add_books_to_reading_list(urls)
