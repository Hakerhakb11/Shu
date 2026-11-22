"""Domain models for Catalog Service."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ItemStatus(str, Enum):
    """Lifecycle status of a catalog item."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


class UserRole(str, Enum):
    """User roles recognized by the system."""

    CLIENT = "CLIENT"
    SELLER = "SELLER"
    MODERATOR = "MODERATOR"


@dataclass
class Category:
    """Book category entity."""

    name: str
    slug: str
    id: int | None = None
    description: str | None = None


@dataclass
class ItemCharacteristic:
    """Attribute/characteristic of a book item (e.g. ISBN, publisher, pages, condition)."""

    name: str
    value: str
    id: int | None = None
    item_id: int | None = None


@dataclass
class ItemStock:
    """Stock availability for a catalog item."""

    quantity: int = 1
    id: int | None = None
    item_id: int | None = None


@dataclass
class Item:
    """Core domain entity representing a book item in the marketplace."""

    title: str
    author: str
    description: str
    price: float
    category_id: int
    seller_id: str
    id: int | None = None
    status: ItemStatus = ItemStatus.PENDING
    image_url: str | None = None
    stock: int = 1
    characteristics: list[ItemCharacteristic] = field(default_factory=list)
    category: Category | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def can_be_edited_by(self, user_id: str, role: UserRole | str) -> bool:
        """Moderators can edit any item; sellers can only edit their own items."""
        role_str = role.value if isinstance(role, UserRole) else str(role).upper()
        if role_str == UserRole.MODERATOR.value:
            return True
        if role_str == UserRole.SELLER.value and str(self.seller_id) == str(user_id):
            return True
        return False

    def can_be_deleted_by(self, user_id: str, role: UserRole | str) -> bool:
        """Moderators can delete any item; sellers can only delete their own items."""
        return self.can_be_edited_by(user_id, role)

    def is_available(self) -> bool:
        """Returns True if the item is approved for sale and in stock."""
        return self.status == ItemStatus.APPROVED and self.stock > 0

    def approve(self) -> None:
        """Moderator approval."""
        self.status = ItemStatus.APPROVED

    def reject(self) -> None:
        """Moderator rejection."""
        self.status = ItemStatus.REJECTED

    def block(self) -> None:
        """Moderator block for violations."""
        self.status = ItemStatus.BLOCKED

    def change_status(self, new_status: ItemStatus) -> None:
        """Controlled status transition."""
        self.status = new_status

    def update_stock(self, new_quantity: int) -> None:
        """Update available quantity."""
        if new_quantity < 0:
            raise ValueError("Остаток на складе не может быть отрицательным.")
        self.stock = new_quantity

    def update_details(
        self,
        title: str | None = None,
        author: str | None = None,
        description: str | None = None,
        price: float | None = None,
        image_url: str | None = None,
        characteristics: list[ItemCharacteristic] | None = None,
        stock: int | None = None,
    ) -> None:
        """Encapsulated domain logic for updating item state with invariant validation."""
        if title is not None:
            if not title.strip():
                raise ValueError("Название товара не может быть пустым.")
            self.title = title
        if author is not None:
            if not author.strip():
                raise ValueError("Автор товара не может быть пустым.")
            self.author = author
        if description is not None:
            self.description = description
        if price is not None:
            if price <= 0:
                raise ValueError("Цена товара должна быть больше нуля.")
            self.price = price
        if stock is not None:
            self.update_stock(stock)
        if image_url is not None:
            self.image_url = image_url
        if characteristics is not None:
            self.characteristics = characteristics
