from app.db.models.sent_vacancy import ProcessingStatus
from app.db.models.user import BotStatus
from admin_app.services.db_service import AdminDBService


class AnalyticsService:
    def __init__(self) -> None:
        self.db = AdminDBService()

    def get_dashboard_summary(self) -> dict[str, int]:
        return {
            "users_total": self.db.count_users(),
            "users_active": self.db.count_users_by_status(BotStatus.ACTIVE),
            "users_paused": self.db.count_users_by_status(BotStatus.PAUSED),
            "vacancies_total": self.db.count_vacancies(),
            "queued_total": self.db.count_sent_by_status(ProcessingStatus.QUEUED),
            "processing_total": self.db.count_sent_by_status(ProcessingStatus.PROCESSING),
            "failed_total": self.db.count_sent_by_status(ProcessingStatus.FAILED),
            "sent_today": self.db.count_sent_by_status(ProcessingStatus.SENT),
        }

    def get_recent_sent_vacancies(self) -> list[dict]:
        return self.db.get_recent_sent_vacancies()

    def get_recent_users(self) -> list[dict]:
        return self.db.get_recent_users()
