from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.search_setting import SearchSetting


class SearchSettingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user_id(self, user_id: int) -> SearchSetting | None:
        stmt = select(SearchSetting).where(SearchSetting.user_id == user_id)
        return self.session.scalar(stmt)

    def get_or_create(self, user_id: int) -> SearchSetting:
        settings = self.get_by_user_id(user_id)
        if settings is not None:
            return settings

        settings = SearchSetting(user_id=user_id)
        self.session.add(settings)
        self.session.flush()
        return settings
