"""Tests for the search flow (function 1 from the spec).

These use the authenticated `page` fixture, not `anonymous_page`.
OpenLibrary's search endpoint is technically public, but anonymous
headless browsers are routinely redirected to a `/verify_human`
bot-detection page. A logged-in session passes through without the
challenge, and that matches the real usage scenario for the framework.

The two explicit tests below are sanity baselines for the function
contract. `test_search_data_driven` adds the JSON-file-driven sweep
required for the Data-Driven grading item.
"""

from typing import Any

import pytest
from playwright.async_api import Page

from pages.search_page import SearchPage
from utils.data_loader import load_data

_SEARCH_CASES = load_data("search_cases.json")


async def test_search_returns_urls_under_max_year(page: Page, config: dict[str, Any]) -> None:
    """Happy path: a known query returns at least one URL, capped by `limit`."""
    sp = SearchPage(page, config["base_url"])
    urls = await sp.search_books_by_title_under_year("Dune", 1980, limit=3)

    assert 0 < len(urls) <= 3, f"expected 1..3 URLs, got {len(urls)}"
    for u in urls:
        assert u.startswith(config["base_url"]), f"unexpected URL: {u}"


async def test_search_empty_when_no_results_under_year(page: Page, config: dict[str, Any]) -> None:
    """No editions of Dune exist before year 1000 -- result must be empty.

    Exercises the `year > max_year` early-exit branch: with sort=old, the
    very first result with a parseable year is > 1000, so the loop
    returns the empty accumulator.
    """
    sp = SearchPage(page, config["base_url"])
    urls = await sp.search_books_by_title_under_year("Dune", 1000, limit=5)

    assert urls == []


@pytest.mark.parametrize(
    "case",
    _SEARCH_CASES,
    ids=[c["description"] for c in _SEARCH_CASES],
)
async def test_search_data_driven(case: dict[str, Any], page: Page, config: dict[str, Any]) -> None:
    """Cases from data/search_cases.json.

    Each case asserts the URL count falls inside expected_min..expected_max
    (expected_max defaults to `limit`), and every URL is absolute under
    base_url. A case can pin the result to exactly empty by setting both
    expected_min_count and expected_max_count to 0.
    """
    sp = SearchPage(page, config["base_url"])
    urls = await sp.search_books_by_title_under_year(
        case["query"], case["max_year"], limit=case["limit"]
    )
    min_count = case.get("expected_min_count", 0)
    max_count = case.get("expected_max_count", case["limit"])
    assert min_count <= len(urls) <= max_count, (
        f"expected {min_count}..{max_count} URLs, got {len(urls)}"
    )
    for u in urls:
        assert u.startswith(config["base_url"]), f"unexpected URL: {u}"
