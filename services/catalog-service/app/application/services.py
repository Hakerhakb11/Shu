"""Application use cases / services."""

from app.application.interfaces import (
    CacheServiceInterface,
    CategoryRepositoryInterface,
    ItemRepositoryInterface,
)
from app.domain.exceptions import (
    CategoryNotFoundError,
    ItemNotFoundError,
    PermissionDeniedError,
)
from app.domain.models import Category, Item, ItemCharacteristic, ItemStatus, UserRole


class CatalogService:
    """Orchestrates catalog domain logic, repository persistence, and cache invalidation."""

    def __init__(
        self,
        item_repo: ItemRepositoryInterface,
        category_repo: CategoryRepositoryInterface,
        cache_service: CacheServiceInterface,
    ) -> None:
        self.item_repo = item_repo
        self.category_repo = category_repo
        self.cache_service = cache_service

    async def get_item(self, item_id: int) -> Item:
        """Fetch single item: checks Redis first; falls back to Postgres and saves to cache."""
        cached = await self.cache_service.get_item(item_id)
        if cached is not None:
            return cached

        item = await self.item_repo.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)

        # Cache in Redis for 2 minutes (120 seconds)
        await self.cache_service.set_item(item, ttl_seconds=120)
        return item

    async def get_items_batch(self, item_ids: list[int]) -> list[Item]:
        """Fetch multiple items by IDs (used by Cart Service)."""
        if not item_ids:
            return []
        return await self.item_repo.get_batch(item_ids)

    async def list_public_items(
        self,
        page: int = 1,
        size: int = 20,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
    ) -> tuple[list[Item], int]:
        """Public listing: returns only APPROVED items with pagination, filters, and search."""
        return await self.item_repo.list_items(
            page=page,
            size=size,
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
            status=ItemStatus.APPROVED,
        )

    async def create_item(
        self,
        title: str,
        author: str,
        description: str,
        price: float,
        category_id: int,
        seller_id: str,
        user_role: str,
        characteristics: list[ItemCharacteristic] | None = None,
        stock: int = 1,
        image_url: str | None = None,
    ) -> Item:
        """Create a new item by a seller. Initial status is PENDING moderation."""
        role_normalized = str(user_role).upper()
        if role_normalized != UserRole.SELLER.value:
            raise PermissionDeniedError("Только продавец (SELLER) может создавать товары.")

        category = await self.category_repo.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError(category_id)

        item = Item(
            title=title,
            author=author,
            description=description,
            price=price,
            category_id=category_id,
            seller_id=str(seller_id),
            status=ItemStatus.PENDING,
            image_url=image_url,
            stock=max(0, stock),
            characteristics=characteristics or [],
        )

        return await self.item_repo.create(item)

    async def update_item(
        self,
        item_id: int,
        user_id: str,
        user_role: str,
        title: str | None = None,
        author: str | None = None,
        description: str | None = None,
        price: float | None = None,
        category_id: int | None = None,
        characteristics: list[ItemCharacteristic] | None = None,
        stock: int | None = None,
        image_url: str | None = None,
    ) -> Item:
        """Update item details. Allowed for owner (SELLER) or MODERATOR."""
        item = await self.item_repo.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)

        if not item.can_be_edited_by(user_id=user_id, role=user_role):
            raise PermissionDeniedError("Нет прав на редактирование данного товара.")

        if category_id is not None and category_id != item.category_id:
            category = await self.category_repo.get_by_id(category_id)
            if category is None:
                raise CategoryNotFoundError(category_id)
            item.category_id = category_id

        item.update_details(
            title=title,
            author=author,
            description=description,
            price=price,
            image_url=image_url,
            characteristics=characteristics,
            stock=stock,
        )

        updated_item = await self.item_repo.update(item)
        # Invalidate cache
        await self.cache_service.invalidate_item(item_id)
        return updated_item

    async def delete_item(self, item_id: int, user_id: str, user_role: str) -> None:
        """Delete an item. Allowed for owner (SELLER) or MODERATOR."""
        item = await self.item_repo.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)

        if not item.can_be_deleted_by(user_id=user_id, role=user_role):
            raise PermissionDeniedError("Нет прав на удаление данного товара.")

        await self.item_repo.delete(item_id)
        # Invalidate cache
        await self.cache_service.invalidate_item(item_id)

    async def list_moderation_items(
        self,
        user_role: str,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Item], int]:
        """Moderator listing of items awaiting review (PENDING)."""
        role_normalized = str(user_role).upper()
        if role_normalized != UserRole.MODERATOR.value:
            raise PermissionDeniedError("Доступ запрещен: требуется роль MODERATOR.")

        return await self.item_repo.list_items(
            page=page,
            size=size,
            status=ItemStatus.PENDING,
        )

    async def update_item_status(
        self,
        item_id: int,
        new_status: ItemStatus,
        user_role: str,
    ) -> Item:
        """Change item status (APPROVED, REJECTED, BLOCKED). Moderator only."""
        role_normalized = str(user_role).upper()
        if role_normalized != UserRole.MODERATOR.value:
            raise PermissionDeniedError("Доступ запрещен: требуется роль MODERATOR.")

        item = await self.item_repo.get_by_id(item_id)
        if item is None:
            raise ItemNotFoundError(item_id)

        item.change_status(new_status)
        updated_item = await self.item_repo.update_status(item_id, new_status)
        await self.cache_service.invalidate_item(item_id)
        return updated_item

    async def list_categories(self) -> list[Category]:
        """Fetch all categories."""
        return await self.category_repo.get_all()

    async def create_category(
        self, name: str, slug: str, description: str | None = None
    ) -> Category:
        """Create a new category."""
        category = Category(name=name, slug=slug, description=description)
        return await self.category_repo.create(category)
