from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery, Message

from app.services.resume_service import ResumeService

router = Router(name="onboarding")
resume_service = ResumeService()


@router.callback_query(F.data == "onboarding:upload_resume")
async def upload_resume_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Отправьте резюме PDF-файлом или текстом одним сообщением.")
    await callback.answer()


@router.callback_query(F.data == "onboarding:resume_link")
async def resume_link_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Отправьте ссылку на резюме одним сообщением.")
    await callback.answer()


@router.message(F.document.mime_type == "application/pdf")
async def pdf_resume_handler(message: Message, bot: Bot) -> None:
    document = message.document
    if document is None or message.from_user is None:
        await message.answer("Не удалось обработать PDF.")
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
        f"Нормализованный текст: {len(result.normalized_text)} символов."
    )


@router.message(F.text.startswith("http"))
async def resume_link_handler(message: Message) -> None:
    if message.from_user is None or message.text is None:
        await message.answer("Не удалось сохранить ссылку на резюме.")
        return

    resume_service.save_resume_link(
        telegram_user=message.from_user,
        resume_link=message.text.strip(),
    )
    await message.answer("Ссылка на резюме сохранена.")


@router.message(F.text)
async def text_message_handler(message: Message) -> None:
    if message.text is None or message.text.startswith("/") or message.from_user is None:
        return

    result = resume_service.save_text_resume(
        telegram_user=message.from_user,
        text=message.text,
    )
    await message.answer(
        "Текстовое резюме сохранено.\n"
        f"Исходный текст: {len(result.resume.raw_text)} символов\n"
        f"Нормализованный текст: {len(result.normalized_text)} символов."
    )
