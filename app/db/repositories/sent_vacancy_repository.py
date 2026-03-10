from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.sent_vacancy import SentVacancy


class SentVacancyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_and_vacancy(self, *, user_id: int, vacancy_id: int) -> SentVacancy | None:
        stmt = select(SentVacancy).where(
            SentVacancy.user_id == user_id,
            SentVacancy.vacancy_id == vacancy_id,
        )
        return self.session.scalar(stmt)

    def create_or_update(
        self,
        *,
        user_id: int,
        vacancy_id: int,
        vacancy_tag: str,
        match_score: int | None = None,
        match_summary: str | None = None,
        missing_skills_json: list[str] | None = None,
        employer_check_json: dict | None = None,
        cover_letter: str | None = None,
    ) -> SentVacancy:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            sent_vacancy = SentVacancy(
                user_id=user_id,
                vacancy_id=vacancy_id,
                vacancy_tag=vacancy_tag,
                match_score=match_score,
                match_summary=match_summary,
                missing_skills_json=missing_skills_json,
                employer_check_json=employer_check_json,
                cover_letter=cover_letter,
            )
            self.session.add(sent_vacancy)
            self.session.flush()
            return sent_vacancy

        sent_vacancy.vacancy_tag = vacancy_tag
        sent_vacancy.match_score = match_score
        sent_vacancy.match_summary = match_summary
        sent_vacancy.missing_skills_json = missing_skills_json
        sent_vacancy.employer_check_json = employer_check_json
        sent_vacancy.cover_letter = cover_letter
        self.session.flush()
        return sent_vacancy

    def set_telegram_message_id(
        self,
        *,
        user_id: int,
        vacancy_id: int,
        telegram_message_id: str,
    ) -> SentVacancy | None:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            return None
        sent_vacancy.telegram_message_id = telegram_message_id
        self.session.flush()
        return sent_vacancy
