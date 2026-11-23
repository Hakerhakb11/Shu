"""Провайдеры Dependency Injection для FastAPI."""

import httpx
from fastapi import Depends, Request, Security
from fastapi.security import APIKeyHeader
from redis.asyncio import Redis

from app.application.interfaces import CartRepositoryInterface, CatalogClientInterface
from app.application.services import CartService
from app.core.config import Settings, get_settings
from app.domain.exceptions import UnauthorizedUserError
from app.infrastructure.clients.catalog_client import HttpCatalogClient
from app.infrastructure.repositories.cart_repository import RedisCartRepository

user_id_header_scheme = APIKeyHeader(
    name="X-User-Id",
    scheme_name="UserIdAuth",
    description="Идентификатор пользователя, проброшенный API Gateway после проверки JWT",
    auto_error=False,
)


def get_current_user_id(
    x_user_id: str | None = Security(user_id_header_scheme),
) -> str:
    """Извлечь и проверить заголовок X-User-Id от API Gateway."""
    if x_user_id is None or not x_user_id.strip():
        raise UnauthorizedUserError("Отсутствует обязательный заголовок X-User-Id")
    return x_user_id.strip()


def get_redis_client(request: Request) -> Redis:
    """Получить клиент Redis из состояния приложения."""
    return request.app.state.redis


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Получить общий httpx.AsyncClient из состояния приложения."""
    return request.app.state.http_client


def get_cart_repository(
    redis_client: Redis = Depends(get_redis_client),
    settings: Settings = Depends(get_settings),
) -> CartRepositoryInterface:
    """Создать репозиторий корзины на базе Redis."""
    return RedisCartRepository(
        redis_client=redis_client,
        cart_ttl_seconds=settings.cart_ttl_seconds,
    )


def get_catalog_client(
    http_client: httpx.AsyncClient = Depends(get_http_client),
) -> CatalogClientInterface:
    """Создать HTTP-клиент для Catalog Service."""
    return HttpCatalogClient(http_client=http_client)


def get_cart_service(
    cart_repository: CartRepositoryInterface = Depends(get_cart_repository),
    catalog_client: CatalogClientInterface = Depends(get_catalog_client),
    settings: Settings = Depends(get_settings),
) -> CartService:
    """Собрать экземпляр CartService со всеми зависимостями."""
    return CartService(
        cart_repository=cart_repository,
        catalog_client=catalog_client,
        max_item_quantity=settings.max_item_quantity,
    )
