"""Shared pytest fixtures for BM-Anything tests."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from bm.config.paths import reset_default_paths
from bm.config.settings import reset_settings_cache
from bm.infrastructure.database.sqlite import reset_database


@pytest.fixture(autouse=True)
def _isolate_bm_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Point BM_HOME / BM_CACHE_HOME at a tmp_path for every test.

    Guarantees:
    - No test writes to the real OS user-data directory.
    - No test depends on a pre-existing BM_HOME.
    - repo root / cwd is never used as durable data root.
    """
    home = tmp_path / "bm-home"
    cache = tmp_path / "bm-cache"
    monkeypatch.setenv("BM_HOME", str(home))
    monkeypatch.setenv("BM_CACHE_HOME", str(cache))
    # Clear any explicit overrides that would shadow env.
    monkeypatch.delenv("BM_DATA_ROOT", raising=False)
    monkeypatch.delenv("BM_CACHE_ROOT", raising=False)
    monkeypatch.delenv("BM_DATABASE_URL", raising=False)

    reset_default_paths()
    reset_settings_cache()
    reset_database()

    yield home

    reset_default_paths()
    reset_settings_cache()
    reset_database()


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove BM_* env vars so tests can assert true OS-default behaviour."""
    for key in list(os.environ):
        if key.startswith("BM_"):
            monkeypatch.delenv(key, raising=False)
    reset_default_paths()
    reset_settings_cache()
    reset_database()
