import hashlib
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse, parse_qsl, urlencode

from bs4 import BeautifulSoup


RAW_HEADERS = [
    "supplier","source_product_id","source_variant_id","source_url","source_category",
    "supplier_sku","ean_gtin","ean_status","brand","title_original","description_original",
    "color_original","size_original","variant_original","material_original","weight_g",
    "rrp_gross_eur","purchase_net_eur","vat_rate","supplier_stock","supplier_warehouse_code",
    "supplier_lead_days","image_1_url","image_2_url","image_3_url","attributes_json",
    "source_updated_at","imported_at","raw_hash"
]


def _num(value):
    if value is None:
        return None
    s = str(value).replace("\xa0", " ").replace("€", "").strip().replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group(0)) if m else None


def _product_jsonld(soup):
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "Product":
                return item
    return {}


def _spec_value(text, label, reject=None):
    reject = set(x.lower() for x in (reject or []))
    pat = re.compile(rf"(?:^|\s){re.escape(label)}\s+([^|\n]+?)(?=\s{2,}|\s(?:Symbol|Producer code|Size|Color|Colour|Weight \[g\]|Pack size|Fill weight \[g\])\s|$)", re.I)
    matches = [m.group(1).strip() for m in pat.finditer(text)]
    for value in reversed(matches):
        low = value.lower().strip(" :,-")
        if not low or low in reject:
            continue
        if len(value) > 80:
            continue
        return value.strip()
    return ""


def _short_spec(value, bad_terms=None):
    value = re.sub(r"\\s+", " ", str(value or "")).strip(" :,-")
    if not value or len(value) > 32:
        return ""
    low = value.lower()
    if any(term.lower() in low for term in (bad_terms or [])):
        return ""
    return value


def _active_variant(soup):
    block = soup.select_one(".projector_versions__block.--active")
    scope = block or soup
    qty = scope.select_one(".projector_versions__quantity[data-amount]")
    variant_id = ""
    stock = None
    if qty is not None:
        name = qty.get("name") or ""
        match = re.search(r"set_quantity\\[(\\d+)\\]", name)
        if match:
            variant_id = match.group(1)
        amount = str(qty.get("data-amount") or "").strip()
        if amount.isdigit():
            stock = int(amount)

    size = ""
    if block is not None:
        block_text = " ".join(block.stripped_strings)
        match = re.match(r"^(.{1,32}?)\\s+\\d+[,.]\\d{2}\\s*(?:€|EUR)", block_text, re.I)
        if match:
            size = _short_spec(match.group(1), ["price", "quantity", "availability", "discount", "shipping"])
    return variant_id, stock, size


def _breadcrumb_category(soup):
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "BreadcrumbList":
            names = []
            for el in data.get("itemListElement", []):
                item = el.get("item", {}) if isinstance(el, dict) else {}
                name = item.get("name")
                if name and str(name).lower() != "home page":
                    names.append(str(name))
            if names:
                return " > ".join(names[:-1] or names)
    return ""


def _offer_prices(product):
    offers = product.get("offers") or []
    if isinstance(offers, dict):
        offers = [offers]
    sale = list_price = msrp = None
    availability = ""
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        availability = offer.get("availability") or availability
        specs = offer.get("priceSpecification") or []
        if isinstance(specs, dict):
            specs = [specs]
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            ptype = str(spec.get("priceType") or "")
            price = _num(spec.get("price"))
            if "SalePrice" in ptype:
                sale = price
            elif "ListPrice" in ptype:
                list_price = price
            elif "MSRP" in ptype:
                msrp = price
    return sale, list_price, msrp, availability


