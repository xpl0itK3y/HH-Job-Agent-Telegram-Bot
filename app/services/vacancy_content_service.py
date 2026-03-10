from app.integrations.deepseek.client import DeepSeekClient
from app.utils.html_cleaner import clean_html
from app.utils.text_normalizer import normalize_text


class VacancyContentService:
    def __init__(self) -> None:
        self.deepseek_client = DeepSeekClient()

    def enrich(self, vacancy_data: dict) -> dict:
        raw_description = vacancy_data.get("description_raw") or ""
        description_clean = normalize_text(clean_html(raw_description), max_chunk_length=4000)
        description_ai_summary = self.deepseek_client.summarize_vacancy_description(
            description_clean
        )

        enriched = dict(vacancy_data)
        enriched["description_raw"] = raw_description
        enriched["description_clean"] = description_clean
        enriched["description_ai_summary"] = description_ai_summary or description_clean
        return enriched
