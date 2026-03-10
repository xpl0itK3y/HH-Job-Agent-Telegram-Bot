from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.sent_vacancy import SentVacancy


class SentVacancyLookupRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_tag_for_user(self, *, user_id: int, vacancy_tag: str) -> SentVacancy | None:
        stmt = select(SentVacancy).where(
            SentVacancy.user_id == user_id,
            SentVacancy.vacancy_tag == vacancy_tag,
        )
        return self.session.scalar(stmt)
