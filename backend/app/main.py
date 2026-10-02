"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import chat, conversations, health
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.memory.vector import init_vector_store
from app.models.db import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — startup and shutdown logic."""
    settings = get_settings()
    configure_logging()
    logger.info("startup", app=settings.app_name, version=settings.app_version)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    # Initialize vector store
    if settings.enable_memory:
        await init_vector_store()
        logger.info("vector_store_initialized")

    logger.info("ready", host=settings.api_host, port=settings.api_port)
    yield

    logger.info("shutdown")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Polyvalent AI assistant — research, code, content, automation.",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router, tags=["health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(conversations.router, prefix="/api/v1", tags=["conversations"])

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request, exc):  # noqa: ARG001
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": type(exc).__name__},
        )

    return app


app = create_app()
