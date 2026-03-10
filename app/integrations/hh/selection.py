from enum import StrEnum


class CountryChoice(StrEnum):
    KZ = "KZ"
    RU = "RU"


def resolve_selected_countries(selected: str) -> list[str]:
    normalized = selected.strip().upper()
    if normalized == CountryChoice.KZ:
        return [CountryChoice.KZ]
    if normalized == CountryChoice.RU:
        return [CountryChoice.RU]
    raise ValueError(f"Unsupported country selection: {selected}")
