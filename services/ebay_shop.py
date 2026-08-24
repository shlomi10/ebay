from __future__ import annotations

import allure
from playwright.sync_api import Error as PlaywrightError

from config.settings import Settings
from pages.item_page import ItemPage
from utils.logger import get_logger
from utils.reporting import attach_trace, save_screenshot


class EbayShop:
    def __init__(self, pages, settings: Settings) -> None:
        self.page = pages.page
        self.settings = settings
        self.logger = get_logger(self.__class__.__name__)
        self.home = pages.home_page
        self.login = pages.login_page
        self.search_results = pages.search_results_page
        self.cart = pages.cart_page

    @allure.step("Authenticate")
    def authenticate(self) -> None:
        if self.settings.guest_mode:
            self.login.authenticate_guest(self.settings.base_url)
            return
        self.login.authenticate_user(
            self.settings.base_url, self.settings.username, self.settings.password
        )

    @allure.step("Search '{query}' under {max_price}")
    def search_items_by_name_under_price(
        self, query: str, max_price: float, limit: int = 5
    ) -> list[str]:
        self.home.search(query, self.settings.base_url)
        self.search_results.apply_price_and_format_filters(
            max_price, self.settings.buy_it_now_only, self.settings.free_shipping_only
        )
        collected: list[str] = []
        seen: set[str] = set()
        target = limit
        while len(collected) < target:
            batch = self.search_results.collect_urls_under_price(
                max_price, target - len(collected), self.settings.base_url, seen
            )
            collected.extend(batch)
            if len(collected) >= target:
                break
            if not self.search_results.go_to_next_page():
                break
        allure.attach("\n".join(collected) or "(none)", name="item-urls", attachment_type=allure.attachment_type.TEXT)
        return collected

    @allure.step("Add items to cart")
    def add_items_to_cart(self, urls: list[str], needed: int | None = None) -> int:
        needed = needed if needed is not None else len(urls)
        added = 0
        for url in urls:
            if added >= needed:
                break
            item_page = ItemPage(self.page.context.new_page())
            try:
                item_page.open(url)
                item_page.add_to_cart()
                added += 1
            except AssertionError:
                self.logger.info("Skip item that could not be added: %s", url)
            finally:
                item_page.page.close()
            self.page.bring_to_front()
        if added == 0:
            raise AssertionError("No items were added to cart")
        return added

    @allure.step("Read cart budget {budget_per_item} * {items_count}")
    def read_cart_budget(self, budget_per_item: float, items_count: int) -> tuple[float, float]:
        trace_path = self.settings.trace_dir / "cart-total.zip"
        tracing_started = False
        try:
            self.page.context.tracing.start(screenshots=True, snapshots=True, sources=True)
            tracing_started = True
        except PlaywrightError:
            tracing_started = False
        try:
            self.cart.open()
            save_screenshot(self.page, self.settings.screenshot_dir, "cart-total")
            total = self.cart.read_subtotal()
            limit = budget_per_item * items_count
            allure.attach(
                f"cart_subtotal={total}; limit={limit}; items={items_count}",
                name="cart-budget",
                attachment_type=allure.attachment_type.TEXT,
            )
            return total, limit
        finally:
            if tracing_started:
                self.page.context.tracing.stop(path=str(trace_path))
                attach_trace(trace_path)
