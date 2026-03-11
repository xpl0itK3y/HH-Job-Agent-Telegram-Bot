from enum import StrEnum

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import values_enum
from app.db.models.mixins import TimestampMixin


class AdminRole(StrEnum):
    ADMIN = "admin"
    VIEWER = "viewer"


class AdminUser(TimestampMixin, Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    role: Mapped[AdminRole] = mapped_column(
        values_enum(AdminRole, name="admin_role_enum"),
        nullable=False,
        default=AdminRole.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
