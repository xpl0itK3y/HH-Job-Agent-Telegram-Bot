from typing import Any

import httpx

from app.integrations.hh.config import HHProviderConfig, PROVIDERS, get_provider_config


class HHClient:
    def __init__(self, timeout: float = 20.0) -> None:
        self.timeout = timeout

    def search_vacancies(self, provider: str, filters: dict[str, Any]) -> list[dict[str, Any]]:
        config = self.get_provider_config(provider)
        params = {
            "text": filters.get("text"),
            "area": filters.get("area") or config.default_area_id,
            "per_page": filters.get("per_page", 20),
            "page": filters.get("page", 0),
            "employment": filters.get("employment"),
            "schedule": filters.get("schedule"),
        }
        response = self._request("GET", config, "/vacancies", params=_drop_none(params))
        return response.get("items", [])

    def get_vacancy(self, provider: str, vacancy_id: str) -> dict[str, Any]:
        config = self.get_provider_config(provider)
        return self._request("GET", config, f"/vacancies/{vacancy_id}")

    def get_employer(self, provider: str, employer_id: str) -> dict[str, Any]:
        config = self.get_provider_config(provider)
        return self._request("GET", config, f"/employers/{employer_id}")

    def get_provider_config(self, provider: str) -> HHProviderConfig:
        normalized = provider.upper()
        if normalized in PROVIDERS:
            return get_provider_config(normalized)

        for config in PROVIDERS.values():
            if config.provider == provider:
                return config
        raise ValueError(f"Unsupported HH provider: {provider}")

    def _request(
        self,
        method: str,
        config: HHProviderConfig,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method,
                f"{config.api_base_url.rstrip('/')}{path}",
                params=params,
            )
            response.raise_for_status()
            return response.json()


def _drop_none(values: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in values.items() if value is not None}
