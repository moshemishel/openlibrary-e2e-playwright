"""End-to-end flow test: chain functions 1 -> 2 -> 3 -> 4 in one scenario.

Headline scenario from the spec:
    1. Search for books published under a target year (function 1).
    2. Add the returned URLs to a random shelf each (function 2).
    3. Assert the reading-list count grew by 0..len(urls) (function 3).
    4. Measure performance of the reading-list landing page (function 4).

Uses the authenticated `page` fixture -- steps 2/3 require login.

Why a delta-based count assertion: function 2 is idempotent. If the
test ran before, the books are already on a shelf and the count
delta is 0. If they were not, the delta is len(urls). Both are
correct outcomes, so the test asserts the safe range and not a
specific value. This is what lets the test pass on repeat runs
without a cleanup step.
"""

import random
from typing import Any

from playwright.async_api import Page

from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from pages.search_page import SearchPage
from utils.performance import measure_page_performance


async def test_e2e_search_add_assert_measure(page: Page, config: dict[str, Any]) -> None:
    """Chain all four spec functions in a single test."""
    base_url = config["base_url"]
    # Seeded so the random shelf choice in function 2 is reproducible.
    random.seed(42)

    # ----- Step 1: function 1 -- search -----
    sp = SearchPage(page, base_url)
    urls = await sp.search_books_by_title_under_year("Dune", 1980, limit=2)
    assert urls, "search returned no urls -- E2E chain cannot proceed"

    # Snapshot the reading-list count BEFORE the add so we can
    # compute a delta in step 3. Must goto() once to refresh the page.
    rlp = ReadingListPage(page, base_url)
    await rlp.goto()
    before = await rlp.total_count()

    # ----- Step 2: function 2 -- add to random shelves -----
    book = BookPage(page, base_url)
    await book.add_books_to_reading_list(urls)

    # Function 2 contract: each book ends on WTR or AR.
    for url in urls:
        await book.goto(url)
        assert await book.current_shelf() in {"want_to_read", "already_read"}, (
            f"book {url} not on WTR/AR after add"
        )

    # ----- Step 3: function 3 -- assert count -----
    await rlp.goto()
    after = await rlp.total_count()
    delta = after - before
    assert 0 <= delta <= len(urls), (
        f"reading-list delta out of range: "
        f"before={before} after={after} delta={delta} len(urls)={len(urls)}"
    )
    # Direct exercise of function 3 with the observed post-add count.
    await rlp.assert_reading_list_count(after)

    # ----- Step 4: function 4 -- measure perf of /account/books -----
    record = await measure_page_performance(
        page,
        base_url + ReadingListPage.LANDING_PATH,
        threshold_ms=config["thresholds"]["reading_list"],
    )
    # E2E checks the contract, not the SLO: we don't pin `breached`,
    # just verify the shape. The dedicated perf tests already cover
    # the breach-flag relationship.
    for key in ("load_time_ms", "dom_content_loaded_ms", "first_paint_ms"):
        assert key in record, f"perf record missing key: {key}"
    assert isinstance(record["breached"], bool)
