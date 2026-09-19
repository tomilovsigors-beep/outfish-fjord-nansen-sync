import re

MASTER_HEADERS = [
    "sync_status","publish_ready","manual_block","supplier","brand","source_product_id",
    "source_variant_id","internal_item_id","supplier_sku","effective_sku","ean_gtin","ean_status",
    "shopify_product_id","shopify_variant_id","shopify_handle","title_en","title_lv","title_ru",
    "description_html_en","description_html_lv","description_html_ru","seo_title_en","seo_title_lv",
    "seo_title_ru","seo_description_en","seo_description_lv","seo_description_ru","product_type",
    "collections","tags","color","size","variant_label","own_stock","supplier_stock","sellable_stock",
    "stock_source","supplier_warehouse_code","supplier_lead_days","delivery_text_en","delivery_text_lv",
    "delivery_text_ru","rrp_gross_eur","selling_price_override_eur","effective_price_eur",
    "compare_at_price_eur","image_primary_source","image_primary_url","image_processed_url",
    "supplier_source_url","last_supplier_sync","last_shopify_sync","error_message","notes"
]

def _num(value, default=0):
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default

def _clean_number(value):
    n = _num(value, None)
    if n is None:
        return ""
    if float(n).is_integer():
        return int(n)
    return n

def _deterministic_sku(raw):
    supplier_sku = str(raw.get("supplier_sku") or "").strip()
    if supplier_sku:
        return supplier_sku
    variant_id = str(raw.get("source_variant_id") or "").strip()
    product_id = str(raw.get("source_product_id") or "").strip()
    stable = variant_id or product_id
    return f"FN-AUTO-{stable}" if stable else ""

def _seed_product_type(category):
    parts = [p.strip() for p in str(category or "").split(">") if p.strip()]
    return parts[-1] if parts else ""

def build_master_row(raw: dict, existing: dict | None = None) -> dict:
    existing = existing or {}
    variant_id = str(raw.get("source_variant_id") or "").strip()
    product_id = str(raw.get("source_product_id") or "").strip()
    supplier_stock = max(0, int(_num(raw.get("supplier_stock"), 0)))
    own_stock = max(0, int(_num(existing.get("own_stock"), 0)))
    sellable_stock = own_stock if own_stock > 0 else supplier_stock
    stock_source = "OWN" if own_stock > 0 else ("SUPPLIER" if supplier_stock > 0 else "NONE")

    rrp = _clean_number(raw.get("rrp_gross_eur"))
    override = existing.get("selling_price_override_eur", "")
    override_num = _num(override, None)
    effective_price = _clean_number(override_num if override_num is not None else rrp)

    compare_at = ""
    rrp_num = _num(rrp, None)
    if override_num is not None and rrp_num is not None and override_num < rrp_num:
        compare_at = _clean_number(rrp_num)

    processed_image = str(existing.get("image_processed_url") or "").strip()
    existing_image_source = str(existing.get("image_primary_source") or "").strip().lower()
    existing_primary = str(existing.get("image_primary_url") or "").strip()
    if processed_image:
        image_source = "processed"
        image_primary = processed_image
    elif existing_primary and existing_image_source not in {"", "supplier"}:
        image_source = existing.get("image_primary_source") or "manual"
        image_primary = existing_primary
    else:
        image_source = "supplier"
        image_primary = raw.get("image_1_url") or ""

    lead = raw.get("supplier_lead_days") or ""
    wh = raw.get("supplier_warehouse_code") or ""
    if own_stock > 0:
        delivery_en = "Delivery in 1–2 days"
        delivery_lv = "Piegāde 1–2 dienu laikā"
        delivery_ru = "Доставка за 1–2 дня"
    elif supplier_stock > 0 and str(lead).strip():
        lead_text = str(lead).strip()
        delivery_en = f"Delivery in {lead_text} days"
        delivery_lv = f"Piegāde {lead_text} dienu laikā"
        delivery_ru = f"Доставка за {lead_text} дней"
    else:
        delivery_en = delivery_lv = delivery_ru = ""

    row = {
        "sync_status": existing.get("sync_status") or "NEW",
        "publish_ready": existing.get("publish_ready") or "NO",
        "manual_block": existing.get("manual_block") or "NO",
        "supplier": raw.get("supplier") or "Fjord Nansen",
        "brand": raw.get("brand") or "Fjord Nansen",
        "source_product_id": product_id,
        "source_variant_id": variant_id,
        "internal_item_id": f"FN-{variant_id}" if variant_id else (f"FN-{product_id}" if product_id else ""),
        "supplier_sku": raw.get("supplier_sku") or "",
        "effective_sku": _deterministic_sku(raw),
        "ean_gtin": raw.get("ean_gtin") or "",
        "ean_status": raw.get("ean_status") or ("present" if raw.get("ean_gtin") else "missing"),
        "shopify_product_id": existing.get("shopify_product_id") or "",
        "shopify_variant_id": existing.get("shopify_variant_id") or "",
        "shopify_handle": existing.get("shopify_handle") or "",
        "title_en": existing.get("title_en") or raw.get("title_original") or "",
        "title_lv": existing.get("title_lv") or "",
        "title_ru": existing.get("title_ru") or "",
        "description_html_en": existing.get("description_html_en") or raw.get("description_original") or "",
        "description_html_lv": existing.get("description_html_lv") or "",
        "description_html_ru": existing.get("description_html_ru") or "",
        "seo_title_en": existing.get("seo_title_en") or "",
        "seo_title_lv": existing.get("seo_title_lv") or "",
        "seo_title_ru": existing.get("seo_title_ru") or "",
        "seo_description_en": existing.get("seo_description_en") or "",
        "seo_description_lv": existing.get("seo_description_lv") or "",
        "seo_description_ru": existing.get("seo_description_ru") or "",
        "product_type": existing.get("product_type") or _seed_product_type(raw.get("source_category")),
        "collections": existing.get("collections") or "",
        "tags": existing.get("tags") or "Fjord Nansen",
        "color": raw.get("color_original") or "",
        "size": raw.get("size_original") or "",
        "variant_label": raw.get("variant_original") or raw.get("size_original") or "",
        "own_stock": own_stock,
        "supplier_stock": supplier_stock,
        "sellable_stock": sellable_stock,
        "stock_source": stock_source,
        "supplier_warehouse_code": wh,
        "supplier_lead_days": lead,
        "delivery_text_en": delivery_en,
        "delivery_text_lv": delivery_lv,
        "delivery_text_ru": delivery_ru,
        "rrp_gross_eur": rrp,
        "selling_price_override_eur": override,
        "effective_price_eur": effective_price,
        "compare_at_price_eur": compare_at,
        "image_primary_source": image_source,
        "image_primary_url": image_primary,
        "image_processed_url": processed_image,
        "supplier_source_url": raw.get("source_url") or "",
        "last_supplier_sync": raw.get("source_updated_at") or raw.get("imported_at") or "",
        "last_shopify_sync": existing.get("last_shopify_sync") or "",
        "error_message": "",
        "notes": existing.get("notes") or "",
    }
    return {h: row.get(h, "") for h in MASTER_HEADERS}
