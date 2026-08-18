"""
This file contains the login page
"""

from __future__ import annotations

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Login page")
class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.sign_in_link = page.get_by_role("link", name="Sign in")
        self.user_input = page.locator("#userid")
        self.continue_button = page.locator("#signin-continue-btn")
        self.password_input = page.locator("#pass")
        self.submit_button = page.locator("#sgnBt")
        self.captcha_frame = page.locator("iframe[src*='captcha']")
        self.challenge_frame = page.locator("iframe[title*='challenge' i]")
        self.captcha = page.locator("#captcha")
        self.interruption_text = page.get_by_text("Pardon Our Interruption")
        self.search_box = page.locator("#gh-ac")
        self.search_by_placeholder = page.get_by_placeholder("Search for anything")
        self.go_to_homepage_button = page.get_by_role("button", name="Go to homepage")
        self.go_to_homepage_link = page.get_by_role("link", name="Go to homepage")
        self.ebay_homepage_link = page.get_by_role("link", name="eBay Homepage")
        self.something_went_wrong = page.get_by_text("Something went wrong")
        self.sorry_text = page.get_by_text("SORRY")
        self.country_field = page.get_by_label("Country")
        self.united_states_option = page.get_by_role("option", name="United States")
        self.zip_input = page.get_by_label("ZIP", exact=False)
        self.ship_to_done = page.get_by_role("button", name="Done")

    @allure.step("authenticate as guest")
    def authenticate_guest(self, base_url: str) -> None:
        self.logger.info("Authenticate as guest")
        for _ in range(3):
            self.open(base_url)
            if self.is_visible(self.search_box, timeout=10000) or self.is_visible(
                self.search_by_placeholder, timeout=2000
            ):
                self._set_ship_to_united_states()
                return
            if self.shown(self.something_went_wrong) or self.shown(self.sorry_text):
                self.click_visible(self.go_to_homepage_button, timeout=1500) or self.click_visible(
                    self.go_to_homepage_link, timeout=800
                ) or self.click_visible(self.ebay_homepage_link, timeout=800)
        self.page.screenshot(path="reports/screenshots/auth-guest-failed.png")
        raise AssertionError("Guest session did not land on an eBay page with search")

    @allure.step("authenticate as user")
    def authenticate_user(self, base_url: str, username: str, password: str) -> None:
        self.logger.info("Authenticate as user")
        self.open(base_url)
        self.click(self.sign_in_link)
        self.page.wait_for_load_state("domcontentloaded")
        if self._challenge_visible():
            self.authenticate_guest(base_url)
            return
        self.fill(self.user_input, username)
        self.click(self.continue_button)
        if self._challenge_visible():
            self.authenticate_guest(base_url)
            return
        self.fill(self.password_input, password)
        self.click(self.submit_button)
        self.page.wait_for_load_state("domcontentloaded")
        if self._challenge_visible():
            self.authenticate_guest(base_url)

    @allure.step("set ship to United States")
    def _set_ship_to_united_states(self) -> None:
        self.logger.info("Complete ship-to form if it is already open")
        country_open = False
        zip_open = False
        try:
            country_open = self.country_field.first.is_visible()
        except Exception:
            pass
        try:
            zip_open = self.zip_input.first.is_visible()
        except Exception:
            pass
        if not country_open and not zip_open:
            return
        try:
            self.select_dropdown_option(self.country_field.first, "United States")
        except Exception:
            try:
                self.country_field.first.select_option(label="United States")
            except Exception:
                pass
        if self.shown(self.zip_input):
            self.fill(self.zip_input.first, "10001")
        self.click_visible(self.ship_to_done, timeout=3000)
        self.page.wait_for_load_state("domcontentloaded")
        self.dismiss_overlays()

    @allure.step("check if challenge is visible")
    def _challenge_visible(self) -> bool:
        self.logger.info("Check if challenge is visible")
        return (
            self.shown(self.captcha_frame)
            or self.shown(self.challenge_frame)
            or self.shown(self.captcha)
            or self.shown(self.interruption_text)
        )
