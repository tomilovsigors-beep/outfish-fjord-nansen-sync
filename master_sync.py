import json
import sys

from config import settings
from sheet_writer import sync_fn_master_from_raw


def main() -> int:
    cfg = settings()
    if not cfg["google_credentials_ready"]:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not configured")
    if cfg["shopify_write_enabled"]:
        raise RuntimeError("Safety lock: Shopify write must stay disabled during FN_MASTER sync")

    result = sync_fn_master_from_raw(
        cfg["sheet_id"],
        cfg["google_service_account_json"],
    )
    print("FN_MASTER_WRITE=" + json.dumps(result, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr, flush=True)
        raise
