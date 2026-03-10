from datetime import UTC, datetime, timedelta

from aiogram.types import User as TelegramUser

from app.core.config import get_settings
from app.db.models.user import BotStatus
from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.tasks.reminders import send_resume_reminder


class UserControlService:
    def pause(self, *, telegram_user: TelegramUser) -> dict:
        settings = get_settings()
        with session_scope() as session:
            repository = UserRepository(session)
            user = repository.create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            repository.set_bot_status(
                telegram_user_id=telegram_user.id,
                bot_status=BotStatus.PAUSED,
            )
            reminder_repo = ScheduledReminderRepository(session)
            run_at = datetime.now(UTC) + timedelta(hours=settings.reminder_after_hours)
            reminder = reminder_repo.create(
                user_id=user.id,
                reminder_type="resume_search",
                run_at=run_at,
            )
            send_resume_reminder.apply_async(args=[telegram_user.id, reminder.id], eta=run_at)
            return {"bot_status": BotStatus.PAUSED, "reminder_id": reminder.id, "run_at": run_at.isoformat()}

    def resume(self, *, telegram_user: TelegramUser) -> dict:
        with session_scope() as session:
            repository = UserRepository(session)
            user = repository.create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            repository.set_bot_status(
                telegram_user_id=telegram_user.id,
                bot_status=BotStatus.ACTIVE,
            )
            reminder_repo = ScheduledReminderRepository(session)
            for reminder in reminder_repo.get_pending(user_id=user.id, reminder_type="resume_search"):
                reminder_repo.mark_cancelled(reminder.id)
            return {"bot_status": BotStatus.ACTIVE}
