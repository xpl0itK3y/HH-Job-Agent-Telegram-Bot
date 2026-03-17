import asyncio
import logging

from aiogram.types import User as TelegramUser

from app.core.config import get_settings
from app.core.locks import vacancy_send_lock
from app.db.models.sent_vacancy import PipelineStep
from app.db.models.user import BotStatus
from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.integrations.telegram.client import create_telegram_bot
from app.services.vacancy_pipeline_service import VacancyPipelineService
from app.tasks.celery_app import celery_app

logger = logging.getLogger("app.celery.analysis")


@celery_app.task(
    name="tasks.analyze_and_send_vacancy",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def analyze_and_send_vacancy(self, telegram_user_id: int, vacancy_id: int) -> dict:
    settings = get_settings()
    pipeline = VacancyPipelineService()

    with vacancy_send_lock(telegram_user_id) as acquired:
        if not acquired:
            raise self.retry(
                countdown=max(settings.vacancy_send_delay_seconds, 5),
                exc=RuntimeError(
                    f"User {telegram_user_id} is locked for vacancy delivery, retrying vacancy {vacancy_id}"
                ),
            )

        with session_scope() as session:
            user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
            if user is None:
                raise ValueError(f"User with telegram id {telegram_user_id} not found")
            search_settings = SearchSettingRepository(session).get_or_create(user.id)
            if not search_settings.is_enabled or user.bot_status != BotStatus.ACTIVE:
                SentVacancyRepository(session).mark_failed(
                    user_id=user.id,
                    vacancy_id=vacancy_id,
                    error_text="Отправка остановлена: поток вакансий отключен пользователем.",
                )
                return {
                    "status": "disabled",
                    "telegram_user_id": telegram_user_id,
                    "vacancy_id": vacancy_id,
                }
            SentVacancyRepository(session).mark_processing(
                user_id=user.id,
                vacancy_id=vacancy_id,
                step=PipelineStep.MATCH_ANALYSIS,
            )

        telegram_user = TelegramUser(id=telegram_user_id, is_bot=False, first_name="User")
        try:
            prepared = pipeline.prepare_vacancy(
                telegram_user=telegram_user,
                vacancy_id=vacancy_id,
            )
            if not prepared.get("should_send", True):
                return {
                    "status": "skipped",
                    "telegram_user_id": telegram_user_id,
                    "vacancy_id": vacancy_id,
                    "reason": prepared.get("skip_reason") or "filtered",
                }
            with session_scope() as session:
                user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
                if user is None:
                    raise ValueError(f"User with telegram id {telegram_user_id} not found")
                search_settings = SearchSettingRepository(session).get_or_create(user.id)
                if not search_settings.is_enabled or user.bot_status != BotStatus.ACTIVE:
                    SentVacancyRepository(session).mark_failed(
                        user_id=user.id,
                        vacancy_id=vacancy_id,
                        error_text="Отправка остановлена перед доставкой: поток вакансий отключен пользователем.",
                    )
                    return {
                        "status": "disabled",
                        "telegram_user_id": telegram_user_id,
                        "vacancy_id": vacancy_id,
                    }
            bot = create_telegram_bot()
            asyncio.run(
                pipeline.deliver_prepared_vacancy(
                    bot=bot,
                    telegram_user=telegram_user,
                    prepared_vacancy=prepared,
                )
            )
            pipeline.add_send_delay(settings.vacancy_send_delay_seconds)
            return {"status": "sent", "telegram_user_id": telegram_user_id, "vacancy_id": vacancy_id}
        except Exception as exc:
            logger.exception("Celery vacancy analysis pipeline failed")
            with session_scope() as session:
                user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
                if user is not None:
                    SentVacancyRepository(session).mark_failed(
                        user_id=user.id,
                        vacancy_id=vacancy_id,
                        error_text=str(exc),
                    )
            raise
