from sqlalchemy.orm import Session

from app.db.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus, SentVacancy
from app.db.models.user import BotStatus, User
from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.session import session_scope


class AdminActionsService:
    def pause_user(self, user_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            user.bot_status = BotStatus.PAUSED
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="pause_user",
                entity_type="user",
                entity_id=str(user_id),
                details_json={"bot_status": BotStatus.PAUSED.value},
            )
            session.flush()
            return {"ok": True, "message": f"User {user_id} paused"}

    def resume_user(self, user_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            user.bot_status = BotStatus.ACTIVE
            reminder_repo = ScheduledReminderRepository(session)
            for reminder in reminder_repo.get_pending(user_id=user.id, reminder_type="resume_search"):
                reminder_repo.mark_cancelled(reminder.id)
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="resume_user",
                entity_type="user",
                entity_id=str(user_id),
                details_json={"bot_status": BotStatus.ACTIVE.value},
            )
            session.flush()
            return {"ok": True, "message": f"User {user_id} resumed"}

    def requeue_sent_vacancy(self, sent_vacancy_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            sent_vacancy = session.get(SentVacancy, sent_vacancy_id)
            if sent_vacancy is None:
                return {"ok": False, "message": "Sent vacancy not found"}
            sent_vacancy.processing_status = ProcessingStatus.QUEUED
            sent_vacancy.current_pipeline_step = PipelineStep.CLEANING
            sent_vacancy.last_error_text = None
            sent_vacancy.processing_started_at = None
            sent_vacancy.ready_to_send_at = None
            sent_vacancy.failed_at = None
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="requeue_sent_vacancy",
                entity_type="sent_vacancy",
                entity_id=str(sent_vacancy_id),
                details_json={"processing_status": ProcessingStatus.QUEUED.value},
            )
            session.flush()
            return {"ok": True, "message": f"Sent vacancy {sent_vacancy_id} moved to queue"}

    def mark_sent_vacancy_failed(
        self,
        sent_vacancy_id: int,
        error_text: str,
        *,
        admin_user_id: int | None = None,
    ) -> dict:
        with session_scope() as session:
            sent_vacancy = session.get(SentVacancy, sent_vacancy_id)
            if sent_vacancy is None:
                return {"ok": False, "message": "Sent vacancy not found"}
            sent_vacancy.processing_status = ProcessingStatus.FAILED
            sent_vacancy.last_error_text = error_text or "Manually marked as failed"
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="mark_sent_vacancy_failed",
                entity_type="sent_vacancy",
                entity_id=str(sent_vacancy_id),
                details_json={
                    "processing_status": ProcessingStatus.FAILED.value,
                    "error_text": sent_vacancy.last_error_text,
                },
            )
            session.flush()
            return {"ok": True, "message": f"Sent vacancy {sent_vacancy_id} marked failed"}

    @staticmethod
    def _write_audit_log(
        *,
        session: Session,
        admin_user_id: int | None,
        action_type: str,
        entity_type: str,
        entity_id: str,
        details_json: dict | None = None,
    ) -> None:
        if admin_user_id is None:
            return
        AdminAuditLogRepository(session).create(
            admin_user_id=admin_user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details_json=details_json,
        )
