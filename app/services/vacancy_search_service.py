from typing import Any

from aiogram.types import User as TelegramUser

from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.vacancy_repository import VacancyRepository
from app.db.session import session_scope
from app.integrations.hh.aggregator import deduplicate_vacancies, merge_vacancy_results
from app.integrations.hh.client import HHClient
from app.integrations.hh.mapper import map_hh_vacancy
from app.services.vacancy_content_service import VacancyContentService


class VacancySearchService:
    def __init__(self) -> None:
        self.hh_client = HHClient()
        self.vacancy_content_service = VacancyContentService()

    def search_for_user(self, *, telegram_user: TelegramUser) -> list[dict[str, Any]]:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            search_settings = SearchSettingRepository(session).get_or_create(user.id)
            resume = ResumeRepository(session).get_latest_by_user_id(user.id)
            resume_profile = (resume.parsed_profile_json if resume else None) or {}
            countries = search_settings.selected_countries_json or ["KZ"]
            market_results = []

            for country in countries:
                raw_vacancies = self.hh_client.search_vacancies(
                    country,
                    self._build_filters(search_settings, resume_profile),
                )
                normalized = [
                    self.vacancy_content_service.enrich(
                        map_hh_vacancy(
                            self.hh_client.get_vacancy(country, str(vacancy["id"])),
                            self.hh_client.get_provider_config(country),
                        ),
                        generate_ai_summary=False,
                    )
                    for vacancy in raw_vacancies
                ]
                market_results.append(normalized)

            merged = merge_vacancy_results(*market_results)
            deduplicated = deduplicate_vacancies(merged)
            repository = VacancyRepository(session)
            stored = [repository.upsert(vacancy_data) for vacancy_data in deduplicated]
            return [self._serialize_vacancy(vacancy) for vacancy in stored]

    def get_vacancy_details(self, *, provider: str, vacancy_id: str) -> dict[str, Any]:
        config = self.hh_client.get_provider_config(provider)
        return self.vacancy_content_service.enrich(
            map_hh_vacancy(self.hh_client.get_vacancy(provider, vacancy_id), config)
        )

    def get_employer_details(self, *, provider: str, employer_id: str) -> dict[str, Any]:
        return self.hh_client.get_employer(provider, employer_id)

    def _build_filters(self, search_settings: Any, resume_profile: dict[str, Any]) -> dict[str, Any]:
        area_ids = search_settings.area_ids_json or []
        return {
            "text": self._build_search_text(search_settings, resume_profile),
            "area": area_ids[0] if area_ids else None,
            "employment": self._normalize_employment(search_settings.employment_type),
            "schedule": self._normalize_schedule(search_settings.work_format),
            "per_page": 20,
            "page": 0,
        }

    def _build_search_text(self, search_settings: Any, resume_profile: dict[str, Any]) -> str | None:
        if search_settings.keywords:
            return search_settings.keywords

        parts: list[str] = []
        if search_settings.professional_role:
            parts.append(search_settings.professional_role)

        position = resume_profile.get("position")
        if position:
            parts.append(str(position))

        for stack_key in ("primary_stack", "secondary_stack"):
            for skill in resume_profile.get(stack_key) or []:
                if isinstance(skill, str) and skill.strip():
                    parts.append(skill.strip())

        deduplicated: list[str] = []
        seen: set[str] = set()
        for part in parts:
            normalized = part.casefold()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduplicated.append(part)

        if not deduplicated:
            return None
        return " ".join(deduplicated[:6])

    def _serialize_vacancy(self, vacancy: Any) -> dict[str, Any]:
        return {
            "id": vacancy.id,
            "provider": vacancy.provider,
            "hh_vacancy_id": vacancy.hh_vacancy_id,
            "title": vacancy.title,
            "company_name": vacancy.company_name,
            "alternate_url": vacancy.alternate_url,
            "source_country_code": vacancy.source_country_code,
        }

    def _normalize_employment(self, employment_type: str | None) -> str | None:
        if not employment_type:
            return None
        mapping = {
            "full-time": "full",
            "part-time": "part",
            "project": "project",
        }
        return mapping.get(employment_type, employment_type)

    def _normalize_schedule(self, work_format: str | None) -> str | None:
        if not work_format:
            return None
        mapping = {
            "remote": "remote",
            # HH schedule filter does not support office/hybrid values from our UI.
            "office": None,
            "hybrid": None,
        }
        return mapping.get(work_format, work_format)
