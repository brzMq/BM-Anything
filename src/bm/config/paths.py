"""BM-Anything path resolution.

Implements v0.3.1 §6 (Local Artifact & Local Data Lifecycle):

- Durable data root defaults to OS user-data directory via ``platformdirs``.
- ``BM_HOME`` environment variable overrides the default.
- Explicit config (``BMSettings.data_root``) overrides ``BM_HOME``.
- Cache uses OS cache directory (``BM_CACHE_HOME`` override).
- Temp uses OS temp directory; only discardable content allowed.

Durable / Cache / Temp lifecycles are strictly separated.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_cache_dir, user_data_dir

APP_NAME = "BM-Anything"
APP_AUTHOR = "BM-Anything"


@dataclass(frozen=True)
class BMPaths:
    """Resolved BM-Anything local filesystem layout."""

    home: Path
    data: Path
    artifacts: Path
    blobs: Path
    manifests: Path
    plugins: Path
    runtime: Path
    backups: Path
    cache: Path
    temp: Path

    @property
    def business_db(self) -> Path:
        return self.data / "bm.sqlite3"

    @property
    def execution_db(self) -> Path:
        return self.data / "execution.sqlite3"


def _resolve_home(explicit: str | os.PathLike[str] | None = None) -> Path:
    """Resolve BM_HOME with priority: explicit config > BM_HOME env > OS user-data dir."""
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("BM_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path(user_data_dir(APP_NAME, APP_AUTHOR, ensure_exists=False)).resolve()


def _resolve_cache(explicit: str | os.PathLike[str] | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    env = os.environ.get("BM_CACHE_HOME")
    if env:
        return Path(env).expanduser().resolve()
    return Path(user_cache_dir(APP_NAME, APP_AUTHOR, ensure_exists=False)).resolve()


def resolve_paths(
    home: str | os.PathLike[str] | None = None,
    cache: str | os.PathLike[str] | None = None,
    *,
    create: bool = False,
) -> BMPaths:
    """Resolve the full BM local directory layout.

    Parameters
    ----------
    home:
        Explicit durable data root. Overrides ``BM_HOME`` env and OS default.
    cache:
        Explicit cache root. Overrides ``BM_CACHE_HOME`` env and OS default.
    create:
        When True, create all durable/cache directories on disk. Temp is left
        to the OS (always exists).
    """
    home_path = _resolve_home(home)
    cache_path = _resolve_cache(cache)
    temp_path = Path(tempfile.gettempdir()).resolve()

    paths = BMPaths(
        home=home_path,
        data=home_path / "data",
        artifacts=home_path / "artifacts",
        blobs=home_path / "artifacts" / "blobs",
        manifests=home_path / "artifacts" / "manifests",
        plugins=home_path / "plugins",
        runtime=home_path / "runtime",
        backups=home_path / "backups",
        cache=cache_path,
        temp=temp_path,
    )

    if create:
        for d in (
            paths.data,
            paths.artifacts,
            paths.blobs,
            paths.manifests,
            paths.plugins,
            paths.runtime,
            paths.backups,
            paths.cache,
        ):
            d.mkdir(parents=True, exist_ok=True)

    return paths


# Module-level singleton for the common "just give me the paths" case.
_default_paths: BMPaths | None = None


def get_paths() -> BMPaths:
    """Return the process-wide default BMPaths (lazily resolved, not created)."""
    global _default_paths
    if _default_paths is None:
        _default_paths = resolve_paths()
    return _default_paths


def reset_default_paths() -> None:
    """Reset the cached default paths (used by tests after env mutation)."""
    global _default_paths
    _default_paths = None
