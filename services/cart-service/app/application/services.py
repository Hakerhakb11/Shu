"""Слой сценариев использования (Use Cases) сервиса корзины."""

from app.application.interfaces import CartRepositoryInterface, CatalogClientInterface
from app.domain.exceptions import (
    CartLimitExceededError,
    CartStorageUnavailableError,
    InvalidCartOperationError,
    ItemNotInCartError,
)
from app.domain.models import Cart, CartItemQuantity


class CartService:
    """Оркестратор бизнес-операций с корзиной пользователя."""

    def __init__(
        self,
        cart_repository: CartRepositoryInterface,
        catalog_client: CatalogClientInterface,
        max_item_quantity: int = 99,
    ) -> None:
        self._cart_repository = cart_repository
        self._catalog_client = catalog_client
        self._max_item_quantity = max_item_quantity

    async def get_cart(self, user_id: str) -> Cart:
        """Получить корзину пользователя с актуальными данными из Catalog Service."""
        raw_items = await self._cart_repository.get_items(user_id)
        if not raw_items:
            return Cart(user_id=user_id, items=[])

        catalog_snapshots = await self._catalog_client.get_items_batch(
            list(raw_items.keys())
        )
        return Cart.build(
            user_id=user_id,
            raw_items=raw_items,
            catalog_snapshots=catalog_snapshots,
        )

    async def add_item(
        self,
        user_id: str,
        item_id: int,
        quantity: int = 1,
    ) -> CartItemQuantity:
        """Добавить товар в корзину или увеличить его количество."""
        self._validate_positive_id(item_id)
        self._validate_positive_quantity(quantity)

        current_quantity = await self._cart_repository.get_item_quantity(user_id, item_id)
        projected_quantity = (current_quantity or 0) + quantity
        if projected_quantity > self._max_item_quantity:
            raise CartLimitExceededError(
                f"Нельзя добавить больше {self._max_item_quantity} шт. одного товара в корзину"
            )

        updated_quantity = await self._cart_repository.increment_item(
            user_id=user_id,
            item_id=item_id,
            delta=quantity,
        )
        return CartItemQuantity(item_id=item_id, quantity=updated_quantity)

    async def remove_item(
        self,
        user_id: str,
        item_id: int,
        quantity: int | None = None,
    ) -> CartItemQuantity:
        """Уменьшить количество товара или удалить позицию целиком."""
        self._validate_positive_id(item_id)
        if quantity is not None:
            self._validate_positive_quantity(quantity)

        current_quantity = await self._cart_repository.get_item_quantity(user_id, item_id)
        if current_quantity is None:
            raise ItemNotInCartError(item_id)

        if quantity is None or current_quantity - quantity <= 0:
            await self._cart_repository.remove_item(user_id, item_id)
            return CartItemQuantity(item_id=item_id, quantity=0)

        new_quantity = current_quantity - quantity
        saved_quantity = await self._cart_repository.set_item_quantity(
            user_id=user_id,
            item_id=item_id,
            quantity=new_quantity,
        )
        return CartItemQuantity(item_id=item_id, quantity=saved_quantity)

    async def clear_cart(self, user_id: str) -> None:
        """Полностью очистить корзину пользователя."""
        await self._cart_repository.clear_cart(user_id)

    async def check_health(self) -> dict[str, str]:
        """Проверить готовность сервиса и соединение с Redis."""
        is_redis_alive = await self._cart_repository.ping()
        if not is_redis_alive:
            raise CartStorageUnavailableError("Хранилище Redis недоступно")
        return {"status": "ok", "redis": "ok"}

    @staticmethod
    def _validate_positive_id(item_id: int) -> None:
        if item_id < 1:
            raise InvalidCartOperationError("Идентификатор товара должен быть больше 0")

    @staticmethod
    def _validate_positive_quantity(quantity: int) -> None:
        if quantity < 1:
            raise InvalidCartOperationError("Количество товара должно быть больше 0")
