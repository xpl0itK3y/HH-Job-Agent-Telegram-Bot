from collections.abc import Iterable
from typing import Any


def merge_vacancy_results(*market_results: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for vacancies in market_results:
        merged.extend(vacancies)
    return merged
