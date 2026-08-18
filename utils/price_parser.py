from __future__ import annotations

import re

_RANGE_SPLIT = re.compile(r"\s+(?:to|–|-|—)\s+", re.I)
_AMOUNT = re.compile(r"([\d][\d.,]*)")
_ITEMS_LINE = re.compile(
    r"Items\s*\(\d+\)\s*(?:[^\n]{0,60}?)((?:US\s*)?\$\s*[\d,.]+|ILS\s*[\d,.]+|EUR\s*[\d,.]+|GBP\s*[\d,.]+|₪\s*[\d,.]+|[\d,.]+)",
    re.I,
)


def parse_price(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = text.replace("\xa0", " ").strip()
    if not cleaned:
        return None
    if _RANGE_SPLIT.search(cleaned):
        parts = [parse_price(part) for part in _RANGE_SPLIT.split(cleaned)]
        values = [part for part in parts if part is not None]
        return min(values) if values else None
    match = _AMOUNT.search(cleaned)
    if not match:
        return None
    raw = match.group(1)
    if raw.count(",") == 1 and raw.count(".") == 0 and re.search(r",\d{1,2}$", raw):
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def parse_items_total(text: str | None) -> float | None:
    if not text:
        return None
    match = _ITEMS_LINE.search(text.replace("\xa0", " "))
    if not match:
        return None
    return parse_price(match.group(1))
