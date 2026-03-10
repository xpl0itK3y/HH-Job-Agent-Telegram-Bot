from app.tasks.celery_app import celery_app


@celery_app.task(name="tasks.send_resume_reminder")
def send_resume_reminder(telegram_user_id: int) -> dict:
    return {"status": "scheduled", "telegram_user_id": telegram_user_id}
