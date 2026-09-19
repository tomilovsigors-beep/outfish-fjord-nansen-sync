FJORD_MANAGED_NAMESPACE = "outfish"
FJORD_MANAGED_KEY = "fjord_managed"
FJORD_MANAGED_VALUE = "true"


def is_pipeline_managed(metafield_value) -> bool:
    return str(metafield_value or "").strip().lower() == FJORD_MANAGED_VALUE


def may_mass_update_content(metafield_value) -> bool:
    return is_pipeline_managed(metafield_value)


def may_mass_update_price(metafield_value, manual_price_override=False) -> bool:
    return is_pipeline_managed(metafield_value) and not bool(manual_price_override)


def may_sync_inventory(explicit_supplier_match: bool) -> bool:
    # Inventory/availability can sync for either pipeline-created or manually
    # managed products, but only after an explicit supplier match exists.
    return bool(explicit_supplier_match)


def ownership_metafield_input() -> dict:
    # Apply only when the Fjord pipeline itself creates a new Shopify product.
    return {
        "namespace": FJORD_MANAGED_NAMESPACE,
        "key": FJORD_MANAGED_KEY,
        "type": "boolean",
        "value": FJORD_MANAGED_VALUE,
    }
