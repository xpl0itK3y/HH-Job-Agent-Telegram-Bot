from enum import StrEnum


class CountryChoice(StrEnum):
    KZ = "KZ"
    RU = "RU"
    KZ_RU = "KZ+RU"


def resolve_selected_countries(selected: str) -> list[str]:
    normalized = selected.strip().upper()
    if normalized == CountryChoice.KZ:
        return [CountryChoice.KZ]
    if normalized == CountryChoice.RU:
        return [CountryChoice.RU]
    if normalized in {CountryChoice.KZ_RU, "RU+KZ", "KZ + RU", "RU + KZ"}:
        return [CountryChoice.KZ, CountryChoice.RU]
    raise ValueError(f"Unsupported country selection: {selected}")
