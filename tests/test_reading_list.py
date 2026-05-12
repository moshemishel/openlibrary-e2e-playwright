"""Tests for the reading list flow (function 2 from the spec).

Uses the `page` fixture from `conftest.py`, which is pre-authenticated
via the session-scoped `auth_storage_state`.

Stateful caveat: there is no cleanup between runs yet. Tests rely on
the idempotency of `BookPage.add_to_shelf` -- adding to the same
shelf twice is a no-op. A second run will find the book already on
a shelf and pass without doing anything.
"""

import random
from typing import Any

from playwright.async_api import Page

from pages.book_page import BookPage

# Dune by Frank Herbert -- stable OpenLibrary work used as a test fixture.
DUNE_PATH = "/works/OL893415W"


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
