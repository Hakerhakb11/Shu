"""HTTP-маршруты (FastAPI APIRouter) сервиса корзины."""

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.application.services import CartService
from app.core.dependencies import get_cart_service, get_current_user_id
from app.presentation.schemas import (
    CartItemAddRequest,
    CartItemQuantityResponse,
    CartResponse,
    ErrorResponse,
)

cart_router = APIRouter(prefix="/cart", tags=["Cart"])
health_router = APIRouter(tags=["Health"])


@cart_router.get(
    "",
    response_model=CartResponse,
    operation_id="get_cart",
    summary="Получить содержимое корзины текущего пользователя",
    responses={
        401: {"model": ErrorResponse, "description": "Отсутствует заголовок X-User-Id"},
        503: {"model": ErrorResponse, "description": "Catalog Service или Redis недоступны"},
    },
)
async def get_cart(
    user_id: str = Depends(get_current_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> CartResponse:
    """Получить корзину текущего пользователя с актуальными ценами из каталога."""
    cart = await cart_service.get_cart(user_id)
    return CartResponse.from_domain(cart)


@cart_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="clear_cart",
    summary="Полностью очистить корзину пользователя",
    responses={
        401: {"model": ErrorResponse, "description": "Отсутствует заголовок X-User-Id"},
        503: {"model": ErrorResponse, "description": "Redis недоступен"},
    },
)
async def clear_cart(
    user_id: str = Depends(get_current_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> Response:
    """Очистить все позиции корзины пользователя."""
    await cart_service.clear_cart(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cart_router.post(
    "/items",
    response_model=CartItemQuantityResponse,
    operation_id="add_cart_item",
    summary="Добавить товар в корзину или увеличить его количество",
    responses={
        400: {"model": ErrorResponse, "description": "Превышен лимит или некорректная операция"},
        401: {"model": ErrorResponse, "description": "Отсутствует заголовок X-User-Id"},
        503: {"model": ErrorResponse, "description": "Redis недоступен"},
    },
)
async def add_cart_item(
    payload: CartItemAddRequest,
    user_id: str = Depends(get_current_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> CartItemQuantityResponse:
    """Добавить книгу в корзину или увеличить ее счетчик."""
    result = await cart_service.add_item(
        user_id=user_id,
        item_id=payload.item_id,
        quantity=payload.quantity,
    )
    return CartItemQuantityResponse.from_domain(result)


@cart_router.delete(
    "/items/{item_id}",
    response_model=CartItemQuantityResponse,
    operation_id="remove_cart_item",
    summary="Уменьшить количество или удалить товар из корзины",
    responses={
        401: {"model": ErrorResponse, "description": "Отсутствует заголовок X-User-Id"},
        404: {"model": ErrorResponse, "description": "Товар отсутствует в корзине"},
        503: {"model": ErrorResponse, "description": "Redis недоступен"},
    },
)
async def remove_cart_item(
    item_id: int = Path(..., ge=1, description="ID книги из Catalog Service"),
    quantity: int | None = Query(
        default=None,
        ge=1,
        description="На сколько уменьшить количество (если не указано — удалить позицию целиком)",
    ),
    user_id: str = Depends(get_current_user_id),
    cart_service: CartService = Depends(get_cart_service),
) -> CartItemQuantityResponse:
    """Уменьшить количество или удалить позицию из корзины."""
    result = await cart_service.remove_item(
        user_id=user_id,
        item_id=item_id,
        quantity=quantity,
    )
    return CartItemQuantityResponse.from_domain(result)


@health_router.get(
    "/health",
    response_model=dict[str, str],
    operation_id="health_check",
    summary="Health Check",
    responses={
        503: {"model": ErrorResponse, "description": "Redis недоступен"},
    },
)
async def health_check(
    cart_service: CartService = Depends(get_cart_service),
) -> dict[str, str]:
    """Проверка работоспособности сервиса и доступности Redis."""
    return await cart_service.check_health()
