from collections.abc import Iterable
from typing import Any


def merge_vacancy_results(*market_results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for vacancies in market_results:
        merged.extend(vacancies)
    return merged


def deduplicate_vacancies(vacancies: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for vacancy in vacancies:
        key = (
            str(vacancy.get("provider", "")),
            str(vacancy.get("hh_vacancy_id", vacancy.get("id", ""))),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(vacancy)

    return unique
