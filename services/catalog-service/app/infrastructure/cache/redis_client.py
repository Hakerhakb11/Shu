"""Redis cache implementation for catalog items."""

import json
import logging
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.application.interfaces import CacheServiceInterface
from app.domain.models import Category, Item, ItemCharacteristic, ItemStatus

logger = logging.getLogger(__name__)


class RedisCacheService(CacheServiceInterface):
    """Redis cache for fast item retrieval and automatic TTL expiration."""

    def __init__(self, redis_client: Redis, default_ttl_seconds: int = 120) -> None:
        self.redis = redis_client
        self.default_ttl = default_ttl_seconds

    def _item_key(self, item_id: int) -> str:
        return f"catalog:item:{item_id}"

    def _serialize_item(self, item: Item) -> str:
        data: dict[str, Any] = {
            "id": item.id,
            "title": item.title,
            "author": item.author,
            "description": item.description,
            "price": item.price,
            "category_id": item.category_id,
            "seller_id": str(item.seller_id),
            "status": item.status.value,
            "image_url": item.image_url,
            "stock": item.stock,
            "characteristics": [
                {"name": c.name, "value": c.value, "id": c.id} for c in item.characteristics
            ],
            "category": (
                {
                    "id": item.category.id,
                    "name": item.category.name,
                    "slug": item.category.slug,
                    "description": item.category.description,
                }
                if item.category
                else None
            ),
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        return json.dumps(data)

    def _deserialize_item(self, payload: str) -> Item:
        data = json.loads(payload)
        category = None
        if data.get("category"):
            category = Category(
                id=data["category"].get("id"),
                name=data["category"]["name"],
                slug=data["category"]["slug"],
                description=data["category"].get("description"),
            )

        characteristics = [
            ItemCharacteristic(
                name=c["name"],
                value=c["value"],
                id=c.get("id"),
            )
            for c in data.get("characteristics", [])
        ]

        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None

        return Item(
            id=data.get("id"),
            title=data["title"],
            author=data["author"],
            description=data["description"],
            price=float(data["price"]),
            category_id=int(data["category_id"]),
            seller_id=str(data["seller_id"]),
            status=ItemStatus(data["status"]),
            image_url=data.get("image_url"),
            stock=int(data.get("stock", 1)),
            characteristics=characteristics,
            category=category,
            created_at=created_at,
            updated_at=updated_at,
        )

    async def get_item(self, item_id: int) -> Item | None:
        """Fetch item from Redis. Returns None on cache miss or connection error."""
        try:
            cached_data = await self.redis.get(self._item_key(item_id))
            if cached_data:
                return self._deserialize_item(
                    cached_data.decode("utf-8") if isinstance(cached_data, bytes) else cached_data
                )
        except Exception as exc:
            logger.warning("Failed to read item %s from Redis cache: %s", item_id, exc)
        return None

    async def set_item(self, item: Item, ttl_seconds: int = 120) -> None:
        """Save item in Redis with TTL (default 2 minutes)."""
        if item.id is None:
            return
        try:
            payload = self._serialize_item(item)
            await self.redis.set(self._item_key(item.id), payload, ex=ttl_seconds)
        except Exception as exc:
            logger.warning("Failed to save item %s to Redis cache: %s", item.id, exc)

    async def invalidate_item(self, item_id: int) -> None:
        """Delete item key from Redis."""
        try:
            await self.redis.delete(self._item_key(item_id))
        except Exception as exc:
            logger.warning("Failed to invalidate item %s in Redis cache: %s", item_id, exc)


class InMemoryCacheService(CacheServiceInterface):
    """In-memory cache implementation for tests or environments without Redis."""

    def __init__(self) -> None:
        self._store: dict[int, Item] = {}

    async def get_item(self, item_id: int) -> Item | None:
        return self._store.get(item_id)

    async def set_item(self, item: Item, ttl_seconds: int = 120) -> None:
        if item.id is not None:
            self._store[item.id] = item

    async def invalidate_item(self, item_id: int) -> None:
        self._store.pop(item_id, None)
