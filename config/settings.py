from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
TEST_DATA_PATH = ROOT / "data" / "test_data.json"


def _bool(value: str) -> bool:
    return value.lower() in {"1", "true", "yes"}


@dataclass
class Settings:
    base_url: str
    cart_url: str
    timeout_ms: int
    buy_it_now_only: bool
    free_shipping_only: bool
    username: str | None
    password: str | None
    headless: bool
    screenshot_dir: Path
    trace_dir: Path

    @property
    def guest_mode(self) -> bool:
        return not (self.username and self.password)


def load_settings() -> Settings:
    load_dotenv(ROOT / ".env")
    screenshot_dir = ROOT / "reports" / "screenshots"
    trace_dir = ROOT / "reports" / "traces"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    trace_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        base_url=os.environ["EBAY_BASE_URL"],
        cart_url=os.environ["EBAY_CART_URL"],
        timeout_ms=int(os.environ["EBAY_TIMEOUT_MS"]),
        buy_it_now_only=_bool(os.environ["EBAY_BUY_IT_NOW_ONLY"]),
        free_shipping_only=_bool(os.environ["EBAY_FREE_SHIPPING_ONLY"]),
        username=os.getenv("EBAY_USER") or None,
        password=os.getenv("EBAY_PASS") or None,
        headless=_bool(os.getenv("HEADLESS", "false")),
        screenshot_dir=screenshot_dir,
        trace_dir=trace_dir,
    )
