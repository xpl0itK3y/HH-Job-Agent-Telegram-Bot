from enum import StrEnum


class CountryChoice(StrEnum):
    KZ = "KZ"


def resolve_selected_countries(selected: str) -> list[str]:
    normalized = selected.strip().upper()
    if normalized == CountryChoice.KZ:
        return [CountryChoice.KZ]
    raise ValueError(f"Unsupported country selection: {selected}")
