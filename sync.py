import json
import os
import sys

from config import settings
from importer import collect_catalog
from sheet_writer import upsert_fn_raw
from supplier_client import FjordNansenClient


def emit(label: str, value) -> None:
    print(f"{label}={json.dumps(value, ensure_ascii=False)}", flush=True)


def write_jsonl(path: str, rows: list[dict]) -> None:
    if not path:
        return
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"OUTPUT_JSONL={path} rows={len(rows)}", flush=True)


def main() -> int:
    cfg = settings()

    print("Outfish Fjord Nansen standalone sync", flush=True)
    emit("MODE", {
        "dry_run": cfg["dry_run"],
        "sheet_write_enabled": cfg["sheet_write_enabled"],
        "google_credentials_ready": cfg["google_credentials_ready"],
        "shopify_write_enabled": cfg["shopify_write_enabled"],
    })

    if cfg["shopify_write_enabled"]:
        raise RuntimeError("Safety lock: Shopify write stage is not approved yet")

    if not cfg["b2b_credentials_ready"]:
        print("B2B credentials not configured; safe no-op.", flush=True)
        return 0

    client = FjordNansenClient(
        base_url=cfg["base_url"],
        login=cfg["login"],
        password=cfg["password"],
    )

    try:
        result = collect_catalog(client)
    except RuntimeError as exc:
        if str(exc).startswith("B2B_UNAVAILABLE:"):
            emit("B2B_UNAVAILABLE", {"reason": str(exc)})
            print("Supplier B2B temporarily unavailable; safe no-op.", flush=True)
            return 0
        raise

    rows = result["rows"]
    write_jsonl(os.getenv("OUTPUT_JSONL_PATH", "").strip(), rows)

    audit = {
        "stock_positive": 0,
        "stock_zero": 0,
        "stock_missing": 0,
        "variant_id_missing": 0,
        "sku_missing": 0,
        "ean_missing": 0,
        "size_present": 0,
        "color_present": 0,
        "availability_conflicts": 0,
    }
    for row in rows:
        stock = row.get("supplier_stock")
        if stock is None:
            audit["stock_missing"] += 1
        elif stock > 0:
            audit["stock_positive"] += 1
        else:
            audit["stock_zero"] += 1
        if not row.get("source_variant_id"):
            audit["variant_id_missing"] += 1
        if not row.get("supplier_sku"):
            audit["sku_missing"] += 1
        if not row.get("ean_gtin"):
            audit["ean_missing"] += 1
        if row.get("size_original"):
            audit["size_present"] += 1
        if row.get("color_original"):
            audit["color_present"] += 1
        try:
            attrs = json.loads(row.get("attributes_json") or "{}")
        except Exception:
            attrs = {}
        if attrs.get("availability_conflict"):
            audit["availability_conflicts"] += 1

    emit("CATALOG_SUMMARY", {
        "products_discovered": result["product_count"],
        "rows_parsed": len(rows),
        "categories": result["category_count"],
        "errors": len(result["errors"]),
        "stopped_early": result.get("stopped_early", False),
        "processed_count": result.get("processed_count"),
        "audit": audit,
    })

    if result["errors"]:
        emit("CATALOG_ERRORS", result["errors"][:20])

    if cfg["sheet_write_enabled"]:
        if not cfg["google_credentials_ready"]:
            raise RuntimeError("SHEET_WRITE_ENABLED=true but GOOGLE_SERVICE_ACCOUNT_JSON is not configured")
        write_result = upsert_fn_raw(cfg["sheet_id"], cfg["google_service_account_json"], rows)
        emit("FN_RAW_WRITE", write_result)
    else:
        print("FN_RAW write disabled; catalogue parsed only.", flush=True)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        raise
