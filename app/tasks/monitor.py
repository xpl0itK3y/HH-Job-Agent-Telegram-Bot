from aiogram.types import User as TelegramUser

from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.services.vacancy_search_service import VacancySearchService
from app.tasks.analysis import analyze_and_send_vacancy
from app.tasks.celery_app import celery_app


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
        if not settings.is_enabled:
            return {"status": "disabled", "telegram_user_id": telegram_user_id}

    telegram_user = TelegramUser(id=telegram_user_id, is_bot=False, first_name="User")
    vacancies = search_service.search_for_user(telegram_user=telegram_user)
    for vacancy in vacancies:
        analyze_and_send_vacancy.delay(telegram_user_id, vacancy["id"])
    return {"status": "queued", "telegram_user_id": telegram_user_id, "count": len(vacancies)}
