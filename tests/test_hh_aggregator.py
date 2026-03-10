from app.integrations.hh.aggregator import deduplicate_vacancies


def test_deduplicate_vacancies_by_provider_and_hh_id() -> None:
    vacancies = [
        {"provider": "hh_kz", "hh_vacancy_id": "1", "title": "A"},
        {"provider": "hh_kz", "hh_vacancy_id": "1", "title": "B"},
        {"provider": "hh_ru", "hh_vacancy_id": "1", "title": "C"},
    ]
    result = deduplicate_vacancies(vacancies)
    assert len(result) == 2
    assert result[0]["title"] == "A"
    assert result[1]["title"] == "C"
