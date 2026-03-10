from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main import build_main_menu_keyboard

router = Router(name="start")


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    await message.answer(
        "HH Job Agent Bot запущен.\n"
        "Загрузите резюме или откройте настройки поиска.",
        reply_markup=build_main_menu_keyboard(),
    )
