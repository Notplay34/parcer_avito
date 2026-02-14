"""Fetch and parse Avito search page; extract ad list from embedded JSON."""
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}
TIMEOUT = 10


@dataclass
class ParsedAd:
    id: str
    title: str
    price: str
    url: str


def fetch_search_page(url: str) -> tuple[int, str | None, str | None]:
    """
    GET search URL. Returns (status_code, html_or_none, error_message).
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        return r.status_code, r.text, None
    except requests.Timeout:
        return 0, None, "timeout"
    except requests.RequestException as e:
        logger.exception("Request failed: %s", e)
        return 0, None, str(e)


def _extract_json_from_script(html: str) -> list[dict[str, Any]]:
    """Try to find JSON with ad items in script tags or in page text."""
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script", type="application/json")
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
            items = _find_items_in_json(data)
            if items:
                return items
        except (json.JSONDecodeError, TypeError):
            continue
    # Avito often puts state in script with id or data
    for script in soup.find_all("script"):
        if not script.string:
            continue
        s = script.string
        if "itemId" not in s and "itemListElement" not in s and "avito.ru/item/" not in s:
            continue
        # Try to extract JSON object from __initialData__ or similar
        for pattern in (
            r'__initialData__\s*=\s*(\{.*?\});?\s*(?:</script>|$)',
            r'"itemListElement"\s*:\s*(\[[^\]]*(?:\{[^\]]*\}[^\]]*)*\])',
            r'"items"\s*:\s*(\[[^\]]*(?:\{[^\]]*\}[^\]]*)*\])',
        ):
            m = re.search(pattern, s, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                    items = _find_items_in_json(data if isinstance(data, dict) else {"items": data})
                    if items:
                        return items
                except (json.JSONDecodeError, TypeError, KeyError):
                    continue
    # Fallback: find links to /item/ID and build minimal ad dict
    item_ids = re.findall(r'avito\.ru/item/(\d+)', html)
    seen = set()
    fallback = []
    for i in item_ids:
        if i not in seen:
            seen.add(i)
            fallback.append({"itemId": i, "title": "Объявление", "price": "—", "url": f"https://www.avito.ru/item/{i}"})
    return fallback[:50]


def _find_items_in_json(node: Any) -> list[dict[str, Any]]:
    """Recursively find list of ad-like objects (with id and price/title)."""
    if isinstance(node, list):
        for item in node:
            if isinstance(item, dict) and _looks_like_ad(item):
                return node if all(_looks_like_ad(x) for x in node if isinstance(x, dict)) else [item]
        for item in node:
            found = _find_items_in_json(item)
            if found:
                return found
    if isinstance(node, dict):
        if _looks_like_ad(node):
            return [node]
        for v in node.values():
            found = _find_items_in_json(v)
            if found:
                return found
    return []


def _looks_like_ad(obj: dict) -> bool:
    return isinstance(obj, dict) and (
        "itemId" in obj or "id" in obj
    ) and (
        "title" in obj or "name" in obj or "value" in obj
    )


def _normalize_ad(raw: dict) -> ParsedAd | None:
    """Build ParsedAd from raw JSON node."""
    ad_id = str(raw.get("itemId") or raw.get("id") or raw.get("value") or "")
    if not ad_id or not ad_id.isdigit():
        return None
    title = (raw.get("title") or raw.get("name") or raw.get("titlePrefix") or "").strip() or "Без названия"
    price_node = raw.get("price") or raw.get("priceStr")
    if isinstance(price_node, dict):
        price = str(price_node.get("value") or price_node.get("price") or "")
    else:
        price = str(price_node or "")
    if not price:
        price = "—"
    url = raw.get("url") or raw.get("link") or ""
    if url and not url.startswith("http"):
        url = "https://www.avito.ru" + (url if url.startswith("/") else "/" + url)
    if not url:
        url = f"https://www.avito.ru/item/{ad_id}"
    return ParsedAd(id=ad_id, title=title, price=price, url=url)


def parse_search_page(html: str) -> list[ParsedAd]:
    """Parse HTML and return list of ParsedAd."""
    raw_list = _extract_json_from_script(html)
    result = []
    for raw in raw_list:
        ad = _normalize_ad(raw)
        if ad:
            result.append(ad)
    return result
