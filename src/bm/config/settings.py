"""BM-Anything application settings.

Centralised, typed configuration. Reads from environment (``BM_*``) and
optional ``config/local.env`` file. Never hardcodes absolute paths; always
defers to :mod:`bm.config.paths` for filesystem layout.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bm.config.paths import BMPaths, resolve_paths


class BMSettings(BaseSettings):
    """Top-level BM-Anything settings."""

    model_config = SettingsConfigDict(
        env_prefix="BM_",
        env_file=("config/local.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Deployment profile -------------------------------------------------
    profile: Literal["local", "scale", "large"] = Field(
        default="local",
        description="Deployment profile. P0 only implements 'local'.",
    )

    # --- Data root overrides ------------------------------------------------
    data_root: Path | None = Field(
        default=None,
        description="Explicit durable data root. Overrides BM_HOME env and OS default.",
    )
    cache_root: Path | None = Field(
        default=None,
        description="Explicit cache root. Overrides BM_CACHE_HOME env and OS default.",
    )

    # --- API ----------------------------------------------------------------
    api_host: str = Field(default="127.0.0.1")
    api_port: int = Field(default=8200, ge=1, le=65535)

    # --- Database -----------------------------------------------------------
    # Business SQLite path is derived from paths.business_db; this field only
    # exists for tests that need to point at an in-memory or temp DB.
    database_url: str | None = Field(
        default=None,
        description=(
            "SQLAlchemy URL override. When None, derived from BMPaths.business_db "
            "(sqlite:///<data>/bm.sqlite3)."
        ),
    )

    def paths(self, *, create: bool = False) -> BMPaths:
        """Resolve the BM local filesystem layout from current settings."""
        return resolve_paths(self.data_root, self.cache_root, create=create)

    def effective_database_url(self) -> str:
        """Return the SQLAlchemy URL for the business database."""
        if self.database_url is not None:
            return self.database_url
        paths = self.paths()
        return f"sqlite:///{paths.business_db}"


@lru_cache(maxsize=1)
def get_settings() -> BMSettings:
    """Process-wide cached settings instance."""
    return BMSettings()


def reset_settings_cache() -> None:
    """Clear the settings cache (used by tests after env mutation)."""
    get_settings.cache_clear()
