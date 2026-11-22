"""Pydantic schemas (DTOs) for API request and response data transfer."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ItemStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"


# --- Category DTOs ---


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None = None


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=255)
    description: str | None = None


# --- Characteristic DTOs ---


class CharacteristicCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    value: str = Field(..., min_length=1, max_length=255)


class CharacteristicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    value: str


# --- Item Request DTOs ---


class ItemCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Название книги")
    author: str = Field(..., min_length=1, max_length=255, description="Автор книги")
    description: str = Field(..., min_length=1, description="Описание состояния и содержания")
    price: float = Field(..., gt=0, description="Цена в рублях")
    category_id: int = Field(..., description="ID категории")
    stock: int = Field(default=1, ge=0, description="Остаток на складе")
    image_url: str | None = Field(default=None, description="Ссылка на фото обложки")
    characteristics: list[CharacteristicCreate] = Field(
        default_factory=list, description="Характеристики (ISBN, переплет, издательство и т.д.)"
    )


class ItemUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    price: float | None = Field(default=None, gt=0)
    category_id: int | None = None
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    characteristics: list[CharacteristicCreate] | None = None


class ItemStatusUpdateRequest(BaseModel):
    status: ItemStatusEnum = Field(..., description="Новый статус товара")


class BatchItemsRequest(BaseModel):
    item_ids: list[int] = Field(..., description="Список идентификаторов товаров")


# --- Item Response DTOs ---


class ItemListItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    price: float
    category_id: int
    seller_id: str
    status: str
    image_url: str | None = None
    stock: int


class ItemResponse(BaseModel):
    """Detailed item card."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    description: str
    price: float
    category_id: int
    seller_id: str
    status: str
    image_url: str | None = None
    stock: int
    characteristics: list[CharacteristicResponse] = Field(default_factory=list)
    category: CategoryResponse | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedItemListResponse(BaseModel):
    items: list[ItemListItemResponse]
    total: int
    page: int
    size: int
    pages: int


class BatchItemResponse(BaseModel):
    """Data required by Cart Service for items in cart."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: str
    price: float
    image_url: str | None = None
    status: str
    stock: int
    available: bool
