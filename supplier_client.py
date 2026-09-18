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

    def inspect_public_signin(self) -> dict:
        response = self.session.get(self.signin_url(), timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        forms = soup.find_all("form")
        password_inputs = soup.find_all("input", {"type": "password"})

        return {
            "url": response.url,
            "status_code": response.status_code,
            "forms_found": len(forms),
            "password_fields_found": len(password_inputs),
            "reachable": True,
        }

    def authenticated_audit(self) -> dict:
        # Login implementation is deliberately deferred until credentials are
        # present and the real form/action/field names can be inspected safely.
        # This prevents guessing the supplier authentication flow.
        if not self.login or not self.password:
            return {
                "authenticated": False,
                "reason": "credentials_not_configured",
            }

        return {
            "authenticated": False,
            "reason": "credentials_present_login_mapping_pending",
        }
