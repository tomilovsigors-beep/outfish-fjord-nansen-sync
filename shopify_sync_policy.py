# Shopify sync field policy

EXISTING_PRODUCT_ALLOWED_UPDATES = {
    "inventory",
    "availability",
}

EXISTING_PRODUCT_BLOCKED_UPDATES = {
    "price",
    "compare_at_price",
    "title",
    "description_html",
    "seo_title",
    "seo_description",
    "handle",
    "product_type",
    "collections",
    "tags",
    "images",
    "translations",
    "publication_status",
}

NEW_PRODUCT_RULES = {
    "status": "DRAFT",
    "price_source": "effective_price_eur",
    "content_source": "approved_FN_CONTENT_DRAFT",
    "collections_source": "FN_MASTER",
}

def allowed_shopify_fields(existing_product: bool) -> set[str]:
    if existing_product:
        return set(EXISTING_PRODUCT_ALLOWED_UPDATES)
    return {
        "inventory",
        "availability",
        "price",
        "title",
        "description_html",
        "seo_title",
        "seo_description",
        "product_type",
        "collections",
        "tags",
        "images",
        "translations",
        "publication_status",
    }

def assert_field_allowed(existing_product: bool, field: str) -> None:
    allowed = allowed_shopify_fields(existing_product)
    if field not in allowed:
        scope = "existing" if existing_product else "new"
        raise RuntimeError(f"Shopify write blocked for {scope} product field: {field}")
