from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import and_, case, func, select

from app.db.models.resume import Resume
from app.db.models.chat_message import ChatMessage
from app.db.models.sent_vacancy import ProcessingStatus, SentVacancy
from app.db.models.search_setting import SearchSetting
from app.db.models.user import BotStatus, User
from app.db.models.vacancy import Vacancy
from app.db.session import session_scope


class AdminDBService:
    def get_users(self, *, filters: dict | None = None, limit: int = 50) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            resume_exists = (
                select(func.count(Resume.id) > 0)
                .where(Resume.user_id == User.id)
                .correlate(User)
                .scalar_subquery()
            )
            settings_exists = (
                select(func.count(SearchSetting.id) > 0)
                .where(SearchSetting.user_id == User.id, SearchSetting.is_enabled.is_(True))
                .correlate(User)
                .scalar_subquery()
            )
            sent_count = (
                select(func.count(SentVacancy.id))
                .where(
                    SentVacancy.user_id == User.id,
                    SentVacancy.processing_status == ProcessingStatus.SENT,
                )
                .correlate(User)
                .scalar_subquery()
            )
            failed_count = (
                select(func.count(SentVacancy.id))
                .where(
                    SentVacancy.user_id == User.id,
                    SentVacancy.processing_status == ProcessingStatus.FAILED,
                )
                .correlate(User)
                .scalar_subquery()
            )
            country_stmt = (
                select(SearchSetting.selected_countries_json)
                .where(SearchSetting.user_id == User.id)
                .order_by(
                    case((SearchSetting.is_enabled.is_(True), 0), else_=1),
                    SearchSetting.updated_at.desc(),
                    SearchSetting.id.desc(),
                )
                .limit(1)
                .correlate(User)
                .scalar_subquery()
            )

            stmt = (
                select(
                    User,
                    resume_exists.label("has_resume"),
                    settings_exists.label("has_search_settings"),
                    sent_count.label("sent_count"),
                    failed_count.label("failed_count"),
                    country_stmt.label("selected_countries"),
                )
                .order_by(User.created_at.desc())
                .limit(limit)
            )
            if filters.get("telegram_user_id") is not None:
                stmt = stmt.where(User.telegram_user_id == filters["telegram_user_id"])
            if filters.get("username"):
                stmt = stmt.where(User.username.ilike(f"%{filters['username']}%"))
            if filters.get("bot_status"):
                stmt = stmt.where(User.bot_status == BotStatus(filters["bot_status"]))
            rows = list(session.execute(stmt))

        users = []
        for user, has_resume, has_search_settings, sent_count, failed_count, selected_countries in rows:
            countries = ", ".join(selected_countries or []) if selected_countries else "none"
            if filters.get("country") and filters["country"] not in (selected_countries or []):
                continue
            users.append(
                {
                    "id": user.id,
                    "telegram_user_id": user.telegram_user_id,
                    "username": user.username,
                    "bot_status": user.bot_status.value,
                    "countries": countries,
                    "has_resume": bool(has_resume),
                    "has_search_settings": bool(has_search_settings),
                    "sent_count": int(sent_count or 0),
                    "failed_count": int(failed_count or 0),
                    "created_at": user.created_at.isoformat(),
                }
            )

        return users[:limit]

    def count_users(self) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(User)) or 0

    def count_users_by_status(self, status: BotStatus) -> int:
        with session_scope() as session:
            stmt = select(func.count()).select_from(User).where(User.bot_status == status)
            return session.scalar(stmt) or 0

    def count_vacancies(self) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(Vacancy)) or 0

    def count_sent_by_status(self, status: ProcessingStatus) -> int:
        with session_scope() as session:
            stmt = select(func.count()).select_from(SentVacancy).where(SentVacancy.processing_status == status)
            return session.scalar(stmt) or 0

    def count_sent_today(self) -> int:
        start_of_day = datetime.combine(date.today(), time.min, tzinfo=UTC)
        with session_scope() as session:
            stmt = (
                select(func.count())
                .select_from(SentVacancy)
                .where(
                    and_(
                        SentVacancy.processing_status == ProcessingStatus.SENT,
                        SentVacancy.sent_at.is_not(None),
                        SentVacancy.sent_at >= start_of_day,
                    )
                )
            )
            return session.scalar(stmt) or 0

    def get_recent_sent_vacancies(self, limit: int = 10) -> list[dict]:
        with session_scope() as session:
            stmt = select(SentVacancy).order_by(SentVacancy.id.desc()).limit(limit)
            rows = list(session.scalars(stmt))
        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "vacancy_id": row.vacancy_id,
                "vacancy_tag": row.vacancy_tag,
                "status": row.processing_status.value,
                "sent_at": row.sent_at.isoformat() if row.sent_at else None,
            }
            for row in rows
        ]

    def get_recent_users(self, limit: int = 10) -> list[dict]:
        return self.get_users(limit=limit)

    def get_country_split(self) -> list[dict]:
        with session_scope() as session:
            rows = list(
                session.execute(
                    select(SearchSetting.selected_countries_json)
                    .where(SearchSetting.is_enabled.is_(True))
                    .order_by(SearchSetting.id.desc())
                )
            )

        counters = {
            "KZ": 0,
            "RU": 0,
            "KZ + RU": 0,
            "Other": 0,
        }
        for (selected_countries,) in rows:
            selected = tuple(sorted(selected_countries or []))
            if selected == ("KZ",):
                counters["KZ"] += 1
            elif selected == ("RU",):
                counters["RU"] += 1
            elif selected == ("KZ", "RU"):
                counters["KZ + RU"] += 1
            else:
                counters["Other"] += 1

        return [{"segment": segment, "users": total} for segment, total in counters.items() if total]

    def get_vacancy_activity(self, days: int = 7) -> list[dict]:
        start_at = datetime.now(UTC) - timedelta(days=max(days - 1, 0))
        with session_scope() as session:
            rows = list(
                session.execute(
                    select(
                        func.date_trunc("day", SentVacancy.queued_at).label("day"),
                        func.count().label("queued"),
                    )
                    .where(SentVacancy.queued_at.is_not(None), SentVacancy.queued_at >= start_at)
                    .group_by("day")
                    .order_by("day")
                )
            )
            sent_rows = list(
                session.execute(
                    select(
                        func.date_trunc("day", SentVacancy.sent_at).label("day"),
                        func.count().label("sent"),
                    )
                    .where(SentVacancy.sent_at.is_not(None), SentVacancy.sent_at >= start_at)
                    .group_by("day")
                    .order_by("day")
                )
            )

        activity_map: dict[str, dict[str, int | str]] = {}
        for day, queued in rows:
            key = day.date().isoformat()
            activity_map[key] = {"date": key, "queued": int(queued), "sent": 0}
        for day, sent in sent_rows:
            key = day.date().isoformat()
            if key not in activity_map:
                activity_map[key] = {"date": key, "queued": 0, "sent": 0}
            activity_map[key]["sent"] = int(sent)

        return [activity_map[key] for key in sorted(activity_map)]

    def get_recent_failures(self, limit: int = 20) -> list[dict]:
        with session_scope() as session:
            stmt = (
                select(SentVacancy)
                .where(SentVacancy.processing_status == ProcessingStatus.FAILED)
                .order_by(SentVacancy.failed_at.desc().nullslast(), SentVacancy.id.desc())
                .limit(limit)
            )
            rows = list(session.scalars(stmt))

        return [
            {
                "id": row.id,
                "user_id": row.user_id,
                "vacancy_id": row.vacancy_id,
                "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                "retries": row.retry_count,
                "failed_at": row.failed_at.isoformat() if row.failed_at else None,
                "error": row.last_error_text,
            }
            for row in rows
        ]

    def get_user_detail(self, user_id: int) -> dict | None:
        with session_scope() as session:
            user = session.get(User, user_id)
            if user is None:
                return None

            resume = session.scalar(
                select(Resume).where(Resume.user_id == user_id).order_by(Resume.updated_at.desc(), Resume.id.desc()).limit(1)
            )
            search_setting = session.scalar(
                select(SearchSetting)
                .where(SearchSetting.user_id == user_id)
                .order_by(
                    case((SearchSetting.is_enabled.is_(True), 0), else_=1),
                    SearchSetting.updated_at.desc(),
                    SearchSetting.id.desc(),
                )
                .limit(1)
            )
            sent_rows = list(
                session.scalars(
                    select(SentVacancy)
                    .where(SentVacancy.user_id == user_id)
                    .order_by(SentVacancy.id.desc())
                    .limit(10)
                )
            )
            chat_rows = list(
                session.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                    .order_by(ChatMessage.id.desc())
                    .limit(10)
                )
            )

        return {
            "user": {
                "id": user.id,
                "telegram_user_id": user.telegram_user_id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "language_code": user.language_code,
                "is_active": user.is_active,
                "bot_status": user.bot_status.value,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
            },
            "resume": None
            if resume is None
            else {
                "source_type": resume.source_type.value,
                "summary": resume.summary,
                "raw_text": resume.raw_text,
                "resume_link": resume.resume_link,
                "parsed_profile_json": resume.parsed_profile_json,
                "updated_at": resume.updated_at.isoformat(),
            },
            "search_setting": None
            if search_setting is None
            else {
                "keywords": search_setting.keywords,
                "selected_countries_json": search_setting.selected_countries_json,
                "area_ids_json": search_setting.area_ids_json,
                "employment_type": search_setting.employment_type,
                "work_format": search_setting.work_format,
                "professional_role": search_setting.professional_role,
                "search_extra_json": search_setting.search_extra_json,
                "is_enabled": search_setting.is_enabled,
                "updated_at": search_setting.updated_at.isoformat(),
            },
            "sent_vacancies": [
                {
                    "vacancy_id": row.vacancy_id,
                    "tag": row.vacancy_tag,
                    "message_id": row.telegram_message_id,
                    "status": row.processing_status.value,
                    "score": row.match_score,
                    "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                    "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                    "error": row.last_error_text,
                }
                for row in sent_rows
            ],
            "chat_messages": [
                {
                    "vacancy_id": row.vacancy_id,
                    "role": row.role.value,
                    "message_text": row.message_text,
                    "created_at": row.created_at.isoformat(),
                }
                for row in chat_rows
            ],
        }
