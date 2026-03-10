from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class AdminAuditLog(TimestampMixin, Base):
    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("admin_users.id"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    details_json: Mapped[dict | None] = mapped_column(JSONB)

    admin_user = relationship("AdminUser")
