from aiogram.types import User as TelegramUser

from app.db.models.user import BotStatus
from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope


class BotStatusService:
    def get_summary(self, *, telegram_user: TelegramUser) -> str:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            resume = ResumeRepository(session).get_latest_by_user_id(user.id)
            settings = SearchSettingRepository(session).get_or_create(user.id)

            countries = settings.selected_countries_json or []
            countries_text = ", ".join(_country_label(country) for country in countries) if countries else "не выбраны"

            return (
                "Текущий статус:\n"
                f"Резюме: {'загружено' if resume else 'не загружено'}\n"
                f"Ссылка на резюме: {'есть' if resume and resume.resume_link else 'нет'}\n"
                f"Страны поиска: {countries_text}\n"
                f"Формат работы: {_work_format_label(settings.work_format)}\n"
                f"Занятость: {_employment_label(settings.employment_type)}\n"
                f"Поиск вакансий: {'идет' if settings.is_enabled and user.bot_status == BotStatus.ACTIVE else 'остановлен'}\n"
                f"Статус бота: {'активен' if user.bot_status == BotStatus.ACTIVE else 'на паузе'}"
            )


def _country_label(value: str) -> str:
    mapping = {
        "KZ": "Казахстан",
        "RU": "Россия",
    }
    return mapping.get(value, value)


def _work_format_label(value: str | None) -> str:
    mapping = {
        "remote": "Удаленно",
        "office": "Офис",
        "hybrid": "Гибрид",
        "any": "Не важно",
    }
    return mapping.get(value or "", "не выбран")


def _employment_label(value: str | None) -> str:
    mapping = {
        "full-time": "Полная занятость",
        "part-time": "Частичная занятость",
        "project": "Проектная работа",
        "internship": "Стажировка",
        "volunteer": "Волонтерство",
        "combined": "Совмещение",
        "any": "Не важно",
    }
    return mapping.get(value or "", "не выбрана")
