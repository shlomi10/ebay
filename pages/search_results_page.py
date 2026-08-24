"""
This file contains the search results page
"""

from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import allure
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage
from utils.price_parser import parse_price
from utils.url_tools import canonical_item_url


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Search results page")
class SearchResultsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.results_list = page.locator("ul.srp-results, .srp-river-results")
        self.result_cards = page.locator(
            "xpath=//li[contains(@class,'s-card')][.//a[contains(@href,'/itm/')]]"
        )
        self.max_price_input = page.get_by_label("Maximum", exact=False)
        self.min_price_input = page.get_by_label("Minimum", exact=False)
        self.price_submit = page.locator("button.x-textrange__button")
        self.buy_it_now_filter = page.get_by_label("Buy It Now")
        self.next_page = page.locator("a.pagination__next")

    @allure.step("wait for search results")
    def wait_for_results(self) -> None:
        self.logger.info("Wait for search results")
        if "splashui/challenge" in self.page.url:
            raise AssertionError("ebay showed a bot-challenge page instead of search results")
        try:
            self.wait_visible(self.results_list.first, timeout=8000)
        except (PlaywrightTimeoutError, AssertionError):
            self.wait_visible(self.result_cards.first, timeout=8000)
        self.dismiss_overlays()

    @allure.step("apply price and format filters")
    def apply_price_and_format_filters(
        self, max_price: float, buy_it_now: bool, free_shipping: bool = True
    ) -> None:
        self.logger.info("Apply filters max_price=%s buy_it_now=%s free_shipping=%s", max_price, buy_it_now, free_shipping)
        self.wait_for_results()
        self._apply_ui_price_filter(max_price)
        self._apply_url_price_filter(max_price, buy_it_now, free_shipping)

    @allure.step("collect item urls under price {max_price}")
    def collect_urls_under_price(self, max_price: float, remaining: int, base_url: str, seen: set[str]) -> list[str]:
        collected: list[str] = []
        count = self.result_cards.count()
        self.logger.info("Found %s result cards", count)
        for index in range(count):
            if len(collected) >= remaining:
                break
            card = self.result_cards.nth(index)
            url = self._card_url_if_matches(card, max_price, base_url, seen)
            if url:
                seen.add(url)
                collected.append(url)
        return collected

    @allure.step("go to next search page")
    def go_to_next_page(self) -> bool:
        self.logger.info("Go to next search page")
        try:
            if self.next_page.count() == 0:
                return False
            aria_disabled = (self.next_page.first.get_attribute("aria-disabled") or "").lower()
            class_name = self.next_page.first.get_attribute("class") or ""
            if aria_disabled == "true" or "disabled" in class_name:
                return False
            self.click(self.next_page.first, timeout=3000)
            self.page.wait_for_load_state("domcontentloaded")
            self.wait_for_results()
            return True
        except PlaywrightTimeoutError:
            self.logger.info("Next page is not available")
            return False

    @allure.step("apply UI price filter {max_price}")
    def _apply_ui_price_filter(self, max_price: float) -> bool:
        self.logger.info("Apply UI price filter %s", max_price)
        if not self.shown(self.max_price_input):
            return False
        self.fill(self.max_price_input.first, str(int(max_price)))
        if self.shown(self.min_price_input):
            self.fill(self.min_price_input.first, "0")
        if not self.click_visible(self.price_submit, timeout=800):
            self.max_price_input.first.press("Enter")
        return True

    @allure.step("apply URL price filter {max_price}")
    def _apply_url_price_filter(self, max_price: float, buy_it_now: bool, free_shipping: bool) -> None:
        self.logger.info("Apply URL price filter %s", max_price)
        parsed = urlparse(self.page.url)
        params = dict(parse_qsl(parsed.query, keep_blank_values=True))
        params["_udhi"] = str(int(max_price))
        params["_ipg"] = params.get("_ipg", "60")
        if buy_it_now:
            params["LH_BIN"] = "1"
        if free_shipping:
            params["LH_FS"] = "1"
        next_url = urlunparse(parsed._replace(query=urlencode(params)))
        self.open(next_url)
        self.wait_for_results()

    @allure.step("get card title locator")
    def _card_title(self, card: Locator) -> Locator:
        return card.locator(".s-card__title")

    @allure.step("get card price locator")
    def _card_price(self, card: Locator) -> Locator:
        return card.locator(".s-card__price")

    @allure.step("get card link locator")
    def _card_link(self, card: Locator) -> Locator:
        return card.locator("a[href*='/itm/']")

    @allure.step("match card url under price")
    def _card_url_if_matches(
        self, card: Locator, max_price: float, base_url: str, seen: set[str]
    ) -> str | None:
        try:
            title = ""
            title_loc = self._card_title(card).first
            if title_loc.count() > 0:
                title = (title_loc.inner_text(timeout=800) or "").strip()
            if "shop on ebay" in title.lower():
                return None
            price_loc = self._card_price(card).first
            if price_loc.count() == 0:
                return None
            price = parse_price(price_loc.inner_text(timeout=800))
            if price is None or price > max_price:
                return None
            link = self._card_link(card).first
            if link.count() == 0:
                return None
            url = canonical_item_url(link.get_attribute("href"), base_url)
            if not url or url in seen:
                return None
            return url
        except PlaywrightTimeoutError:
            return None
