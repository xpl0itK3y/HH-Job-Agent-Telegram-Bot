from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def build_search_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Казахстан", callback_data="settings:country:KZ")
    builder.button(text="Россия", callback_data="settings:country:RU")
    builder.button(text="Казахстан и Россия", callback_data="settings:country:KZ+RU")
    builder.button(text="Удаленно", callback_data="settings:format:remote")
    builder.button(text="Офис", callback_data="settings:format:office")
    builder.button(text="Гибрид", callback_data="settings:format:hybrid")
    builder.button(text="Не важно", callback_data="settings:format:any")
    builder.button(text="Полная занятость", callback_data="settings:employment:full-time")
    builder.button(text="Частичная занятость", callback_data="settings:employment:part-time")
    builder.button(text="Проектная работа", callback_data="settings:employment:project")
    builder.button(text="Стажировка", callback_data="settings:employment:internship")
    builder.button(text="Волонтерство", callback_data="settings:employment:volunteer")
    builder.button(text="Совмещение", callback_data="settings:employment:combined")
    builder.button(text="Не важно", callback_data="settings:employment:any")
    builder.button(text="Запустить поток вакансий", callback_data="settings:toggle:on")
    builder.button(text="Остановить поток вакансий", callback_data="settings:toggle:off")
    builder.adjust(1)
    return builder.as_markup()


def build_resume_input_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отправить текстом", callback_data="onboarding:resume:text")
    builder.button(text="Отправить файлом", callback_data="onboarding:resume:file")
    builder.button(text="У меня есть ссылка на резюме", callback_data="onboarding:resume:link")
    builder.adjust(1)
    return builder.as_markup()


def build_resume_link_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Пропустить", callback_data="onboarding:resume_link:skip")
    builder.adjust(1)
    return builder.as_markup()


def build_search_country_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Казахстан", callback_data="onboarding:country:KZ")
    builder.button(text="Россия", callback_data="onboarding:country:RU")
    builder.button(text="Казахстан и Россия", callback_data="onboarding:country:KZ+RU")
    builder.adjust(1)
    return builder.as_markup()


def build_work_format_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Удаленно", callback_data="onboarding:format:remote")
    builder.button(text="Офис", callback_data="onboarding:format:office")
    builder.button(text="Гибрид", callback_data="onboarding:format:hybrid")
    builder.button(text="Не важно", callback_data="onboarding:format:any")
    builder.adjust(1)
    return builder.as_markup()


def build_employment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Полная занятость", callback_data="onboarding:employment:full-time")
    builder.button(text="Частичная занятость", callback_data="onboarding:employment:part-time")
    builder.button(text="Проектная работа", callback_data="onboarding:employment:project")
    builder.button(text="Стажировка", callback_data="onboarding:employment:internship")
    builder.button(text="Волонтерство", callback_data="onboarding:employment:volunteer")
    builder.button(text="Совмещение", callback_data="onboarding:employment:combined")
    builder.button(text="Не важно", callback_data="onboarding:employment:any")
    builder.adjust(1)
    return builder.as_markup()


def build_stream_control_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Начать поток вакансий", callback_data="onboarding:stream:start")
    builder.button(text="Показать статус", callback_data="status:show")
    builder.adjust(1)
    return builder.as_markup()
