from aiogram.types import User as TelegramUser

from app.db.repositories.search_setting_repository import SearchSettingRepository
from app.db.repositories.user_repository import UserRepository
from app.db.session import session_scope
from app.integrations.hh.selection import resolve_selected_countries
from app.tasks.triggers import trigger_user_monitoring


class SearchSettingService:
    def update_keywords(self, *, telegram_user: TelegramUser, keywords: str) -> None:
        self._update_fields(telegram_user=telegram_user, keywords=keywords)

    def update_countries(self, *, telegram_user: TelegramUser, selected: str) -> None:
        countries = resolve_selected_countries(selected)
        self._update_fields(telegram_user=telegram_user, selected_countries_json=countries)

    def update_area_ids(self, *, telegram_user: TelegramUser, area_ids: list[int]) -> None:
        self._update_fields(telegram_user=telegram_user, area_ids_json=area_ids)

    def update_employment_type(self, *, telegram_user: TelegramUser, employment_type: str) -> None:
        self._update_fields(telegram_user=telegram_user, employment_type=employment_type)

    def update_work_format(self, *, telegram_user: TelegramUser, work_format: str) -> None:
        self._update_fields(telegram_user=telegram_user, work_format=work_format)

    def update_professional_role(self, *, telegram_user: TelegramUser, professional_role: str) -> None:
        self._update_fields(telegram_user=telegram_user, professional_role=professional_role)

    def set_enabled(self, *, telegram_user: TelegramUser, is_enabled: bool) -> None:
        self._update_fields(telegram_user=telegram_user, is_enabled=is_enabled)
        if is_enabled:
            trigger_user_monitoring(telegram_user.id)

    def get_summary(self, *, telegram_user: TelegramUser) -> str:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            settings = SearchSettingRepository(session).get_or_create(user.id)
            return (
                "Текущие настройки поиска:\n"
                f"- ключевые слова: {settings.keywords or 'не заданы'}\n"
                f"- страны: {self._format_countries(settings.selected_countries_json)}\n"
                f"- регионы: {settings.area_ids_json or 'не заданы'}\n"
                f"- занятость: {self._employment_label(settings.employment_type)}\n"
                f"- формат работы: {self._work_format_label(settings.work_format)}\n"
                f"- роль: {settings.professional_role or 'не задана'}\n"
                f"- поток вакансий: {'включен' if settings.is_enabled else 'выключен'}"
            )

    def _update_fields(self, *, telegram_user: TelegramUser, **fields: object) -> None:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            settings = SearchSettingRepository(session).get_or_create(user.id)
            for key, value in fields.items():
                setattr(settings, key, value)
            session.flush()

    def _format_countries(self, countries: list | None) -> str:
        if not countries:
            return "не заданы"
        mapping = {"KZ": "Казахстан", "RU": "Россия"}
        return ", ".join(mapping.get(country, str(country)) for country in countries)

    def _work_format_label(self, value: str | None) -> str:
        mapping = {
            "remote": "Удаленно",
            "office": "Офис",
            "hybrid": "Гибрид",
            "any": "Не важно",
        }
        return mapping.get(value or "", "не задан")

    def _employment_label(self, value: str | None) -> str:
        mapping = {
            "full-time": "Полная занятость",
            "part-time": "Частичная занятость",
            "project": "Проектная работа",
            "internship": "Стажировка",
            "volunteer": "Волонтерство",
            "combined": "Совмещение",
            "any": "Не важно",
        }
        return mapping.get(value or "", "не задана")
