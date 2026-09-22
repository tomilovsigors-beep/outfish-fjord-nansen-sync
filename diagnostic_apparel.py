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
    if not cfg["b2b_credentials_ready"]:
        raise RuntimeError("B2B credentials missing")

    client = FjordNansenClient(cfg["base_url"], cfg["login"], cfg["password"])
    response, auth = client._authenticate()
    if response is None or not auth.get("authenticated"):
        raise RuntimeError("Authentication failed")

    r = client.session.get(PRODUCT_URL, timeout=30, allow_redirects=True)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    rows = []
    blocks = soup.select(".projector_versions__block")
    for idx, block in enumerate(blocks):
        qty = block.select_one(".projector_versions__quantity[data-amount]")
        if qty is None:
            continue

        name = qty.get("name") or ""
        m = re.search(r"set_quantity\[(\d+)\]", name)
        variant_id = m.group(1) if m else ""
        amount_raw = clean(qty.get("data-amount"))
        amount = int(amount_raw) if amount_raw.isdigit() else None

        attrs = {}
        for tag in block.find_all(True):
            for k, v in (tag.attrs or {}).items():
                ks = str(k).lower()
                if any(x in ks for x in ["size", "variant", "product", "stock", "amount", "quantity"]):
                    attrs[k] = v

        text = clean(" ".join(block.stripped_strings))
        rows.append({
            "index": idx,
            "active": "--active" in (block.get("class") or []),
            "variant_id": variant_id,
            "quantity": amount,
            "quantity_raw": amount_raw,
            "text": text[:500],
            "attrs": attrs,
        })

    print("APPAREL_CONTROL=" + json.dumps({
        "product_url": r.url,
        "http_status": r.status_code,
        "variant_blocks": len(blocks),
        "rows": rows,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
