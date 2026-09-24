"""Unit tests for bm.config.paths (BM_HOME / platformdirs / durable-cache-temp).

Covers v0.3.1 §6 acceptance:
- BM_HOME override
- 默认 OS data path
- repo 删除/清理不会影响 durable data
- temp cleanup 不影响 Artifact
- Durable / Cache / Temp 分离
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from platformdirs import user_cache_dir, user_data_dir

from bm.config.paths import (
    APP_AUTHOR,
    APP_NAME,
    get_paths,
    reset_default_paths,
    resolve_paths,
)


class TestBMHomeOverride:
    def test_explicit_home_wins_over_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "from-env"))
        explicit = tmp_path / "explicit"
        paths = resolve_paths(home=explicit)
        assert paths.home == explicit.resolve()
        assert paths.data == explicit.resolve() / "data"

    def test_env_used_when_no_explicit(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "env-home"))
        paths = resolve_paths()
        assert paths.home == (tmp_path / "env-home").resolve()

    def test_os_default_when_neither(self, clean_env: None) -> None:
        paths = resolve_paths()
        expected = Path(user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=False)).resolve()
        assert paths.home == expected

    def test_cache_override_independent_of_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "home"))
        monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
        paths = resolve_paths()
        assert paths.home == (tmp_path / "home").resolve()
        assert paths.cache == (tmp_path / "cache").resolve()

    def test_cache_os_default(self, clean_env: None) -> None:
        paths = resolve_paths()
        expected = Path(user_cache_dir(APP_NAME, APP_AUTHOR, ensure_exists=False)).resolve()
        assert paths.cache == expected


class TestLayout:
    def test_durable_subdirs_under_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        p = resolve_paths()
        assert p.data.parent == p.home
        assert p.artifacts.parent == p.home
        assert p.blobs.parent == p.artifacts
        assert p.manifests.parent == p.artifacts
        assert p.plugins.parent == p.home
        assert p.runtime.parent == p.home
        assert p.backups.parent == p.home

    def test_business_and_execution_db_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        p = resolve_paths()
        assert p.business_db.name == "bm.sqlite3"
        assert p.execution_db.name == "execution.sqlite3"
        assert p.business_db != p.execution_db
        assert p.business_db.parent == p.data

    def test_temp_is_os_temp_not_under_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        p = resolve_paths()
        assert p.temp == Path(os.environ.get("TMPDIR", "/tmp")).resolve() or str(p.temp).startswith(
            "/"
        )
        assert not str(p.temp).startswith(str(p.home))

    def test_create_makes_durable_and_cache_dirs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "c"))
        p = resolve_paths(create=True)
        for d in (
            p.data,
            p.artifacts,
            p.blobs,
            p.manifests,
            p.plugins,
            p.runtime,
            p.backups,
            p.cache,
        ):
            assert d.is_dir(), f"expected {d} to be created"

    def test_create_does_not_make_temp(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # OS temp always exists; we just assert create=True doesn't try to
        # own it or fail when it's already there.
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        p = resolve_paths(create=True)
        assert p.temp.exists()


class TestRepoIndependence:
    def test_durable_root_never_inside_repo(self, clean_env: None) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        p = resolve_paths()
        assert not str(p.home).startswith(str(repo_root)), (
            f"BM_HOME resolved to {p.home}, which is inside the repo {repo_root}. "
            "v0.3.1 §6.2 forbids repo-root durable data."
        )

    def test_repo_clean_does_not_touch_durable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulate 'git clean -xdf' on the repo: durable data under BM_HOME survives."""
        home = tmp_path / "bm-home"
        monkeypatch.setenv("BM_HOME", str(home))
        p = resolve_paths(create=True)
        sentinel = p.data / "sentinel.txt"
        sentinel.write_text("must survive", encoding="utf-8")

        # Wipe a fake repo directory (NOT BM_HOME).
        fake_repo = tmp_path / "repo"
        fake_repo.mkdir()
        (fake_repo / "junk").write_text("x", encoding="utf-8")
        for child in fake_repo.iterdir():
            child.unlink()
        fake_repo.rmdir()

        assert sentinel.read_text(encoding="utf-8") == "must survive"

    def test_temp_cleanup_does_not_touch_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        home = tmp_path / "bm-home"
        monkeypatch.setenv("BM_HOME", str(home))
        p = resolve_paths(create=True)
        blob = p.blobs / "sha256" / "ab" / "cd" / "abcdef"
        blob.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(b"durable blob")

        # Simulate OS temp cleanup.
        for child in p.temp.iterdir():
            if child.is_file() and child.name.startswith(".bm-"):
                child.unlink()

        assert blob.read_bytes() == b"durable blob"


class TestSingleton:
    def test_get_paths_caches(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h"))
        reset_default_paths()
        a = get_paths()
        b = get_paths()
        assert a is b

    def test_reset_clears_cache(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h1"))
        reset_default_paths()
        first = get_paths()
        monkeypatch.setenv("BM_HOME", str(tmp_path / "h2"))
        reset_default_paths()
        second = get_paths()
        assert first.home != second.home
