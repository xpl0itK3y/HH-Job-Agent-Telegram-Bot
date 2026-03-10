import hashlib
from dataclasses import dataclass

from app.db.models.admin_user import AdminRole
from app.db.repositories.admin_user_repository import AdminUserRepository
from app.db.session import session_scope
from app.core.config import get_settings


@dataclass(slots=True)
class AdminAuthResult:
    admin_user_id: int | None
    username: str
    role: str


class AdminAuthService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def authenticate(self, username: str, password: str) -> AdminAuthResult | None:
        password_hash = self.hash_password(password)

        env_username = getattr(self.settings, "streamlit_admin_username", "")
        env_password_hash = getattr(self.settings, "streamlit_admin_password_hash", "")
        if env_username and env_password_hash:
            if username == env_username and password_hash == env_password_hash:
                with session_scope() as session:
                    admin_user = AdminUserRepository(session).get_by_username(username)
                return AdminAuthResult(
                    admin_user_id=admin_user.id if admin_user else None,
                    username=username,
                    role=AdminRole.ADMIN.value,
                )

        with session_scope() as session:
            admin_user = AdminUserRepository(session).get_by_username(username)
            if admin_user and admin_user.password_hash == password_hash:
                return AdminAuthResult(
                    admin_user_id=admin_user.id,
                    username=admin_user.username,
                    role=admin_user.role.value,
                )
        return None

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()
