from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus, SentVacancy
from app.db.models.user import BotStatus, User
from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.session import session_scope


class AdminActionsService:
    def pause_user(self, user_id: int) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            user.bot_status = BotStatus.PAUSED
            session.flush()
            return {"ok": True, "message": f"User {user_id} paused"}

    def resume_user(self, user_id: int) -> dict:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return {"ok": False, "message": "User not found"}
            user.bot_status = BotStatus.ACTIVE
            reminder_repo = ScheduledReminderRepository(session)
            for reminder in reminder_repo.get_pending(user_id=user.id, reminder_type="resume_search"):
                reminder_repo.mark_cancelled(reminder.id)
            session.flush()
            return {"ok": True, "message": f"User {user_id} resumed"}

    def requeue_sent_vacancy(self, sent_vacancy_id: int) -> dict:
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
            session.flush()
            return {"ok": True, "message": f"Sent vacancy {sent_vacancy_id} moved to queue"}

    def mark_sent_vacancy_failed(self, sent_vacancy_id: int, error_text: str) -> dict:
        with session_scope() as session:
            sent_vacancy = session.get(SentVacancy, sent_vacancy_id)
            if sent_vacancy is None:
                return {"ok": False, "message": "Sent vacancy not found"}
            sent_vacancy.processing_status = ProcessingStatus.FAILED
            sent_vacancy.last_error_text = error_text or "Manually marked as failed"
            session.flush()
            return {"ok": True, "message": f"Sent vacancy {sent_vacancy_id} marked failed"}
