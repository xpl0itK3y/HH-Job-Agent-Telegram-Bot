from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Загрузить резюме", callback_data="onboarding:upload_resume")
    builder.button(text="Указать ссылку на резюме", callback_data="onboarding:resume_link")
    builder.button(text="Настроить поиск", callback_data="settings:open")
    builder.button(text="Остановить бота", callback_data="control:pause")
    builder.button(text="Возобновить поиск", callback_data="control:resume")
    builder.adjust(1)
    return builder.as_markup()
