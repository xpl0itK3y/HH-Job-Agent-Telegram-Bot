"""Database models package."""

from app.db.models.chat_message import ChatMessage, ChatMessageRole
from app.db.models.resume import Resume, ResumeSourceType
from app.db.models.search_setting import SearchSetting
from app.db.models.sent_vacancy import SentVacancy
from app.db.models.user import BotStatus, User
from app.db.models.vacancy import Vacancy

__all__ = [
    "BotStatus",
    "ChatMessage",
    "ChatMessageRole",
    "Resume",
    "ResumeSourceType",
    "SearchSetting",
    "SentVacancy",
    "User",
    "Vacancy",
]
