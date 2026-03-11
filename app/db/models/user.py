from enum import StrEnum

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import values_enum
from app.db.models.mixins import TimestampMixin


class BotStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    bot_status: Mapped[BotStatus] = mapped_column(
        values_enum(BotStatus, name="bot_status_enum"),
        default=BotStatus.ACTIVE,
        nullable=False,
    )
