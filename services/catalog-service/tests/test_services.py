"""Unit tests for CatalogService use cases and caching logic."""

import pytest

from app.application.services import CatalogService
from app.domain.exceptions import (
    CategoryNotFoundError,
    ItemNotFoundError,
    PermissionDeniedError,
)
from app.domain.models import ItemCharacteristic, ItemStatus, UserRole
from app.infrastructure.cache.redis_client import InMemoryCacheService
from app.infrastructure.repositories.category_repository import CategoryRepository
from app.infrastructure.repositories.item_repository import ItemRepository


@pytest.mark.asyncio
async def test_catalog_service_cache_hit_and_invalidation(test_session) -> None:
    item_repo = ItemRepository(test_session)
    category_repo = CategoryRepository(test_session)
    cache = InMemoryCacheService()

    service = CatalogService(item_repo, category_repo, cache)

    # 1. Create Category
    cat = await service.create_category("Наука", "science")

    # 2. Create Item
    item = await service.create_item(
        title="Краткая история времени",
        author="Стивен Хокинг",
        description="Книга по физике",
        price=700.0,
        category_id=cat.id,  # type: ignore[arg-type]
        seller_id="seller_1",
        user_role=UserRole.SELLER.value,
        characteristics=[ItemCharacteristic(name="Год", value="1988")],
        stock=3,
    )
    assert item.id is not None

    # Cache should be empty initially for this item
    assert await cache.get_item(item.id) is None

    # First fetch: populates cache
    fetched1 = await service.get_item(item.id)
    assert fetched1.title == "Краткая история времени"
    assert await cache.get_item(item.id) is not None

    # Modify item in cache directly to verify next get_item hits the cache
    cached_obj = await cache.get_item(item.id)
    assert cached_obj is not None
    cached_obj.title = "Измененный заголовок из кэша"
    await cache.set_item(cached_obj)

    fetched2 = await service.get_item(item.id)
    assert fetched2.title == "Измененный заголовок из кэша"

    # Updating item invalidates cache
    await service.update_item(
        item_id=item.id,
        user_id="seller_1",
        user_role=UserRole.SELLER.value,
        title="Краткая история времени (Новое издание)",
    )
    assert await cache.get_item(item.id) is None

    # Next fetch gets fresh from DB and re-caches
    fetched3 = await service.get_item(item.id)
    assert fetched3.title == "Краткая история времени (Новое издание)"
    assert await cache.get_item(item.id) is not None

    # Delete invalidates cache
    await service.delete_item(item.id, user_id="seller_1", user_role=UserRole.SELLER.value)
    assert await cache.get_item(item.id) is None

    with pytest.raises(ItemNotFoundError):
        await service.get_item(item.id)


@pytest.mark.asyncio
async def test_catalog_service_permissions_and_validation(test_session) -> None:
    item_repo = ItemRepository(test_session)
    category_repo = CategoryRepository(test_session)
    cache = InMemoryCacheService()

    service = CatalogService(item_repo, category_repo, cache)
    cat = await service.create_category("Искусство", "art")

    # Non-seller cannot create item
    with pytest.raises(PermissionDeniedError):
        await service.create_item(
            title="История искусства",
            author="Гомбрих",
            description="Книга",
            price=1200.0,
            category_id=cat.id,  # type: ignore[arg-type]
            seller_id="client_1",
            user_role="CLIENT",
        )

    # Invalid category
    with pytest.raises(CategoryNotFoundError):
        await service.create_item(
            title="История искусства",
            author="Гомбрих",
            description="Книга",
            price=1200.0,
            category_id=99999,
            seller_id="seller_1",
            user_role="SELLER",
        )

    # Valid creation
    item = await service.create_item(
        title="История искусства",
        author="Гомбрих",
        description="Книга",
        price=1200.0,
        category_id=cat.id,  # type: ignore[arg-type]
        seller_id="seller_1",
        user_role="SELLER",
    )

    # Non-owner cannot update
    with pytest.raises(PermissionDeniedError):
        await service.update_item(
            item_id=item.id,  # type: ignore[arg-type]
            user_id="seller_2",
            user_role="SELLER",
            title="Попытка взлома",
        )

    # Moderator can update status
    updated = await service.update_item_status(
        item_id=item.id,  # type: ignore[arg-type]
        new_status=ItemStatus.APPROVED,
        user_role="MODERATOR",
    )
    assert updated.status == ItemStatus.APPROVED

    # Non-moderator cannot update status
    with pytest.raises(PermissionDeniedError):
        await service.update_item_status(
            item_id=item.id,  # type: ignore[arg-type]
            new_status=ItemStatus.REJECTED,
            user_role="SELLER",
        )
