from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus, SentVacancy


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
        llm_prompt_version: str | None = None,
        llm_model_name: str | None = None,
        llm_generated_at=None,
        processing_status: ProcessingStatus = ProcessingStatus.QUEUED,
        current_pipeline_step: PipelineStep | None = PipelineStep.CLEANING,
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
                llm_prompt_version=llm_prompt_version,
                llm_model_name=llm_model_name,
                llm_generated_at=llm_generated_at,
                processing_status=processing_status,
                current_pipeline_step=current_pipeline_step,
                queued_at=datetime.now(UTC),
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
        sent_vacancy.llm_prompt_version = llm_prompt_version
        sent_vacancy.llm_model_name = llm_model_name
        sent_vacancy.llm_generated_at = llm_generated_at
        sent_vacancy.processing_status = processing_status
        sent_vacancy.current_pipeline_step = current_pipeline_step
        self.session.flush()
        return sent_vacancy

    def has_cached_ai_results(self, *, user_id: int, vacancy_id: int) -> bool:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            return False
        return bool(sent_vacancy.match_summary and sent_vacancy.cover_letter)

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
        sent_vacancy.processing_status = ProcessingStatus.SENT
        sent_vacancy.sent_at = datetime.now(UTC)
        self.session.flush()
        return sent_vacancy

    def mark_processing(
        self,
        *,
        user_id: int,
        vacancy_id: int,
        step: PipelineStep,
    ) -> SentVacancy | None:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            return None
        sent_vacancy.processing_status = ProcessingStatus.PROCESSING
        sent_vacancy.current_pipeline_step = step
        if sent_vacancy.processing_started_at is None:
            sent_vacancy.processing_started_at = datetime.now(UTC)
        self.session.flush()
        return sent_vacancy

    def mark_ready_to_send(self, *, user_id: int, vacancy_id: int) -> SentVacancy | None:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            return None
        sent_vacancy.processing_status = ProcessingStatus.READY_TO_SEND
        sent_vacancy.current_pipeline_step = PipelineStep.READY_TO_SEND
        sent_vacancy.ready_to_send_at = datetime.now(UTC)
        self.session.flush()
        return sent_vacancy

    def mark_failed(self, *, user_id: int, vacancy_id: int, error_text: str) -> SentVacancy | None:
        sent_vacancy = self.get_by_user_and_vacancy(user_id=user_id, vacancy_id=vacancy_id)
        if sent_vacancy is None:
            return None
        sent_vacancy.processing_status = ProcessingStatus.FAILED
        sent_vacancy.last_error_text = error_text
        sent_vacancy.retry_count += 1
        sent_vacancy.failed_at = datetime.now(UTC)
        self.session.flush()
        return sent_vacancy
