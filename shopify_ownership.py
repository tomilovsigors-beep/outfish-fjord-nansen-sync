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


def classify_shopify_ownership(
    shopify_product_id: str,
    created_by_fjord_pipeline: bool,
    ownership_marker_value=None,
) -> str:
    """
    Return one of:
      - NEW_UNCREATED: no Shopify product exists yet
      - FJORD_MANAGED: product was created by this pipeline and carries marker
      - PROTECTED_EXISTING: any pre-existing/manual/external product

    A SKU/EAN match alone must never grant Fjord ownership.
    """
    if not str(shopify_product_id or "").strip():
        return "NEW_UNCREATED"

    if created_by_fjord_pipeline and is_pipeline_managed(ownership_marker_value):
        return "FJORD_MANAGED"

    return "PROTECTED_EXISTING"


def should_attach_ownership_marker(
    operation: str,
    product_existed_before_operation: bool,
    creation_succeeded: bool,
) -> bool:
    """
    The ownership marker may be attached only during a successful CREATE
    operation for a product that did not exist before that operation.
    """
    return (
        str(operation or "").upper() == "CREATE"
        and not bool(product_existed_before_operation)
        and bool(creation_succeeded)
    )


def assert_marker_assignment_is_safe(
    operation: str,
    product_existed_before_operation: bool,
    creation_succeeded: bool,
) -> None:
    if not should_attach_ownership_marker(
        operation,
        product_existed_before_operation,
        creation_succeeded,
    ):
        raise RuntimeError(
            "Fjord ownership marker assignment blocked: "
            "marker is allowed only on a newly created product created by the Fjord pipeline"
        )
