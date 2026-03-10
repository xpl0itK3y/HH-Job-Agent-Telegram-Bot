from types import SimpleNamespace

from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus
from app.db.models.user import BotStatus
from admin_app.services.admin_actions_service import AdminActionsService


class _DummyExecuteResult:
    def __init__(self, rowcount: int) -> None:
        self.rowcount = rowcount


class _DummySession:
    def __init__(self) -> None:
        self.users: dict[int, object] = {}
        self.sent_vacancies: dict[int, object] = {}
        self.resumes: dict[int, object] = {}
        self.rowcounts: dict[str, int] = {}
        self.deleted: list[object] = []

    def get(self, model, entity_id: int):
        model_name = model.__name__
        if model_name == "User":
            return self.users.get(entity_id)
        if model_name == "SentVacancy":
            return self.sent_vacancies.get(entity_id)
        return None

    def execute(self, stmt):
        table_name = stmt.table.name
        return _DummyExecuteResult(self.rowcounts.get(table_name, 0))

    def delete(self, obj) -> None:
        self.deleted.append(obj)

    def flush(self) -> None:
        return None


class _DummyScope:
    def __init__(self, session: _DummySession) -> None:
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class _AuditRecorder:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def create(self, **kwargs):
        self.entries.append(kwargs)
        return SimpleNamespace(**kwargs)


def test_pause_user_updates_status_and_writes_audit(monkeypatch) -> None:
    session = _DummySession()
    session.users[7] = SimpleNamespace(id=7, bot_status=BotStatus.ACTIVE)
    audit = _AuditRecorder()

    monkeypatch.setattr("admin_app.services.admin_actions_service.session_scope", lambda: _DummyScope(session))
    monkeypatch.setattr("admin_app.services.admin_actions_service.AdminAuditLogRepository", lambda session: audit)

    service = AdminActionsService()
    result = service.pause_user(7, admin_user_id=99)

    assert result["ok"] is True
    assert session.users[7].bot_status == BotStatus.PAUSED
    assert audit.entries[0]["action_type"] == "pause_user"
    assert audit.entries[0]["admin_user_id"] == 99


def test_rerun_sent_vacancy_resets_state_and_enqueues_task(monkeypatch) -> None:
    session = _DummySession()
    session.users[5] = SimpleNamespace(id=5, telegram_user_id=123456)
    session.sent_vacancies[11] = SimpleNamespace(
        id=11,
        user_id=5,
        vacancy_id=77,
        processing_status=ProcessingStatus.FAILED,
        current_pipeline_step=PipelineStep.MATCH_ANALYSIS,
        last_error_text="boom",
        processing_started_at="started",
        ready_to_send_at="ready",
        failed_at="failed",
    )
    audit = _AuditRecorder()
    queued: list[tuple[int, int]] = []

    monkeypatch.setattr("admin_app.services.admin_actions_service.session_scope", lambda: _DummyScope(session))
    monkeypatch.setattr("admin_app.services.admin_actions_service.AdminAuditLogRepository", lambda session: audit)
    monkeypatch.setattr(
        "admin_app.services.admin_actions_service.analyze_and_send_vacancy.delay",
        lambda telegram_user_id, vacancy_id: queued.append((telegram_user_id, vacancy_id)),
    )

    service = AdminActionsService()
    result = service.rerun_sent_vacancy(11, admin_user_id=42)

    sent = session.sent_vacancies[11]
    assert result["ok"] is True
    assert sent.processing_status == ProcessingStatus.QUEUED
    assert sent.current_pipeline_step == PipelineStep.CLEANING
    assert sent.last_error_text is None
    assert queued == [(123456, 77)]
    assert audit.entries[0]["action_type"] == "rerun_sent_vacancy"


def test_reprocess_resume_creates_new_resume_and_audit(monkeypatch) -> None:
    session = _DummySession()
    session.users[3] = SimpleNamespace(id=3)
    latest_resume = SimpleNamespace(
        id=8,
        source_type=SimpleNamespace(value="text"),
        file_path=None,
        resume_link=None,
        raw_text="python backend engineer",
    )
    created_payload: dict = {}
    audit = _AuditRecorder()

    class _ResumeRepo:
        def __init__(self, session_obj) -> None:
            self.session = session_obj

        def get_latest_by_user_id(self, user_id: int):
            return latest_resume

        def create(self, **kwargs):
            created_payload.update(kwargs)
            return SimpleNamespace(id=99, **kwargs)

    class _Deepseek:
        settings = SimpleNamespace(deepseek_model="deepseek-test")

        def extract_resume_profile(self, text: str):
            return SimpleNamespace(summary="summary", model_dump=lambda: {"summary": "summary", "status": "ok"})

    monkeypatch.setattr("admin_app.services.admin_actions_service.session_scope", lambda: _DummyScope(session))
    monkeypatch.setattr("admin_app.services.admin_actions_service.ResumeRepository", _ResumeRepo)
    monkeypatch.setattr("admin_app.services.admin_actions_service.AdminAuditLogRepository", lambda session: audit)

    service = AdminActionsService()
    service.deepseek_client = _Deepseek()
    result = service.reprocess_resume(3, admin_user_id=55)

    assert result["ok"] is True
    assert created_payload["user_id"] == 3
    assert created_payload["raw_text"] == "python backend engineer"
    assert created_payload["summary"] == "summary"
    assert audit.entries[0]["action_type"] == "reprocess_resume"


def test_delete_user_removes_related_entities_and_writes_audit(monkeypatch) -> None:
    session = _DummySession()
    user = SimpleNamespace(id=10)
    session.users[10] = user
    session.rowcounts = {
        "chat_messages": 4,
        "sent_vacancies": 2,
        "resumes": 1,
        "search_settings": 1,
        "scheduled_reminders": 3,
    }
    audit = _AuditRecorder()

    monkeypatch.setattr("admin_app.services.admin_actions_service.session_scope", lambda: _DummyScope(session))
    monkeypatch.setattr("admin_app.services.admin_actions_service.AdminAuditLogRepository", lambda session: audit)

    service = AdminActionsService()
    result = service.delete_user(10, admin_user_id=1)

    assert result["ok"] is True
    assert user in session.deleted
    assert audit.entries[0]["action_type"] == "delete_user"
    assert audit.entries[0]["details_json"]["deleted_chat"] == 4
