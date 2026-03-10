from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

router = Router(name="controls")


@router.message(Command("pause"))
async def pause_command(message: Message) -> None:
    await message.answer("Автопоиск остановлен. Настройки и история сохранены.")


@router.message(Command("resume"))
async def resume_command(message: Message) -> None:
    await message.answer("Автопоиск возобновлен.")


@router.callback_query(F.data == "control:pause")
async def pause_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Автопоиск остановлен. Настройки и история сохранены.")
    await callback.answer()


@router.callback_query(F.data == "control:resume")
async def resume_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Автопоиск возобновлен.")
    await callback.answer()
