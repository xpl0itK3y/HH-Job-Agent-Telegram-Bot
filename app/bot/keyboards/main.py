from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Запустить настройку", callback_data="onboarding:start")
    builder.button(text="Показать статус", callback_data="status:show")
    builder.button(text="Настроить поиск", callback_data="settings:open")
    builder.button(text="Остановить поток вакансий", callback_data="control:pause")
    builder.button(text="Возобновить поток вакансий", callback_data="control:resume")
    builder.adjust(1)
    return builder.as_markup()
