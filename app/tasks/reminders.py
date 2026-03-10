import asyncio

from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.integrations.telegram.client import create_telegram_bot
from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.send_resume_reminder")
def send_resume_reminder(telegram_user_id: int, reminder_id: int) -> dict:
    bot = create_telegram_bot()
    asyncio.run(
        bot.send_message(
            chat_id=telegram_user_id,
            text="Поиск вакансий остановлен. Можно возобновить его командой /resume.",
        )
    )
    with session_scope() as session:
        user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
        if user is not None:
            ScheduledReminderRepository(session).mark_sent(reminder_id)
    return {"status": "sent", "telegram_user_id": telegram_user_id, "reminder_id": reminder_id}
