"""
This file contains the cart page
"""

from __future__ import annotations

import re

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage
from utils.price_parser import parse_items_total, parse_price


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Cart page")
class CartPage(BasePage):
    def __init__(self, page: Page, cart_url: str):
        super().__init__(page)
        self.cart_url = cart_url
        self.cart_icon = page.get_by_label(re.compile(r"(your shopping cart|expand cart)", re.I))
        self.item_total = page.get_by_test_id("ITEM_TOTAL")
        self.items_line = page.get_by_text(re.compile(r"Items \("))

    @allure.step("open the cart page")
    def open(self) -> None:
        self.logger.info("Open cart")
        try:
            self.click(self.cart_icon, timeout=4000)
            self.page.wait_for_load_state("domcontentloaded")
            self.dismiss_overlays()
            return
        except Exception:
            super().open(self.cart_url)

    @allure.step("read cart items total")
    def read_subtotal(self) -> float:
        self.logger.info("Read cart items total")
        locator = self.item_total if self.is_visible(self.item_total, timeout=5000) else self.items_line
        text = self.get_clean_text(locator.first)
        amount = parse_items_total(text)
        if amount is None:
            amount = parse_price(text)
        if amount is None:
            raise AssertionError("Could not read cart items total from the cart page")
        self.logger.info("Cart items total is %s", amount)
        return amount
