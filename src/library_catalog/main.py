"""
Точка входа FastAPI приложения Library Catalog.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from .api.dependencies import get_openlibrary_client
from .api.middleware.request_id import RequestIdMiddleware
from .api.v1.routers import books, health
from .core.config import settings
from .core.database import dispose_engine
from .core.exceptions import register_exception_handlers
from .core.logging_config import setup_logging
from .core.logging_context import REQUEST_ID_HEADER

logger = logging.getLogger(__name__)


# ========== LIFECYCLE EVENTS ==========


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifecycle manager для FastAPI.

    Выполняется при:
    - startup: настройка логирования
    - shutdown: закрытие HTTP-клиента и подключений к БД
    """
    # Startup
    setup_logging(
        level=settings.log_level,
        json_format=settings.log_format == "json",
    )
    openlibrary_client = get_openlibrary_client()
    logger.info("🚀 Application started")

    try:
        yield
    finally:
        # Shutdown
        await openlibrary_client.close()
        get_openlibrary_client.cache_clear()
        await dispose_engine()
        logger.info("👋 Application stopped")


# ========== CREATE APP ==========
app = FastAPI(
    title=settings.app_name,
    description="REST API для управления библиотечным каталогом",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)


# ========== METRICS ==========

app.mount("/metrics", make_asgi_app())


# ========== MIDDLEWARE ==========

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[REQUEST_ID_HEADER],
)

app.add_middleware(RequestIdMiddleware)


# ========== EXCEPTION HANDLERS ==========

register_exception_handlers(app)

# ========== ROUTERS ==========

# Версия 1 API
app.include_router(
    books.router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    health.router,
    prefix=settings.api_v1_prefix,
)


# ========== ROOT ENDPOINT ==========


@app.get("/")
async def root() -> dict[str, str]:
    """Корневой эндпоинт."""
    return {
        "message": "Welcome to Library Catalog API",
        "docs": settings.docs_url,
        "version": "1.0.0",
    }


# ========== RUN ==========

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
