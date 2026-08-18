"""
This file contains the homepage
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Home page")
class HomePage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.search_box = page.locator("#gh-ac")
        self.search_by_placeholder = page.get_by_placeholder("Search for anything")
        self.search_button = page.locator("#gh-btn")

    @allure.step("search for {query}")
    def search(self, query: str, base_url: str | None = None) -> None:
        self.logger.info(f"Search for {query}")
        box = self.search_box if self.shown(self.search_box) else self.search_by_placeholder
        if not self.shown(box):
            if not base_url:
                raise AssertionError("Search input was not found on the home page")
            self.open(base_url)
            box = self.search_box if self.shown(self.search_box) else self.search_by_placeholder
        self.click(box)
        self.fill(box, query)
        box.press("Enter")
        try:
            self.page.wait_for_url("**/sch/**", timeout=8000)
        except PlaywrightTimeoutError:
            self.logger.info("Search did not navigate to results url")
        self.dismiss_overlays()
