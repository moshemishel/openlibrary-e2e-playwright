"""Pytest fixtures for OpenLibrary E2E tests.

This file is where pytest finds the shared setup for the whole test session.
It does the following:

  1. Loads `.env` once, before any test or fixture runs.
  2. Loads `config/config.json` once per session.
  3. Starts a single browser per session.
  4. Performs a single login per session and captures the storage state
     in memory (`auth_storage_state`).
  5. Exposes two per-test page fixtures:
     - `anonymous_page` -- clean signed-out context (search, performance)
     - `page` -- clean context pre-loaded with the session cookie
       (reading list tests)

`.env` is loaded here -- not inside `config_loader` -- because the env vars
need to be in place before the loader, or any test, reads them.
"""

import json
import logging
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from playwright.async_api import Browser, Page, Playwright, async_playwright

from pages.login_page import LoginError, LoginPage
from utils.config_loader import get_credentials, load_config
from utils.performance import get_results as get_perf_results

# Load .env before any fixture runs. No effect if the file is missing.
load_dotenv()

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def config() -> dict[str, Any]:
    """The merged configuration dict, loaded once per test run."""
    cfg = load_config()
    logger.info("active config: %s", cfg)
    return cfg


@pytest_asyncio.fixture(scope="session")
async def playwright_instance() -> AsyncIterator[Playwright]:
    """The Playwright runtime. Started once, shut down at session end."""
    async with async_playwright() as p:
        yield p


@pytest_asyncio.fixture(scope="session")
async def browser(
    playwright_instance: Playwright, config: dict[str, Any]
) -> AsyncIterator[Browser]:
    """A single Chromium browser shared by every test in the session."""
    b = await playwright_instance.chromium.launch(
        headless=config["headless"],
        slow_mo=config["slow_mo"],
    )
    yield b
    await b.close()


@pytest_asyncio.fixture
async def anonymous_page(browser: Browser, config: dict[str, Any]) -> AsyncIterator[Page]:
    """A fresh signed-out page. New context per test for clean isolation."""
    context = await browser.new_context(viewport=config["viewport"])
    page = await context.new_page()
    yield page
    await context.close()


@pytest_asyncio.fixture(scope="session")
async def auth_storage_state(browser: Browser, config: dict[str, Any]) -> dict[str, Any]:
    """Login once per session, return the captured storage state.

    Skips dependent tests if credentials are missing or if login fails.
    The state stays in memory only -- never written to disk.
    """
    username, password = get_credentials()
    if not username or not password:
        pytest.skip(
            "OL_USERNAME / OL_PASSWORD not set in .env -- tests that need login are skipped"
        )

    context = await browser.new_context(viewport=config["viewport"])
    try:
        page = await context.new_page()
        login_page = LoginPage(page, config["base_url"])
        try:
            await login_page.login(username, password)
        except LoginError as e:
            pytest.skip(f"login failed: {e}")
        return await context.storage_state()
    finally:
        await context.close()


@pytest_asyncio.fixture
async def page(
    browser: Browser,
    config: dict[str, Any],
    auth_storage_state: dict[str, Any],
) -> AsyncIterator[Page]:
    """A fresh page with the session cookie pre-loaded. New context per test."""
    context = await browser.new_context(
        viewport=config["viewport"],
        storage_state=auth_storage_state,
    )
    page = await context.new_page()
    yield page
    await context.close()


# Performance report: aggregate every `measure_page_performance` call
# made during the run into one JSON file. Decision recorded in
# README -> "Decisions Made" -> "Performance report aggregation".
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Dump all perf measurements to performance_report.json at the project root."""
    results = get_perf_results()
    if not results:
        return
    report = {
        "runs": results,
        "summary": {
            "total": len(results),
            "breached": sum(1 for r in results if r["breached"]),
        },
    }
    report_path = Path(__file__).parent / "performance_report.json"
    report_path.write_text(json.dumps(report, indent=2))
    logger.info("wrote %d perf records to %s", len(results), report_path)
