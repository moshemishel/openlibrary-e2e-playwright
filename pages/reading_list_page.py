"""Page Object for OpenLibrary's reading-list landing page.

Implements `assert_reading_list_count` (function 3 from the spec):
opens /account/books, reads the per-shelf counts from the section H2
headings, and asserts the sum equals the expected count.

Why heading-role: each shelf has a desktop H2 like "Want to Read (13)".
The mobile sidebar repeats the link but NOT inside an H2, so a
heading-role lookup picks one element per shelf -- no strict-mode
collision and no class-scoped fallback needed.

Why sum across CR + WTR + AR: function 2 from the spec adds books
to either Want to Read or Already Read at random. Counting one
shelf alone would fail whenever a book lands on the other shelf.
Loans (operational) and Lists (user-curated) are deliberately
excluded -- they are not reading-list shelves.
"""

import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urljoin

from playwright.async_api import Page

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://openlibrary.org"
SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots"

# Internal key -> visible label that appears in the H2 heading text.
# The trailing " (N)" is optional in the heading: CR-when-empty omits
# it, every other shelf includes it. _COUNT_REGEX handles both.
SHELF_LABELS = {
    "currently_reading": "Currently Reading",
    "want_to_read": "Want to Read",
    "already_read": "Already Read",
}

# `[\d,]+` tolerates a thousands-separator like "(1,234)" in case
# OpenLibrary ever renders one. Plain "(13)" is the common case today.
# The comma is stripped before `int()`.
_COUNT_REGEX = re.compile(r"\(([\d,]+)\)")


def _screenshot_timestamp() -> str:
    """UTC timestamp used to keep assertion screenshots from different runs distinct."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")


class ReadingListPage:
    # /account/books redirects to /people/<username>/books -- safer than
    # hardcoding the username, works for whichever user is logged in.
    LANDING_PATH = "/account/books"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    async def goto(self) -> None:
        await self.page.goto(urljoin(self.base_url, self.LANDING_PATH))

    async def _shelf_count(self, label: str) -> int:
        """Read the count for one shelf from its H2 heading.

        Heading text is "Label (N)" when the shelf has items, or just
        "Label" when empty (observed for Currently Reading -- WTR/AR
        always include the count). A missing-count case maps to 0.

        The regex anchors at the start and accepts either end-of-name
        or " (" right after the label, so neighbours like "Currently
        Reading Stats" cannot accidentally match.
        """
        heading = self.page.get_by_role(
            "heading",
            name=re.compile(rf"^{re.escape(label)}(?:$| \()"),
        )
        if await heading.count() == 0:
            logger.warning("shelf heading %r not found, treating as 0", label)
            return 0
        text = (await heading.first.inner_text()).strip()
        match = _COUNT_REGEX.search(text)
        return int(match.group(1).replace(",", "")) if match else 0

    async def get_shelf_counts(self) -> dict[str, int]:
        """Return a {shelf_key: count} dict for the three status shelves."""
        counts = {key: await self._shelf_count(label) for key, label in SHELF_LABELS.items()}
        logger.info("shelf counts: %s", counts)
        return counts

    async def total_count(self) -> int:
        """Sum of books across Currently Reading + Want to Read + Already Read."""
        return sum((await self.get_shelf_counts()).values())

    async def assert_reading_list_count(self, expected_count: int) -> None:
        """Function 3 from the spec.

        Navigates to the landing page, sums the three status-shelf
        counts, saves a screenshot, and asserts equality. Raises
        AssertionError on mismatch.
        """
        await self.goto()
        actual = await self.total_count()
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        shot_name = (
            f"assert_count_{_screenshot_timestamp()}_expected_{expected_count}_actual_{actual}.png"
        )
        shot_path = SCREENSHOT_DIR / shot_name
        await self.page.screenshot(path=str(shot_path))
        logger.info("reading-list count screenshot saved: %s", shot_path)
        assert actual == expected_count, (
            f"reading list count mismatch: expected {expected_count}, got {actual}"
        )


async def assert_reading_list_count(
    page: Page,
    expected_count: int,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> None:
    """Standalone wrapper for function 3 from the assignment spec."""
    await ReadingListPage(page, base_url).assert_reading_list_count(expected_count)
