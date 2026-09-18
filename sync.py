import json
import sys

from config import settings
from supplier_client import FjordNansenClient


def emit(label: str, value) -> None:
    print(f"{label}={json.dumps(value, ensure_ascii=False)}", flush=True)


def main() -> int:
    cfg = settings()

    print("Outfish Fjord Nansen standalone sync", flush=True)
    print(f"DRY_RUN={cfg['dry_run']}", flush=True)
    print(f"SHOPIFY_WRITE_ENABLED={cfg['shopify_write_enabled']}", flush=True)

    if cfg["shopify_write_enabled"] and cfg["dry_run"]:
        raise RuntimeError(
            "Safety lock: SHOPIFY_WRITE_ENABLED=true is incompatible with DRY_RUN=true"
        )

    client = FjordNansenClient(
        base_url=cfg["base_url"],
        login=cfg["login"],
        password=cfg["password"],
    )

    public_check = client.inspect_public_signin()
    emit("PUBLIC_SIGNIN", public_check)

    if not cfg["b2b_credentials_ready"]:
        print("FJORD_B2B_LOGIN / FJORD_B2B_PASSWORD not configured; safe no-op.", flush=True)
        return 0

    audit = client.authenticated_audit()

    emit("AUTH_SUMMARY", {
        "authenticated": audit.get("authenticated"),
        "final_url": audit.get("final_url"),
        "page_title": audit.get("page_title"),
    })
    emit("CATEGORY_LINKS", audit.get("category_links", [])[:40])
    emit("DISCOVERY_PAGES", audit.get("discovery_pages", [])[:15])
    emit("PRODUCT_CANDIDATES", audit.get("product_candidates", [])[:20])
    emit("SAMPLE_PRODUCT_PAGES", audit.get("sample_product_pages", [])[:3])

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        raise
