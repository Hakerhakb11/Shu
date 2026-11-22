"""Application settings and configuration."""

import os

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Catalog Service"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    PORT: int = 5000

    # PostgreSQL configuration
    CATALOG_DB_HOST: str = "localhost"
    CATALOG_DB_PORT: int = 5433
    CATALOG_DB_USER: str = "catalog_user"
    CATALOG_DB_PASSWORD: str = "catalog_password"
    CATALOG_DB_NAME: str = "catalog_db"
    DATABASE_URL: str | None = None

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str | None = None
    REDIS_CACHE_TTL_SECONDS: int = 120

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Convert postgresql:// to postgresql+asyncpg:// if needed
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url
        return (
            f"postgresql+asyncpg://{self.CATALOG_DB_USER}:{self.CATALOG_DB_PASSWORD}"
            f"@{self.CATALOG_DB_HOST}:{self.CATALOG_DB_PORT}/{self.CATALOG_DB_NAME}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings = Settings()
