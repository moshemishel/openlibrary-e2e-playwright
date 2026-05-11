"""Smoke test for the authentication flow.

Verifies the full auth chain works end-to-end:
  - `LoginPage.login()` succeeded (run inside `auth_storage_state`)
  - `auth_storage_state` captured the session cookie
  - `page` injected the storage state into a fresh context

Run only this file:
    pytest tests/test_auth_smoke.py -v
"""

from typing import Any

from playwright.async_api import Page


async def test_logged_in_context_reaches_account_books(
    page: Page, config: dict[str, Any]
) -> None:
    """`/account/books` requires login; logged-out users get redirected."""
    await page.goto(f"{config['base_url']}/account/books")
    assert "/account/login" not in page.url, (
        f"expected to stay on /account/books but landed on {page.url} -- "
        "the auth fixture is not actually logged in"
    )
