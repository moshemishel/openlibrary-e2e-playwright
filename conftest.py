"""Pytest fixtures for OpenLibrary E2E tests.

  This file is where pytest finds the shared setup for the whole test session.                                                                                                                  
  It does three things:

    1. Loads `.env` once, before any test or fixture runs.
    2. Loads `config/config.json` once per session.
    3. Starts a single browser per session and gives each test a fresh,                                                                                                                         
       signed-out browser context (`anonymous_page`).

  Auth fixtures (a logged-in `page`) will be added later, before function 2.

  `.env` is loaded here -- not inside `config_loader` -- because the env vars                                                                                                                   
  need to be in place before the loader, or any test, reads them.
  """
  
import logging
from collections.abc import AsyncIterator
from typing import Any

import pytest                                                                                                                                                                                 
import pytest_asyncio
from dotenv import load_dotenv
from playwright.async_api import Browser, Page, Playwright, async_playwright

from utils.config_loader import load_config

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
async def anonymous_page(
    browser: Browser, config: dict[str, Any]
) -> AsyncIterator[Page]:
    """A fresh signed-out page. New context per test for clean isolation."""
    context = await browser.new_context(viewport=config["viewport"])
    page = await context.new_page()
    yield page
    await context.close()