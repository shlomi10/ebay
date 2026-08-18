from __future__ import annotations

from pathlib import Path

import allure
from playwright.sync_api import Page


def save_screenshot(page: Page, directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def attach_trace(path: Path) -> None:
    if path.exists():
        allure.attach.file(str(path), name=path.name, attachment_type=allure.attachment_type.ZIP)
