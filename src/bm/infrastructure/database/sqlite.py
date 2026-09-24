"""SQLite / SQLAlchemy database bootstrap for Local Profile.

Application Persistence is separate from Execution Persistence (v0.3 §7.1,
v0.3.1 §3.1). This module only manages the BM business database. The
execution engine (when chosen in P3) will own ``execution.sqlite3``.

Domain code MUST NOT import this module directly; go through Repository
interfaces defined in ``bm.domain`` / ``bm.application``.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from bm.config.settings import BMSettings, get_settings


def _make_engine(url: str, *, echo: bool = False) -> Engine:
    engine = create_engine(url, echo=echo, future=True)

    if url.startswith("sqlite"):
        # Enable WAL + foreign keys for local SQLite. These are pragmatic
        # defaults for a single-user local app; Scale Profile adapters may
        # choose different settings.
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.close()

    return engine


class Database:
    """Thin wrapper around Engine + sessionmaker for the BM business DB."""

    def __init__(self, settings: BMSettings | None = None, *, echo: bool = False) -> None:
        self._settings = settings or get_settings()
        self._url = self._settings.effective_database_url()
        self._engine = _make_engine(self._url, echo=echo)
        self._session_factory = sessionmaker(
            bind=self._engine, autoflush=False, autocommit=False, expire_on_commit=False
        )

    @property
    def url(self) -> str:
        return self._url

    @property
    def engine(self) -> Engine:
        return self._engine

    def session(self) -> Session:
        return self._session_factory()

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        """Transactional scope: commit on success, rollback on exception."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        self._engine.dispose()


_default_db: Database | None = None


def get_database() -> Database:
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db


def reset_database() -> None:
    global _default_db
    if _default_db is not None:
        _default_db.dispose()
    _default_db = None
