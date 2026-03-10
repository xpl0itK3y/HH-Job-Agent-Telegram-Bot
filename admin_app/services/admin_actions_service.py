from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.models.chat_message import ChatMessage
from app.db.repositories.admin_audit_log_repository import AdminAuditLogRepository
from app.db.repositories.resume_repository import ResumeRepository
from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus, SentVacancy
from app.db.models.user import BotStatus, User
from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.session import session_scope
from app.integrations.deepseek.client import DeepSeekClient
from app.tasks.analysis import analyze_and_send_vacancy


class AdminActionsService:
    def __init__(self) -> None:
        self.deepseek_client = DeepSeekClient()

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

    def rerun_sent_vacancy(self, sent_vacancy_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            sent_vacancy = session.get(SentVacancy, sent_vacancy_id)
            if sent_vacancy is None:
                return {"ok": False, "message": "Sent vacancy not found"}
            user = session.get(User, sent_vacancy.user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            sent_vacancy.processing_status = ProcessingStatus.QUEUED
            sent_vacancy.current_pipeline_step = PipelineStep.CLEANING
            sent_vacancy.last_error_text = None
            sent_vacancy.processing_started_at = None
            sent_vacancy.ready_to_send_at = None
            sent_vacancy.failed_at = None
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="rerun_sent_vacancy",
                entity_type="sent_vacancy",
                entity_id=str(sent_vacancy_id),
                details_json={"vacancy_id": sent_vacancy.vacancy_id, "user_id": sent_vacancy.user_id},
            )
            telegram_user_id = user.telegram_user_id
            vacancy_id = sent_vacancy.vacancy_id
            session.flush()

        analyze_and_send_vacancy.delay(telegram_user_id, vacancy_id)
        return {"ok": True, "message": f"Sent vacancy {sent_vacancy_id} restarted"}

    def reprocess_resume(self, user_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            latest_resume = ResumeRepository(session).get_latest_by_user_id(user_id)
            if latest_resume is None:
                return {"ok": False, "message": "Resume not found"}

            profile = self.deepseek_client.extract_resume_profile(latest_resume.raw_text)
            new_resume = ResumeRepository(session).create(
                user_id=user_id,
                source_type=latest_resume.source_type,
                file_path=latest_resume.file_path,
                resume_link=latest_resume.resume_link,
                raw_text=latest_resume.raw_text,
                parsed_profile_json=profile.model_dump(),
                summary=profile.summary,
                llm_prompt_version="resume_profile_v1",
                llm_model_name=self.deepseek_client.settings.deepseek_model,
                llm_generated_at=datetime.now(UTC),
            )
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="reprocess_resume",
                entity_type="resume",
                entity_id=str(new_resume.id),
                details_json={"user_id": user_id, "source_type": latest_resume.source_type.value},
            )
            session.flush()
            return {"ok": True, "message": f"Resume for user {user_id} reprocessed"}

    def delete_chat_history(self, user_id: int, *, admin_user_id: int | None = None) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            deleted_count = session.execute(
                delete(ChatMessage).where(ChatMessage.user_id == user_id)
            ).rowcount or 0
            self._write_audit_log(
                session=session,
                admin_user_id=admin_user_id,
                action_type="delete_chat_history",
                entity_type="user",
                entity_id=str(user_id),
                details_json={"deleted_messages": deleted_count},
            )
            session.flush()
            return {"ok": True, "message": f"Deleted {deleted_count} chat messages for user {user_id}"}

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
