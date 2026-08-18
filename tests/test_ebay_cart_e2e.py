from __future__ import annotations

import json

import allure
import pytest

from config.settings import TEST_DATA_PATH
from services.ebay_shop import EbayShop

CASES = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))["cases"]


@allure.epic("ebay")
@allure.feature("Search, cart, budget")
@pytest.mark.e2e
@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_search_add_to_cart_budget(page_setup, settings, case):
    shop = EbayShop(page_setup, settings)
    shop.authenticate()
    urls = shop.search_items_by_name_under_price(
        case["query"], case["max_price"], case["limit"]
    )
    added = shop.add_items_to_cart(urls, needed=case["limit"])
    shop.assert_cart_total_not_exceeds(case["max_price"], added)
