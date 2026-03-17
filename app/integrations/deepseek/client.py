import json
import logging
from typing import Any

import httpx
from pydantic import ValidationError

from app.core.config import get_settings
from app.integrations.deepseek.prompts import (
    COVER_LETTER_SYSTEM_PROMPT,
    RESUME_PROFILE_SYSTEM_PROMPT,
    VACANCY_ANALYSIS_SYSTEM_PROMPT,
    VACANCY_QA_SYSTEM_PROMPT,
    VACANCY_SUMMARY_SYSTEM_PROMPT,
)
from app.integrations.deepseek.schemas import ResumeProfileSchema
from app.integrations.deepseek.schemas import CoverLetterSchema, VacancyAnalysisSchema


class DeepSeekClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = logging.getLogger("app.deepseek")

    def extract_resume_profile(self, text: str) -> ResumeProfileSchema:
        if not self.settings.deepseek_api_key or not self.settings.deepseek_base_url:
            return ResumeProfileSchema(
                status="needs_review",
                error="DeepSeek credentials are not configured.",
            )

        user_prompt = (
            "Верни JSON с полями: "
            "position, seniority, primary_stack, secondary_stack, "
            "domains, years_experience, english_level, summary.\n\n"
            f"Resume:\n{text}"
        )
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": RESUME_PROFILE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        last_error = "DeepSeek response validation failed."
        for _ in range(2):
            try:
                content = self._chat_completion(payload)
                parsed = ResumeProfileSchema.model_validate(json.loads(content))
                parsed.status = "ok"
                parsed.error = None
                return parsed
            except (httpx.HTTPError, json.JSONDecodeError, ValidationError) as exc:
                self.logger.exception("DeepSeek resume profile extraction failed")
                last_error = str(exc)

        return ResumeProfileSchema(status="needs_review", error=last_error)

    def analyze_vacancy(self, user_profile: dict[str, Any], vacancy: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.deepseek_api_key or not self.settings.deepseek_base_url:
            return VacancyAnalysisSchema(
                match_score=0,
                match_summary="DeepSeek credentials are not configured.",
                missing_skills=[],
            ).model_dump()

        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": VACANCY_ANALYSIS_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Верни JSON с полями match_score, match_summary, missing_skills.\n"
                        "match_score: целое число 0-100.\n"
                        "match_summary: 3-5 полных предложений, не одно короткое.\n"
                        "missing_skills: только конкретные пробелы, без воды.\n\n"
                        f"User profile:\n{json.dumps(user_profile, ensure_ascii=False)}\n\n"
                        f"Vacancy:\n{json.dumps(vacancy, ensure_ascii=False)}"
                    ),
                },
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
        try:
            content = self._chat_completion(payload)
            return VacancyAnalysisSchema.model_validate(json.loads(content)).model_dump()
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError):
            self.logger.exception("DeepSeek vacancy analysis failed")
            return VacancyAnalysisSchema(
                match_score=0,
                match_summary="Не удалось получить AI-анализ вакансии.",
                missing_skills=[],
            ).model_dump()

    def summarize_vacancy_description(self, description_clean: str) -> str:
        if not description_clean:
            return ""
        if not self.settings.deepseek_api_key or not self.settings.deepseek_base_url:
            return description_clean

        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": VACANCY_SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Сожми описание вакансии до полезной сути для кандидата.\n\n"
                        f"{description_clean}"
                    ),
                },
            ],
            "temperature": 0.1,
        }
        try:
            return self._chat_completion(payload).strip() or description_clean
        except httpx.HTTPError:
            self.logger.exception("DeepSeek vacancy summary failed")
            return description_clean

    def generate_cover_letter(
        self,
        user_profile: dict[str, Any],
        vacancy: dict[str, Any],
    ) -> dict[str, Any]:
        if not self.settings.deepseek_api_key or not self.settings.deepseek_base_url:
            return CoverLetterSchema(
                cover_letter="Короткое сопроводительное письмо недоступно: не настроен DeepSeek."
            ).model_dump()

        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": COVER_LETTER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Верни JSON с полем cover_letter.\n"
                        "Сделай сообщение коротким и конкретным под вакансию.\n"
                        "Обязательно опирайся только на реальные данные кандидата.\n"
                        "Не пиши длинное письмо: 2-4 короткие строки, максимум 450 символов.\n"
                        "Используй простой стиль, как в коротком отклике в Telegram или HH.\n"
                        "Если в данных есть resume_link, добавь короткую строку вида 'Резюме: ...'.\n\n"
                        f"User profile:\n{json.dumps(user_profile, ensure_ascii=False)}\n\n"
                        f"Vacancy:\n{json.dumps(vacancy, ensure_ascii=False)}"
                    ),
                },
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"},
        }
        try:
            content = self._chat_completion(payload)
            return CoverLetterSchema.model_validate(json.loads(content)).model_dump()
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError):
            self.logger.exception("DeepSeek cover letter generation failed")
            return CoverLetterSchema(
                cover_letter="Не удалось сгенерировать сопроводительное письмо."
            ).model_dump()

    def answer_about_vacancy(
        self,
        user_profile: dict[str, Any],
        vacancy: dict[str, Any],
        chat_history: list[dict[str, Any]],
        question: str,
    ) -> dict[str, Any]:
        if not self.settings.deepseek_api_key or not self.settings.deepseek_base_url:
            return {"answer": "Ответ по вакансии недоступен: не настроен DeepSeek."}

        trimmed_history = chat_history[-10:]
        payload = {
            "model": self.settings.deepseek_model,
            "messages": [
                {"role": "system", "content": VACANCY_QA_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"User profile:\n{json.dumps(user_profile, ensure_ascii=False)}\n\n"
                        f"Vacancy:\n{json.dumps(vacancy, ensure_ascii=False)}\n\n"
                        f"Chat history:\n{json.dumps(trimmed_history, ensure_ascii=False)}\n\n"
                        f"Question:\n{question}"
                    ),
                },
            ],
            "temperature": 0.2,
        }
        try:
            return {"answer": self._chat_completion(payload).strip()}
        except httpx.HTTPError:
            self.logger.exception("DeepSeek vacancy Q&A failed")
            return {"answer": "Не удалось получить ответ по вакансии."}

    def _chat_completion(self, payload: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.settings.deepseek_base_url.rstrip('/')}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"]
