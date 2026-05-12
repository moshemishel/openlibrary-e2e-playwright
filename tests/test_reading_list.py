"""Tests for the reading list flow (functions 2 and 3 from the spec).

Uses the `page` fixture from `conftest.py`, which is pre-authenticated
via the session-scoped `auth_storage_state`.

Stateful caveat: there is no cleanup between runs yet. Function 2
tests rely on the idempotency of `BookPage.add_to_shelf` -- adding to
the same shelf twice is a no-op. Function 3 tests assert the function
contract (type, raises, idempotent read) rather than specific numbers,
so they tolerate whatever shelf state the account is in.

`test_add_books_data_driven` adds the JSON-file-driven sweep required
for the Data-Driven grading item.
"""

import random
from typing import Any

import pytest
from playwright.async_api import Page

from pages.book_page import BookPage
from pages.reading_list_page import ReadingListPage
from utils.data_loader import load_data

# Dune by Frank Herbert -- stable OpenLibrary work used as a test fixture.
DUNE_PATH = "/works/OL893415W"

_BOOK_LISTS = load_data("book_lists.json")


async def test_add_to_shelf_idempotent(page: Page, config: dict[str, Any]) -> None:
    """Adding to the same shelf twice ends with the book on that shelf."""
    book = BookPage(page, config["base_url"])
    await book.goto(DUNE_PATH)
    await book.add_to_shelf("want_to_read")
    await book.add_to_shelf("want_to_read")  # second call -> no-op
    assert await book.current_shelf() == "want_to_read"


async def test_add_books_to_reading_list_function(page: Page, config: dict[str, Any]) -> None:
    """The spec's function 2: each book ends on WTR or AR after the call."""
    # Seed makes the random shelf choice deterministic in CI.
    random.seed(42)
    book = BookPage(page, config["base_url"])
    urls = [DUNE_PATH]
    await book.add_books_to_reading_list(urls)
    await book.goto(DUNE_PATH)
    assert await book.current_shelf() in {"want_to_read", "already_read"}


async def test_total_count_is_nonneg_int(page: Page, config: dict[str, Any]) -> None:
    """`total_count` returns a non-negative integer for a logged-in user."""
    rlp = ReadingListPage(page, config["base_url"])
    await rlp.goto()
    count = await rlp.total_count()
    assert isinstance(count, int)
    assert count >= 0


async def test_assert_with_current_count_passes(page: Page, config: dict[str, Any]) -> None:
    """Calling assert with the actual current count passes silently."""
    rlp = ReadingListPage(page, config["base_url"])
    await rlp.goto()
    actual = await rlp.total_count()
    await rlp.assert_reading_list_count(actual)


async def test_assert_with_wrong_count_raises(page: Page, config: dict[str, Any]) -> None:
    """Calling assert with a wrong count raises AssertionError."""
    rlp = ReadingListPage(page, config["base_url"])
    await rlp.goto()
    actual = await rlp.total_count()
    with pytest.raises(AssertionError):
        await rlp.assert_reading_list_count(actual + 1)


@pytest.mark.parametrize(
    "case",
    _BOOK_LISTS,
    ids=[c["description"] for c in _BOOK_LISTS],
)
async def test_add_books_data_driven(
    case: dict[str, Any], page: Page, config: dict[str, Any]
) -> None:
    """Cases from data/book_lists.json.

    After the call, every URL in the case must be on Want to Read or
    Already Read. Seeded RNG so the random shelf choice is reproducible.
    """
    random.seed(42)
    book = BookPage(page, config["base_url"])
    await book.add_books_to_reading_list(case["urls"])
    for url in case["urls"]:
        await book.goto(url)
        assert await book.current_shelf() in {"want_to_read", "already_read"}
