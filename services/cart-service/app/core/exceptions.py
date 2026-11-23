"""Глобальные обработчики доменных исключений FastAPI."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    CartStorageUnavailableError,
    CatalogServiceUnavailableError,
    DomainError,
    InvalidCartOperationError,
    ItemNotInCartError,
    UnauthorizedUserError,
)
from app.presentation.schemas import ErrorResponse


def _build_error_response(status_code: int, exc: DomainError) -> JSONResponse:
    payload = ErrorResponse(detail=exc.message, error_code=exc.error_code)
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Зарегистрировать маппинг доменных исключений в HTTP-ответы."""

    @app.exception_handler(UnauthorizedUserError)
    async def handle_unauthorized(
        _request: Request,
        exc: UnauthorizedUserError,
    ) -> JSONResponse:
        return _build_error_response(status.HTTP_401_UNAUTHORIZED, exc)

    @app.exception_handler(InvalidCartOperationError)
    async def handle_invalid_operation(
        _request: Request,
        exc: InvalidCartOperationError,
    ) -> JSONResponse:
        return _build_error_response(status.HTTP_400_BAD_REQUEST, exc)

    @app.exception_handler(ItemNotInCartError)
    async def handle_item_not_in_cart(
        _request: Request,
        exc: ItemNotInCartError,
    ) -> JSONResponse:
        return _build_error_response(status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(CatalogServiceUnavailableError)
    async def handle_catalog_unavailable(
        _request: Request,
        exc: CatalogServiceUnavailableError,
    ) -> JSONResponse:
        return _build_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, exc)

    @app.exception_handler(CartStorageUnavailableError)
    async def handle_storage_unavailable(
        _request: Request,
        exc: CartStorageUnavailableError,
    ) -> JSONResponse:
        return _build_error_response(status.HTTP_503_SERVICE_UNAVAILABLE, exc)
