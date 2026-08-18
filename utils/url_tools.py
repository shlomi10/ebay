from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

_ITEM_ID = re.compile(r"/itm/(?:[^/?#]+/)?(\d{8,})")


def canonical_item_url(href: str | None, base_url: str) -> str | None:
    if not href:
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    match = _ITEM_ID.search(parsed.path)
    if not match:
        return None
    path = f"/itm/{match.group(1)}"
    return urlunparse((parsed.scheme or "https", parsed.netloc, path, "", "", ""))