def parse_product(html, url, default_vat=0.23):
    soup = BeautifulSoup(html, "html.parser")
    product = _product_jsonld(soup)
    text = " ".join(soup.stripped_strings)
    path = urlparse(url).path

    m = re.search(r"product-eng-(\d+)-", path)
    product_id = m.group(1) if m else ""

    title = product.get("name") or (soup.title.get_text(" ", strip=True).split("|")[0].strip() if soup.title else "")
    description = product.get("description") or ""
    brand_obj = product.get("brand") or {}
    brand = brand_obj.get("name") if isinstance(brand_obj, dict) else str(brand_obj or "")
    product_id_field = str(product.get("productID") or "")
    supplier_sku = product_id_field.replace("mpn:", "", 1) if product_id_field.startswith("mpn:") else ""

    producer_code = ""
    mcode = re.search(r"Producer code\s+([0-9A-Za-z._-]+)", text, re.I)
    if mcode:
        producer_code = mcode.group(1)
    ean = producer_code if re.fullmatch(r"\d{8}|\d{12}|\d{13}|\d{14}", producer_code or "") else ""

    active_variant_id, active_stock, active_size = _active_variant(soup)
    size = active_size or _short_spec(
        _spec_value(text, "Size", reject={"price", "quantity", "price / item"}),
        ["shape", "material", "dimensions", "fabric", "filling", "zipper", "price", "quantity", "availability", "discount", "circumference"],
    )
    color = _short_spec(
        _spec_value(text, "Color", reject={"palette", "palette,"}) or _spec_value(text, "Colour"),
        ["fabric", "material", "price", "quantity", "availability"],
    )
    weight = _num(_spec_value(text, "Weight [g]"))
    pack_size = _spec_value(text, "Pack size")
    fill_weight = _num(_spec_value(text, "Fill weight [g]"))

    stock = active_stock
    if stock is None:
        active_block = soup.select_one(".projector_versions__block.--active")
        active_text = " ".join(active_block.stripped_strings) if active_block else ""
        ms = re.search(r"\(\s*(\d+)\s+items? in stock\s*\)", active_text, re.I)
        if ms:
            stock = int(ms.group(1))
        elif active_block and active_block.select_one(".projector_versions__tell_availability"):
            stock = 0

    sale_net, list_net, msrp_gross, availability = _offer_prices(product)

    images = product.get("image") or []
    if isinstance(images, str):
        images = [images]
    if len(images) < 3:
        for img in soup.find_all("img", src=True):
            src = urljoin(url, img["src"])
            if "/hpeciai/" in src and src not in images:
                images.append(src)

    variants = []
    for inp in soup.find_all("input"):
        name = inp.get("name") or ""
        if name.startswith("product["):
            key = name.split("[",1)[1].split("]",1)[0]
            variants.append((key, inp.get("value")))
    variant_key = active_variant_id or (variants[0][0] if variants else (product_id + "1" if product_id else ""))

    category = _breadcrumb_category(soup)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    attrs = {
        "source_list_price_net_eur": list_net,
        "source_msrp_gross_eur": msrp_gross,
        "source_sale_price_net_eur": sale_net,
        "availability": availability,
        "pack_size": pack_size,
        "fill_weight_g": fill_weight,
        "source_price_type": "net",
    }

    raw = {
        "supplier":"Fjord Nansen",
        "source_product_id":product_id,
        "source_variant_id":variant_key,
        "source_url":url,
        "source_category":category,
        "supplier_sku":supplier_sku,
        "ean_gtin":ean,
        "ean_status":"present" if ean else "missing",
        "brand":brand or "Fjord Nansen",
        "title_original":title,
        "description_original":description,
        "color_original":color,
        "size_original":size,
        "variant_original":" ".join(x for x in [size] if x),
        "material_original":"",
        "weight_g":weight,
        "rrp_gross_eur":msrp_gross,
        "purchase_net_eur":sale_net,
        "vat_rate":default_vat,
        "supplier_stock":stock,
        "supplier_warehouse_code":"",
        "supplier_lead_days":"",
        "image_1_url":images[0] if len(images)>0 else "",
        "image_2_url":images[1] if len(images)>1 else "",
        "image_3_url":images[2] if len(images)>2 else "",
        "attributes_json":json.dumps(attrs, ensure_ascii=False, separators=(",",":")),
        "source_updated_at":now,
        "imported_at":now,
        "raw_hash":"",
    }
    digest_source = "|".join(str(raw.get(h,"")) for h in RAW_HEADERS if h not in {"source_updated_at","imported_at","raw_hash"})
    raw["raw_hash"] = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
    return raw


def discover_product_urls(client, max_categories=200, max_pages_per_category=25):
    response, auth = client._authenticate()
    if response is None or not auth.get("authenticated"):
        raise RuntimeError(f"B2B authentication failed: {auth}")

    categories = client._extract_menu_categories(response.text, response.url)
    category_urls = []
    seen_cat = set()
    for c in categories[:max_categories]:
        u = c["url"]
        if u not in seen_cat:
            seen_cat.add(u)
            category_urls.append(u)

    products = {}
    for category_url in category_urls:
        queue = [category_url]
        seen_pages = set()
        pages = 0
        while queue and pages < max_pages_per_category:
            page_url = queue.pop(0)
            if page_url in seen_pages:
                continue
            seen_pages.add(page_url)
            pages += 1
            r = client.session.get(page_url, timeout=30, allow_redirects=True)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = urljoin(r.url, a["href"]).split("#")[0]
                if "product-eng-" in urlparse(href).path:
                    m = re.search(r"product-eng-(\d+)-", urlparse(href).path)
                    if m:
                        products[m.group(1)] = href

            for a in soup.find_all("a", href=True):
                href = urljoin(r.url, a["href"]).split("#")[0]
                p = urlparse(href)
                if p.netloc != urlparse(category_url).netloc:
                    continue
                if p.path != urlparse(category_url).path:
                    continue
                if href not in seen_pages and href not in queue:
                    query = dict(parse_qsl(p.query))
                    if query:
                        queue.append(href)

    return list(products.values()), category_urls


def _get_with_retries(client, url, attempts=2):
    last_status = None
    for attempt in range(1, attempts + 1):
        r = client.session.get(url, timeout=30, allow_redirects=True)
        last_status = r.status_code
        if r.status_code < 400:
            return r

        if r.status_code in {401, 403, 429}:
            # Refresh authenticated session and slow down before retrying.
            try:
                client._authenticate()
            except Exception:
                pass
            time.sleep(min(3.0, 0.8 * attempt))
            continue

        r.raise_for_status()
    raise RuntimeError(f"HTTP status {last_status} after {attempts} attempts")


def collect_catalog(client, limit=None):
    urls, categories = discover_product_urls(client)
    if limit:
        urls = urls[:limit]
    rows = []
    errors = []
    consecutive_errors = 0
    stopped_early = False

    for idx, url in enumerate(urls, start=1):
        try:
            r = _get_with_retries(client, url)
            rows.append(parse_product(r.text, r.url))
            consecutive_errors = 0
        except Exception as exc:
            consecutive_errors += 1
            errors.append({"url":url,"error":type(exc).__name__,"message":str(exc)[:180]})
            if consecutive_errors >= 5:
                print(
                    f"CIRCUIT_BREAKER=stopping after {consecutive_errors} consecutive product errors at {idx}/{len(urls)}",
                    flush=True,
                )
                stopped_early = True
                break

        if idx % 10 == 0:
            print(f"CATALOG_PROGRESS={idx}/{len(urls)}", flush=True)
        time.sleep(0.35)

    return {
        "rows":rows,
        "errors":errors,
        "product_count":len(urls),
        "category_count":len(categories),
        "stopped_early":stopped_early,
        "processed_count":len(rows)+len(errors),
    }
