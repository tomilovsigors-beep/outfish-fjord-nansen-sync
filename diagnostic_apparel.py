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
    for idx, qty in enumerate(soup.select(".projector_versions__quantity[data-amount]")):
        name = qty.get("name") or ""
        m = re.search(r"set_quantity\[(\d+)\]", name)
        variant_id = m.group(1) if m else ""
        amount_raw = clean(qty.get("data-amount"))
        amount = int(amount_raw) if amount_raw.isdigit() else None

        parent = qty
        chain = []
        for depth in range(5):
            if parent is None:
                break
            text = clean(" ".join(parent.stripped_strings))
            attrs = {k:v for k,v in (parent.attrs or {}).items() if k in {"class","data-size","data-product-id","data-product_size","data-amount","id"}}
            chain.append({"depth":depth,"tag":parent.name,"attrs":attrs,"text":text[:320]})
            parent = parent.parent

        rows.append({
            "index": idx,
            "variant_id": variant_id,
            "quantity": amount,
            "quantity_raw": amount_raw,
            "name": name,
            "value": qty.get("value"),
            "classes": qty.get("class"),
            "chain": chain,
        })

    print("APPAREL_QTYS=" + json.dumps({
        "product_url": r.url,
        "http_status": r.status_code,
        "quantity_nodes": len(rows),
        "rows": rows,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
