"""Общие фикстуры и in-memory фейки для тестов Cart Service."""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI

from app.application.interfaces import CartRepositoryInterface, CatalogClientInterface
from app.application.services import CartService
from app.core.dependencies import get_cart_service
from app.core.exceptions import register_exception_handlers
from app.domain.exceptions import CatalogServiceUnavailableError
from app.domain.models import CatalogItemSnapshot
from app.presentation.routers import cart_router, health_router


class InMemoryCartRepository(CartRepositoryInterface):
    """In-memory реализация репозитория корзины для быстрых изолированных тестов."""

    def __init__(self) -> None:
        self.storage: dict[str, dict[int, int]] = {}
        self.is_healthy: bool = True

    async def get_items(self, user_id: str) -> dict[int, int]:
        return dict(self.storage.get(user_id, {}))

    async def get_item_quantity(self, user_id: str, item_id: int) -> int | None:
        return self.storage.get(user_id, {}).get(item_id)

    async def increment_item(self, user_id: str, item_id: int, delta: int) -> int:
        user_cart = self.storage.setdefault(user_id, {})
        new_qty = user_cart.get(item_id, 0) + delta
        user_cart[item_id] = new_qty
        return new_qty

    async def set_item_quantity(self, user_id: str, item_id: int, quantity: int) -> int:
        user_cart = self.storage.setdefault(user_id, {})
        user_cart[item_id] = quantity
        return quantity

    async def remove_item(self, user_id: str, item_id: int) -> bool:
        user_cart = self.storage.get(user_id)
        if not user_cart or item_id not in user_cart:
            return False
        del user_cart[item_id]
        return True

    async def clear_cart(self, user_id: str) -> None:
        self.storage.pop(user_id, None)

    async def ping(self) -> bool:
        return self.is_healthy


class FakeCatalogClient(CatalogClientInterface):
    """Фейковый клиент Catalog Service для unit и API тестов."""

    def __init__(self, snapshots: dict[int, CatalogItemSnapshot] | None = None) -> None:
        self.snapshots: dict[int, CatalogItemSnapshot] = snapshots or {}
        self.should_fail: bool = False
        self.called_with: list[list[int]] = []

    async def get_items_batch(self, item_ids: list[int]) -> dict[int, CatalogItemSnapshot]:
        self.called_with.append(list(item_ids))
        if self.should_fail:
            raise CatalogServiceUnavailableError("Сервис каталога временно недоступен")
        return {
            item_id: self.snapshots[item_id]
            for item_id in item_ids
            if item_id in self.snapshots
        }


@pytest.fixture
def fake_repo() -> InMemoryCartRepository:
    return InMemoryCartRepository()


@pytest.fixture
def fake_catalog() -> FakeCatalogClient:
    return FakeCatalogClient()


@pytest.fixture
def cart_service(
    fake_repo: InMemoryCartRepository,
    fake_catalog: FakeCatalogClient,
) -> CartService:
    return CartService(
        cart_repository=fake_repo,
        catalog_client=fake_catalog,
        max_item_quantity=99,
    )


@pytest.fixture
def test_app(cart_service: CartService) -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(cart_router)
    app.include_router(health_router)
    app.dependency_overrides[get_cart_service] = lambda: cart_service
    return app


@pytest.fixture
async def api_client(test_app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
