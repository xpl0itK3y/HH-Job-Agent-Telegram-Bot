from collections.abc import Sequence

from sqlalchemy import func, select

from app.db.models.sent_vacancy import ProcessingStatus, SentVacancy
from app.db.models.user import BotStatus, User
from app.db.models.vacancy import Vacancy
from app.db.session import session_scope


class AdminDBService:
    def get_users(self, *, filters: dict | None = None, limit: int = 50) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = select(User).order_by(User.created_at.desc()).limit(limit)
            if filters.get("username"):
                stmt = stmt.where(User.username.ilike(f"%{filters['username']}%"))
            if filters.get("bot_status"):
                stmt = stmt.where(User.bot_status == BotStatus(filters["bot_status"]))
            users = list(session.scalars(stmt))
        return [
            {
                "id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "username": user.username,
                "bot_status": user.bot_status.value,
                "created_at": user.created_at.isoformat(),
            }
            for user in users
        ]

    def count_users(self) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(User)) or 0

    def count_users_by_status(self, status: BotStatus) -> int:
        with session_scope() as session:
            stmt = select(func.count()).select_from(User).where(User.bot_status == status)
            return session.scalar(stmt) or 0

    def count_vacancies(self) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(Vacancy)) or 0

    def count_sent_by_status(self, status: ProcessingStatus) -> int:
        with session_scope() as session:
            stmt = select(func.count()).select_from(SentVacancy).where(SentVacancy.processing_status == status)
            return session.scalar(stmt) or 0

    def get_recent_sent_vacancies(self, limit: int = 10) -> list[dict]:
        with session_scope() as session:
            stmt = select(SentVacancy).order_by(SentVacancy.id.desc()).limit(limit)
            rows = list(session.scalars(stmt))
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "vacancy_id": row.vacancy_id,
                "vacancy_tag": row.vacancy_tag,
                "status": row.processing_status.value,
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            }
            for row in rows
        ]

    def get_recent_users(self, limit: int = 10) -> list[dict]:
        return self.get_users(limit=limit)
