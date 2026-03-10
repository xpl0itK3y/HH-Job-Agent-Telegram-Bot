from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "/start - открыть главное меню\n"
        "/help - показать помощь\n"
        "/pause - остановить поиск вакансий\n"
        "/resume - возобновить поиск\n"
        "/settings - открыть настройки поиска"
    )
