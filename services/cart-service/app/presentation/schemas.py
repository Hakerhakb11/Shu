"""Pydantic DTO-схемы запросов и ответов Cart Service."""

from pydantic import BaseModel, Field

from app.domain.models import Cart, CartItem, CartItemQuantity, UnavailableReason


class CartItemAddRequest(BaseModel):
    """Запрос на добавление книги в корзину или увеличение количества."""

    item_id: int = Field(..., ge=1, description="ID книги из Catalog Service", examples=[42])
    quantity: int = Field(
        default=1,
        ge=1,
        le=99,
        description="Количество добавляемых экземпляров",
        examples=[1],
    )


class CartItemQuantityResponse(BaseModel):
    """Ответ после добавления, уменьшения или удаления позиции."""

    item_id: int = Field(..., examples=[42])
    quantity: int = Field(
        ...,
        ge=0,
        description="Итоговое количество товара в корзине (0 означает, что позиция удалена)",
        examples=[2],
    )

    @classmethod
    def from_domain(cls, model: CartItemQuantity) -> "CartItemQuantityResponse":
        """Преобразовать доменный результат в DTO."""
        return cls(item_id=model.item_id, quantity=model.quantity)


class CartItemResponse(BaseModel):
    """DTO одной позиции корзины с актуальными данными каталога."""

    item_id: int = Field(..., examples=[42])
    quantity: int = Field(..., ge=1, examples=[2])
    available: bool = Field(
        ...,
        description="true, если книга APPROVED в Catalog Service и stock >= quantity",
        examples=[True],
    )
    unavailable_reason: UnavailableReason | None = Field(default=None)
    message: str | None = Field(
        default=None,
        description="Сообщение для пользователя, если available=false",
        examples=[None],
    )
    title: str | None = Field(default=None, examples=["Дюна"])
    author: str | None = Field(default=None, examples=["Фрэнк Герберт"])
    price: float | None = Field(default=None, examples=[890.0])
    stock: int | None = Field(
        default=None,
        description="Актуальный остаток на складе из Catalog Service",
        examples=[5],
    )
    image_url: str | None = Field(default=None, examples=["https://example.com/dune.jpg"])
    line_total: float = Field(
        ...,
        ge=0,
        description="price * quantity, либо 0 если available=false",
        examples=[1780.0],
    )

    @classmethod
    def from_domain(cls, item: CartItem) -> "CartItemResponse":
        """Преобразовать доменную сущность CartItem в DTO."""
        return cls(
            item_id=item.item_id,
            quantity=item.quantity,
            available=item.available,
            unavailable_reason=item.unavailable_reason,
            message=item.message,
            title=item.title,
            author=item.author,
            price=float(item.price) if item.price is not None else None,
            stock=item.stock,
            image_url=item.image_url,
            line_total=float(item.line_total),
        )


class CartResponse(BaseModel):
    """DTO полного содержимого корзины пользователя."""

    user_id: str = Field(..., examples=["user-123"])
    items: list[CartItemResponse]
    total_price: float = Field(
        ...,
        ge=0,
        description="Сумма line_total только по доступным (available=true) товарам",
        examples=[1780.0],
    )
    has_unavailable_items: bool = Field(
        ...,
        description="true, если в корзине есть хотя бы один недоступный товар",
        examples=[False],
    )

    @classmethod
    def from_domain(cls, cart: Cart) -> "CartResponse":
        """Преобразовать доменный агрегат Cart в DTO."""
        return cls(
            user_id=cart.user_id,
            items=[CartItemResponse.from_domain(item) for item in cart.items],
            total_price=float(cart.total_price),
            has_unavailable_items=cart.has_unavailable_items,
        )


class ErrorResponse(BaseModel):
    """Стандартизированный формат ошибки API."""

    detail: str = Field(..., description="Человекочитаемое описание ошибки")
    error_code: str = Field(..., description="Машиночитаемый код ошибки")
