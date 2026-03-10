"""Database models package."""

from app.db.models.admin_user import AdminRole, AdminUser
from app.db.models.chat_message import ChatMessage, ChatMessageRole
from app.db.models.resume import Resume, ResumeSourceType
from app.db.models.search_setting import SearchSetting
from app.db.models.scheduled_reminder import ScheduledReminder
from app.db.models.sent_vacancy import SentVacancy
from app.db.models.user import BotStatus, User
from app.db.models.vacancy import Vacancy

__all__ = [
    "BotStatus",
    "AdminRole",
    "AdminUser",
    "ChatMessage",
    "ChatMessageRole",
    "Resume",
    "ResumeSourceType",
    "ScheduledReminder",
    "SearchSetting",
    "SentVacancy",
    "User",
    "Vacancy",
]
