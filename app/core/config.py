from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TIMEMACHINE-AI API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"

    DATABASE_URL: str = "sqlite:///./app/data/app.db"

    LANGCHAIN_MODEL: str = "gpt-4o-mini"
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_TRACING: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
