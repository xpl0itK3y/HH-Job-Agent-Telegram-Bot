from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main import build_main_menu_keyboard
from app.bot.keyboards.search_settings import (
    build_employment_keyboard,
    build_resume_input_keyboard,
    build_resume_link_keyboard,
    build_search_country_keyboard,
    build_stream_control_keyboard,
    build_work_format_keyboard,
)
from app.bot.states.onboarding import OnboardingFlow
from app.services.bot_status_service import BotStatusService
from app.services.resume_service import ResumeService
from app.services.search_setting_service import SearchSettingService
from app.utils.document import UnsupportedDocumentFormatError

router = Router(name="onboarding")
resume_service = ResumeService()
search_setting_service = SearchSettingService()
bot_status_service = BotStatusService()
MAX_RESUME_FILE_SIZE_BYTES = 10 * 1024 * 1024


@router.callback_query(F.data == "onboarding:start")
async def onboarding_start_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await state.clear()
        await callback.message.answer(
            "Шаг 1 из 5. Выберите, как отправить резюме.",
            reply_markup=build_resume_input_keyboard(),
        )
    await callback.answer()


@router.callback_query(F.data == "onboarding:resume:text")
async def resume_text_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await state.set_state(OnboardingFlow.waiting_for_resume_text)
        await callback.message.answer(
            "Отправьте резюме одним сообщением текстом.\n\n"
            "Статус: ожидаю текст резюме."
        )
    await callback.answer()


@router.callback_query(F.data == "onboarding:resume:file")
async def resume_file_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await state.set_state(OnboardingFlow.waiting_for_resume_file)
        await callback.message.answer(
            "Отправьте резюме файлом.\n"
            "Поддерживаются: PDF, DOCX, ODT, TXT, MD, HTML, RTF. Размер файла до 10 MB.\n\n"
            "Статус: ожидаю файл резюме."
        )
    await callback.answer()


@router.callback_query(F.data == "onboarding:resume:link")
async def resume_direct_link_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await state.set_state(OnboardingFlow.waiting_for_resume_link)
        await callback.message.answer(
            "Пришлите ссылку на резюме, чтобы использовать ее в сопроводительном письме.",
            reply_markup=build_resume_link_keyboard(),
        )
    await callback.answer()


async def _ask_resume_link(message: Message, state: FSMContext) -> None:
    await state.set_state(OnboardingFlow.waiting_for_resume_link)
    await message.answer(
        "Шаг 2 из 5. Пришлите ссылку на резюме для сопроводительного письма.\n"
        "Если ссылки нет, нажмите «Пропустить».",
        reply_markup=build_resume_link_keyboard(),
    )


async def _ask_country(message: Message) -> None:
    await message.answer(
        "Шаг 3 из 5. Выберите страну поиска вакансий.",
        reply_markup=build_search_country_keyboard(),
    )


async def _ask_work_format(message: Message) -> None:
    await message.answer(
        "Шаг 4 из 5. Выберите формат работы.",
        reply_markup=build_work_format_keyboard(),
    )


async def _ask_employment(message: Message) -> None:
    await message.answer(
        "Шаг 5 из 5. Выберите тип занятости.",
        reply_markup=build_employment_keyboard(),
    )


async def _show_stream_start(message: Message, telegram_user) -> None:
    await message.answer(
        "Настройки сохранены. Можно запускать поток вакансий.\n\n"
        f"{bot_status_service.get_summary(telegram_user=telegram_user)}",
        reply_markup=build_stream_control_keyboard(),
    )


@router.message(F.document.mime_type == "application/pdf")
async def pdf_resume_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    document = message.document
    if document is None or message.from_user is None:
        await message.answer("Не удалось обработать PDF.")
        return
    current_state = await state.get_state()
    if current_state != OnboardingFlow.waiting_for_resume_file.state:
        await message.answer("Сначала нажмите «Запустить настройку», потом выберите отправку файла.")
        return
    if document.file_size and document.file_size > MAX_RESUME_FILE_SIZE_BYTES:
        await message.answer("Файл слишком большой. Отправьте файл до 10 MB.")
        return

    file_info = await bot.get_file(document.file_id)
    file_data = await bot.download_file(file_info.file_path)
    pdf_bytes = file_data.read()

    try:
        result = resume_service.save_pdf_resume(
            telegram_user=message.from_user,
            filename=document.file_name or "resume.pdf",
            pdf_bytes=pdf_bytes,
        )
    except Exception:
        await message.answer("Не удалось извлечь текст из PDF. Попробуйте другой файл.")
        return

    await message.answer(
        "PDF-резюме сохранено.\n"
        f"Извлечено символов: {len(result.resume.raw_text)}\n"
        f"Нормализованный текст: {len(result.normalized_text)} символов.\n\n"
        "Статус: резюме загружено."
    )
    await _ask_resume_link(message, state)


