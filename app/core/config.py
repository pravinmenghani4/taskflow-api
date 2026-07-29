"""Application configuration.

Settings are loaded once at import time from environment variables and/or a
local `.env` file (see `.env.example`). Import the shared `settings` object
anywhere you need configuration — never read `os.environ` directly elsewhere.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "TaskFlow API"
    environment: str = "development"
    database_url: str = "sqlite:///./taskflow.db"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        """Split the comma-separated CORS origins into a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (built only once per process)."""
    return Settings()


settings = get_settings()
