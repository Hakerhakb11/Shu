"""Dependency Injection providers for FastAPI routers."""

from collections.abc import AsyncGenerator

from fastapi import Depends, Header, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.application.interfaces import (
    CacheServiceInterface,
    CategoryRepositoryInterface,
    ItemRepositoryInterface,
)
from app.application.services import CatalogService
from app.core.config import settings
from app.infrastructure.cache.redis_client import RedisCacheService
from app.infrastructure.db.session import get_engine, get_session_maker
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.item_repository import ItemRepository

# Engine & Session Maker Singletons
_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None
_redis_client: Redis | None = None


def get_global_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = get_engine(settings.async_database_url)
    return _engine


def get_global_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_maker
    if _session_maker is None:
        _session_maker = get_session_maker(get_global_engine())
    return _session_maker


async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.redis_connection_url,
            encoding="utf-8",
            decode_responses=False,
        )
    return _redis_client


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an active async database session with automatic transaction handling."""
    session_maker = get_global_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_item_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ItemRepositoryInterface:
    return ItemRepository(session)


def get_category_repository(
    session: AsyncSession = Depends(get_db_session),
) -> CategoryRepositoryInterface:
    return CategoryRepository(session)


async def get_cache_service(
    redis: Redis = Depends(get_redis),
) -> CacheServiceInterface:
    return RedisCacheService(redis, default_ttl_seconds=settings.REDIS_CACHE_TTL_SECONDS)


def get_catalog_service(
    item_repo: ItemRepositoryInterface = Depends(get_item_repository),
    category_repo: CategoryRepositoryInterface = Depends(get_category_repository),
    cache_service: CacheServiceInterface = Depends(get_cache_service),
) -> CatalogService:
    return CatalogService(
        item_repo=item_repo,
        category_repo=category_repo,
        cache_service=cache_service,
    )


# --- Role & Header Verification Dependencies ---


def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str | None:
    return x_user_id


def get_current_user_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> str | None:
    return x_user_role


def require_seller_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> tuple[str, str]:
    """Verify that caller has SELLER role."""
    if not x_user_role or x_user_role.upper() == "CLIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль SELLER.",
        )
    if x_user_role.upper() != "SELLER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль SELLER.",
        )
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заголовок X-User-Id обязателен для создания товара.",
        )
    return x_user_id, x_user_role.upper()


def require_seller_or_moderator(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> tuple[str, str]:
    """Verify that caller is either SELLER (for own item) or MODERATOR (for any item)."""
    if not x_user_role or x_user_role.upper() == "CLIENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: роль CLIENT не может изменять или удалять товары.",
        )
    role_norm = x_user_role.upper()
    if role_norm not in ("SELLER", "MODERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав.",
        )
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Заголовок X-User-Id обязателен.",
        )
    return x_user_id, role_norm


def require_moderator_role(
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> str:
    """Verify that caller has MODERATOR role."""
    if not x_user_role or x_user_role.upper() in ("CLIENT", "SELLER"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль MODERATOR.",
        )
    role_norm = x_user_role.upper()
    if role_norm != "MODERATOR":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещен: требуется роль MODERATOR.",
        )
    return role_norm
