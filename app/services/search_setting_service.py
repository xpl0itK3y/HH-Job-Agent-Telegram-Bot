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
                f"- keywords: {settings.keywords or 'не заданы'}\n"
                f"- countries: {settings.selected_countries_json or 'не заданы'}\n"
                f"- area_ids: {settings.area_ids_json or 'не заданы'}\n"
                f"- employment: {settings.employment_type or 'не задано'}\n"
                f"- work_format: {settings.work_format or 'не задан'}\n"
                f"- role: {settings.professional_role or 'не задана'}\n"
                f"- enabled: {'yes' if settings.is_enabled else 'no'}"
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
