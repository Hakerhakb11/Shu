"""Точка входа FastAPI приложения Cart Service."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.infrastructure.cache.redis_client import create_redis_client
from app.presentation.routers import cart_router, health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Управление жизненным циклом подключений к Redis и Catalog Service."""
    settings: Settings = get_settings()
    redis_client = create_redis_client(
        redis_url=settings.redis_url,
        socket_timeout=settings.redis_socket_timeout,
    )
    http_client = httpx.AsyncClient(
        base_url=settings.catalog_service_url,
        timeout=settings.catalog_timeout_seconds,
    )
    app.state.redis = redis_client
    app.state.http_client = http_client
    try:
        yield
    finally:
        await http_client.aclose()
        await redis_client.aclose()


def create_app() -> FastAPI:
    """Создать и сконфигурировать экземпляр FastAPI."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Сервис корзины книжного маркетплейса Shu на базе Redis "
            "с проверкой актуальности товаров в Catalog Service."
        ),
        lifespan=lifespan,
    )
    register_exception_handlers(app)
    app.include_router(cart_router)
    app.include_router(health_router)
    return app


app = create_app()


if __name__ == "__main__":
    cfg = get_settings()
    uvicorn.run(
        "app.main:app",
        host=cfg.app_host,
        port=cfg.app_port,
        reload=False,
    )
