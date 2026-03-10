from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class SearchSetting(TimestampMixin, Base):
    __tablename__ = "search_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    keywords: Mapped[str | None] = mapped_column(String(512))
    selected_countries_json: Mapped[list | None] = mapped_column(JSONB)
    area_ids_json: Mapped[list | None] = mapped_column(JSONB)
    employment_type: Mapped[str | None] = mapped_column(String(128))
    work_format: Mapped[str | None] = mapped_column(String(128))
    professional_role: Mapped[str | None] = mapped_column(String(255))
    search_extra_json: Mapped[dict | None] = mapped_column(JSONB)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user = relationship("User")
