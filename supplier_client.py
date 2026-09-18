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

    def _sanitized_login_forms(self, html: str, page_url: str) -> list[dict]:
        soup = BeautifulSoup(html, "html.parser")
        forms = []
        for index, form in enumerate(soup.find_all("form")):
            inputs = []
            has_password = False
            for tag in form.find_all(["input", "select", "textarea"]):
                field_type = (tag.get("type") or tag.name or "").lower()
                name = tag.get("name")
                if field_type == "password":
                    has_password = True
                inputs.append({
                    "tag": tag.name,
                    "type": field_type,
                    "name": name,
                    "has_value": bool(tag.get("value")),
                })

            if has_password:
                action = form.get("action") or page_url
                forms.append({
                    "index": index,
                    "method": (form.get("method") or "GET").upper(),
                    "action": urljoin(page_url, action),
                    "fields": inputs,
                })
        return forms

    def inspect_public_signin(self) -> dict:
        response = self.session.get(self.signin_url(), timeout=30)
        response.raise_for_status()

        login_forms = self._sanitized_login_forms(response.text, response.url)

        return {
            "url": response.url,
            "status_code": response.status_code,
            "reachable": True,
            "login_forms": login_forms,
            "login_forms_found": len(login_forms),
        }

    def authenticated_audit(self) -> dict:
        if not self.login or not self.password:
            return {
                "authenticated": False,
                "reason": "credentials_not_configured",
            }

        # Credentials are intentionally not submitted until the exact supplier
        # login form mapping has been observed from a real Render run.
        public = self.inspect_public_signin()
        return {
            "authenticated": False,
            "reason": "credentials_present_form_mapping_captured",
            "login_forms_found": public["login_forms_found"],
            "next_step": "map exact login field names and implement authenticated POST",
        }
