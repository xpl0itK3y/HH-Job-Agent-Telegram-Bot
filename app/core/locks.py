from contextlib import contextmanager
from typing import Generator

from app.core.redis import get_redis_client


@contextmanager
def vacancy_send_lock(user_id: int, timeout_seconds: int = 300) -> Generator[bool, None, None]:
    client = get_redis_client()
    lock = client.lock(
        f"vacancy_send_lock:{user_id}",
        timeout=timeout_seconds,
        blocking_timeout=1,
    )
    acquired = lock.acquire(blocking=False)
    try:
        yield acquired
    finally:
        if acquired:
            lock.release()
