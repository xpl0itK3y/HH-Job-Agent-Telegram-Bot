import logging

from aiogram import Bot
from aiogram.types import FSInputFile, Message, User as TelegramUser

from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope


class VacancyDeliveryService:
    def __init__(self) -> None:
        self.logger = logging.getLogger("app.telegram")

    async def send_to_user(
        self,
        *,
        bot: Bot,
        telegram_user: TelegramUser,
        prepared_vacancy: dict,
    ) -> dict:
        animation = FSInputFile(prepared_vacancy["card_path"])
        caption = self._build_caption(prepared_vacancy)
        full_text = self._build_full_text(prepared_vacancy)
        try:
            media_message = await bot.send_document(
                chat_id=telegram_user.id,
                document=animation,
                caption=caption,
            )
            message = await bot.send_message(
                chat_id=telegram_user.id,
                text=full_text,
                disable_web_page_preview=True,
            )
        except Exception:
            self.logger.exception("Telegram delivery failed")
            raise
        self._save_telegram_message_id(
            telegram_user=telegram_user,
            vacancy_id=prepared_vacancy["vacancy_id"],
            telegram_message_id=str(message.message_id),
        )
        return {
            "animation_sent": True,
            "message_id": message.message_id,
            "media_message_id": media_message.message_id,
        }

    def _build_caption(self, prepared_vacancy: dict) -> str:
        summary = self._trim(prepared_vacancy.get("match_summary") or "-", 240)
        lines = [
            prepared_vacancy["vacancy_tag"],
            prepared_vacancy.get("title") or "Untitled vacancy",
            prepared_vacancy.get("company_name") or "Unknown company",
            "",
            f"Match score: {prepared_vacancy.get('match_score')}",
            summary,
        ]
        return self._trim("\n".join(lines), 1024)

    def _build_full_text(self, prepared_vacancy: dict) -> str:
        missing_skills = prepared_vacancy.get("missing_skills_json") or []
        employer = prepared_vacancy.get("employer_check_json") or {}
        summary = prepared_vacancy.get("match_summary") or "-"
        cover_letter = prepared_vacancy.get("cover_letter") or "-"
        missing = ", ".join(missing_skills) if missing_skills else "-"
        resume_link = prepared_vacancy.get("resume_link")
        lines = [
            prepared_vacancy["vacancy_tag"],
            prepared_vacancy.get("title") or "Untitled vacancy",
            prepared_vacancy.get("company_name") or "Unknown company",
            "",
            f"Match score: {prepared_vacancy.get('match_score')}",
            f"Employer check: {employer.get('status', '-')}",
            f"Missing skills: {missing}",
            "",
            summary,
            "",
            cover_letter,
            "",
        ]
        if resume_link:
            lines.extend(
                [
                    f"Resume: {resume_link}",
                    "",
                ]
            )
        lines.extend(
            [
            prepared_vacancy.get("alternate_url") or "-",
            ]
        )
        return "\n".join(lines)

    def _trim(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: max(limit - 1, 0)].rstrip() + "…"

    def _save_telegram_message_id(
        self,
        *,
        telegram_user: TelegramUser,
        vacancy_id: int,
        telegram_message_id: str,
    ) -> None:
        with session_scope() as session:
            user = UserRepository(session).get_by_telegram_user_id(telegram_user.id)
            if user is None:
                return
            SentVacancyRepository(session).set_telegram_message_id(
                user_id=user.id,
                vacancy_id=vacancy_id,
                telegram_message_id=telegram_message_id,
            )
