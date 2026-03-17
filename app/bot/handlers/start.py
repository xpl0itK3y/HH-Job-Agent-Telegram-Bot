from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.main import build_main_menu_keyboard
from app.services.bot_status_service import BotStatusService

router = Router(name="start")
bot_status_service = BotStatusService()


@router.message(CommandStart())
async def start_command(message: Message) -> None:
    status_text = (
        bot_status_service.get_summary(telegram_user=message.from_user)
        if message.from_user is not None
        else "Статус пока недоступен."
    )
    await message.answer(
        "Добро пожаловать в HH Job Agent.\n"
        "Сначала загрузите резюме, затем укажите ссылку на него, настройте поиск и запустите поток вакансий.\n\n"
        f"{status_text}",
        reply_markup=build_main_menu_keyboard(),
    )
