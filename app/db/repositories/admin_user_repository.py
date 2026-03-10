from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.admin_user import AdminUser


class AdminUserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_username(self, username: str) -> AdminUser | None:
        stmt = select(AdminUser).where(AdminUser.username == username, AdminUser.is_active.is_(True))
        return self.session.scalar(stmt)
