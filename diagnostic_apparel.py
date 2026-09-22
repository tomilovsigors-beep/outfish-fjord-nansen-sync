import json
import re
from bs4 import BeautifulSoup

from config import settings
from supplier_client import FjordNansenClient

PRODUCT_URL = "https://b2b.fjordnansen.com/product-eng-40857-RIX-T-SHIRT-WOMEN-T-Shirt.html"


def clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def main():
    cfg = settings()
    client = FjordNansenClient(cfg["base_url"], cfg["login"], cfg["password"])
    response, auth = client._authenticate()
    if response is None or not auth.get("authenticated"):
        raise RuntimeError("Authentication failed")

    r = client.session.get(PRODUCT_URL, timeout=30, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = []
    for idx, block in enumerate(soup.select(".projector_versions__size")):
        text = clean(" ".join(block.stripped_strings))
        qty = block.select_one(".projector_versions__quantity[data-amount]")
        name = qty.get("name") if qty else ""
        m = re.search(r"set_quantity\[(\d+)\]", name or "")
        variant_id = m.group(1) if m else ""
        amount_raw = clean(qty.get("data-amount")) if qty else ""
        amount = int(amount_raw) if amount_raw.isdigit() else None
        rows.append({
            "index": idx,
            "classes": block.get("class"),
            "data_size": block.get("data-size"),
            "variant_id": variant_id,
            "quantity": amount,
            "has_qty_input": qty is not None,
            "has_tell_availability": block.select_one(".projector_versions__tell_availability") is not None,
            "text": text[:420],
        })

    print("APPAREL_SIZES=" + json.dumps({
        "product_url": r.url,
        "http_status": r.status_code,
        "size_blocks": len(rows),
        "rows": rows,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
