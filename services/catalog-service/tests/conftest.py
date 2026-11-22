"""Pytest fixtures for Catalog Service testing."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.application.interfaces import CacheServiceInterface
from app.core.dependencies import get_cache_service, get_db_session
from app.infrastructure.cache.redis_client import InMemoryCacheService
from app.infrastructure.db.models import Base
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def test_engine():
    """Create a fresh in-memory SQLite engine for tests."""
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an active db session for a test."""
    session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    async with session_maker() as session:
        yield session


@pytest.fixture
def fake_cache() -> CacheServiceInterface:
    """Provide an in-memory cache implementation."""
    return InMemoryCacheService()


@pytest.fixture
async def client(
    test_session: AsyncSession, fake_cache: CacheServiceInterface
) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with overridden dependencies."""

    async def _override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield test_session

    async def _override_get_cache_service() -> CacheServiceInterface:
        return fake_cache

    app.dependency_overrides[get_db_session] = _override_get_db_session
    app.dependency_overrides[get_cache_service] = _override_get_cache_service

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
