from datetime import datetime

from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import values_enum
from app.db.models.mixins import TimestampMixin


class ResumeSourceType(StrEnum):
    PDF = "pdf"
    TEXT = "text"
    LINK = "link"


class Resume(TimestampMixin, Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    source_type: Mapped[ResumeSourceType] = mapped_column(
        values_enum(ResumeSourceType, name="resume_source_type_enum"),
        nullable=False,
    )
    file_path: Mapped[str | None] = mapped_column(String(1024))
    resume_link: Mapped[str | None] = mapped_column(String(2048))
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_profile_json: Mapped[dict | None] = mapped_column(JSONB)
    summary: Mapped[str | None] = mapped_column(Text)
    llm_prompt_version: Mapped[str | None] = mapped_column(String(64))
    llm_model_name: Mapped[str | None] = mapped_column(String(128))
    llm_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User")
