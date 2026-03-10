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
        try:
            await bot.send_animation(
                chat_id=telegram_user.id,
                animation=animation,
                caption=f"{prepared_vacancy['vacancy_tag']} {prepared_vacancy.get('title', '')}".strip(),
            )
            message = await bot.send_message(
                chat_id=telegram_user.id,
                text=self._build_text(prepared_vacancy),
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
        }

    def _build_text(self, prepared_vacancy: dict) -> str:
        missing_skills = prepared_vacancy.get("missing_skills_json") or []
        employer = prepared_vacancy.get("employer_check_json") or {}
        lines = [
            prepared_vacancy["vacancy_tag"],
            prepared_vacancy.get("title") or "Untitled vacancy",
            prepared_vacancy.get("company_name") or "Unknown company",
            "",
            f"Match score: {prepared_vacancy.get('match_score')}",
            f"Match summary: {prepared_vacancy.get('match_summary') or '-'}",
            f"Employer check: {employer.get('status', '-')}",
            f"Missing skills: {', '.join(missing_skills) if missing_skills else '-'}",
            "",
            prepared_vacancy.get("cover_letter") or "-",
            "",
            prepared_vacancy.get("alternate_url") or "-",
        ]
        return "\n".join(lines)

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
