"""Main FastAPI application entrypoint for Catalog Service."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.dependencies import _engine, _redis_client, get_global_engine
from app.core.exceptions import setup_exception_handlers
from app.infrastructure.db.session import init_models
from app.presentation.routers import router as catalog_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("catalog-service")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown events."""
    logger.info("Initializing Catalog Service...")
    # Initialize database tables if not already created
    try:
        engine = get_global_engine()
        await init_models(engine)
        logger.info("Database models verified/created.")
    except Exception as exc:
        logger.warning(
            "Could not initialize database on startup (may be running in test or offline): %s", exc
        )

    yield

    # Teardown
    logger.info("Shutting down Catalog Service...")
    if _redis_client is not None:
        await _redis_client.close()
    if _engine is not None:
        await _engine.dispose()


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Catalog Service",
        description=(
            "Book marketplace catalog microservice with Clean Architecture, "
            "PostgreSQL, and Redis caching."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # Register custom exception handlers for domain errors
    setup_exception_handlers(app)

    # Register API routers
    app.include_router(catalog_router)

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "catalog-service"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
