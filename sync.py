import json
import sys

from config import settings
from supplier_client import FjordNansenClient


def main() -> int:
    cfg = settings()

    print("Outfish Fjord Nansen standalone sync")
    print(f"DRY_RUN={cfg['dry_run']}")
    print(f"SHOPIFY_WRITE_ENABLED={cfg['shopify_write_enabled']}")

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
    print(json.dumps({"public_signin": public_check}, ensure_ascii=False))

    if not cfg["b2b_credentials_ready"]:
        print("FJORD_B2B_LOGIN / FJORD_B2B_PASSWORD not configured; safe no-op.")
        return 0

    audit = client.authenticated_audit()
    print(json.dumps({"authenticated_audit": audit}, ensure_ascii=False))

    # No Google Sheet or Shopify mutation at bootstrap stage.
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
