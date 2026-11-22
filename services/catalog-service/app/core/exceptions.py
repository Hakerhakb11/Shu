"""Exception handlers for mapping domain errors to HTTP responses."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    CategoryNotFoundError,
    DomainError,
    EntityNotFoundError,
    InvalidOperationError,
    ItemNotFoundError,
    PermissionDeniedError,
)


def setup_exception_handlers(app: FastAPI) -> None:
    """Register domain exception handlers with the FastAPI application."""

    @app.exception_handler(ItemNotFoundError)
    async def item_not_found_handler(request: Request, exc: ItemNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message, "error_code": "ITEM_NOT_FOUND"},
        )

    @app.exception_handler(CategoryNotFoundError)
    async def category_not_found_handler(
        request: Request, exc: CategoryNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message, "error_code": "CATEGORY_NOT_FOUND"},
        )

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.message, "error_code": "NOT_FOUND"},
        )

    @app.exception_handler(PermissionDeniedError)
    async def permission_denied_handler(
        request: Request, exc: PermissionDeniedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": exc.message, "error_code": "FORBIDDEN"},
        )

    @app.exception_handler(InvalidOperationError)
    async def invalid_operation_handler(
        request: Request, exc: InvalidOperationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "error_code": "INVALID_OPERATION"},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": exc.message, "error_code": "DOMAIN_ERROR"},
        )
