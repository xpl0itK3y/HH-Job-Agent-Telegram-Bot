from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.vacancy import Vacancy


class VacancyRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, vacancy_id: int) -> Vacancy | None:
        return self.session.get(Vacancy, vacancy_id)

    def get_by_provider_and_hh_vacancy_id(
        self,
        *,
        provider: str,
        hh_vacancy_id: str,
    ) -> Vacancy | None:
        stmt = select(Vacancy).where(
            Vacancy.provider == provider,
            Vacancy.hh_vacancy_id == hh_vacancy_id,
        )
        return self.session.scalar(stmt)

    def upsert(self, vacancy_data: dict) -> Vacancy:
        provider = str(vacancy_data["provider"])
        hh_vacancy_id = str(vacancy_data["hh_vacancy_id"])
        vacancy = self.get_by_provider_and_hh_vacancy_id(
            provider=provider,
            hh_vacancy_id=hh_vacancy_id,
        )
        if vacancy is None:
            vacancy = Vacancy(**vacancy_data)
            self.session.add(vacancy)
            self.session.flush()
            return vacancy

        for key, value in vacancy_data.items():
            setattr(vacancy, key, value)
        self.session.flush()
        return vacancy
