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
    ) -> Resume:
        resume = Resume(
            user_id=user_id,
            source_type=source_type,
            file_path=file_path,
            resume_link=resume_link,
            raw_text=raw_text,
            parsed_profile_json=parsed_profile_json,
            summary=summary,
        )
        self.session.add(resume)
        self.session.flush()
        return resume
