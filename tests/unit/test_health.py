"""Unit tests for the FastAPI health endpoints.

Covers P0 acceptance: "无需外部服务即可完成健康检查" and
"干净环境按文档启动".
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bm.api.app import create_app
from bm.infrastructure.database.sqlite import reset_database


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("BM_HOME", str(tmp_path / "bm"))
    monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
    reset_database()
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_database()


class TestLiveness:
    def test_health_returns_ok(self, client: TestClient) -> None:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "ok"
        assert body["service"] == "bm-anything"
        assert body["version"] == "0.1.0"

    def test_health_needs_no_db(self, client: TestClient) -> None:
        """Liveness must succeed even if the DB file does not yet exist."""
        # The fixture's app startup creates paths but not the DB file itself
        # until first session use. /health must not touch the DB.
        r = client.get("/health")
        assert r.status_code == 200


class TestReadiness:
    def test_ready_reports_profile(self, client: TestClient) -> None:
        r = client.get("/health/ready")
        assert r.status_code == 200
        body = r.json()
        assert body["profile"] == "local"

    def test_ready_db_ok_after_migration(self, client: TestClient) -> None:
        """After the lifespan startup creates the DB, readiness must report ok."""
        r = client.get("/health/ready")
        body = r.json()
        # The DB may not have tables yet (no migration run in this fixture),
        # but SELECT 1 must succeed against a fresh SQLite file.
        assert body["database"]["ok"] is True
        assert body["status"] == "ok"

    def test_ready_url_is_sqlite(self, client: TestClient) -> None:
        r = client.get("/health/ready")
        body = r.json()
        assert body["database"]["url"].startswith("sqlite:///")

    def test_ready_url_redacts_credentials(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scale Profile URLs with credentials must be redacted in health output."""
        from bm.api.health import _redact

        assert _redact("postgresql://user:secret@host:5432/db") == "postgresql://***@host:5432/db"
        assert _redact("sqlite:///foo/bar.db") == "sqlite:///foo/bar.db"


class TestRoot:
    def test_root_returns_service_info(self, client: TestClient) -> None:
        r = client.get("/")
        assert r.status_code == 200
        body = r.json()
        assert body["service"] == "bm-anything"
        assert body["docs"] == "/docs"
        assert body["health"] == "/health"

    def test_openapi_available(self, client: TestClient) -> None:
        r = client.get("/openapi.json")
        assert r.status_code == 200
        assert "paths" in r.json()
