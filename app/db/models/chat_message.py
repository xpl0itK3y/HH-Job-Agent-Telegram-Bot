from enum import StrEnum

from sqlalchemy import ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.enums import values_enum
from app.db.models.mixins import TimestampMixin


class ChatMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(TimestampMixin, Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False, index=True)
    role: Mapped[ChatMessageRole] = mapped_column(
        values_enum(ChatMessageRole, name="chat_message_role_enum"),
        nullable=False,
    )
    message_text: Mapped[str] = mapped_column(Text, nullable=False)

    user = relationship("User")
    vacancy = relationship("Vacancy")
