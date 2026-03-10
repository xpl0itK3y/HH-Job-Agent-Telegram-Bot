from app.services.vacancy_content_service import VacancyContentService


class _DummySession:
    def close(self) -> None:
        return None


class _DummyRepo:
    def __init__(self, session) -> None:
        self.session = session

    def get_cached_summary(self, **kwargs):
        return None


def test_vacancy_content_service_falls_back_to_clean_description(monkeypatch) -> None:
    service = VacancyContentService()
    monkeypatch.setattr("app.services.vacancy_content_service.SessionLocal", lambda: _DummySession())
    monkeypatch.setattr("app.services.vacancy_content_service.VacancyRepository", _DummyRepo)
    monkeypatch.setattr(service.deepseek_client, "summarize_vacancy_description", lambda text: "")

    enriched = service.enrich(
        {
            "provider": "hh_kz",
            "hh_vacancy_id": "1",
            "description_raw": "<p>Hello <b>world</b></p>",
        }
    )
    assert enriched["description_clean"] == "Hello world"
    assert enriched["description_ai_summary"] == "Hello world"
