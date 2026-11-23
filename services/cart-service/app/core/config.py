"""Конфигурация сервиса корзины через переменные окружения."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения Cart Service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Cart Service API"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8002

    redis_url: str = "redis://localhost:6379/1"
    redis_socket_timeout: float = 3.0
    cart_ttl_seconds: int = 2_592_000  # 30 дней
    max_item_quantity: int = 99

    catalog_service_url: str = "http://catalog-service:8000"
    catalog_timeout_seconds: float = 3.0


@lru_cache
def get_settings() -> Settings:
    """Вернуть кэшированный экземпляр настроек приложения."""
    return Settings()
