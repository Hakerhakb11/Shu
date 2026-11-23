"""Модульные тесты слоя приложений (CartService)."""

from decimal import Decimal

import pytest

from app.application.services import CartService
from app.domain.exceptions import (
    CartLimitExceededError,
    CartStorageUnavailableError,
    ItemNotInCartError,
)
from app.domain.models import CatalogItemSnapshot, UnavailableReason
from tests.conftest import FakeCatalogClient, InMemoryCartRepository


@pytest.mark.asyncio
async def test_get_cart_empty_skips_catalog_call(
    cart_service: CartService,
    fake_catalog: FakeCatalogClient,
) -> None:
    cart = await cart_service.get_cart("user-empty")

    assert cart.user_id == "user-empty"
    assert cart.items == []
    assert cart.total_price == Decimal("0.00")
    assert cart.has_unavailable_items is False
    assert fake_catalog.called_with == []


@pytest.mark.asyncio
async def test_add_and_get_cart_with_deleted_item(
    cart_service: CartService,
    fake_catalog: FakeCatalogClient,
) -> None:
    fake_catalog.snapshots[10] = CatalogItemSnapshot(
        id=10,
        title="Мастер и Маргарита",
        author="Михаил Булгаков",
        price=Decimal("750.00"),
        image_url=None,
        status="APPROVED",
        stock=4,
        available=True,
    )

    res1 = await cart_service.add_item("user-1", item_id=10, quantity=2)
    res2 = await cart_service.add_item("user-1", item_id=999, quantity=1)
    assert res1.quantity == 2
    assert res2.quantity == 1

    cart = await cart_service.get_cart("user-1")
    assert len(cart.items) == 2
    assert cart.total_price == Decimal("1500.00")
    assert cart.has_unavailable_items is True

    deleted_item = next(item for item in cart.items if item.item_id == 999)
    assert deleted_item.available is False
    assert deleted_item.unavailable_reason == UnavailableReason.DELETED
    assert deleted_item.message == "Товар недоступен"


@pytest.mark.asyncio
async def test_add_item_exceeding_limit_raises_error(cart_service: CartService) -> None:
    await cart_service.add_item("user-1", item_id=10, quantity=90)
    with pytest.raises(CartLimitExceededError):
        await cart_service.add_item("user-1", item_id=10, quantity=15)


@pytest.mark.asyncio
async def test_remove_item_decrement_and_full_delete(cart_service: CartService) -> None:
    await cart_service.add_item("user-1", item_id=10, quantity=3)

    after_dec = await cart_service.remove_item("user-1", item_id=10, quantity=1)
    assert after_dec.quantity == 2

    after_del = await cart_service.remove_item("user-1", item_id=10)
    assert after_del.quantity == 0

    with pytest.raises(ItemNotInCartError):
        await cart_service.remove_item("user-1", item_id=10)


@pytest.mark.asyncio
async def test_clear_cart(cart_service: CartService, fake_repo: InMemoryCartRepository) -> None:
    await cart_service.add_item("user-1", item_id=1, quantity=2)
    await cart_service.clear_cart("user-1")
    assert await fake_repo.get_items("user-1") == {}


@pytest.mark.asyncio
async def test_health_check_fails_when_redis_down(
    cart_service: CartService,
    fake_repo: InMemoryCartRepository,
) -> None:
    fake_repo.is_healthy = False
    with pytest.raises(CartStorageUnavailableError):
        await cart_service.check_health()
