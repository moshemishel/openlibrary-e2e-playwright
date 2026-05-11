"""Page Object for OpenLibrary's search results page."""
                                                                                                                                                                                                
import logging
import re
from urllib.parse import quote_plus, urljoin

from playwright.async_api import Locator, Page

logger = logging.getLogger(__name__)

YEAR_REGEX = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")                                                                                                                                        


class SearchPage:
    """OpenLibrary search results page.

    Holds the Playwright `page` and the `base_url` as state, so the public                                                                                                                    
    function signature does not need to receive them (matches the spec).
    """   

    SEARCH_PATH = "/search"
    RESULT_ITEM = 'li[itemtype$="Book"]'
    RESULT_LINK = '[itemprop="name"] a[itemprop="url"]'
    RESULT_DETAILS_SPAN = ".resultDetails span"
    PAGINATION = "ol-pagination"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    def _build_search_url(self, query: str, page_num: int) -> str:                                                                                                                            
        # sort=old returns oldest first -- lets us stop early when year > max_year.
        return (
            f"{self.base_url}{self.SEARCH_PATH}"
            f"?q={quote_plus(query)}&mode=everything&sort=old&page={page_num}"                                                                                                                
        )

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

    async def _extract_year(self, item: Locator) -> int | None:
        """Pull a 4-digit year (1000-2099) out of the result's details text.                                                                                                                  

        Returns None when no year is found. A result may legitimately have
        no year (a generic edition entry, for example).
        """
        year_span = (
            item.locator(self.RESULT_DETAILS_SPAN)
            .filter(has_text=YEAR_REGEX)
            .first
        ) 
        if await year_span.count() == 0:                                                                                                                                                      
            return None
        text = await year_span.inner_text()
        match = YEAR_REGEX.search(text)
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
            await self.page.goto(url)

            if total_pages is None:
                total_pages = await self._get_total_pages()
                logger.info("total pages for query=%r: %d", query, total_pages)

            items = await self.page.locator(self.RESULT_ITEM).all()                                                                                                                           
            if not items:
                logger.info("no results on page %d, stopping", page_num)
                break

            for item in items:
                year = await self._extract_year(item)
                if year is None:
                    continue
                if year > max_year:
                    logger.info(
                        "year %d > max_year %d, stopping early (sort=old)",                                                                                                                   
                        year, max_year,
                    )
                    return collected
                book_url = await self._extract_url(item)
                if book_url is None:
                    continue
                collected.append(book_url)                                                                                                                                                    
                if len(collected) >= limit:
                    return collected

            page_num += 1
            if page_num > total_pages:
                logger.info("reached last page (%d), stopping", total_pages)
                break

        return collected
    