"""Unit tests for the SQLite database bootstrap + Alembic migration.

Covers P0 acceptance: "数据库迁移可从空库执行".
"""

from __future__ import annotations

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from bm.config.paths import resolve_paths
from bm.infrastructure.database.models import SchemaMeta
from bm.infrastructure.database.sqlite import Database, reset_database


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Database:
    monkeypatch.setenv("BM_HOME", str(tmp_path / "bm"))
    monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
    reset_database()
    resolve_paths(create=True)
    return Database()


class TestDatabaseBootstrap:
    def test_url_is_sqlite_under_bm_home(self, db: Database) -> None:
        assert db.url.startswith("sqlite:///")
        assert "bm.sqlite3" in db.url

    def test_session_scope_commits(self, db: Database) -> None:
        with db.session_scope() as s:
            s.execute(text("CREATE TABLE IF NOT EXISTS t (x INTEGER)"))
            s.execute(text("INSERT INTO t VALUES (42)"))
        with db.session_scope() as s:
            row = s.execute(text("SELECT x FROM t")).scalar()
            assert row == 42

    def test_session_scope_rollbacks_on_error(self, db: Database) -> None:
        # Use DML (INSERT) rather than DDL (CREATE TABLE) because SQLite
        # implicitly commits DDL outside the transaction in some modes.
        with db.session_scope() as s:
            s.execute(text("CREATE TABLE IF NOT EXISTS t2 (x INTEGER)"))
        with pytest.raises(RuntimeError), db.session_scope() as s:
            s.execute(text("INSERT INTO t2 VALUES (1)"))
            raise RuntimeError("boom")
        with db.session_scope() as s:
            count = s.execute(text("SELECT COUNT(*) FROM t2")).scalar()
            assert count == 0

    def test_sqlite_pragmas_applied(self, db: Database) -> None:
        with db.session_scope() as s:
            mode = s.execute(text("PRAGMA journal_mode")).scalar()
            fk = s.execute(text("PRAGMA foreign_keys")).scalar()
            assert str(mode).lower() == "wal"
            assert int(fk) == 1


class TestAlembicMigration:
    def test_upgrade_head_from_empty_db(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        home = tmp_path / "bm-mig"
        monkeypatch.setenv("BM_HOME", str(home))
        monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
        reset_database()
        paths = resolve_paths(create=True)
        db_path = paths.business_db
        assert not db_path.exists() or db_path.stat().st_size == 0

        repo_root = Path(__file__).resolve().parents[2]
        cfg = Config(str(repo_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(repo_root / "migrations"))
        command.upgrade(cfg, "head")

        assert db_path.exists()
        from sqlalchemy import create_engine

        eng = create_engine(f"sqlite:///{db_path}")
        insp = inspect(eng)
        assert "schema_meta" in insp.get_table_names()
        assert "alembic_version" in insp.get_table_names()

    def test_schema_meta_seeded(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        home = tmp_path / "bm-seed"
        monkeypatch.setenv("BM_HOME", str(home))
        monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
        reset_database()
        paths = resolve_paths(create=True)

        repo_root = Path(__file__).resolve().parents[2]
        cfg = Config(str(repo_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(repo_root / "migrations"))
        command.upgrade(cfg, "head")

        from sqlalchemy import create_engine

        eng = create_engine(f"sqlite:///{paths.business_db}")
        with eng.connect() as conn:
            rows = dict(conn.execute(text("SELECT key, value FROM schema_meta")).all())
        assert rows["bm_schema_version"] == "0.1.0"
        assert rows["created_by"] == "bm-anything/alembic"

    def test_downgrade_drops_table(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        home = tmp_path / "bm-down"
        monkeypatch.setenv("BM_HOME", str(home))
        monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
        reset_database()
        paths = resolve_paths(create=True)

        repo_root = Path(__file__).resolve().parents[2]
        cfg = Config(str(repo_root / "alembic.ini"))
        cfg.set_main_option("script_location", str(repo_root / "migrations"))
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")

        from sqlalchemy import create_engine

        eng = create_engine(f"sqlite:///{paths.business_db}")
        insp = inspect(eng)
        assert "schema_meta" not in insp.get_table_names()


class TestModels:
    def test_base_has_schema_meta(self) -> None:
        assert SchemaMeta.__tablename__ == "schema_meta"
        assert SchemaMeta.__table__ is not None
        assert "key" in SchemaMeta.__table__.c
