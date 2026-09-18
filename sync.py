import json
import sys

from config import settings
from importer import collect_catalog
from sheet_writer import upsert_fn_raw
from supplier_client import FjordNansenClient


def emit(label: str, value) -> None:
    print(f"{label}={json.dumps(value, ensure_ascii=False)}", flush=True)


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

    result = collect_catalog(client)
    rows = result["rows"]

    emit("CATALOG_SUMMARY", {
        "products_discovered": result["product_count"],
        "rows_parsed": len(rows),
        "categories": result["category_count"],
        "errors": len(result["errors"]),
        "sample": rows[:2],
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
