from datetime import UTC, datetime

from app.db.models.user import BotStatus
from app.services.user_control_service import UserControlService


class DummyReminderRepo:
    def __init__(self) -> None:
        self.created = []
        self.pending = [type("Reminder", (), {"id": 10})()]
        self.cancelled = []

    def create(self, **kwargs):
        self.created.append(kwargs)
        return type("Reminder", (), {"id": 1})()

    def get_pending(self, **kwargs):
        return self.pending

    def mark_cancelled(self, reminder_id: int):
        self.cancelled.append(reminder_id)


class DummyUserRepo:
    def __init__(self) -> None:
        self.status = None
        self.user = type("User", (), {"id": 7})()

    def create_or_update_telegram_user(self, **kwargs):
        return self.user

    def set_bot_status(self, *, telegram_user_id: int, bot_status: BotStatus):
        self.status = bot_status
        return self.user


class DummySession:
    pass


def test_pause_sets_paused_and_creates_reminder(monkeypatch) -> None:
    service = UserControlService()
    user_repo = DummyUserRepo()
    reminder_repo = DummyReminderRepo()

    class DummyScope:
        def __enter__(self):
            return DummySession()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.services.user_control_service.session_scope", lambda: DummyScope())
    monkeypatch.setattr("app.services.user_control_service.UserRepository", lambda session: user_repo)
    monkeypatch.setattr("app.services.user_control_service.ScheduledReminderRepository", lambda session: reminder_repo)
    monkeypatch.setattr("app.services.user_control_service.send_resume_reminder.apply_async", lambda *args, **kwargs: None)

    telegram_user = type("TelegramUser", (), {"id": 11, "username": "u", "first_name": "F", "last_name": "L", "language_code": "ru"})()
    result = service.pause(telegram_user=telegram_user)
    assert user_repo.status == BotStatus.PAUSED
    assert reminder_repo.created
    assert result["bot_status"] == BotStatus.PAUSED


def test_resume_sets_active_and_cancels_reminders(monkeypatch) -> None:
    service = UserControlService()
    user_repo = DummyUserRepo()
    reminder_repo = DummyReminderRepo()

    class DummyScope:
        def __enter__(self):
            return DummySession()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr("app.services.user_control_service.session_scope", lambda: DummyScope())
    monkeypatch.setattr("app.services.user_control_service.UserRepository", lambda session: user_repo)
    monkeypatch.setattr("app.services.user_control_service.ScheduledReminderRepository", lambda session: reminder_repo)

    telegram_user = type("TelegramUser", (), {"id": 11, "username": "u", "first_name": "F", "last_name": "L", "language_code": "ru"})()
    result = service.resume(telegram_user=telegram_user)
    assert user_repo.status == BotStatus.ACTIVE
    assert reminder_repo.cancelled == [10]
    assert result["bot_status"] == BotStatus.ACTIVE
