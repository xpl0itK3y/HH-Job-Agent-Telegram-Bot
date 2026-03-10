from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

router = Router(name="onboarding")


@router.callback_query(F.data == "onboarding:upload_resume")
async def upload_resume_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Отправьте резюме PDF-файлом или текстом одним сообщением.")
    await callback.answer()


@router.callback_query(F.data == "onboarding:resume_link")
async def resume_link_callback(callback: CallbackQuery) -> None:
    await callback.message.answer("Отправьте ссылку на резюме одним сообщением.")
    await callback.answer()


@router.message(F.document.mime_type == "application/pdf")
async def pdf_resume_handler(message: Message) -> None:
    await message.answer("PDF получен. Следующий шаг: скачать файл и извлечь текст.")


@router.message(F.text.startswith("http"))
async def resume_link_handler(message: Message) -> None:
    await message.answer("Ссылка на резюме получена. Следующий шаг: сохранить и обработать ее.")


@router.message(F.text)
async def text_message_handler(message: Message) -> None:
    if message.text.startswith("/"):
        return
    await message.answer(
        "Текст получен. Можно использовать его как резюме или уточнение по вакансии."
    )
