from dataclasses import dataclass


@dataclass(frozen=True)
class HHProviderConfig:
    country_code: str
    provider: str
    api_base_url: str
    site_base_url: str
    default_area_id: int


PROVIDERS: dict[str, HHProviderConfig] = {
    "KZ": HHProviderConfig(
        country_code="KZ",
        provider="hh_kz",
        api_base_url="https://api.hh.kz",
        site_base_url="https://hh.kz",
        default_area_id=40,
    ),
}


def get_provider_config(country_code: str) -> HHProviderConfig:
    try:
        return PROVIDERS[country_code.upper()]
    except KeyError as exc:
        raise ValueError(f"Unsupported country code: {country_code}") from exc
