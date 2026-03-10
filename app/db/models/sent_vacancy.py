from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


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
    telegram_message_id: Mapped[str | None] = mapped_column(String(128))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User")
    vacancy = relationship("Vacancy")
