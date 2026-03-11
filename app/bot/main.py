import asyncio

from app.bot.router import build_dispatcher
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.integrations.telegram.client import create_telegram_bot


async def run_polling() -> None:
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    bot = create_telegram_bot()
    dispatcher = build_dispatcher()

    await bot.delete_webhook(drop_pending_updates=False)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


def main() -> None:
    configure_logging()
    asyncio.run(run_polling())


if __name__ == "__main__":
    main()
