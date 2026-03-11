import time

from aiogram import Bot
from aiogram.types import User as TelegramUser

from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.services.vacancy_ai_service import VacancyAIService
from app.services.vacancy_delivery_service import VacancyDeliveryService


class VacancyPipelineService:
    def __init__(self) -> None:
        self.vacancy_ai_service = VacancyAIService()
        self.vacancy_delivery_service = VacancyDeliveryService()

    def prepare_vacancy(self, *, telegram_user: TelegramUser, vacancy_id: int) -> dict:
        prepared = self.vacancy_ai_service.analyze_and_prepare(
            telegram_user=telegram_user,
            vacancy_id=vacancy_id,
        )
        if not prepared.get("should_send", True):
            return prepared
        with session_scope() as session:
            user = UserRepository(session).get_by_telegram_user_id(telegram_user.id)
            if user is not None:
                SentVacancyRepository(session).mark_ready_to_send(
                    user_id=user.id,
                    vacancy_id=vacancy_id,
                )
        return prepared

    async def deliver_prepared_vacancy(
        self,
        *,
        bot: Bot,
        telegram_user: TelegramUser,
        prepared_vacancy: dict,
    ) -> dict:
        return await self.vacancy_delivery_service.send_to_user(
            bot=bot,
            telegram_user=telegram_user,
            prepared_vacancy=prepared_vacancy,
        )

    def add_send_delay(self, delay_seconds: int) -> None:
        if delay_seconds > 0:
            time.sleep(delay_seconds)
