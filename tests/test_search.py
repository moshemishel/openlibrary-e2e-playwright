"""Tests for the search flow (function 1 from the spec).

These use the authenticated `page` fixture, not `anonymous_page`.
OpenLibrary's search endpoint is technically public, but anonymous
headless browsers are routinely redirected to a `/verify_human`
bot-detection page. A logged-in session passes through without the
challenge, and that matches the real usage scenario for the framework.

These are sanity tests for the function contract. Data-driven cases
(multiple queries with parametrize from a JSON file) will be added
later as part of the data-driven refactor.
"""

from typing import Any

from playwright.async_api import Page

from pages.search_page import SearchPage


async def test_search_returns_urls_under_max_year(
    page: Page, config: dict[str, Any]
) -> None:
    """Happy path: a known query returns at least one URL, capped by `limit`."""
    sp = SearchPage(page, config["base_url"])
    urls = await sp.search_books_by_title_under_year("Dune", 1980, limit=3)

    assert 0 < len(urls) <= 3, f"expected 1..3 URLs, got {len(urls)}"
    for u in urls:
        assert u.startswith(config["base_url"]), f"unexpected URL: {u}"


async def test_search_empty_when_no_results_under_year(
    page: Page, config: dict[str, Any]
) -> None:
    """No editions of Dune exist before year 1000 -- result must be empty.

    Exercises the `year > max_year` early-exit branch: with sort=old, the
    very first result with a parseable year is > 1000, so the loop
    returns the empty accumulator.
    """
    sp = SearchPage(page, config["base_url"])
    urls = await sp.search_books_by_title_under_year("Dune", 1000, limit=5)

    assert urls == []
