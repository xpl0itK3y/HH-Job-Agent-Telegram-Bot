from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models.resume import Resume, ResumeSourceType


class ResumeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_latest_by_user_id(self, user_id: int) -> Resume | None:
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(desc(Resume.created_at))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def get_cached_by_raw_text(self, *, user_id: int, raw_text: str) -> Resume | None:
        stmt = (
            select(Resume)
            .where(Resume.user_id == user_id, Resume.raw_text == raw_text)
            .order_by(desc(Resume.created_at))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def create(
        self,
        *,
        user_id: int,
        source_type: ResumeSourceType,
        raw_text: str,
        file_path: str | None = None,
        resume_link: str | None = None,
        parsed_profile_json: dict | None = None,
        summary: str | None = None,
        llm_prompt_version: str | None = None,
        llm_model_name: str | None = None,
        llm_generated_at=None,
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            source_type=source_type,
            file_path=file_path,
            resume_link=resume_link,
            raw_text=raw_text,
            parsed_profile_json=parsed_profile_json,
            summary=summary,
            llm_prompt_version=llm_prompt_version,
            llm_model_name=llm_model_name,
            llm_generated_at=llm_generated_at,
        )
        self.session.add(resume)
        self.session.flush()
        return resume
