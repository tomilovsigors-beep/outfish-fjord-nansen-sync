import os

DEFAULT_BASE_URL = "https://b2b.fjordnansen.com"
DEFAULT_SHEET_ID = "1RRsV9mHZMV3gfQGIJq1OGQgc0qyI4zqJ-yv9Fg9Ygl8"


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def flag(name: str, default: bool = False) -> bool:
    raw = env(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "on"}


def is_missing(value: str) -> bool:
    return value in {"", "__SET_ME__", "SET_ME", "CHANGEME"}


def settings() -> dict:
    login = env("FJORD_B2B_LOGIN")
    password = env("FJORD_B2B_PASSWORD")
    google_sa = env("GOOGLE_SERVICE_ACCOUNT_JSON")

    return {
        "base_url": env("FJORD_B2B_BASE_URL", DEFAULT_BASE_URL),
        "login": login,
        "password": password,
        "sheet_id": env("FJORD_SUPPLIER_SHEET_ID", DEFAULT_SHEET_ID),
        "google_service_account_json": google_sa,
        "google_credentials_ready": not is_missing(google_sa),
        "dry_run": flag("DRY_RUN", True),
        "sheet_write_enabled": flag("SHEET_WRITE_ENABLED", False),
        "shopify_write_enabled": flag("SHOPIFY_WRITE_ENABLED", False),
        "shopify_store_domain": env("SHOPIFY_STORE_DOMAIN"),
        "shopify_admin_access_token": env("SHOPIFY_ADMIN_ACCESS_TOKEN"),
        "b2b_credentials_ready": not is_missing(login) and not is_missing(password),
    }
