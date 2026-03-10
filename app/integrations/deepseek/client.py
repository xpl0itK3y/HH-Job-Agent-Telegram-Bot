import json
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


class DeepSeekClient:
    def __init__(self) -> None:
        self.settings = get_settings()

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
                last_error = str(exc)

        return ResumeProfileSchema(status="needs_review", error=last_error)

    def analyze_vacancy(self, user_profile: dict[str, Any], vacancy: dict[str, Any]) -> dict[str, Any]:
        return {
            "prompt": VACANCY_ANALYSIS_SYSTEM_PROMPT,
            "user_profile": user_profile,
            "vacancy": vacancy,
        }

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
            return description_clean

    def generate_cover_letter(
        self,
        user_profile: dict[str, Any],
        vacancy: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "prompt": COVER_LETTER_SYSTEM_PROMPT,
            "user_profile": user_profile,
            "vacancy": vacancy,
        }

    def answer_about_vacancy(
        self,
        user_profile: dict[str, Any],
        vacancy: dict[str, Any],
        chat_history: list[dict[str, Any]],
        question: str,
    ) -> dict[str, Any]:
        return {
            "prompt": VACANCY_QA_SYSTEM_PROMPT,
            "user_profile": user_profile,
            "vacancy": vacancy,
            "chat_history": chat_history,
            "question": question,
        }

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
