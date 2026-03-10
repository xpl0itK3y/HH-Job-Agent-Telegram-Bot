from celery import Celery

from app.core.redis import build_redis_url


def create_celery() -> Celery:
    redis_url = build_redis_url()
    app = Celery("hh_job_agent", broker=redis_url, backend=redis_url)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
    )
    return app


celery_app = create_celery()
