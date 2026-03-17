from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.search_settings import build_search_settings_keyboard
from app.services.search_setting_service import SearchSettingService

router = Router(name="search_settings")
search_setting_service = SearchSettingService()


@router.message(Command("settings"))
async def settings_command(message: Message) -> None:
    if message.from_user is None:
        await message.answer("Не удалось открыть настройки.")
        return

    await message.answer(
        search_setting_service.get_summary(telegram_user=message.from_user),
        reply_markup=build_search_settings_keyboard(),
    )


@router.callback_query(F.data == "settings:open")
async def settings_callback(callback: CallbackQuery) -> None:
    if callback.message is None or callback.from_user is None:
        await callback.answer()
        return

    await callback.message.answer(
        search_setting_service.get_summary(telegram_user=callback.from_user),
        reply_markup=build_search_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:country:"))
async def settings_country_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer()
        return

    selected = callback.data.removeprefix("settings:country:")
    search_setting_service.update_countries(telegram_user=callback.from_user, selected=selected)
    await callback.message.answer("Страны поиска сохранены.")
    await callback.answer()


@router.callback_query(F.data.startswith("settings:format:"))
async def settings_format_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer()
        return

    work_format = callback.data.removeprefix("settings:format:")
    search_setting_service.update_work_format(
        telegram_user=callback.from_user,
        work_format=work_format,
    )
    await callback.message.answer("Формат работы сохранен.")
    await callback.answer()


@router.callback_query(F.data.startswith("settings:employment:"))
async def settings_employment_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer()
        return

    employment_type = callback.data.removeprefix("settings:employment:")
    search_setting_service.update_employment_type(
        telegram_user=callback.from_user,
        employment_type=employment_type,
    )
    await callback.message.answer("Тип занятости сохранен.")
    await callback.answer()


@router.callback_query(F.data.startswith("settings:toggle:"))
async def settings_toggle_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None or callback.message is None:
        await callback.answer()
        return

    is_enabled = callback.data.removeprefix("settings:toggle:") == "on"
    search_setting_service.set_enabled(
        telegram_user=callback.from_user,
        is_enabled=is_enabled,
    )
    await callback.message.answer(
        "Поток вакансий включен." if is_enabled else "Поток вакансий отключен."
    )
    await callback.answer()


@router.message(F.text.startswith("keywords:"))
async def keywords_message_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    keywords = message.text.removeprefix("keywords:").strip()
    search_setting_service.update_keywords(telegram_user=message.from_user, keywords=keywords)
    await message.answer(f"Ключевые слова сохранены: {keywords}")


@router.message(F.text.startswith("areas:"))
async def areas_message_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    raw_area_ids = message.text.removeprefix("areas:").strip()
    try:
        area_ids = [int(item.strip()) for item in raw_area_ids.split(",") if item.strip()]
    except ValueError:
        await message.answer("Неверный формат areas. Используйте, например: areas: 40,113")
        return
    search_setting_service.update_area_ids(telegram_user=message.from_user, area_ids=area_ids)
    await message.answer(f"Идентификаторы регионов сохранены: {area_ids}")


@router.message(F.text.startswith("role:"))
async def role_message_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        return

    professional_role = message.text.removeprefix("role:").strip()
    search_setting_service.update_professional_role(
        telegram_user=message.from_user,
        professional_role=professional_role,
    )
    await message.answer(f"Роль сохранена: {professional_role}")
