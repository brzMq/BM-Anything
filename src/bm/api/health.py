"""Health endpoints for BM-Anything API.

P0 acceptance: "无需外部服务即可完成健康检查". The health endpoint must work
without PostgreSQL, Redis, cloud services, or any external dependency.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from bm.config.settings import get_settings
from bm.infrastructure.database.sqlite import get_database

router = APIRouter(tags=["health"])


def _redact(url: str) -> str:
    """Avoid leaking credentials in health output."""
    if "@" in url and "://" in url:
        scheme, rest = url.split("://", 1)
        _creds, _, host = rest.rpartition("@")
        return f"{scheme}://***@{host}"
    return url


@router.get("/health", summary="Liveness probe")
def health() -> dict[str, Any]:
    """Always-available liveness signal. No external dependencies."""
    return {"status": "ok", "service": "bm-anything", "version": "0.1.0"}


@router.get("/health/ready", summary="Readiness probe (DB reachable)")
def readiness() -> dict[str, Any]:
    """Readiness: verifies the business SQLite database is reachable."""
    settings = get_settings()
    db = get_database()
    db_ok = False
    detail: str | None = None
    try:
        with db.session_scope() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception as exc:  # pragma: no cover - defensive
        detail = f"{type(exc).__name__}: {exc}"
    return {
        "status": "ok" if db_ok else "degraded",
        "profile": settings.profile,
        "database": {"ok": db_ok, "url": _redact(db.url), "detail": detail},
    }
