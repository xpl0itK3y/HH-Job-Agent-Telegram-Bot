from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.search_setting import SearchSetting
from app.db.models.user import BotStatus, User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        stmt = select(User).where(User.telegram_user_id == telegram_user_id)
        return self.session.scalar(stmt)

    def create_or_update_telegram_user(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        last_name: str | None,
        language_code: str | None,
    ) -> User:
        user = self.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                language_code=language_code,
            )
            self.session.add(user)
            self.session.flush()
            return user

        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.language_code = language_code
        self.session.flush()
        return user

    def set_bot_status(self, *, telegram_user_id: int, bot_status: BotStatus) -> User | None:
        user = self.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            return None
        user.bot_status = bot_status
        self.session.flush()
        return user

    def list_monitorable_telegram_user_ids(self) -> list[int]:
        stmt = (
            select(User.telegram_user_id)
            .join(SearchSetting, SearchSetting.user_id == User.id)
            .where(
                User.is_active.is_(True),
                User.bot_status == BotStatus.ACTIVE,
                SearchSetting.is_enabled.is_(True),
            )
            .distinct()
            .order_by(User.id.asc())
        )
        return list(self.session.scalars(stmt))
