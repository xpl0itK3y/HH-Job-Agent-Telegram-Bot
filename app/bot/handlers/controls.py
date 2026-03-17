from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main import build_main_menu_keyboard
from app.services.bot_status_service import BotStatusService
from app.services.user_control_service import UserControlService

router = Router(name="controls")
user_control_service = UserControlService()
bot_status_service = BotStatusService()


@router.message(Command("pause"))
async def pause_command(message: Message) -> None:
    if message.from_user is not None:
        user_control_service.pause(telegram_user=message.from_user)
        await message.answer(
            "Поток вакансий остановлен. Настройки и история сохранены.\n\n"
            f"{bot_status_service.get_summary(telegram_user=message.from_user)}",
            reply_markup=build_main_menu_keyboard(),
        )


@router.message(Command("resume"))
async def resume_command(message: Message) -> None:
    if message.from_user is not None:
        user_control_service.resume(telegram_user=message.from_user)
        await message.answer(
            "Поток вакансий возобновлен.\n\n"
            f"{bot_status_service.get_summary(telegram_user=message.from_user)}",
            reply_markup=build_main_menu_keyboard(),
        )


@router.callback_query(F.data == "control:pause")
async def pause_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None:
        user_control_service.pause(telegram_user=callback.from_user)
        await callback.message.answer(
            "Поток вакансий остановлен. Настройки и история сохранены.\n\n"
            f"{bot_status_service.get_summary(telegram_user=callback.from_user)}",
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "control:resume")
async def resume_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None:
        user_control_service.resume(telegram_user=callback.from_user)
        await callback.message.answer(
            "Поток вакансий возобновлен.\n\n"
            f"{bot_status_service.get_summary(telegram_user=callback.from_user)}",
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "status:show")
async def status_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None and callback.message is not None:
        await callback.message.answer(
            bot_status_service.get_summary(telegram_user=callback.from_user),
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer()
