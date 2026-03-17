from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_env: str = Field(default="local")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)

    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="hh_job_agent")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    telegram_bot_token: str = Field(default="")
    telegram_webhook_secret: str = Field(default="")

    deepseek_api_key: str = Field(default="")
    deepseek_base_url: str = Field(default="")
    deepseek_model: str = Field(default="deepseek-chat")

    hh_kz_api_base_url: str = Field(default="https://api.hh.kz")
    hh_kz_site_base_url: str = Field(default="https://hh.kz")
    hh_kz_default_area_id: int = Field(default=40)

    hh_ru_api_base_url: str = Field(default="https://api.hh.ru")
    hh_ru_site_base_url: str = Field(default="https://hh.ru")
    hh_ru_default_area_id: int = Field(default=113)

    monitor_interval_minutes: int = Field(default=30)
    vacancy_send_delay_seconds: int = Field(default=60)
    vacancy_min_match_score: int = Field(default=60)
    reminder_after_hours: int = Field(default=24)

    streamlit_admin_username: str = Field(default="")
    streamlit_admin_password_hash: str = Field(default="")
    streamlit_secret_key: str = Field(default="")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
