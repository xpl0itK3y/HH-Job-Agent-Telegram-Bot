from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


def build_redis_url() -> str:
    settings = get_settings()
    return f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


@lru_cache(maxsize=1)
def get_redis_client() -> Redis:
    return Redis.from_url(build_redis_url(), decode_responses=True)