@router.message(F.document & (F.document.mime_type != "application/pdf"))
async def document_resume_handler(message: Message, bot: Bot, state: FSMContext) -> None:
    document = message.document
    if document is None or message.from_user is None:
        await message.answer("Не удалось обработать файл.")
        return
    current_state = await state.get_state()
    if current_state != OnboardingFlow.waiting_for_resume_file.state:
        await message.answer("Сначала нажмите «Запустить настройку», потом выберите отправку файла.")
        return
    if document.file_size and document.file_size > MAX_RESUME_FILE_SIZE_BYTES:
        await message.answer("Файл слишком большой. Отправьте файл до 10 MB.")
        return

    file_info = await bot.get_file(document.file_id)
    file_data = await bot.download_file(file_info.file_path)
    file_bytes = file_data.read()

    try:
        result = resume_service.save_document_resume(
            telegram_user=message.from_user,
            filename=document.file_name or "resume",
            mime_type=document.mime_type,
            file_bytes=file_bytes,
        )
    except UnsupportedDocumentFormatError as exc:
        await message.answer(str(exc))
        return
    except Exception:
        await message.answer("Не удалось извлечь текст из файла. Попробуйте другой формат.")
        return

    await message.answer(
        "Файл-резюме сохранен.\n"
        f"Извлечено символов: {len(result.resume.raw_text)}\n"
        f"Нормализованный текст: {len(result.normalized_text)} символов.\n\n"
        "Статус: резюме загружено."
    )
    await _ask_resume_link(message, state)


@router.message(F.text.startswith("http"))
async def resume_link_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        await message.answer("Не удалось сохранить ссылку на резюме.")
        return

    current_state = await state.get_state()
    if current_state != OnboardingFlow.waiting_for_resume_link.state:
        await message.answer("Ссылку можно отправить после загрузки резюме в шаге настройки.")
        return

    resume_service.save_resume_link(
        telegram_user=message.from_user,
        resume_link=message.text.strip(),
    )
    await state.clear()
    await message.answer("Ссылка на резюме сохранена.\n\nСтатус: ссылка добавлена.")
    await _ask_country(message)


@router.callback_query(F.data == "onboarding:resume_link:skip")
async def skip_resume_link_callback(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.message is not None:
        await state.clear()
        await callback.message.answer("Ссылку пропустили. Ее можно добавить позже.\n\nСтатус: продолжаем настройку.")
        await _ask_country(callback.message)
    await callback.answer()


@router.message(F.text)
async def text_message_handler(message: Message, state: FSMContext) -> None:
    if message.text is None or message.text.startswith("/") or message.from_user is None:
        return
    current_state = await state.get_state()
    if current_state != OnboardingFlow.waiting_for_resume_text.state:
        return

    result = resume_service.save_text_resume(
        telegram_user=message.from_user,
        text=message.text,
    )
    await message.answer(
        "Текстовое резюме сохранено.\n"
        f"Исходный текст: {len(result.resume.raw_text)} символов\n"
        f"Нормализованный текст: {len(result.normalized_text)} символов.\n\n"
        "Статус: резюме загружено."
    )
    await _ask_resume_link(message, state)


@router.callback_query(F.data.startswith("onboarding:country:"))
async def onboarding_country_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return
    selected = callback.data.removeprefix("onboarding:country:")
    search_setting_service.update_countries(telegram_user=callback.from_user, selected=selected)
    await callback.message.answer("Страна поиска сохранена.\n\nСтатус: страна выбрана.")
    await _ask_work_format(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("onboarding:format:"))
async def onboarding_format_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return
    work_format = callback.data.removeprefix("onboarding:format:")
    search_setting_service.update_work_format(telegram_user=callback.from_user, work_format=work_format)
    await callback.message.answer("Формат работы сохранен.\n\nСтатус: формат работы выбран.")
    await _ask_employment(callback.message)
    await callback.answer()


@router.callback_query(F.data.startswith("onboarding:employment:"))
async def onboarding_employment_callback(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.message is None or callback.data is None:
        await callback.answer()
        return
    employment_type = callback.data.removeprefix("onboarding:employment:")
    search_setting_service.update_employment_type(
        telegram_user=callback.from_user,
        employment_type=employment_type,
    )
    await callback.message.answer("Тип занятости сохранен.\n\nСтатус: настройки поиска готовы.")
    await _show_stream_start(callback.message, callback.from_user)
    await callback.answer()


@router.callback_query(F.data == "onboarding:stream:start")
async def onboarding_stream_start_callback(callback: CallbackQuery) -> None:
    if callback.from_user is not None and callback.message is not None:
        search_setting_service.set_enabled(telegram_user=callback.from_user, is_enabled=True)
        await callback.message.answer(
            "Поток вакансий запущен.\n"
            "Сейчас начну подбирать и отправлять подходящие вакансии.\n\n"
            f"{bot_status_service.get_summary(telegram_user=callback.from_user)}",
            reply_markup=build_main_menu_keyboard(),
        )
    await callback.answer()
