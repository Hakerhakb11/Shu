"""Реализация репозитория корзины на базе Redis Hash (cart:{user_id})."""

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.application.interfaces import CartRepositoryInterface
from app.domain.exceptions import CartStorageUnavailableError


class RedisCartRepository(CartRepositoryInterface):
    """Хранение корзин пользователей в Redis под ключом cart:{user_id}."""

    def __init__(self, redis_client: Redis, cart_ttl_seconds: int = 2_592_000) -> None:
        self._redis = redis_client
        self._cart_ttl_seconds = cart_ttl_seconds

    @staticmethod
    def _cart_key(user_id: str) -> str:
        return f"cart:{user_id}"

    async def get_items(self, user_id: str) -> dict[int, int]:
        """Прочитать все позиции из Redis Hash cart:{user_id}."""
        try:
            raw_data: dict[str, str] = await self._redis.hgetall(self._cart_key(user_id))
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось прочитать корзину из Redis") from exc

        result: dict[int, int] = {}
        for raw_item_id, raw_qty in raw_data.items():
            try:
                item_id = int(raw_item_id)
                quantity = int(raw_qty)
            except ValueError:
                continue
            if item_id > 0 and quantity > 0:
                result[item_id] = quantity
        return result

    async def get_item_quantity(self, user_id: str, item_id: int) -> int | None:
        """Получить количество конкретного товара в корзине."""
        try:
            raw_qty: str | None = await self._redis.hget(
                self._cart_key(user_id),
                str(item_id),
            )
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось обратиться к Redis") from exc

        if raw_qty is None:
            return None
        try:
            quantity = int(raw_qty)
        except ValueError:
            return None
        return quantity if quantity > 0 else None

    async def increment_item(self, user_id: str, item_id: int, delta: int) -> int:
        """Атомарно увеличить количество товара через HINCRBY и обновить TTL."""
        key = self._cart_key(user_id)
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.hincrby(key, str(item_id), delta)
                pipe.expire(key, self._cart_ttl_seconds)
                results = await pipe.execute()
            return int(results[0])
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось обновить корзину в Redis") from exc

    async def set_item_quantity(self, user_id: str, item_id: int, quantity: int) -> int:
        """Установить точное количество товара и обновить TTL."""
        key = self._cart_key(user_id)
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.hset(key, str(item_id), str(quantity))
                pipe.expire(key, self._cart_ttl_seconds)
                await pipe.execute()
            return quantity
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось обновить корзину в Redis") from exc

    async def remove_item(self, user_id: str, item_id: int) -> bool:
        """Удалить поле item_id из Redis Hash."""
        try:
            removed_count: int = await self._redis.hdel(
                self._cart_key(user_id),
                str(item_id),
            )
            return removed_count > 0
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось удалить товар из Redis") from exc

    async def clear_cart(self, user_id: str) -> None:
        """Удалить ключ корзины пользователя."""
        try:
            await self._redis.delete(self._cart_key(user_id))
        except RedisError as exc:
            raise CartStorageUnavailableError("Не удалось очистить корзину в Redis") from exc

    async def ping(self) -> bool:
        """Проверить соединение с Redis."""
        try:
            return bool(await self._redis.ping())
        except RedisError:
            return False
