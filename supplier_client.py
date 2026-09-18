from urllib.parse import urljoin

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

    def login_and_audit(self) -> dict:
        first = self.session.get(self.signin_url(), timeout=30)
        first.raise_for_status()

        index, form = self._find_login_form(first.text, first.url)
        if form is None:
            return {"authenticated": False, "reason": "login_form_not_found"}

        action = urljoin(first.url, form.get("action") or first.url)
        method = (form.get("method") or "GET").upper()
        payload = self._build_login_payload(form)

        if method == "POST":
            response = self.session.post(
                action,
                data=payload,
                timeout=30,
                allow_redirects=True,
                headers={"Referer": first.url},
            )
        else:
            response = self.session.get(
                action,
                params=payload,
                timeout=30,
                allow_redirects=True,
                headers={"Referer": first.url},
            )

        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        still_has_password = bool(soup.find("input", {"type": "password"}))
        text = " ".join(soup.stripped_strings).lower()
        authenticated_markers = [
            "log out",
            "logout",
            "wyloguj",
            "my account",
            "your account",
            "account details",
            "orders",
        ]
        marker_hits = [m for m in authenticated_markers if m in text]

        links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(response.url, a["href"])
            label = " ".join(a.stripped_strings).strip()
            combined = f"{label} {href}".lower()
            if any(key in combined for key in [
                "product", "category", "offer", "catalog", "search",
                "order", "account", "discount", "stock"
            ]):
                links.append({"label": label[:120], "url": href})

        deduped = []
        seen = set()
        for item in links:
            key = item["url"]
            if key not in seen:
                seen.add(key)
                deduped.append(item)

        authenticated = (not still_has_password) and bool(marker_hits)

        return {
            "authenticated": authenticated,
            "final_url": response.url,
            "status_code": response.status_code,
            "login_form_index": index,
            "still_has_password_form": still_has_password,
            "authenticated_marker_hits": marker_hits[:10],
            "candidate_links": deduped[:40],
            "page_title": soup.title.get_text(" ", strip=True)[:200] if soup.title else "",
        }

    def authenticated_audit(self) -> dict:
        if not self.login or not self.password:
            return {
                "authenticated": False,
                "reason": "credentials_not_configured",
            }
        return self.login_and_audit()
