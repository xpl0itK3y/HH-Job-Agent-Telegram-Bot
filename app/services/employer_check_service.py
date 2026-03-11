from urllib.parse import urlparse

import httpx

from app.integrations.hh.client import HHClient
from app.integrations.whois.service import WhoisService


class EmployerCheckService:
    def __init__(self) -> None:
        self.hh_client = HHClient(timeout=15.0)
        self.whois_service = WhoisService()

    def check_employer(self, *, provider: str, employer_id: str) -> dict:
        try:
            employer = self.hh_client.get_employer(provider, employer_id)
        except httpx.HTTPError as exc:
            return {
                "score": 0,
                "status": "Проверка недоступна",
                "site_url": None,
                "signals": ["hh_lookup_failed"],
                "error": str(exc),
            }
        return self.evaluate_employer(employer)

    def evaluate_employer(self, employer: dict) -> dict:
        site_url = employer.get("site_url")
        score = 0
        signals: list[str] = []

        if employer.get("trusted"):
            score += 2
            signals.append("trusted_hh")
        if site_url:
            score += 1
            signals.append("site_present")
        if site_url and self._site_is_alive(site_url):
            score += 1
            signals.append("site_alive")
        if site_url and self.whois_service.has_valid_domain(self._extract_domain(site_url)):
            score += 1
            signals.append("whois_valid")
        if employer.get("logo_urls"):
            score += 1
            signals.append("logo_present")
        if employer.get("open_vacancies") or employer.get("vacancies_url"):
            score += 1
            signals.append("hh_activity")

        return {
            "score": score,
            "status": self._status_from_score(score),
            "site_url": site_url,
            "signals": signals,
        }

    def _site_is_alive(self, url: str) -> bool:
        try:
            response = httpx.get(url, timeout=5.0, follow_redirects=True)
        except httpx.HTTPError:
            return False
        return response.status_code < 400

    def _extract_domain(self, url: str) -> str:
        parsed = urlparse(url if "://" in url else f"https://{url}")
        return parsed.netloc or parsed.path

    def _status_from_score(self, score: int) -> str:
        if score >= 5:
            return "Надежно"
        if score >= 3:
            return "Нужна дополнительная проверка"
        return "Есть риски"
