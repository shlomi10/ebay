"""
This file contains the item page
"""

from __future__ import annotations

import random

import allure
from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


@allure.severity(allure.severity_level.CRITICAL)
@allure.story("Item page")
class ItemPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.add_to_cart_button = page.locator("#atcBtn_btn_1")
        self.add_to_cart_by_name = page.get_by_role("button", name="Add to cart")
        self.msku = page.locator(".x-msku, .x-msku-evo")
        self.variant_selects = self.msku.locator("select")
        self.msku_listbox_trigger = page.locator("button.listbox-button__control")
        self.listbox_options = page.locator(
            ".listbox-button--expanded [role='option'], .listbox-button--expanded .listbox__option"
        )
        self.msku_swatches = self.msku.locator("button[aria-label]:not(.listbox-button__control)")
        self.please_select = page.get_by_text("Please select")
        self.added_to_cart = page.get_by_text("added to cart")
        self.go_to_cart = page.get_by_role("link", name="Go to cart")
        self.see_in_cart = page.get_by_role("link", name="See in cart")
        self.close_confirmation = page.get_by_role("dialog").get_by_role("button", name="Close")
        self.continue_shopping = page.get_by_role("button", name="Continue shopping")

    @allure.step("add item to cart")
    def add_to_cart(self) -> None:
        self._select_variants()
        if not self._click_add_to_cart():
            raise AssertionError("Add to cart control was not found or not clickable")
        if self.is_visible(self.please_select, timeout=600):
            self._select_variants()
            self._click_add_to_cart()
        if self.shown(self.please_select):
            raise AssertionError("Required item variants were not selected")
        confirmation = self.added_to_cart.or_(self.go_to_cart).or_(self.see_in_cart)
        if not self.is_visible(confirmation, timeout=5000):
            raise AssertionError("Item was not confirmed as added to cart")
        self.click_visible(self.close_confirmation, timeout=800) or self.click_visible(
            self.continue_shopping, timeout=600
        )

    def _click_add_to_cart(self) -> bool:
        for locator in (self.add_to_cart_button, self.add_to_cart_by_name):
            try:
                locator.first.scroll_into_view_if_needed(timeout=2000)
                locator.first.click(timeout=2500)
                return True
            except PlaywrightTimeoutError:
                continue
        return False

    def _select_variants(self) -> None:
        self._select_native_dropdowns()
        self._select_listboxes()
        if self.msku_listbox_trigger.count() == 0:
            visible = [s for s in self.msku_swatches.all() if s.is_visible() and s.is_enabled()]
            if visible:
                try:
                    random.choice(visible).click(timeout=1500)
                except PlaywrightTimeoutError:
                    pass
        self.page.keyboard.press("Escape")

    def _select_native_dropdowns(self) -> None:
        for select in self.variant_selects.all():
            if not select.is_visible():
                continue
            values = [
                option.get_attribute("value") or ""
                for option in select.locator("option:not([disabled])").all()
                if not self._is_placeholder(option.inner_text() or "")
                and (option.get_attribute("value") or "") not in {"", "-1", "default"}
            ]
            if not values:
                continue
            try:
                select.select_option("1" if "1" in values else random.choice(values), timeout=5000)
            except PlaywrightTimeoutError:
                continue

    def _select_listboxes(self) -> None:
        for _ in range(8):
            pending: list[Locator] = []
            for trigger in self.msku_listbox_trigger.all():
                try:
                    if trigger.is_visible() and self._is_placeholder(trigger.inner_text() or ""):
                        pending.append(trigger)
                except PlaywrightTimeoutError:
                    continue
            if not pending:
                return
            try:
                pending[0].scroll_into_view_if_needed(timeout=3000)
                self.click(pending[0], timeout=3000)
                option = self._usable_option()
                if option is None:
                    self.page.keyboard.press("Escape")
                    return
                self.click(option, timeout=2000)
            except PlaywrightTimeoutError:
                self.page.keyboard.press("Escape")
                return

    def _usable_option(self) -> Locator | None:
        self.listbox_options.first.wait_for(state="visible", timeout=4000)
        enabled: list[Locator] = []
        for option in self.listbox_options.all():
            if not option.is_visible() or self._is_placeholder(option.inner_text() or ""):
                continue
            if (option.get_attribute("aria-disabled") or "").lower() == "true":
                continue
            if (option.inner_text() or "").strip() == "1":
                return option
            enabled.append(option)
        return random.choice(enabled) if enabled else None

    def _is_placeholder(self, text: str) -> bool:
        text = text.strip().lower()
        return (not text) or "select" in text or "please" in text or text.startswith("-")
