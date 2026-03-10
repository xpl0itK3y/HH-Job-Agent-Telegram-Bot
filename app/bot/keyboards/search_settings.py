from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_search_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Страна: KZ", callback_data="settings:country:KZ")
    builder.button(text="Страна: RU", callback_data="settings:country:RU")
    builder.button(text="Страна: KZ + RU", callback_data="settings:country:KZ+RU")
    builder.button(text="Формат: remote", callback_data="settings:format:remote")
    builder.button(text="Формат: office", callback_data="settings:format:office")
    builder.button(text="Формат: hybrid", callback_data="settings:format:hybrid")
    builder.button(text="Занятость: full-time", callback_data="settings:employment:full-time")
    builder.button(text="Занятость: part-time", callback_data="settings:employment:part-time")
    builder.button(text="Занятость: project", callback_data="settings:employment:project")
    builder.button(text="Включить поиск", callback_data="settings:toggle:on")
    builder.button(text="Отключить поиск", callback_data="settings:toggle:off")
    builder.adjust(1)
    return builder.as_markup()
