from __future__ import annotations

import base64
import os

import allure
import pytest
from pytest_html import extras

from config.settings import ROOT, load_settings
from pages.cart_page import CartPage
from pages.home_page import HomePage
from pages.login_page import LoginPage
from pages.search_results_page import SearchResultsPage


class Pages:
    def __init__(self, page, settings):
        self.page = page
        self.login_page = LoginPage(page)
        self.home_page = HomePage(page)
        self.search_results_page = SearchResultsPage(page)
        self.cart_page = CartPage(page, settings.cart_url)


def pytest_configure() -> None:
    reports = ROOT / "reports"
    for folder in (
        reports,
        reports / "allure-results",
        reports / "screenshots",
        reports / "traces",
    ):
        folder.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def settings():
    return load_settings()


@pytest.fixture()
def page_setup(page, settings) -> Pages:
    page.set_default_timeout(settings.timeout_ms)
    return Pages(page, settings)


@pytest.fixture(scope="session", autouse=True)
def configure_test_id_attribute(playwright):
    playwright.selectors.set_test_id_attribute("data-test-id")


@pytest.fixture(autouse=True)
def capture_page_logs(request):
    if "page" not in request.fixturenames and "page_setup" not in request.fixturenames:
        yield
        return
    page = request.getfixturevalue("page")
    logs: list[str] = []
    page.on("console", lambda msg: logs.append(f"{msg.type}: {msg.text}"))
    page.on("pageerror", lambda err: logs.append(f"pageerror: {err}"))
    request.node.page_logs = logs
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return
    page = item.funcargs.get("page")
    if page is None:
        pages = item.funcargs.get("page_setup")
        page = pages.page if pages is not None else None
    if page is None:
        return
    logs = getattr(item, "page_logs", [])
    log_text = f"url={page.url}\n" + ("\n".join(logs) if logs else "(no browser logs)")
    html_extras = getattr(report, "extras", [])
    if report.failed:
        try:
            png = page.screenshot(full_page=True)
            allure.attach(png, name="failure-screenshot", attachment_type=allure.attachment_type.PNG)
            html_extras.append(extras.png(base64.b64encode(png).decode("ascii")))
        except Exception:
            pass
        allure.attach(log_text, name="failure-log", attachment_type=allure.attachment_type.TEXT)
        html_extras.append(extras.text(log_text, name="failure-log"))
    elif report.passed:
        allure.attach(log_text, name="success-log", attachment_type=allure.attachment_type.TEXT)
        html_extras.append(extras.text(log_text, name="success-log"))
    report.extras = html_extras


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, settings):
    args = ["--disable-blink-features=AutomationControlled"]
    if os.getenv("CI"):
        args.extend(
            [
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-software-rasterizer",
            ]
        )
    return {
        **browser_type_launch_args,
        "headless": settings.headless,
        "args": args,
    }


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args, settings):
    viewport = {"width": 1280, "height": 720} if os.getenv("CI") else {"width": 1440, "height": 900}
    return {
        **browser_context_args,
        "base_url": settings.base_url,
        "locale": "en-US",
        "timezone_id": "America/New_York",
        "geolocation": {"latitude": 40.7128, "longitude": -74.006},
        "permissions": ["geolocation"],
        "extra_http_headers": {"Accept-Language": "en-US,en;q=0.9"},
        "viewport": viewport,
        "ignore_https_errors": True,
    }
