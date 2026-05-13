"""Page Object for OpenLibrary's search results page."""

import logging
import re
from urllib.parse import quote_plus, urljoin

from playwright.async_api import Locator, Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

FIRST_PUBLISHED_REGEX = re.compile(
    r"\bFirst published in\s+(1[0-9]{3}|20[0-9]{2})\b",
    re.IGNORECASE,
)
DEFAULT_BASE_URL = "https://openlibrary.org"


class SearchResultsParseError(RuntimeError):
    """Raised when OpenLibrary search results no longer match expected markup."""


class SearchPage:
    """OpenLibrary search results page.

    Holds the Playwright `page` and `base_url` for the POM implementation.
    The module-level wrapper accepts `page` explicitly and delegates here.
    """

    SEARCH_PATH = "/search"
    RESULT_ITEM = 'li[itemtype$="Book"]'
    RESULT_LINK = '[itemprop="name"] a[itemprop="url"]'
    RESULT_DETAILS_SPAN = ".resultDetails span"
    PAGINATION = "ol-pagination"
    # OpenLibrary's verify-human script binds this button by id, so this is
    # a stable app hook; role/name would be more sensitive to text/i18n changes.
    VERIFY_HUMAN_BUTTON = "#verify-human-btn"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def _build_search_url(self, query: str, page_num: int) -> str:
        return build_title_search_url(self.base_url, query, page_num)

    async def _get_total_pages(self) -> int:
        """Read total page count from the <ol-pagination> web component.

        Returns 1 when the component is missing (single page of results) or
        when its attribute is missing or unparseable. A missing total should
        not crash the run -- the loop will just run once and exit.
        """
        pagination = self.page.locator(self.PAGINATION)
        if await pagination.count() == 0:
            return 1
        total = await pagination.first.get_attribute("total-pages")
        try:
            return int(total) if total else 1
        except ValueError:
            return 1

    async def _handle_verify_human_if_present(self) -> None:
        """Click OpenLibrary's lightweight verify-human prompt when it appears."""
        button = self.page.locator(self.VERIFY_HUMAN_BUTTON)
        if await button.count() == 0:
            return

        logger.warning("OpenLibrary verify-human prompt detected on search page")
        await button.click()
        try:
            await self.page.wait_for_load_state("domcontentloaded", timeout=10_000)
        except PlaywrightTimeoutError:
            logger.warning("verify-human click did not reach domcontentloaded before timeout")
        try:
            await button.wait_for(state="detached", timeout=10_000)
        except PlaywrightTimeoutError:
            logger.warning("verify-human button still present after click")

    async def _extract_year(self, item: Locator) -> int | None:
        """Pull the first-publication year out of the result's details text.

        Returns None when no year is found. A result may legitimately have
        no year (a generic edition entry, for example).
        """
        year_span = item.locator(self.RESULT_DETAILS_SPAN).filter(
            has_text=FIRST_PUBLISHED_REGEX
        ).first
        if await year_span.count() == 0:
            return None
        text = await year_span.inner_text()
        match = FIRST_PUBLISHED_REGEX.search(text)
        return int(match.group(1)) if match else None

    async def _extract_url(self, item: Locator) -> str | None:
        """Pull the absolute book URL out of a result item.

        Returns None if the result has no name link. Should not happen for
        a valid <li itemtype=...Book>, kept defensive against partial DOM.
        """
        link = item.locator(self.RESULT_LINK).first
        if await link.count() == 0:
            return None
        href = await link.get_attribute("href")
        if not href:
            return None
        return urljoin(self.base_url, href)

    async def search_books_by_title_under_year(
        self, query: str, max_year: int, limit: int = 5
    ) -> list[str]:
        """Return up to `limit` book URLs whose first publication year is <= `max_year`.

        The loop stops on the first of these three conditions:
          1. We collected `limit` URLs.
          2. We hit a result with year > `max_year` (safe because of sort=old).
          3. We ran out of pages.

        Empty list is a valid result.
        """
        collected: list[str] = []
        page_num = 1
        total_pages: int | None = None

        while len(collected) < limit:
            url = self._build_search_url(query, page_num)
            logger.info("search page %d: %s", page_num, url)
            await self.page.goto(url, wait_until="domcontentloaded")
            await self._handle_verify_human_if_present()

            if total_pages is None:
                total_pages = await self._get_total_pages()
                logger.info("total pages for query=%r: %d", query, total_pages)

            items = await self.page.locator(self.RESULT_ITEM).all()
            if not items:
                logger.info("no results on page %d, stopping", page_num)
                break

            parsed_year_count = 0
            for item in items:
                year = await self._extract_year(item)
                if year is None:
                    continue
                parsed_year_count += 1
                if year > max_year:
                    logger.info(
                        "year %d > max_year %d, stopping early (sort=old)",
                        year,
                        max_year,
                    )
                    return collected
                book_url = await self._extract_url(item)
                if book_url is None:
                    continue
                collected.append(book_url)
                if len(collected) >= limit:
                    return collected

            if parsed_year_count == 0:
                raise SearchResultsParseError(
                    f"Search page {page_num} for query={query!r} has {len(items)} "
                    "book result(s), but none matched the expected "
                    "'First published in <year>' details text. OpenLibrary may "
                    "have changed the result wording or markup."
                )

            page_num += 1
            if page_num > total_pages:
                logger.info("reached last page (%d), stopping", total_pages)
                break

        return collected


def build_title_search_url(base_url: str, query: str, page_num: int = 1) -> str:
    """Build a UI search URL constrained to OpenLibrary's title field.

    OpenLibrary supports query syntax inside `q`; `title: "Dune"` must
    be URL-encoded as `title%3A+%22Dune%22`. Use `quote_plus` here so
    spaces, quotes, and punctuation are encoded consistently.
    """
    title_query = f'title: "{query}"'
    encoded_query = quote_plus(title_query)
    return (
        f"{base_url}{SearchPage.SEARCH_PATH}"
        f"?q={encoded_query}&mode=everything&sort=old&page={page_num}"
    )


async def search_books_by_title_under_year(
    page: Page,
    query: str,
    max_year: int,
    limit: int = 5,
    *,
    base_url: str = DEFAULT_BASE_URL,
) -> list[str]:
    """Standalone wrapper for function 1 from the assignment spec.

    The implementation stays in `SearchPage` so selectors and page
    behavior remain inside the Page Object layer. The explicit `page`
    argument follows the executable sample from the PDF.
    """
    return await SearchPage(page, base_url).search_books_by_title_under_year(
        query,
        max_year,
        limit,
    )
