from enum import StrEnum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import values_enum


class ProcessingStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    READY_TO_SEND = "ready_to_send"
    SENT = "sent"
    FAILED = "failed"


class PipelineStep(StrEnum):
    CLEANING = "cleaning"
    AI_SUMMARY = "ai_summary"
    EMPLOYER_CHECK = "employer_check"
    MATCH_ANALYSIS = "match_analysis"
    COVER_LETTER = "cover_letter"
    CARD_GENERATION = "card_generation"
    READY_TO_SEND = "ready_to_send"


class SentVacancy(Base):
    __tablename__ = "sent_vacancies"
    __table_args__ = (UniqueConstraint("user_id", "vacancy_id", name="uq_sent_vacancy_user_vacancy"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False, index=True)
    vacancy_tag: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    match_score: Mapped[int | None] = mapped_column()
    match_summary: Mapped[str | None] = mapped_column(Text)
    missing_skills_json: Mapped[list | None] = mapped_column(JSONB)
    employer_check_json: Mapped[dict | None] = mapped_column(JSONB)
    cover_letter: Mapped[str | None] = mapped_column(Text)
    llm_prompt_version: Mapped[str | None] = mapped_column(String(64))
    llm_model_name: Mapped[str | None] = mapped_column(String(128))
    llm_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        values_enum(ProcessingStatus, name="processing_status_enum"),
        default=ProcessingStatus.QUEUED,
        nullable=False,
    )
    current_pipeline_step: Mapped[PipelineStep | None] = mapped_column(
        values_enum(PipelineStep, name="pipeline_step_enum"),
    )
    last_error_text: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processing_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ready_to_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    telegram_message_id: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User")
    vacancy = relationship("Vacancy")
