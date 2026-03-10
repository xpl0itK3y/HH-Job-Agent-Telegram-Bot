from datetime import UTC, datetime

from app.db.base import SessionLocal
from app.db.repositories.vacancy_repository import VacancyRepository
from app.integrations.deepseek.client import DeepSeekClient
from app.utils.html_cleaner import clean_html
from app.utils.text_normalizer import normalize_text


class VacancyContentService:
    def __init__(self) -> None:
        self.deepseek_client = DeepSeekClient()

    def enrich(self, vacancy_data: dict) -> dict:
        raw_description = vacancy_data.get("description_raw") or ""
        description_clean = normalize_text(clean_html(raw_description), max_chunk_length=4000)
        description_ai_summary = ""
        session = SessionLocal()
        try:
            cached = VacancyRepository(session).get_cached_summary(
                provider=str(vacancy_data["provider"]),
                hh_vacancy_id=str(vacancy_data["hh_vacancy_id"]),
                description_clean=description_clean,
            )
            if cached is not None and cached.description_ai_summary:
                description_ai_summary = cached.description_ai_summary
        finally:
            session.close()

        if not description_ai_summary:
            description_ai_summary = self.deepseek_client.summarize_vacancy_description(
                description_clean
            )

        enriched = dict(vacancy_data)
        enriched["description_raw"] = raw_description
        enriched["description_clean"] = description_clean
        enriched["description_ai_summary"] = description_ai_summary or description_clean
        enriched["llm_prompt_version"] = "vacancy_summary_v1"
        enriched["llm_model_name"] = self.deepseek_client.settings.deepseek_model
        enriched["llm_generated_at"] = datetime.now(UTC)
        return enriched
