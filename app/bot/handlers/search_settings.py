from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router(name="search_settings")


@router.message(Command("settings"))
async def settings_command(message: Message) -> None:
    await message.answer(
        "Настройки поиска:\n"
        "- страна: Казахстан / Россия / Казахстан и Россия\n"
        "- формат: remote / office / hybrid\n"
        "- тип занятости: full-time / part-time / project"
    )


@router.callback_query(F.data == "settings:open")
async def settings_callback(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Откройте настройки поиска и выберите страны: Казахстан, Россия или обе страны."
    )
    await callback.answer()
