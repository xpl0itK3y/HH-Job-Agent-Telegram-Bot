from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.scheduled_reminder import ScheduledReminder


class ScheduledReminderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        reminder_type: str,
        run_at: datetime,
        status: str = "scheduled",
    ) -> ScheduledReminder:
        reminder = ScheduledReminder(
            user_id=user_id,
            reminder_type=reminder_type,
            run_at=run_at,
            status=status,
        )
        self.session.add(reminder)
        self.session.flush()
        return reminder

    def get_pending(self, *, user_id: int, reminder_type: str) -> list[ScheduledReminder]:
        stmt = select(ScheduledReminder).where(
            ScheduledReminder.user_id == user_id,
            ScheduledReminder.reminder_type == reminder_type,
            ScheduledReminder.status == "scheduled",
        )
        return list(self.session.scalars(stmt))

    def mark_cancelled(self, reminder_id: int) -> ScheduledReminder | None:
        reminder = self.session.get(ScheduledReminder, reminder_id)
        if reminder is None:
            return None
        reminder.status = "cancelled"
        self.session.flush()
        return reminder

    def mark_sent(self, reminder_id: int) -> ScheduledReminder | None:
        reminder = self.session.get(ScheduledReminder, reminder_id)
        if reminder is None:
            return None
        reminder.status = "sent"
        self.session.flush()
        return reminder
