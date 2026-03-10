from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.db.models.chat_message import ChatMessage, ChatMessageRole


class ChatMessageRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        vacancy_id: int,
        role: ChatMessageRole,
        message_text: str,
    ) -> ChatMessage:
        message = ChatMessage(
            user_id=user_id,
            vacancy_id=vacancy_id,
            role=role,
            message_text=message_text,
        )
        self.session.add(message)
        self.session.flush()
        return message

    def get_recent_by_vacancy(
        self,
        *,
        user_id: int,
        vacancy_id: int,
        limit: int = 12,
    ) -> list[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.user_id == user_id, ChatMessage.vacancy_id == vacancy_id)
            .order_by(desc(ChatMessage.created_at))
            .limit(limit)
        )
        messages = list(self.session.scalars(stmt))
        messages.reverse()
        return messages
