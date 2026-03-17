from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "/start - открыть главное меню\n"
        "/help - показать помощь\n"
        "/pause - остановить поток вакансий\n"
        "/resume - возобновить поток вакансий\n"
        "/settings - открыть настройки поиска\n"
        "Кнопка «Показать статус» - показать текущий статус бота"
    )
