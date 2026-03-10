from app.services.vacancy_pipeline_service import VacancyPipelineService


class _DummyUser:
    id = 5


class _DummyUserRepo:
    def get_by_telegram_user_id(self, telegram_user_id: int):
        return _DummyUser()


class _DummySentRepo:
    def __init__(self, session) -> None:
        self.called_with = None

    def mark_ready_to_send(self, *, user_id: int, vacancy_id: int):
        self.called_with = (user_id, vacancy_id)
        return None


class _DummyScope:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


def test_prepare_vacancy_marks_ready_to_send(monkeypatch) -> None:
    service = VacancyPipelineService()
    sent_repo = _DummySentRepo(None)
    prepared_payload = {"vacancy_id": 99, "vacancy_tag": "#VAC_00099"}

    monkeypatch.setattr("app.services.vacancy_pipeline_service.session_scope", lambda: _DummyScope())
    monkeypatch.setattr("app.services.vacancy_pipeline_service.UserRepository", lambda session: _DummyUserRepo())
    monkeypatch.setattr("app.services.vacancy_pipeline_service.SentVacancyRepository", lambda session: sent_repo)
    monkeypatch.setattr(service.vacancy_ai_service, "analyze_and_prepare", lambda **kwargs: prepared_payload)

    telegram_user = type("TelegramUser", (), {"id": 11})()
    result = service.prepare_vacancy(telegram_user=telegram_user, vacancy_id=99)
    assert result == prepared_payload
    assert sent_repo.called_with == (5, 99)
