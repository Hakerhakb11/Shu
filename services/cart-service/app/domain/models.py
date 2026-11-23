"""Доменные сущности и бизнес-правила сервиса корзины (чистый Python)."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

TWO_PLACES = Decimal("0.01")
APPROVED_STATUS = "APPROVED"


class UnavailableReason(str, Enum):
    """Причина недоступности товара в корзине."""

    DELETED = "DELETED"
    NOT_APPROVED = "NOT_APPROVED"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"


@dataclass(frozen=True)
class CatalogItemSnapshot:
    """Снимок актуальных данных о книге из Catalog Service."""

    id: int
    title: str
    author: str
    price: Decimal
    image_url: str | None
    status: str
    stock: int
    available: bool


@dataclass(frozen=True)
class CartItemQuantity:
    """Результат изменения количества конкретной позиции в корзине."""

    item_id: int
    quantity: int


@dataclass(frozen=True)
class CartItem:
    """Позиция корзины, обогащенная актуальными данными и статусом доступности."""

    item_id: int
    quantity: int
    available: bool
    line_total: Decimal
    unavailable_reason: UnavailableReason | None = None
    message: str | None = None
    title: str | None = None
    author: str | None = None
    price: Decimal | None = None
    stock: int | None = None
    image_url: str | None = None

    @classmethod
    def from_catalog_snapshot(
        cls,
        item_id: int,
        quantity: int,
        snapshot: CatalogItemSnapshot | None,
    ) -> "CartItem":
        """Создать позицию корзины с проверкой доступности по данным каталога."""
        if snapshot is None:
            return cls(
                item_id=item_id,
                quantity=quantity,
                available=False,
                line_total=Decimal("0.00"),
                unavailable_reason=UnavailableReason.DELETED,
                message="Товар недоступен",
            )

        if snapshot.status != APPROVED_STATUS:
            return cls(
                item_id=item_id,
                quantity=quantity,
                available=False,
                line_total=Decimal("0.00"),
                unavailable_reason=UnavailableReason.NOT_APPROVED,
                message="Товар недоступен",
                title=snapshot.title,
                author=snapshot.author,
                price=snapshot.price,
                stock=snapshot.stock,
                image_url=snapshot.image_url,
            )

        if snapshot.stock <= 0 or not snapshot.available:
            return cls(
                item_id=item_id,
                quantity=quantity,
                available=False,
                line_total=Decimal("0.00"),
                unavailable_reason=UnavailableReason.OUT_OF_STOCK,
                message="Товара нет в наличии",
                title=snapshot.title,
                author=snapshot.author,
                price=snapshot.price,
                stock=snapshot.stock,
                image_url=snapshot.image_url,
            )

        if snapshot.stock < quantity:
            return cls(
                item_id=item_id,
                quantity=quantity,
                available=False,
                line_total=Decimal("0.00"),
                unavailable_reason=UnavailableReason.INSUFFICIENT_STOCK,
                message=f"Недостаточно товара на складе (доступно: {snapshot.stock})",
                title=snapshot.title,
                author=snapshot.author,
                price=snapshot.price,
                stock=snapshot.stock,
                image_url=snapshot.image_url,
            )

        line_total = (snapshot.price * Decimal(quantity)).quantize(
            TWO_PLACES,
            rounding=ROUND_HALF_UP,
        )
        return cls(
            item_id=item_id,
            quantity=quantity,
            available=True,
            line_total=line_total,
            unavailable_reason=None,
            message=None,
            title=snapshot.title,
            author=snapshot.author,
            price=snapshot.price,
            stock=snapshot.stock,
            image_url=snapshot.image_url,
        )


@dataclass(frozen=True)
class Cart:
    """Агрегат корзины пользователя."""

    user_id: str
    items: list[CartItem]

    @property
    def total_price(self) -> Decimal:
        """Итоговая стоимость только доступных товаров в корзине."""
        total = sum(
            (item.line_total for item in self.items if item.available),
            start=Decimal("0.00"),
        )
        return total.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    @property
    def has_unavailable_items(self) -> bool:
        """Есть ли в корзине хотя бы один недоступный товар."""
        return any(not item.available for item in self.items)

    @classmethod
    def build(
        cls,
        user_id: str,
        raw_items: dict[int, int],
        catalog_snapshots: dict[int, CatalogItemSnapshot],
    ) -> "Cart":
        """Собрать корзину из сырых пар (item_id -> quantity) и снимков каталога."""
        items = [
            CartItem.from_catalog_snapshot(
                item_id=item_id,
                quantity=quantity,
                snapshot=catalog_snapshots.get(item_id),
            )
            for item_id, quantity in sorted(raw_items.items())
        ]
        return cls(user_id=user_id, items=items)
