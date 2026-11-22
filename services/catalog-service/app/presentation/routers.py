"""FastAPI Presentation layer: API Routers."""

import math
from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.application.services import CatalogService
from app.core.dependencies import (
    get_catalog_service,
    require_moderator_role,
    require_seller_or_moderator,
    require_seller_role,
)
from app.domain.models import Item, ItemCharacteristic, ItemStatus
from app.presentation.schemas import (
    BatchItemResponse,
    BatchItemsRequest,
    CategoryCreateRequest,
    CategoryResponse,
    CharacteristicResponse,
    ErrorResponse,
    ItemCreateRequest,
    ItemListItemResponse,
    ItemResponse,
    ItemStatusUpdateRequest,
    ItemUpdateRequest,
    PaginatedItemListResponse,
)

router = APIRouter(prefix="/catalog", tags=["Catalog"])

# Standardized OpenAPI error responses
RESPONSES_404: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "Сущность не найдена в системе (ITEM_NOT_FOUND или CATEGORY_NOT_FOUND)",
    }
}

RESPONSES_403: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "Доступ запрещен: недостаточно прав или попытка изменить чужой товар",
    }
}

RESPONSES_400: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": "Некорректные параметры запроса или недопустимая операция",
    }
}


def _to_item_response(item: Item) -> ItemResponse:
    return ItemResponse(
        id=item.id,  # type: ignore[arg-type]
        title=item.title,
        author=item.author,
        description=item.description,
        price=item.price,
        category_id=item.category_id,
        seller_id=str(item.seller_id),
        status=item.status.value,
        image_url=item.image_url,
        stock=item.stock,
        characteristics=[
            CharacteristicResponse(id=c.id, name=c.name, value=c.value)
            for c in item.characteristics
        ],
        category=(
            CategoryResponse(
                id=item.category.id,  # type: ignore[arg-type]
                name=item.category.name,
                slug=item.category.slug,
                description=item.category.description,
            )
            if item.category
            else None
        ),
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _to_list_item_response(item: Item) -> ItemListItemResponse:
    return ItemListItemResponse(
        id=item.id,  # type: ignore[arg-type]
        title=item.title,
        author=item.author,
        price=item.price,
        category_id=item.category_id,
        seller_id=str(item.seller_id),
        status=item.status.value,
        image_url=item.image_url,
        stock=item.stock,
    )


# ==========================================
# 1. Public Endpoints (Доступны всем)
# ==========================================


@router.get(
    "/items",
    response_model=PaginatedItemListResponse,
    summary="Получение списка товаров с пагинацией, фильтрацией и поиском",
    responses={**RESPONSES_400},
)
async def list_items(
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, ge=1, le=100, description="Количество товаров на странице"),
    category_id: int | None = Query(None, description="Фильтр по категории"),
    min_price: float | None = Query(None, ge=0, description="Минимальная цена"),
    max_price: float | None = Query(None, ge=0, description="Максимальная цена"),
    search: str | None = Query(None, description="Полнотекстовый поиск по названию/автору"),
    service: CatalogService = Depends(get_catalog_service),
) -> PaginatedItemListResponse:
    items, total = await service.list_public_items(
        page=page,
        size=size,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
    )
    pages = math.ceil(total / size) if total > 0 else 1
    return PaginatedItemListResponse(
        items=[_to_list_item_response(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Получение подробной карточки конкретного товара (кэшируется в Redis)",
    responses={**RESPONSES_404},
)
async def get_item(
    item_id: int,
    service: CatalogService = Depends(get_catalog_service),
) -> ItemResponse:
    item = await service.get_item(item_id)
    return _to_item_response(item)


@router.post(
    "/items/batch",
    response_model=list[BatchItemResponse],
    summary="Пакетное получение информации о товарах (для Сервиса Корзины)",
    responses={**RESPONSES_400},
)
async def get_items_batch(
    payload: BatchItemsRequest,
    service: CatalogService = Depends(get_catalog_service),
) -> list[BatchItemResponse]:
    items = await service.get_items_batch(payload.item_ids)
    return [
        BatchItemResponse(
            id=item.id,  # type: ignore[arg-type]
            title=item.title,
            author=item.author,
            price=item.price,
            image_url=item.image_url,
            status=item.status.value,
            stock=item.stock,
            available=item.is_available(),
        )
        for item in items
    ]


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
    summary="Получение списка всех категорий",
)
async def list_categories(
    service: CatalogService = Depends(get_catalog_service),
) -> list[CategoryResponse]:
    categories = await service.list_categories()
    return [
        CategoryResponse(
            id=c.id,  # type: ignore[arg-type]
            name=c.name,
            slug=c.slug,
            description=c.description,
        )
        for c in categories
    ]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание категории",
    responses={**RESPONSES_400},
)
async def create_category(
    payload: CategoryCreateRequest,
    service: CatalogService = Depends(get_catalog_service),
) -> CategoryResponse:
    cat = await service.create_category(
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
    )
    return CategoryResponse(
        id=cat.id,  # type: ignore[arg-type]
        name=cat.name,
        slug=cat.slug,
        description=cat.description,
    )


