from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class FjordNansenClient:
    def __init__(self, base_url: str, login: str = "", password: str = ""):
        self.base_url = base_url.rstrip("/") + "/"
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Outfish-Fjord-Nansen-Sync/0.1"
        })

    def signin_url(self) -> str:
        return urljoin(self.base_url, "signin.php")

    def _find_login_form(self, html: str, page_url: str):
        soup = BeautifulSoup(html, "html.parser")
        for index, form in enumerate(soup.find_all("form")):
            if form.find("input", {"type": "password"}):
                return index, form
        return None, None

    def _sanitized_login_form(self, html: str, page_url: str) -> dict:
        index, form = self._find_login_form(html, page_url)
        if form is None:
            return {}

        fields = []
        for tag in form.find_all(["input", "select", "textarea"]):
            field_type = (tag.get("type") or tag.name or "").lower()
            fields.append({
                "tag": tag.name,
                "type": field_type,
                "name": tag.get("name"),
                "has_value": bool(tag.get("value")),
            })

        return {
            "index": index,
            "method": (form.get("method") or "GET").upper(),
            "action": urljoin(page_url, form.get("action") or page_url),
            "fields": fields,
        }

    def inspect_public_signin(self) -> dict:
        response = self.session.get(self.signin_url(), timeout=30)
        response.raise_for_status()
        login_form = self._sanitized_login_form(response.text, response.url)
        return {
            "url": response.url,
            "status_code": response.status_code,
            "reachable": True,
            "login_form": login_form,
            "login_forms_found": 1 if login_form else 0,
        }

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

    def _authenticate(self):
        first = self.session.get(self.signin_url(), timeout=30)
        first.raise_for_status()
        index, form = self._find_login_form(first.text, first.url)
        if form is None:
            return None, {"authenticated": False, "reason": "login_form_not_found"}

        action = urljoin(first.url, form.get("action") or first.url)
        method = (form.get("method") or "GET").upper()
        payload = self._build_login_payload(form)

        if method == "POST":
            response = self.session.post(
                action, data=payload, timeout=30, allow_redirects=True,
                headers={"Referer": first.url},
            )
        else:
            response = self.session.get(
                action, params=payload, timeout=30, allow_redirects=True,
                headers={"Referer": first.url},
            )

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
            if href in seen:
                continue
            seen.add(href)
            label = " ".join(a.stripped_strings).strip()
            out.append({"label": label[:160], "url": href})
        return out

    def _classify_links(self, links: list[dict]) -> dict:
        categories, products, searches = [], [], []
        for item in links:
            s = f"{item['label']} {item['url']}".lower()
            if any(k in s for k in ["category", "menu_categories", "categories"]):
                categories.append(item)
            if any(k in s for k in [
                "product.php", "product-", "/product/", "projector.php",
                "towar", "item.php", "details.php"
            ]):
                products.append(item)
            if "search.php" in s:
                searches.append(item)
        return {
            "category_links": categories[:80],
            "product_links": products[:40],
            "search_links": searches[:20],
        }

    def _inspect_page_fields(self, html: str, page_url: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(" ", strip=True)[:200] if soup.title else ""
        text = " ".join(soup.stripped_strings)

        images = []
        for img in soup.find_all("img", src=True):
            src = urljoin(page_url, img["src"])
            alt = (img.get("alt") or "").strip()
            images.append({"src": src, "alt": alt[:120]})

        labels = []
        keywords = [
            "ean", "gtin", "barcode", "sku", "symbol", "code", "catalog",
            "price", "vat", "availability", "stock", "quantity", "warehouse",
            "size", "colour", "color", "weight"
        ]
        lower = text.lower()
        for kw in keywords:
            if kw in lower:
                labels.append(kw)

        tables = []
        for table in soup.find_all("table")[:10]:
            rows = []
            for tr in table.find_all("tr")[:20]:
                cells = [" ".join(c.stripped_strings)[:160] for c in tr.find_all(["th", "td"])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append(rows)

        return {
            "url": page_url,
            "page_title": title,
            "detected_keywords": labels,
            "images": images[:20],
            "tables": tables[:5],
        }

    def authenticated_audit(self) -> dict:
        if not self.login or not self.password:
            return {"authenticated": False, "reason": "credentials_not_configured"}

        response, auth = self._authenticate()
        if response is None or not auth.get("authenticated"):
            return auth

        links = self._collect_links(response.text, response.url)
        classified = self._classify_links(links)

        # Inspect search results for a generic in-stock catalogue sample if possible.
        sample_pages = []
        candidates = classified["product_links"][:3]
        if not candidates:
            search_candidates = classified["search_links"][:2]
            for item in search_candidates:
                try:
                    r = self.session.get(item["url"], timeout=30, allow_redirects=True)
                    r.raise_for_status()
                    more = self._classify_links(self._collect_links(r.text, r.url))["product_links"]
                    candidates.extend(more[:3])
                except Exception:
                    pass

        seen = set()
        for item in candidates:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            try:
                r = self.session.get(item["url"], timeout=30, allow_redirects=True)
                r.raise_for_status()
                sample_pages.append(self._inspect_page_fields(r.text, r.url))
            except Exception as exc:
                sample_pages.append({"url": item["url"], "error": type(exc).__name__})
            if len(sample_pages) >= 3:
                break

        auth.update({
            "navigation": classified,
            "sample_product_pages": sample_pages,
            "total_internal_links_seen": len(links),
        })
        return auth
