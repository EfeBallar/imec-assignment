from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Social Grouping Backend"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/social_grouping"
    min_match: int = Field(default=2, ge=0)
    grouping_interval_seconds: int = Field(default=30, ge=1)
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
