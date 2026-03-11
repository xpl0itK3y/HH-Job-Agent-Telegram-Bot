from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import and_, case, func, or_, select

from app.core.redis import get_redis_client
from app.db.models.resume import Resume
from app.db.models.chat_message import ChatMessage
from app.db.models.admin_audit_log import AdminAuditLog
from app.db.models.scheduled_reminder import ScheduledReminder
from app.db.models.sent_vacancy import ProcessingStatus, SentVacancy
from app.db.models.search_setting import SearchSetting
from app.db.models.user import BotStatus, User
from app.db.models.admin_user import AdminUser
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
                    SentVacancy.processing_status == ProcessingStatus.SENT.value,
                )
                .correlate(User)
                .scalar_subquery()
            )
            failed_count = (
                select(func.count(SentVacancy.id))
                .where(
                    SentVacancy.user_id == User.id,
                    SentVacancy.processing_status == ProcessingStatus.FAILED.value,
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
                stmt = stmt.where(User.bot_status == filters["bot_status"])
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
            stmt = select(func.count()).select_from(User).where(User.bot_status == status.value)
            return session.scalar(stmt) or 0

    def count_vacancies(self) -> int:
        with session_scope() as session:
            return session.scalar(select(func.count()).select_from(Vacancy)) or 0

    def count_sent_by_status(self, status: ProcessingStatus) -> int:
        with session_scope() as session:
            stmt = select(func.count()).select_from(SentVacancy).where(SentVacancy.processing_status == status.value)
            return session.scalar(stmt) or 0

    def count_sent_today(self) -> int:
        start_of_day = datetime.combine(date.today(), time.min, tzinfo=UTC)
        with session_scope() as session:
            stmt = (
                select(func.count())
                .select_from(SentVacancy)
                .where(
                    and_(
                        SentVacancy.processing_status == ProcessingStatus.SENT.value,
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
                .where(SentVacancy.processing_status == ProcessingStatus.FAILED.value)
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

    def get_resumes(self, *, filters: dict | None = None, limit: int = 100) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = (
                select(Resume, User)
                .join(User, User.id == Resume.user_id)
                .order_by(Resume.updated_at.desc(), Resume.id.desc())
                .limit(limit)
            )
            if filters.get("user_id") is not None:
                stmt = stmt.where(Resume.user_id == filters["user_id"])
            if filters.get("source_type"):
                stmt = stmt.where(Resume.source_type == filters["source_type"])
            if filters.get("username"):
                stmt = stmt.where(User.username.ilike(f"%{filters['username']}%"))
            rows = list(session.execute(stmt))

        return [
            {
                "id": resume.id,
                "user_id": resume.user_id,
                "username": user.username,
                "telegram_user_id": user.telegram_user_id,
                "source_type": resume.source_type.value,
                "file_path": resume.file_path,
                "resume_link": resume.resume_link,
                "raw_text": resume.raw_text,
                "parsed_profile_json": resume.parsed_profile_json,
                "summary": resume.summary,
                "llm_model_name": resume.llm_model_name,
                "llm_prompt_version": resume.llm_prompt_version,
                "llm_generated_at": resume.llm_generated_at.isoformat() if resume.llm_generated_at else None,
                "updated_at": resume.updated_at.isoformat(),
            }
            for resume, user in rows
        ]

    def get_search_settings(self, *, filters: dict | None = None, limit: int = 100) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = (
                select(SearchSetting, User)
                .join(User, User.id == SearchSetting.user_id)
                .order_by(SearchSetting.updated_at.desc(), SearchSetting.id.desc())
                .limit(limit)
            )
            if filters.get("user_id") is not None:
                stmt = stmt.where(SearchSetting.user_id == filters["user_id"])
            if filters.get("username"):
                stmt = stmt.where(User.username.ilike(f"%{filters['username']}%"))
            if filters.get("is_enabled") is True:
                stmt = stmt.where(SearchSetting.is_enabled.is_(True))
            elif filters.get("is_enabled") is False:
                stmt = stmt.where(SearchSetting.is_enabled.is_(False))
            rows = list(session.execute(stmt))

        settings_rows = []
        for search_setting, user in rows:
            countries = search_setting.selected_countries_json or []
            if filters.get("country") and filters["country"] not in countries:
                continue
            settings_rows.append(
                {
                    "id": search_setting.id,
                    "user_id": search_setting.user_id,
                    "username": user.username,
                    "telegram_user_id": user.telegram_user_id,
                    "keywords": search_setting.keywords,
                    "selected_countries_json": countries,
                    "area_ids_json": search_setting.area_ids_json,
                    "employment_type": search_setting.employment_type,
                    "work_format": search_setting.work_format,
                    "professional_role": search_setting.professional_role,
                    "search_extra_json": search_setting.search_extra_json,
                    "is_enabled": search_setting.is_enabled,
                    "updated_at": search_setting.updated_at.isoformat(),
                }
            )

        return settings_rows[:limit]

    def get_chat_history(self, *, filters: dict | None = None, limit: int = 200) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = (
                select(ChatMessage, User, Vacancy, SentVacancy)
                .join(User, User.id == ChatMessage.user_id)
                .join(Vacancy, Vacancy.id == ChatMessage.vacancy_id)
                .outerjoin(
                    SentVacancy,
                    and_(
                        SentVacancy.user_id == ChatMessage.user_id,
                        SentVacancy.vacancy_id == ChatMessage.vacancy_id,
                    ),
                )
                .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
                .limit(limit)
            )
            if filters.get("user_id") is not None:
                stmt = stmt.where(ChatMessage.user_id == filters["user_id"])
            if filters.get("role"):
                stmt = stmt.where(ChatMessage.role == filters["role"])
            if filters.get("vacancy_tag"):
                stmt = stmt.where(SentVacancy.vacancy_tag.ilike(f"%{filters['vacancy_tag']}%"))
            rows = list(session.execute(stmt))

        return [
            {
                "id": message.id,
                "user_id": message.user_id,
                "username": user.username,
                "telegram_user_id": user.telegram_user_id,
                "vacancy_id": message.vacancy_id,
                "vacancy_title": vacancy.title,
                "vacancy_tag": sent_vacancy.vacancy_tag if sent_vacancy else None,
                "role": message.role.value,
                "message_text": message.message_text,
                "created_at": message.created_at.isoformat(),
            }
            for message, user, vacancy, sent_vacancy in rows
        ]

    def get_admin_audit_logs(self, *, filters: dict | None = None, limit: int = 200) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = (
                select(AdminAuditLog, AdminUser)
                .join(AdminUser, AdminUser.id == AdminAuditLog.admin_user_id)
                .order_by(AdminAuditLog.created_at.desc(), AdminAuditLog.id.desc())
                .limit(limit)
            )
            if filters.get("action_type"):
                stmt = stmt.where(AdminAuditLog.action_type.ilike(f"%{filters['action_type']}%"))
            if filters.get("entity_type"):
                stmt = stmt.where(AdminAuditLog.entity_type == filters["entity_type"])
            if filters.get("admin_username"):
                stmt = stmt.where(AdminUser.username.ilike(f"%{filters['admin_username']}%"))
            rows = list(session.execute(stmt))

        return [
            {
                "id": audit.id,
                "admin_user_id": audit.admin_user_id,
                "admin_username": admin_user.username,
                "action_type": audit.action_type,
                "entity_type": audit.entity_type,
                "entity_id": audit.entity_id,
                "details_json": audit.details_json,
                "created_at": audit.created_at.isoformat(),
            }
            for audit, admin_user in rows
        ]

    def get_vacancies(self, *, filters: dict | None = None, limit: int = 100) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = select(Vacancy).order_by(Vacancy.fetched_at.desc().nullslast(), Vacancy.id.desc()).limit(limit)
            if filters.get("provider"):
                stmt = stmt.where(Vacancy.provider == filters["provider"])
            if filters.get("country"):
                stmt = stmt.where(Vacancy.source_country_code == filters["country"])
            if filters.get("company_name"):
                stmt = stmt.where(Vacancy.company_name.ilike(f"%{filters['company_name']}%"))
            if filters.get("title"):
                stmt = stmt.where(Vacancy.title.ilike(f"%{filters['title']}%"))
            if filters.get("has_ai_summary") is True:
                stmt = stmt.where(Vacancy.description_ai_summary.is_not(None))
            elif filters.get("has_ai_summary") is False:
                stmt = stmt.where(Vacancy.description_ai_summary.is_(None))
            rows = list(session.scalars(stmt))

        return [
            {
                "id": row.id,
                "provider": row.provider,
                "hh_vacancy_id": row.hh_vacancy_id,
                "source_country_code": row.source_country_code,
                "title": row.title,
                "company_name": row.company_name,
                "salary": self._format_salary(row.salary_from, row.salary_to, row.salary_currency),
                "published_at": row.published_at.isoformat() if row.published_at else None,
                "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
                "has_ai_summary": bool(row.description_ai_summary),
                "description_raw": row.description_raw,
                "description_clean": row.description_clean,
                "description_ai_summary": row.description_ai_summary,
                "key_skills_json": row.key_skills_json,
                "alternate_url": row.alternate_url,
                "employment_type": row.employment_type,
                "work_format": row.work_format,
                "experience": row.experience,
                "area_name": row.area_name,
            }
            for row in rows
        ]

    def get_sent_vacancies(self, *, filters: dict | None = None, limit: int = 100) -> list[dict]:
        filters = filters or {}
        with session_scope() as session:
            stmt = (
                select(SentVacancy, Vacancy)
                .join(Vacancy, Vacancy.id == SentVacancy.vacancy_id)
                .order_by(SentVacancy.id.desc())
                .limit(limit)
            )
            if filters.get("user_id") is not None:
                stmt = stmt.where(SentVacancy.user_id == filters["user_id"])
            if filters.get("status"):
                stmt = stmt.where(SentVacancy.processing_status == filters["status"])
            if filters.get("vacancy_tag"):
                stmt = stmt.where(SentVacancy.vacancy_tag.ilike(f"%{filters['vacancy_tag']}%"))
            if filters.get("provider"):
                stmt = stmt.where(Vacancy.provider == filters["provider"])
            if filters.get("has_cover_letter") is True:
                stmt = stmt.where(SentVacancy.cover_letter.is_not(None))
            elif filters.get("has_cover_letter") is False:
                stmt = stmt.where(SentVacancy.cover_letter.is_(None))
            rows = list(session.execute(stmt))

        return [
            {
                "id": sent.id,
                "user_id": sent.user_id,
                "vacancy_id": sent.vacancy_id,
                "vacancy_tag": sent.vacancy_tag,
                "provider": vacancy.provider,
                "title": vacancy.title,
                "company_name": vacancy.company_name,
                "processing_status": sent.processing_status.value,
                "match_score": sent.match_score,
                "match_summary": sent.match_summary,
                "missing_skills_json": sent.missing_skills_json,
                "employer_check_json": sent.employer_check_json,
                "cover_letter": sent.cover_letter,
                "telegram_message_id": sent.telegram_message_id,
                "sent_at": sent.sent_at.isoformat() if sent.sent_at else None,
                "current_pipeline_step": sent.current_pipeline_step.value if sent.current_pipeline_step else None,
                "retry_count": sent.retry_count,
                "last_error_text": sent.last_error_text,
                "description_ai_summary": vacancy.description_ai_summary,
                "description_clean": vacancy.description_clean,
                "alternate_url": vacancy.alternate_url,
            }
            for sent, vacancy in rows
        ]

    def get_queue_snapshot(self, *, limit: int = 100) -> dict:
        stale_before = datetime.now(UTC) - timedelta(minutes=15)
        with session_scope() as session:
            queue_rows = list(
                session.scalars(
                    select(SentVacancy)
                    .order_by(
                        case(
                            (SentVacancy.processing_status == ProcessingStatus.PROCESSING.value, 0),
                            (SentVacancy.processing_status == ProcessingStatus.QUEUED.value, 1),
                            else_=2,
                        ),
                        SentVacancy.queued_at.asc().nullslast(),
                        SentVacancy.id.desc(),
                    )
                    .limit(limit)
                )
            )
            reminder_rows = list(
                session.scalars(
                    select(ScheduledReminder)
                    .order_by(ScheduledReminder.run_at.desc())
                    .limit(20)
                )
            )

        queue_items = [
            {
                "id": row.id,
                "user_id": row.user_id,
                "vacancy_id": row.vacancy_id,
                "vacancy_tag": row.vacancy_tag,
                "status": row.processing_status.value,
                "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                "queued_at": row.queued_at.isoformat() if row.queued_at else None,
                "processing_started_at": row.processing_started_at.isoformat() if row.processing_started_at else None,
                "retry_count": row.retry_count,
                "stalled": bool(
                    row.processing_status == ProcessingStatus.PROCESSING
                    and row.processing_started_at
                    and row.processing_started_at < stale_before
                ),
                "last_error_text": row.last_error_text,
            }
            for row in queue_rows
        ]

        return {
            "summary": {
                "queued": sum(1 for row in queue_rows if row.processing_status == ProcessingStatus.QUEUED),
                "processing": sum(1 for row in queue_rows if row.processing_status == ProcessingStatus.PROCESSING),
                "ready_to_send": sum(1 for row in queue_rows if row.processing_status == ProcessingStatus.READY_TO_SEND),
                "failed": sum(1 for row in queue_rows if row.processing_status == ProcessingStatus.FAILED),
                "stalled": sum(1 for row in queue_items if row["stalled"]),
            },
            "queue_items": queue_items,
            "locks": self.get_active_locks(),
            "reminders": [
                {
                    "id": row.id,
                    "user_id": row.user_id,
                    "reminder_type": row.reminder_type,
                    "run_at": row.run_at.isoformat(),
                    "status": row.status,
                }
                for row in reminder_rows
            ],
        }

    def get_active_locks(self) -> list[dict]:
        try:
            client = get_redis_client()
            keys = sorted(client.keys("vacancy_send_lock:*"))
        except Exception as exc:
            return [{"lock_key": "redis_unavailable", "user_id": None, "status": str(exc)}]

        locks = []
        for key in keys:
            user_id = key.rsplit(":", 1)[-1]
            ttl = client.ttl(key)
            locks.append(
                {
                    "lock_key": key,
                    "user_id": int(user_id) if user_id.isdigit() else user_id,
                    "ttl_seconds": ttl,
                    "status": "locked",
                }
            )
        return locks

    def get_operational_logs(self, *, limit: int = 100) -> list[dict]:
        with session_scope() as session:
            failed_rows = list(
                session.scalars(
                    select(SentVacancy)
                    .where(
                        or_(
                            SentVacancy.processing_status == ProcessingStatus.FAILED.value,
                            SentVacancy.last_error_text.is_not(None),
                        )
                    )
                    .order_by(SentVacancy.failed_at.desc().nullslast(), SentVacancy.id.desc())
                    .limit(limit)
                )
            )

        return [
            {
                "entity": "sent_vacancy",
                "entity_id": row.id,
                "user_id": row.user_id,
                "vacancy_id": row.vacancy_id,
                "vacancy_tag": row.vacancy_tag,
                "status": row.processing_status.value,
                "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                "retry_count": row.retry_count,
                "timestamp": row.failed_at.isoformat()
                if row.failed_at
                else row.processing_started_at.isoformat()
                if row.processing_started_at
                else row.queued_at.isoformat()
                if row.queued_at
                else None,
                "message": row.last_error_text or "No error text captured",
            }
            for row in failed_rows
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
                    .limit(25)
                )
            )
            chat_rows = list(
                session.scalars(
                    select(ChatMessage)
                    .where(ChatMessage.user_id == user_id)
                    .order_by(ChatMessage.id.desc())
                    .limit(50)
                )
            )
            vacancy_ids = sorted({row.vacancy_id for row in sent_rows} | {row.vacancy_id for row in chat_rows})
            vacancies = {
                vacancy.id: vacancy
                for vacancy in session.scalars(select(Vacancy).where(Vacancy.id.in_(vacancy_ids)))
            }
            sent_by_vacancy_id = {row.vacancy_id: row for row in sent_rows}

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
                "file_path": resume.file_path,
                "summary": resume.summary,
                "raw_text": resume.raw_text,
                "resume_link": resume.resume_link,
                "parsed_profile_json": resume.parsed_profile_json,
                "llm_model_name": resume.llm_model_name,
                "llm_prompt_version": resume.llm_prompt_version,
                "llm_generated_at": resume.llm_generated_at.isoformat() if resume.llm_generated_at else None,
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
                    "id": row.id,
                    "vacancy_id": row.vacancy_id,
                    "tag": row.vacancy_tag,
                    "title": vacancies.get(row.vacancy_id).title if vacancies.get(row.vacancy_id) else None,
                    "company_name": vacancies.get(row.vacancy_id).company_name if vacancies.get(row.vacancy_id) else None,
                    "provider": vacancies.get(row.vacancy_id).provider if vacancies.get(row.vacancy_id) else None,
                    "source_country_code": (
                        vacancies.get(row.vacancy_id).source_country_code if vacancies.get(row.vacancy_id) else None
                    ),
                    "message_id": row.telegram_message_id,
                    "status": row.processing_status.value,
                    "score": row.match_score,
                    "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                    "match_summary": row.match_summary,
                    "missing_skills_json": row.missing_skills_json,
                    "employer_check_json": row.employer_check_json,
                    "cover_letter": row.cover_letter,
                    "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                    "error": row.last_error_text,
                    "description_raw": vacancies.get(row.vacancy_id).description_raw if vacancies.get(row.vacancy_id) else None,
                    "description_clean": (
                        vacancies.get(row.vacancy_id).description_clean if vacancies.get(row.vacancy_id) else None
                    ),
                    "description_ai_summary": (
                        vacancies.get(row.vacancy_id).description_ai_summary if vacancies.get(row.vacancy_id) else None
                    ),
                    "alternate_url": vacancies.get(row.vacancy_id).alternate_url if vacancies.get(row.vacancy_id) else None,
                    "key_skills_json": vacancies.get(row.vacancy_id).key_skills_json if vacancies.get(row.vacancy_id) else None,
                }
                for row in sent_rows
            ],
            "chat_messages": [
                {
                    "vacancy_id": row.vacancy_id,
                    "vacancy_tag": (
                        sent_by_vacancy_id[row.vacancy_id].vacancy_tag if row.vacancy_id in sent_by_vacancy_id else None
                    ),
                    "vacancy_title": vacancies.get(row.vacancy_id).title if vacancies.get(row.vacancy_id) else None,
                    "role": row.role.value,
                    "message_text": row.message_text,
                    "created_at": row.created_at.isoformat(),
                }
                for row in chat_rows
            ],
            "recent_errors": [
                {
                    "sent_vacancy_id": row.id,
                    "vacancy_id": row.vacancy_id,
                    "vacancy_tag": row.vacancy_tag,
                    "title": vacancies.get(row.vacancy_id).title if vacancies.get(row.vacancy_id) else None,
                    "step": row.current_pipeline_step.value if row.current_pipeline_step else None,
                    "retry_count": row.retry_count,
                    "failed_at": row.failed_at.isoformat() if row.failed_at else None,
                    "error": row.last_error_text,
                }
                for row in sent_rows
                if row.last_error_text or row.processing_status == ProcessingStatus.FAILED
            ],
        }

    @staticmethod
    def _format_salary(salary_from: int | None, salary_to: int | None, salary_currency: str | None) -> str:
        if salary_from is None and salary_to is None:
            return ""
        if salary_from is not None and salary_to is not None:
            amount = f"{salary_from} - {salary_to}"
        else:
            amount = str(salary_from if salary_from is not None else salary_to)
        return f"{amount} {salary_currency or ''}".strip()
