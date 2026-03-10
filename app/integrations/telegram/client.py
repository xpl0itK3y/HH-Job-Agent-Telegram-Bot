from aiogram import Bot

from app.core.config import get_settings


def create_telegram_bot() -> Bot:
    settings = get_settings()
    return Bot(token=settings.telegram_bot_token)
