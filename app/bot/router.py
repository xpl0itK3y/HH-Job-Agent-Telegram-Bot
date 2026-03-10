from aiogram import Dispatcher

from app.bot.handlers.controls import router as controls_router
from app.bot.handlers.help import router as help_router
from app.bot.handlers.onboarding import router as onboarding_router
from app.bot.handlers.search_settings import router as search_settings_router
from app.bot.handlers.start import router as start_router


def build_dispatcher() -> Dispatcher:
    dispatcher = Dispatcher()
    dispatcher.include_router(start_router)
    dispatcher.include_router(help_router)
    dispatcher.include_router(controls_router)
    dispatcher.include_router(search_settings_router)
    dispatcher.include_router(onboarding_router)
    return dispatcher
