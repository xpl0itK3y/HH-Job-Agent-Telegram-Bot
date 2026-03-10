from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.services.user_control_service import UserControlService

router = Router(name="controls")
user_control_service = UserControlService()


@router.message(Command("pause"))
async def pause_command(message: Message) -> None:
    if message.from_user is not None:
        user_control_service.pause(telegram_user=message.from_user)
    await message.answer("Автопоиск остановлен. Настройки и история сохранены.")


@router.message(Command("resume"))
async def resume_command(message: Message) -> None:
    if message.from_user is not None:
        user_control_service.resume(telegram_user=message.from_user)
    await message.answer("Автопоиск возобновлен.")


@router.callback_query(F.data == "control:pause")
async def pause_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None:
        user_control_service.pause(telegram_user=callback.from_user)
    await callback.message.answer("Автопоиск остановлен. Настройки и история сохранены.")
    await callback.answer()


@router.callback_query(F.data == "control:resume")
async def resume_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None:
        user_control_service.resume(telegram_user=callback.from_user)
    await callback.message.answer("Автопоиск возобновлен.")
    await callback.answer()