# ==========================================
# 2. Seller Endpoints (Создание и редактирование)
# ==========================================


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание товара продавцом (требуется X-User-Role: SELLER)",
    responses={**RESPONSES_403, **RESPONSES_404, **RESPONSES_400},
)
async def create_item(
    payload: ItemCreateRequest,
    user_info: tuple[str, str] = Depends(require_seller_role),
    service: CatalogService = Depends(get_catalog_service),
) -> ItemResponse:
    user_id, role = user_info
    characteristics = [
        ItemCharacteristic(name=c.name, value=c.value) for c in payload.characteristics
    ]
    created = await service.create_item(
        title=payload.title,
        author=payload.author,
        description=payload.description,
        price=payload.price,
        category_id=payload.category_id,
        seller_id=user_id,
        user_role=role,
        characteristics=characteristics,
        stock=payload.stock,
        image_url=payload.image_url,
    )
    return _to_item_response(created)


@router.put(
    "/items/{item_id}",
    response_model=ItemResponse,
    summary="Редактирование товара (продавец может менять свой товар, модератор — любой)",
    responses={**RESPONSES_403, **RESPONSES_404, **RESPONSES_400},
)
async def update_item(
    item_id: int,
    payload: ItemUpdateRequest,
    user_info: tuple[str, str] = Depends(require_seller_or_moderator),
    service: CatalogService = Depends(get_catalog_service),
) -> ItemResponse:
    user_id, role = user_info
    characteristics = None
    if payload.characteristics is not None:
        characteristics = [
            ItemCharacteristic(name=c.name, value=c.value) for c in payload.characteristics
        ]

    updated = await service.update_item(
        item_id=item_id,
        user_id=user_id,
        user_role=role,
        title=payload.title,
        author=payload.author,
        description=payload.description,
        price=payload.price,
        category_id=payload.category_id,
        characteristics=characteristics,
        stock=payload.stock,
        image_url=payload.image_url,
    )
    return _to_item_response(updated)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление товара (продавец может удалять свой товар, модератор — любой)",
    responses={**RESPONSES_403, **RESPONSES_404},
)
async def delete_item(
    item_id: int,
    user_info: tuple[str, str] = Depends(require_seller_or_moderator),
    service: CatalogService = Depends(get_catalog_service),
) -> None:
    user_id, role = user_info
    await service.delete_item(item_id=item_id, user_id=user_id, user_role=role)


# ==========================================
# 3. Moderator Endpoints (Модерация)
# ==========================================


@router.get(
    "/moderation/items",
    response_model=PaginatedItemListResponse,
    summary="Получение списка товаров, ожидающих проверки (PENDING). Только MODERATOR",
    responses={**RESPONSES_403},
)
async def get_moderation_items(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: str = Depends(require_moderator_role),
    service: CatalogService = Depends(get_catalog_service),
) -> PaginatedItemListResponse:
    items, total = await service.list_moderation_items(user_role=role, page=page, size=size)
    pages = math.ceil(total / size) if total > 0 else 1
    return PaginatedItemListResponse(
        items=[_to_list_item_response(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.patch(
    "/items/{item_id}/status",
    response_model=ItemResponse,
    summary="Изменить статус товара (APPROVED, REJECTED, BLOCKED). Только MODERATOR",
    responses={**RESPONSES_403, **RESPONSES_404, **RESPONSES_400},
)
async def update_item_status(
    item_id: int,
    payload: ItemStatusUpdateRequest,
    role: str = Depends(require_moderator_role),
    service: CatalogService = Depends(get_catalog_service),
) -> ItemResponse:
    target_status = ItemStatus(payload.status.value)
    updated = await service.update_item_status(
        item_id=item_id,
        new_status=target_status,
        user_role=role,
    )
    return _to_item_response(updated)
