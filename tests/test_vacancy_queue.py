from app.db.models.user import BotStatus
from app.tasks.monitor import monitor_new_vacancies


class _DummyUser:
    id = 7
    bot_status = BotStatus.ACTIVE


class _DummyUserRepo:
    def get_by_telegram_user_id(self, telegram_user_id: int):
        return _DummyUser()


class _DummySettings:
    is_enabled = True


class _DummySettingsRepo:
    def get_or_create(self, user_id: int):
        return _DummySettings()


class _DummyScope:
    def __enter__(self):
        return object()

    def __exit__(self, exc_type, exc, tb):
        return False


def test_monitor_new_vacancies_queues_found_vacancies(monkeypatch) -> None:
    queued: list[tuple[int, int]] = []

    class _DummySearchService:
        def search_for_user(self, *, telegram_user):
            return [{"id": 101}, {"id": 102}]

    monkeypatch.setattr("app.tasks.monitor.session_scope", lambda: _DummyScope())
    monkeypatch.setattr("app.tasks.monitor.UserRepository", lambda session: _DummyUserRepo())
    monkeypatch.setattr("app.tasks.monitor.SearchSettingRepository", lambda session: _DummySettingsRepo())
    monkeypatch.setattr("app.tasks.monitor.VacancySearchService", lambda: _DummySearchService())
    monkeypatch.setattr(
        "app.tasks.monitor.analyze_and_send_vacancy.delay",
        lambda telegram_user_id, vacancy_id: queued.append((telegram_user_id, vacancy_id)),
    )

    result = monitor_new_vacancies(11)
    assert result == {"status": "queued", "telegram_user_id": 11, "count": 2}
    assert queued == [(11, 101), (11, 102)]


def test_monitor_new_vacancies_skips_paused_user(monkeypatch) -> None:
    class _PausedUser:
        id = 7
        bot_status = BotStatus.PAUSED

    class _PausedUserRepo:
        def get_by_telegram_user_id(self, telegram_user_id: int):
            return _PausedUser()

    monkeypatch.setattr("app.tasks.monitor.session_scope", lambda: _DummyScope())
    monkeypatch.setattr("app.tasks.monitor.UserRepository", lambda session: _PausedUserRepo())
    monkeypatch.setattr("app.tasks.monitor.SearchSettingRepository", lambda session: _DummySettingsRepo())

    result = monitor_new_vacancies(11)
    assert result == {"status": "disabled", "telegram_user_id": 11}
