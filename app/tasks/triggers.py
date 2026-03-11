from app.tasks.monitor import monitor_new_vacancies


def trigger_user_monitoring(telegram_user_id: int) -> None:
    monitor_new_vacancies.delay(telegram_user_id)
