"""FastAPI application factory for BM-Anything.

P0 scope: minimal app with health endpoints. No external service required.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from bm.api.health import router as health_router
from bm.config.settings import get_settings
from bm.infrastructure.database.sqlite import get_database, reset_database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Eagerly resolve paths + DB so misconfiguration surfaces at startup,
    # not on first request. Does NOT require any external service.
    settings = get_settings()
    settings.paths(create=True)
    get_database()
    yield
    reset_database()


def create_app() -> FastAPI:
    app = FastAPI(
        title="BM-Anything",
        version="0.1.0",
        description="Local-first AI Capability Platform (P0 Foundation)",
        lifespan=lifespan,
    )
    app.include_router(health_router)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {
            "service": "bm-anything",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
