"""
This file contains the base page
"""

from playwright.sync_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError

from utils.logger import get_logger


class BasePage:
    DEFAULT_TIMEOUT = 10000

    def __init__(self, page: Page):
        self.page = page
        self.logger = get_logger(self.__class__.__name__)
        self.gdpr_accept = page.locator("#gdpr-banner-accept")
        self.onetrust_accept = page.locator("#onetrust-accept-btn-handler")
        self.stay_on_ebay_button = page.get_by_role("button", name="Stay on eBay.com")
        self.maybe_later_button = page.get_by_role("button", name="Maybe later")
        self.lightbox_close = page.locator(".lightbox-dialog__close")

    def open(self, url: str) -> None:
        self.logger.info(f"Open {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        self.dismiss_overlays()

    def click(self, element: Locator, timeout: int = DEFAULT_TIMEOUT, force: bool = False):
        try:
            self.logger.info(f"Click element: {element}")
            element.click(timeout=timeout, force=force)
        except Exception as error:
            self.logger.exception(f"Failed to click element: {element}")
            raise error

    def fill(self, element: Locator, text: str, timeout: int = DEFAULT_TIMEOUT):
        try:
            self.logger.info(f"Fill element: {element}")
            expect(element).to_be_visible(timeout=timeout)
            element.fill(text)
        except Exception as error:
            self.logger.exception(f"Failed to fill element: {element}")
            raise error

    def wait_visible(self, element: Locator, timeout: int = DEFAULT_TIMEOUT):
        try:
            self.logger.info(f"Wait visible: {element}")
            expect(element).to_be_visible(timeout=timeout)
        except Exception as error:
            self.logger.exception(f"Element was not visible: {element}")
            raise error

    def wait_hidden(self, element: Locator, timeout: int = DEFAULT_TIMEOUT):
        try:
            self.logger.info(f"Wait hidden: {element}")
            expect(element).to_be_hidden(timeout=timeout)
        except Exception as error:
            self.logger.exception(f"Element was not hidden: {element}")
            raise error

    def wait_enabled(self, element: Locator, timeout: int = DEFAULT_TIMEOUT):
        try:
            self.logger.info(f"Wait enabled: {element}")
            expect(element).to_be_enabled(timeout=timeout)
        except Exception as error:
            self.logger.exception(f"Element was not enabled: {element}")
            raise error

    def wait_text(self, element: Locator, text: str, timeout: int = DEFAULT_TIMEOUT):
        try:
            self.logger.info(f"Wait text '{text}' in element: {element}")
            expect(element).to_contain_text(text, timeout=timeout)
        except Exception as error:
            self.logger.exception(f"Text '{text}' was not found in element: {element}")
            raise error

    def get_clean_text(self, element: Locator) -> str:
        try:
            text = " ".join(element.inner_text().split())
            self.logger.info(f"Element text: {text}")
            return text
        except Exception as error:
            self.logger.exception(f"Failed to get text from element: {element}")
            raise error

    def select_dropdown_option(self, dropdown: Locator, option: str):
        try:
            self.logger.info(f"Select dropdown option: {option}")
            self.click(dropdown)
            self.click(self.page.get_by_role("option", name=option))
        except Exception as error:
            self.logger.exception(f"Failed to select dropdown option: {option}")
            raise error

    def shown(self, locator: Locator) -> bool:
        try:
            return locator.first.is_visible()
        except Exception:
            return False

    def is_visible(self, locator: Locator, timeout: int = 800) -> bool:
        try:
            locator.first.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def click_visible(self, locator: Locator, timeout: int = 1500) -> bool:
        try:
            locator.first.wait_for(state="visible", timeout=timeout)
            locator.first.click(timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def dismiss_overlays(self) -> None:
        for locator in (
            self.gdpr_accept,
            self.onetrust_accept,
            self.stay_on_ebay_button,
            self.maybe_later_button,
            self.lightbox_close,
        ):
            try:
                if locator.first.is_visible():
                    locator.first.click(timeout=400)
            except Exception:
                continue
