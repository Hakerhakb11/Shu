"""Abstract interfaces for repositories and external services (Application Layer)."""

from abc import ABC, abstractmethod

from app.domain.models import Category, Item, ItemStatus


class ItemRepositoryInterface(ABC):
    """Abstract interface for book item persistence."""

    @abstractmethod
    async def get_by_id(self, item_id: int) -> Item | None:
        """Retrieve single item by id with its relations."""

    @abstractmethod
    async def get_batch(self, item_ids: list[int]) -> list[Item]:
        """Retrieve multiple items by their IDs."""

    @abstractmethod
    async def list_items(
        self,
        page: int,
        size: int,
        category_id: int | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
        status: ItemStatus | None = None,
    ) -> tuple[list[Item], int]:
        """List items with filtering, pagination, and text search."""

    @abstractmethod
    async def create(self, item: Item) -> Item:
        """Create a new item in storage."""

    @abstractmethod
    async def update(self, item: Item) -> Item:
        """Update existing item."""

    @abstractmethod
    async def delete(self, item_id: int) -> bool:
        """Delete item by id."""

    @abstractmethod
    async def update_status(self, item_id: int, status: ItemStatus) -> Item:
        """Update only status of an item."""


class CategoryRepositoryInterface(ABC):
    """Abstract interface for category persistence."""

    @abstractmethod
    async def get_all(self) -> list[Category]:
        """Retrieve all categories."""

    @abstractmethod
    async def get_by_id(self, category_id: int) -> Category | None:
        """Retrieve category by id."""

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Category | None:
        """Retrieve category by slug."""

    @abstractmethod
    async def create(self, category: Category) -> Category:
        """Create a new category."""


class CacheServiceInterface(ABC):
    """Abstract interface for item caching."""

    @abstractmethod
    async def get_item(self, item_id: int) -> Item | None:
        """Retrieve cached item if exists."""

    @abstractmethod
    async def set_item(self, item: Item, ttl_seconds: int = 120) -> None:
        """Cache item for a specified TTL."""

    @abstractmethod
    async def invalidate_item(self, item_id: int) -> None:
        """Purge item from cache."""
