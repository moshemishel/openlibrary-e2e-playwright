"""Page Object for OpenLibrary's login page.

Used once per pytest session by the `auth_storage_state` fixture to log
in and capture the session cookie for reuse across tests.
"""

import logging
from urllib.parse import urljoin

from playwright.async_api import Page
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

# Hardcoded: login is one-time setup. If 10s is not enough something
# deeper is wrong (network, page changed, captcha). The fixture turns
# this timeout into a `pytest.skip` with the reason.
LOGIN_SUCCESS_TIMEOUT_MS = 10_000


class LoginError(Exception):
    """Raised when the login flow does not complete successfully."""


class LoginPage:
    LOGIN_PATH = "/account/login"
    FORM = "form.login"
    ERROR_BOX = "div.error.ol-signup-form__info-box"

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url

    async def goto(self) -> None:
        await self.page.goto(urljoin(self.base_url, self.LOGIN_PATH))

    async def login(self, username: str, password: str) -> None:
        """Fill the form, submit, and confirm the redirect happened.

        Success: URL leaves `/account/login`.
        Failure: timeout fires AND the error box is visible.
        Credentials are never logged.
        """
        await self.goto()

        form = self.page.locator(self.FORM)
        await form.get_by_label("Email").fill(username)
        await form.get_by_label("Password").fill(password)
        await form.get_by_role("button", name="Log In").click()

        try:
            await self.page.wait_for_url(
                lambda url: self.LOGIN_PATH not in url,
                timeout=LOGIN_SUCCESS_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            error_box = self.page.locator(self.ERROR_BOX)
            if await error_box.count() > 0:
                msg = (await error_box.inner_text()).strip()
                raise LoginError(msg) from None
            raise LoginError(
                "login submit did not redirect and no error message was shown"
            ) from None

        logger.info("login successful")
