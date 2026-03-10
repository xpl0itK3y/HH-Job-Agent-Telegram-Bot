"""Database repositories package."""

from app.db.repositories.chat_message_repository import ChatMessageRepository
from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.scheduled_reminder_repository import ScheduledReminderRepository
from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.sent_vacancy_lookup_repository import SentVacancyLookupRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.vacancy_repository import VacancyRepository

__all__ = [
    "ChatMessageRepository",
    "ResumeRepository",
    "ScheduledReminderRepository",
    "SearchSettingRepository",
    "SentVacancyLookupRepository",
    "SentVacancyRepository",
    "UserRepository",
    "VacancyRepository",
]
