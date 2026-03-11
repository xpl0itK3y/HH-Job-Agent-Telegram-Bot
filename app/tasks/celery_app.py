from celery import Celery

from app.core.config import get_settings
from app.core.redis import build_redis_url


def create_celery() -> Celery:
    redis_url = build_redis_url()
    settings = get_settings()
    app = Celery("hh_job_agent", broker=redis_url, backend=redis_url)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        imports=("app.tasks.analysis", "app.tasks.monitor", "app.tasks.reminders"),
        beat_schedule={
            "monitor-new-vacancies": {
                "task": "tasks.monitor_all_users",
                "schedule": settings.monitor_interval_minutes * 60,
            },
        },
    )
    return app


celery_app = create_celery()
