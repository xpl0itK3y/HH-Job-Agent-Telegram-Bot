import asyncio

from aiogram.types import User as TelegramUser

from app.core.config import get_settings
from app.core.locks import vacancy_send_lock
from app.db.models.sent_vacancy import PipelineStep
from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.integrations.telegram.client import create_telegram_bot
from app.services.vacancy_pipeline_service import VacancyPipelineService
from app.tasks.celery_app import celery_app


@celery_app.task(
    name="tasks.analyze_and_send_vacancy",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def analyze_and_send_vacancy(telegram_user_id: int, vacancy_id: int) -> dict:
    settings = get_settings()
    pipeline = VacancyPipelineService()

    with vacancy_send_lock(telegram_user_id) as acquired:
        if not acquired:
            return {"status": "locked", "telegram_user_id": telegram_user_id, "vacancy_id": vacancy_id}

        with session_scope() as session:
            user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
            if user is None:
                raise ValueError(f"User with telegram id {telegram_user_id} not found")
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
            with session_scope() as session:
                user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
                if user is not None:
                    SentVacancyRepository(session).mark_failed(
                        user_id=user.id,
                        vacancy_id=vacancy_id,
                        error_text=str(exc),
                    )
            raise
