from datetime import UTC, datetime

from aiogram.types import User as TelegramUser

from app.core.config import get_settings
from app.db.models.sent_vacancy import PipelineStep, ProcessingStatus
from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.vacancy_repository import VacancyRepository
from app.db.session import session_scope
from app.integrations.deepseek.client import DeepSeekClient
from app.services.employer_check_service import EmployerCheckService
from app.services.vacancy_card_service import VacancyCardService
from app.utils.vacancy_tag import build_vacancy_tag


class VacancyAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.deepseek_client = DeepSeekClient()
        self.employer_check_service = EmployerCheckService()
        self.vacancy_card_service = VacancyCardService()

    def analyze_and_prepare(self, *, telegram_user: TelegramUser, vacancy_id: int) -> dict:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            vacancy_repository = VacancyRepository(session)
            vacancy = vacancy_repository.get_by_id(vacancy_id)
            if vacancy is None:
                raise ValueError(f"Vacancy {vacancy_id} not found")

            resume = ResumeRepository(session).get_latest_by_user_id(user.id)
            user_profile = (resume.parsed_profile_json if resume else None) or {}
            vacancy_payload = {
                "id": vacancy.id,
                "provider": vacancy.provider,
                "hh_vacancy_id": vacancy.hh_vacancy_id,
                "title": vacancy.title,
                "company_name": vacancy.company_name,
                "description_clean": vacancy.description_clean,
                "description_ai_summary": vacancy.description_ai_summary,
                "key_skills_json": vacancy.key_skills_json,
                "source_country_code": vacancy.source_country_code,
                "alternate_url": vacancy.alternate_url,
            }

            analysis = self.deepseek_client.analyze_vacancy(user_profile, vacancy_payload)
            match_score = int(analysis.get("match_score") or 0)
            sent_repository = SentVacancyRepository(session)
            cached_sent = sent_repository.get_by_user_and_vacancy(
                user_id=user.id,
                vacancy_id=vacancy.id,
            )
            if (
                cached_sent is not None
                and cached_sent.match_summary
                and cached_sent.cover_letter
                and cached_sent.missing_skills_json is not None
            ):
                analysis = {
                    "match_score": cached_sent.match_score,
                    "match_summary": cached_sent.match_summary,
                    "missing_skills": cached_sent.missing_skills_json,
                }
                match_score = int(cached_sent.match_score or 0)

            if match_score < self.settings.vacancy_min_match_score:
                sent_vacancy = sent_repository.create_or_update(
                    user_id=user.id,
                    vacancy_id=vacancy.id,
                    vacancy_tag=build_vacancy_tag(vacancy_id=vacancy.id),
                    match_score=match_score,
                    match_summary=analysis.get("match_summary"),
                    missing_skills_json=analysis.get("missing_skills"),
                    processing_status=ProcessingStatus.FAILED,
                    current_pipeline_step=PipelineStep.MATCH_ANALYSIS,
                )
                sent_vacancy.last_error_text = (
                    f"Filtered by low match score: {match_score} < {self.settings.vacancy_min_match_score}"
                )
                sent_vacancy.failed_at = datetime.now(UTC)
                session.flush()
                return {
                    "sent_vacancy_id": sent_vacancy.id,
                    "vacancy_id": vacancy.id,
                    "vacancy_tag": sent_vacancy.vacancy_tag,
                    "title": vacancy.title,
                    "company_name": vacancy.company_name,
                    "match_score": match_score,
                    "match_summary": sent_vacancy.match_summary,
                    "missing_skills_json": sent_vacancy.missing_skills_json,
                    "employer_check_json": {},
                    "cover_letter": "",
                    "card_path": "",
                    "alternate_url": vacancy.alternate_url,
                    "should_send": False,
                    "skip_reason": sent_vacancy.last_error_text,
                }

            employer_check = (
                self.employer_check_service.check_employer(
                    provider=vacancy.provider,
                    employer_id=vacancy.employer_hh_id,
                )
                if vacancy.employer_hh_id
                else {"score": 0, "status": "Есть риски", "signals": []}
            )
            cover_letter_data = self.deepseek_client.generate_cover_letter(
                user_profile,
                {
                    **vacancy_payload,
                    "resume_link": resume.resume_link if resume else None,
                },
            )
            if cached_sent is not None and cached_sent.cover_letter:
                cover_letter_data = {"cover_letter": cached_sent.cover_letter}
            sent_vacancy = sent_repository.create_or_update(
                user_id=user.id,
                vacancy_id=vacancy.id,
                vacancy_tag=build_vacancy_tag(vacancy_id=vacancy.id),
                match_score=analysis.get("match_score"),
                match_summary=analysis.get("match_summary"),
                missing_skills_json=analysis.get("missing_skills"),
                employer_check_json=employer_check,
                cover_letter=cover_letter_data.get("cover_letter"),
                llm_prompt_version="vacancy_match_v1",
                llm_model_name=self.deepseek_client.settings.deepseek_model,
                llm_generated_at=datetime.now(UTC),
                processing_status=ProcessingStatus.PROCESSING,
                current_pipeline_step=PipelineStep.CARD_GENERATION,
            )

            if sent_vacancy.id is not None:
                generated_tag = build_vacancy_tag(sent_vacancy_id=sent_vacancy.id)
                if sent_vacancy.vacancy_tag != generated_tag:
                    sent_vacancy.vacancy_tag = generated_tag
                    session.flush()

            card_path = self.vacancy_card_service.render_gif(
                vacancy={
                    **vacancy_payload,
                    "id": vacancy.id,
                    "salary_from": vacancy.salary_from,
                    "salary_to": vacancy.salary_to,
                    "salary_currency": vacancy.salary_currency,
                    "area_name": vacancy.area_name,
                    "work_format": vacancy.work_format,
                    "experience": vacancy.experience,
                },
                vacancy_tag=sent_vacancy.vacancy_tag,
            )

            return {
                "sent_vacancy_id": sent_vacancy.id,
                "vacancy_id": vacancy.id,
                "vacancy_tag": sent_vacancy.vacancy_tag,
                "title": vacancy.title,
                "company_name": vacancy.company_name,
                "match_score": sent_vacancy.match_score,
                "match_summary": sent_vacancy.match_summary,
                "missing_skills_json": sent_vacancy.missing_skills_json,
                "employer_check_json": sent_vacancy.employer_check_json,
                "cover_letter": sent_vacancy.cover_letter,
                "card_path": str(card_path),
                "alternate_url": vacancy.alternate_url,
                "resume_link": resume.resume_link if resume else None,
                "should_send": True,
            }
