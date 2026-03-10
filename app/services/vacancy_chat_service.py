from aiogram.types import User as TelegramUser

from app.db.models.chat_message import ChatMessageRole
from app.db.repositories.chat_message_repository import ChatMessageRepository
from app.db.repositories.resume_repository import ResumeRepository
from app.db.repositories.sent_vacancy_lookup_repository import SentVacancyLookupRepository
from app.db.repositories.user_repository import UserRepository
from app.db.repositories.vacancy_repository import VacancyRepository
from app.db.session import session_scope
from app.integrations.deepseek.client import DeepSeekClient


class VacancyChatService:
    def __init__(self) -> None:
        self.deepseek_client = DeepSeekClient()

    def answer_by_tag(
        self,
        *,
        telegram_user: TelegramUser,
        vacancy_tag: str,
        question: str,
    ) -> dict:
        with session_scope() as session:
            user = UserRepository(session).create_or_update_telegram_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
            )
            sent_vacancy = SentVacancyLookupRepository(session).get_by_tag_for_user(
                user_id=user.id,
                vacancy_tag=vacancy_tag,
            )
            if sent_vacancy is None:
                raise ValueError("Vacancy tag not found for this user")

            vacancy = VacancyRepository(session).get_by_id(sent_vacancy.vacancy_id)
            if vacancy is None:
                raise ValueError("Vacancy not found")

            resume = ResumeRepository(session).get_latest_by_user_id(user.id)
            user_profile = (resume.parsed_profile_json if resume else None) or {}

            chat_repo = ChatMessageRepository(session)
            history = chat_repo.get_recent_by_vacancy(
                user_id=user.id,
                vacancy_id=vacancy.id,
                limit=10,
            )
            history_payload = [
                {"role": message.role.value, "content": message.message_text}
                for message in history
            ]

            chat_repo.create(
                user_id=user.id,
                vacancy_id=vacancy.id,
                role=ChatMessageRole.USER,
                message_text=question,
            )

            answer = self.deepseek_client.answer_about_vacancy(
                user_profile=user_profile,
                vacancy={
                    "title": vacancy.title,
                    "company_name": vacancy.company_name,
                    "description_ai_summary": vacancy.description_ai_summary,
                    "description_clean": vacancy.description_clean,
                    "alternate_url": vacancy.alternate_url,
                },
                chat_history=history_payload,
                question=question,
            )["answer"]

            chat_repo.create(
                user_id=user.id,
                vacancy_id=vacancy.id,
                role=ChatMessageRole.ASSISTANT,
                message_text=answer,
            )

            return {
                "vacancy_tag": sent_vacancy.vacancy_tag,
                "vacancy_id": vacancy.id,
                "answer": answer,
                "history_size": len(history_payload) + 2,
            }
