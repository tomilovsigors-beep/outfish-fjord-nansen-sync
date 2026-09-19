import json
import re

from bs4 import BeautifulSoup

from config import settings
from supplier_client import FjordNansenClient

PRODUCT_URL = "https://b2b.fjordnansen.com/product-eng-51153-NORDKAPP-300-OLIVE-MID-LEFT-1-C-650G-sleeping-bag.html"


def clean_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    value = re.sub(r"\b\d+[.,]\d{2}\s*(?:EUR|€)\b", "[price-redacted]", value, flags=re.I)
    return value[:220]


def main():
    cfg = settings()
    if not cfg["b2b_credentials_ready"]:
        raise RuntimeError("B2B credentials missing")

    client = FjordNansenClient(cfg["base_url"], cfg["login"], cfg["password"])
    response, auth = client._authenticate()
    if response is None or not auth.get("authenticated"):
        raise RuntimeError("Authentication failed")

    r = client.session.get(PRODUCT_URL, timeout=30, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    print("DIAGNOSTIC_PRODUCT=51153")
    print(f"HTTP_STATUS={r.status_code}")

    # JSON-LD inventory/availability-related fields only.
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict) or item.get("@type") != "Product":
                continue
            offers = item.get("offers") or []
            if isinstance(offers, dict):
                offers = [offers]
            safe = []
            for offer in offers:
                if not isinstance(offer, dict):
                    continue
                row = {}
                for k in ("availability", "inventoryLevel", "eligibleQuantity"):
                    if k in offer:
                        row[k] = offer[k]
                if row:
                    safe.append(row)
            print("JSONLD_STOCK=" + json.dumps(safe, ensure_ascii=False))

    # DOM candidates: only stock/availability/quantity-related nodes and attributes.
    words = re.compile(r"stock|availab|quantity|qty|amount|warehouse", re.I)
    candidates = []
    seen = set()
    for tag in soup.find_all(True):
        attrs = {str(k): v for k, v in tag.attrs.items()}
        attr_text = " ".join([str(k) + "=" + str(v) for k, v in attrs.items()])
        text = clean_text(tag.get_text(" ", strip=True))
        if not (words.search(attr_text) or words.search(text)):
            continue
        # Avoid huge container nodes and price-bearing sales blocks.
        if len(text) > 220:
            continue
        safe_attrs = {}
        for k, v in attrs.items():
            if words.search(k) or words.search(str(v)) or k in {"id", "class", "data-product-id", "data-product_size"}:
                safe_attrs[k] = v
        row = {"tag": tag.name, "attrs": safe_attrs, "text": text}
        key = json.dumps(row, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(row)

    print("DOM_STOCK_CANDIDATES=" + json.dumps(candidates[:80], ensure_ascii=False))


if __name__ == "__main__":
    main()
