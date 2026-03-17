from aiogram.types import User as TelegramUser

from app.db.models.sent_vacancy import ProcessingStatus
from app.db.models.user import BotStatus
from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.sent_vacancy_repository import SentVacancyRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.services.vacancy_search_service import VacancySearchService
from app.tasks.analysis import analyze_and_send_vacancy
from app.tasks.celery_app import celery_app
from app.utils.vacancy_tag import build_vacancy_tag


@celery_app.task(name="tasks.monitor_all_users")
def monitor_all_users() -> dict:
    with session_scope() as session:
        telegram_user_ids = UserRepository(session).list_monitorable_telegram_user_ids()

    for telegram_user_id in telegram_user_ids:
        monitor_new_vacancies.delay(telegram_user_id)

    return {"status": "queued", "user_count": len(telegram_user_ids)}


@celery_app.task(name="tasks.monitor_new_vacancies")
def monitor_new_vacancies(telegram_user_id: int) -> dict:
    search_service = VacancySearchService()
    with session_scope() as session:
        user = UserRepository(session).get_by_telegram_user_id(telegram_user_id)
        if user is None:
            raise ValueError(f"User with telegram id {telegram_user_id} not found")
        settings = SearchSettingRepository(session).get_or_create(user.id)
        if not settings.is_enabled or user.bot_status != BotStatus.ACTIVE:
            return {"status": "disabled", "telegram_user_id": telegram_user_id}

    telegram_user = TelegramUser(id=telegram_user_id, is_bot=False, first_name="User")
    vacancies = search_service.search_for_user(telegram_user=telegram_user)
    queued_vacancy_ids: list[int] = []
    with session_scope() as session:
        sent_repository = SentVacancyRepository(session)
        for vacancy in vacancies:
            sent_vacancy = sent_repository.enqueue(
                user_id=user.id,
                vacancy_id=vacancy["id"],
                vacancy_tag=build_vacancy_tag(vacancy_id=vacancy["id"]),
            )
            if sent_vacancy.processing_status == ProcessingStatus.SENT:
                continue
            queued_vacancy_ids.append(vacancy["id"])

    for vacancy_id in queued_vacancy_ids:
        analyze_and_send_vacancy.delay(telegram_user_id, vacancy_id)
    return {"status": "queued", "telegram_user_id": telegram_user_id, "count": len(queued_vacancy_ids)}
