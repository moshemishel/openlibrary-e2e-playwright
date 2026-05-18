"""End-to-end flow test: chain functions 1 -> 2 -> 3 -> 4 in one scenario.

Headline scenario from the spec:
    1. Search for books published under a target year (function 1).
    2. Add the returned URLs to a random shelf each (function 2).
    3. Assert the reading-list count grew by 0..len(urls) (function 3).
    4. Measure performance of search, book detail, and reading list pages (function 4).

Uses the authenticated `page` fixture -- steps 2/3 require login.

Why a delta-based count assertion: function 2 is idempotent. If the
test ran before, the books are already on a shelf and the count
delta is 0. If they were not, the delta is len(urls). Both are
correct outcomes, so the test asserts the safe range and not a
specific value. This is what lets the test pass on repeat runs
without a cleanup step.
"""

import logging
import random
from typing import Any

from playwright.async_api import Page

from pages.book_page import BookPage, add_books_to_reading_list
from pages.reading_list_page import ReadingListPage, assert_reading_list_count
from pages.search_page import build_title_search_url, search_books_by_title_under_year
from utils.performance import measure_page_performance

logger = logging.getLogger(__name__)


async def test_e2e_search_add_assert_measure(
    page: Page, config: dict[str, Any], record_property: Any, caplog: Any
) -> None:
    """Chain all four spec functions in a single test."""
    caplog.set_level(logging.INFO, logger=__name__)
    base_url = config["base_url"]
    # Seeded so the random shelf choice in function 2 is reproducible.
    random.seed(42)

    # ----- Step 1: function 1 -- search -----
    urls = await search_books_by_title_under_year(
        page,
        "Dune",
        1980,
        limit=2,
        base_url=base_url,
    )
    assert urls, "search returned no urls -- E2E chain cannot proceed"

    # Snapshot the reading-list count BEFORE the add so we can
    # compute a delta in step 3. Must goto() once to refresh the page.
    rlp = ReadingListPage(page, base_url)
    await rlp.goto()
    before = await rlp.total_count()

    # ----- Step 2: function 2 -- add to random shelves -----
    book = BookPage(page, base_url)
    pre_add_shelves: list[tuple[str, str | None]] = []
    for url in urls:
        await book.goto(url)
        pre_add_shelves.append((url, await book.current_shelf()))

    already_on_shelf = sum(shelf is not None for _, shelf in pre_add_shelves)
    logger.info(
        "before add: %d out of %d selected book URL(s) were already on a reading shelf",
        already_on_shelf,
        len(urls),
    )
    record_property("selected_books_already_on_shelf_before_add", already_on_shelf)
    record_property("selected_book_url_count", len(urls))

    await add_books_to_reading_list(page, urls, base_url=base_url)

    # Function 2 contract: each book ends on WTR or AR.
    verified_after_add = 0
    for url in urls:
        await book.goto(url)
        current_shelf = await book.current_shelf()
        assert current_shelf in {"want_to_read", "already_read"}, (
            f"book {url} not on WTR/AR after add"
        )
        verified_after_add += 1

    logger.info(
        "after add: all %d selected book URL(s) verified on Want to Read or Already Read",
        verified_after_add,
    )
    record_property("selected_books_verified_after_add", verified_after_add)

    # ----- Step 3: function 3 -- assert count -----
    await rlp.goto()
    after = await rlp.total_count()
    delta = after - before
    logger.info(
        "reading-list count delta after add: %d (before=%d after=%d selected=%d "
        "already_on_shelf_before=%d)",
        delta,
        before,
        after,
        len(urls),
        already_on_shelf,
    )
    record_property("reading_list_count_before_add", before)
    record_property("reading_list_count_after_add", after)
    record_property("reading_list_count_delta_after_add", delta)
    assert 0 <= delta <= len(urls), (
        f"reading-list delta out of range: "
        f"before={before} after={after} delta={delta} len(urls)={len(urls)}"
    )
    # Direct exercise of function 3 with the observed post-add count.
    await assert_reading_list_count(page, after, base_url=base_url)

    # ----- Step 4: function 4 -- measure perf of all required page types -----
    records = [
        await measure_page_performance(
            page,
            build_title_search_url(base_url, "Dune"),
            threshold_ms=config["thresholds"]["search"],
        ),
        await measure_page_performance(
            page,
            urls[0],
            threshold_ms=config["thresholds"]["book"],
        ),
        await measure_page_performance(
            page,
            base_url + ReadingListPage.LANDING_PATH,
            threshold_ms=config["thresholds"]["reading_list"],
        ),
    ]
    # E2E checks the contract, not the SLO: we don't pin `breached`,
    # just verify the shape. The dedicated perf tests already cover
    # the breach-flag relationship.
    for record in records:
        for key in ("load_time_ms", "dom_content_loaded_ms", "first_paint_ms"):
            assert key in record, f"perf record missing key: {key}"
        assert isinstance(record["breached"], bool)
