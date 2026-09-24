"""Architecture guard: Domain layer MUST NOT import OSS infrastructure SDKs.

Enforces v0.3.1 §8 and ARCHITECTURE_v0.3.md §32 items 19-23.

Scans every ``*.py`` under ``src/bm/domain/`` (recursively) and fails if any
forbidden top-level module is imported. Forbidden list matches the SDKs that
must stay inside ``bm.infrastructure.*`` / ``bm.adapters.*`` / ``bm.providers.*``.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_ROOT = REPO_ROOT / "src" / "bm" / "domain"

FORBIDDEN_TOP_LEVEL = {
    "lfx",
    "langflow",
    "hatchet",
    "temporalio",
    "dbos",
    "qdrant_client",
    "psycopg",
    "psycopg2",
    "boto3",
    "redis",
    "opensearchpy",
    "pymilvus",
    "neo4j",
    "sqlalchemy",  # Domain must use Repository interfaces, not SQLAlchemy directly
    "fastapi",
    "uvicorn",
    "alembic",
}

# Allow ``import typing`` / ``from __future__`` etc. — we only flag the
# top-level module name, so stdlib and pydantic are fine.


def _domain_py_files() -> list[Path]:
    if not DOMAIN_ROOT.exists():
        return []
    return sorted(p for p in DOMAIN_ROOT.rglob("*.py") if p.is_file())


def _imports_in(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tops: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tops.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                # Relative import inside bm.domain — allowed.
                continue
            if node.module:
                tops.add(node.module.split(".")[0])
    return tops


@pytest.mark.parametrize("path", _domain_py_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_domain_file_has_no_forbidden_imports(path: Path) -> None:
    offenders = _imports_in(path) & FORBIDDEN_TOP_LEVEL
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} imports forbidden OSS/infra SDK(s): "
        f"{sorted(offenders)}. Domain must depend only on bm.* contracts; "
        f"move the import to bm.infrastructure.* / bm.adapters.* / bm.providers.*."
    )


def test_domain_root_exists() -> None:
    """Guard against the test silently passing when the directory is missing."""
    assert DOMAIN_ROOT.exists(), f"Expected domain package at {DOMAIN_ROOT}"


def test_forbidden_list_is_nonempty() -> None:
    assert FORBIDDEN_TOP_LEVEL, "Forbidden import list must not be empty"
