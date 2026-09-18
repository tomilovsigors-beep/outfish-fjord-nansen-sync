from urllib.parse import urljoin, urlparse
import time

import requests
from bs4 import BeautifulSoup


class FjordNansenClient:
    def __init__(self, base_url: str, login: str = "", password: str = ""):
        self.base_url = base_url.rstrip("/") + "/"
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Outfish-Fjord-Nansen-Sync/0.1"})

    def signin_url(self) -> str:
        return urljoin(self.base_url, "signin.php")

    def _find_login_form(self, html: str, page_url: str):
        soup = BeautifulSoup(html, "html.parser")
        for index, form in enumerate(soup.find_all("form")):
            if form.find("input", {"type": "password"}):
                return index, form
        return None, None

    def _build_login_payload(self, form) -> dict:
        payload = {}
        for tag in form.find_all("input"):
            name = tag.get("name")
            if not name:
                continue
            field_type = (tag.get("type") or "text").lower()
            if field_type in {"submit", "button", "image", "file"}:
                continue
            if field_type in {"checkbox", "radio"} and not tag.has_attr("checked"):
                continue
            payload[name] = tag.get("value", "")
        payload["login"] = self.login
        payload["password"] = self.password
        return payload

    def inspect_public_signin(self) -> dict:
        response = self.session.get(self.signin_url(), timeout=30)
        response.raise_for_status()
        index, form = self._find_login_form(response.text, response.url)
        fields = []
        if form:
            for tag in form.find_all(["input", "select", "textarea"]):
                fields.append({
                    "tag": tag.name,
                    "type": (tag.get("type") or tag.name or "").lower(),
                    "name": tag.get("name"),
                    "has_value": bool(tag.get("value")),
                })
        return {
            "url": response.url,
            "status_code": response.status_code,
            "reachable": True,
            "login_form": {
                "index": index,
                "method": (form.get("method") or "GET").upper() if form else None,
                "action": urljoin(response.url, form.get("action") or response.url) if form else None,
                "fields": fields,
            } if form else {},
            "login_forms_found": 1 if form else 0,
        }

    def _get_with_startup_retries(self, url: str, attempts: int = 3):
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(url, timeout=(10, 20), allow_redirects=True)
                response.raise_for_status()
                return response
            except (requests.exceptions.ConnectTimeout,
                    requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError) as exc:
                last_error = exc
                if attempt < attempts:
                    time.sleep(2 * attempt)
        raise RuntimeError(f"B2B_UNAVAILABLE: {type(last_error).__name__}")

    def _authenticate(self):
        first = self._get_with_startup_retries(self.signin_url())
        index, form = self._find_login_form(first.text, first.url)
        if form is None:
            return None, {"authenticated": False, "reason": "login_form_not_found"}

        action = urljoin(first.url, form.get("action") or first.url)
        payload = self._build_login_payload(form)
        method = (form.get("method") or "GET").upper()

        if method == "POST":
            response = self.session.post(action, data=payload, timeout=(10, 20), allow_redirects=True, headers={"Referer": first.url})
        else:
            response = self.session.get(action, params=payload, timeout=(10, 20), allow_redirects=True, headers={"Referer": first.url})

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = " ".join(soup.stripped_strings).lower()
        marker_hits = [m for m in ["orders", "logout", "wyloguj", "account"] if m in text]
        authenticated = not bool(soup.find("input", {"type": "password"})) and bool(marker_hits)

        return response, {
            "authenticated": authenticated,
            "final_url": response.url,
            "status_code": response.status_code,
            "authenticated_marker_hits": marker_hits[:10],
            "page_title": soup.title.get_text(" ", strip=True)[:200] if soup.title else "",
        }

    def _same_host(self, url: str) -> bool:
        return urlparse(url).netloc == urlparse(self.base_url).netloc

    def _collect_links(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        out, seen = [], set()
        for a in soup.find_all("a", href=True):
            href = urljoin(page_url, a["href"])
            if not self._same_host(href):
                continue
            href = href.split("#")[0]
            if not href or href in seen:
                continue
            seen.add(href)
            label = " ".join(a.stripped_strings).strip()
            out.append({"label": label[:160], "url": href})
        return out

    def _is_service_url(self, url: str) -> bool:
        path = urlparse(url).path.lower()
        return any(x in path for x in [
            "login.php", "signin.php", "logout", "basket", "order", "client-",
            "rma-", "shoppinglist", "products-bought", "products-requests",
            "noproduct.php", "contact", "newsletter"
        ])

    def _looks_like_product(self, item: dict) -> bool:
        url = item["url"].lower()
        label = item["label"].lower()
        path = urlparse(url).path.lower()
        if self._is_service_url(url):
            return False
        # IdoSell SEO convention on this shop: categories use eng_m_, products use eng_pm_.
        if "product-eng-" in path:
            return True
        if "eng_pm_" in path or "_pm_" in path:
            return True
        if "eng_m_" in path or "_m_" in path:
            return False
        if any(k in path for k in ["projector.php", "product.php", "/product/", "/products/"]):
            return True
        if any(k in url for k in ["-p-", "product_id=", "id_product=", "projector"]):
            return True
        if label and any(k in label for k in ["€", "size", "colour", "color"]) and "search.php" not in url:
            return True
        return False

    def _extract_menu_categories(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        anchors = []
        seen = set()

        menu = soup.find(id="menu_categories")
        containers = [menu] if menu else []

        for tag in soup.find_all(attrs={"class": True}):
            classes = " ".join(tag.get("class", [])).lower()
            if "category" in classes or "categories" in classes:
                containers.append(tag)

        for container in containers[:20]:
            if not container:
                continue
            for a in container.find_all("a", href=True):
                href = urljoin(page_url, a["href"]).split("#")[0]
                if not self._same_host(href) or href in seen or self._is_service_url(href):
                    continue
                seen.add(href)
                label = " ".join(a.stripped_strings).strip()
                if label:
                    anchors.append({"label": label[:160], "url": href})
        return anchors[:120]


    def _inspect_product_blocks(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        samples = []
        for img in soup.find_all("img", src=True):
            src = urljoin(page_url, img["src"])
            if "/hpeciai/" not in src:
                continue

            chain = []
            node = img
            for _ in range(6):
                node = node.parent
                if not node or not getattr(node, "name", None):
                    break
                attrs = {}
                for k, v in (node.attrs or {}).items():
                    if k in {"class", "id", "href", "action", "onclick"} or str(k).startswith("data-"):
                        attrs[k] = v
                links = []
                for a in node.find_all("a", href=True, limit=5):
                    links.append(urljoin(page_url, a["href"]).split("#")[0])
                inputs = []
                for inp in node.find_all("input", limit=10):
                    if inp.get("name"):
                        inputs.append({
                            "name": inp.get("name"),
                            "type": inp.get("type"),
                            "value": inp.get("value"),
                        })
                chain.append({
                    "tag": node.name,
                    "attrs": attrs,
                    "links": links,
                    "inputs": inputs,
                    "text": " ".join(node.stripped_strings)[:400],
                })

            samples.append({
                "image": src,
                "alt": (img.get("alt") or "")[:160],
                "ancestors": chain,
            })
            if len(samples) >= 5:
                break
        return samples

    def _extract_product_facts(self, html: str, page_url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        facts = {}

        # Common IdoSell specification rows / definition lists / labeled containers.
        pairs = []
        for row in soup.find_all(["tr", "li", "div", "p", "dl"]):
            text = " ".join(row.stripped_strings).strip()
            low = text.lower()
            if not text or len(text) > 600:
                continue
            if any(k in low for k in [
                "ean", "symbol", "code", "price", "regular price",
                "availability", "stock", "quantity", "size", "color",
                "colour", "weight", "producer", "manufacturer"
            ]):
                pairs.append(text)

        # Structured attributes often carry exact values even when visual labels vary.
        attrs = []
        for tag in soup.find_all(True):
            selected = {}
            for k, v in (tag.attrs or {}).items():
                ks = str(k).lower()
                if any(x in ks for x in [
                    "ean", "code", "symbol", "product", "size", "stock",
                    "quantity", "price", "availability", "color", "weight"
                ]):
                    selected[k] = v
            if selected:
                attrs.append({
                    "tag": tag.name,
                    "attrs": selected,
                    "text": " ".join(tag.stripped_strings)[:220],
                })
            if len(attrs) >= 80:
                break

        variants = []
        seen = set()
        for inp in soup.find_all("input"):
            name = inp.get("name") or ""
            if name.startswith("product["):
                variant_key = name.split("[", 1)[1].split("]", 1)[0]
                if variant_key in seen:
                    continue
                seen.add(variant_key)
                block = inp
                for _ in range(4):
                    block = block.parent
                    if not block:
                        break
                    t = " ".join(block.stripped_strings).strip()
                    if t and len(t) < 1200:
                        variants.append({
                            "variant_key": variant_key,
                            "product_value": inp.get("value"),
                            "text": t[:800],
                        })
                        break

        # Schema.org / JSON-LD can contain EAN/GTIN, SKU, price and availability.
        jsonld = []
        import json as _json
        for script in soup.find_all("script", {"type": "application/ld+json"}):
            raw = script.string or script.get_text()
            if not raw:
                continue
            try:
                data = _json.loads(raw)
                jsonld.append(data)
            except Exception:
                continue

        return {
            "label_value_texts": pairs[:80],
            "structured_attrs": attrs[:80],
            "variants": variants[:30],
            "jsonld": jsonld[:10],
        }

    def _inspect_page_fields(self, html: str, page_url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(" ", strip=True)[:200] if soup.title else ""
        text = " ".join(soup.stripped_strings)

        images = []
        for img in soup.find_all("img", src=True):
            src = urljoin(page_url, img["src"])
            alt = (img.get("alt") or "").strip()
            if "logo_" in src or "poweredby" in src or "checkup.php" in src:
                continue
            images.append({"src": src, "alt": alt[:120]})

        keywords = [
            "ean", "gtin", "barcode", "sku", "symbol", "code", "catalog",
            "price", "vat", "availability", "stock", "quantity", "warehouse",
            "size", "colour", "color", "weight"
        ]
        lower = text.lower()
        detected = [kw for kw in keywords if kw in lower]

        tables = []
        for table in soup.find_all("table")[:10]:
            rows = []
            for tr in table.find_all("tr")[:30]:
                cells = [" ".join(c.stripped_strings)[:180] for c in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)

        forms = []
        for form in soup.find_all("form")[:10]:
            fields = []
            for tag in form.find_all(["input", "select", "textarea"]):
                fields.append({
                    "tag": tag.name,
                    "type": (tag.get("type") or tag.name or "").lower(),
                    "name": tag.get("name"),
                })
            forms.append({
                "action": urljoin(page_url, form.get("action") or page_url),
                "method": (form.get("method") or "GET").upper(),
                "fields": fields[:30],
            })

        return {
            "url": page_url,
            "page_title": title,
            "detected_keywords": detected,
            "images": images[:30],
            "tables": tables[:8],
            "forms": forms[:8],
            "facts": self._extract_product_facts(html, page_url),
        }

    def authenticated_audit(self) -> dict:
        if not self.login or not self.password:
            return {"authenticated": False, "reason": "credentials_not_configured"}

        response, auth = self._authenticate()
        if response is None or not auth.get("authenticated"):
            return auth

        home_links = self._collect_links(response.text, response.url)
        categories = self._extract_menu_categories(response.text, response.url)

        # Probe categories and search/promotions to discover real product URLs.
        discovery_pages = []
        seed_urls = [urljoin(self.base_url, "search.php?promo=y")]
        seed_urls += [c["url"] for c in categories[:12]]

        product_candidates = []
        seen_products = set()
        product_block_samples = []

        for url in seed_urls[:15]:
            try:
                r = self.session.get(url, timeout=30, allow_redirects=True)
                r.raise_for_status()
                links = self._collect_links(r.text, r.url)
                product_links = [x for x in links if self._looks_like_product(x)]

                # Product cards often wrap the product image in the canonical product link.
                soup = BeautifulSoup(r.text, "html.parser")
                if not product_block_samples:
                    product_block_samples = self._inspect_product_blocks(r.text, r.url)

                for img in soup.find_all("img", src=True):
                    a = img.find_parent("a", href=True)
                    if a:
                        href = urljoin(r.url, a["href"]).split("#")[0]
                        item = {"label": (img.get("alt") or " ".join(a.stripped_strings)).strip()[:160], "url": href}
                        if self._same_host(href) and self._looks_like_product(item):
                            product_links.append(item)

                    parent = img.parent
                    for _ in range(4):
                        if not parent:
                            break
                        product_id = parent.attrs.get("data-product-id") or parent.attrs.get("data-product_id")
                        if product_id:
                            for aa in parent.find_all("a", href=True, limit=6):
                                href = urljoin(r.url, aa["href"]).split("#")[0]
                                item = {"label": (img.get("alt") or "").strip()[:160], "url": href}
                                if self._same_host(href) and self._looks_like_product(item):
                                    product_links.append(item)
                                    break
                            break
                        parent = parent.parent

                dedup = []
                seen_page = set()
                for item in product_links:
                    if item["url"] not in seen_page:
                        seen_page.add(item["url"])
                        dedup.append(item)
                product_links = dedup
                for item in product_links:
                    if item["url"] not in seen_products:
                        seen_products.add(item["url"])
                        product_candidates.append(item)
                discovery_pages.append({
                    "url": r.url,
                    "title": BeautifulSoup(r.text, "html.parser").title.get_text(" ", strip=True)[:160]
                    if BeautifulSoup(r.text, "html.parser").title else "",
                    "links_seen": len(links),
                    "product_candidates_found": len(product_links),
                    "sample_product_links": product_links[:8],
                })
            except Exception as exc:
                discovery_pages.append({"url": url, "error": type(exc).__name__})

        sample_pages = []
        for item in product_candidates[:5]:
            try:
                r = self.session.get(item["url"], timeout=30, allow_redirects=True)
                r.raise_for_status()
                if "noproduct.php" in r.url.lower():
                    continue
                sample_pages.append(self._inspect_page_fields(r.text, r.url))
            except Exception as exc:
                sample_pages.append({"url": item["url"], "error": type(exc).__name__})
            if len(sample_pages) >= 3:
                break

        auth.update({
            "category_links": categories,
            "discovery_pages": discovery_pages[:15],
            "product_candidates": product_candidates[:30],
            "product_block_samples": product_block_samples[:5],
            "sample_product_pages": sample_pages,
            "total_home_links_seen": len(home_links),
        })
        return auth
