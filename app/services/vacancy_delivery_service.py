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
        try:
            message = await bot.send_animation(
                chat_id=telegram_user.id,
                animation=animation,
                caption=caption,
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
        }

    def _build_caption(self, prepared_vacancy: dict) -> str:
        missing_skills = prepared_vacancy.get("missing_skills_json") or []
        employer = prepared_vacancy.get("employer_check_json") or {}
        summary = self._trim(prepared_vacancy.get("match_summary") or "-", 280)
        cover_letter = self._trim(prepared_vacancy.get("cover_letter") or "-", 220)
        missing = ", ".join(missing_skills[:5]) if missing_skills else "-"
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
            prepared_vacancy.get("alternate_url") or "-",
        ]
        caption = "\n".join(lines)
        return self._trim(caption, 1024)

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
