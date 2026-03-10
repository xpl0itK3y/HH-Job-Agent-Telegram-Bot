from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hh_vacancy_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    employer_hh_id: Mapped[str | None] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company_name: Mapped[str] = mapped_column(String(512), nullable=False)
    salary_from: Mapped[int | None] = mapped_column(Integer)
    salary_to: Mapped[int | None] = mapped_column(Integer)
    salary_currency: Mapped[str | None] = mapped_column(String(16))
    employment_type: Mapped[str | None] = mapped_column(String(128))
    work_format: Mapped[str | None] = mapped_column(String(128))
    experience: Mapped[str | None] = mapped_column(String(128))
    area_name: Mapped[str | None] = mapped_column(String(255))
    description_raw: Mapped[str | None] = mapped_column(Text)
    description_clean: Mapped[str | None] = mapped_column(Text)
    description_ai_summary: Mapped[str | None] = mapped_column(Text)
    llm_prompt_version: Mapped[str | None] = mapped_column(String(64))
    llm_model_name: Mapped[str | None] = mapped_column(String(128))
    llm_generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    key_skills_json: Mapped[list | None] = mapped_column(JSONB)
    alternate_url: Mapped[str | None] = mapped_column(String(2048))
    source_country_code: Mapped[str] = mapped_column(String(2), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
