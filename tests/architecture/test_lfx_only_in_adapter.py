"""Architecture guard: LFX / Langflow may be imported ONLY inside the adapter.

Enforces v0.3.1 §4 and ARCHITECTURE_v0.3.md §10.1/§10.3:

    BM -> Adapter -> LFX   (allowed)
    LFX -> BM              (forbidden)

Any ``import lfx`` / ``import langflow`` (top-level or in-function) anywhere
under ``src/bm`` is a violation UNLESS the file lives under
``src/bm/infrastructure/adapters/lfx/``. This proves LFX is a swappable
implementation behind one adapter, not a core dependency.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "bm"
ADAPTER_ROOT = SRC_ROOT / "infrastructure" / "adapters" / "lfx"

FORBIDDEN = {"lfx", "langflow"}


def _all_bm_py_files() -> list[Path]:
    return sorted(p for p in SRC_ROOT.rglob("*.py") if p.is_file())


def _imported_tops(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tops: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                tops.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue
            if node.module:
                tops.add(node.module.split(".")[0])
    return tops


def test_adapter_root_exists() -> None:
    assert ADAPTER_ROOT.is_dir(), f"Expected LFX adapter package at {ADAPTER_ROOT}"


@pytest.mark.parametrize("path", _all_bm_py_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_lfx_only_imported_in_adapter(path: Path) -> None:
    offenders = _imported_tops(path) & FORBIDDEN
    if not offenders:
        return
    under_adapter = ADAPTER_ROOT in path.parents or path.parent == ADAPTER_ROOT
    assert under_adapter, (
        f"{path.relative_to(REPO_ROOT)} imports {sorted(offenders)} but is not "
        f"under bm.infrastructure.adapters.lfx. LFX/Langflow types must stay behind "
        f"the adapter (v0.3.1 §4)."
    )


def test_core_namespaces_are_lfx_free() -> None:
    """Explicit belt-and-suspenders over the namespaces that MUST stay clean."""
    core_dirs = [
        SRC_ROOT / "domain",
        SRC_ROOT / "capability" / "contract",
        SRC_ROOT / "capability" / "registry",
        SRC_ROOT / "capability" / "provider",
        SRC_ROOT / "workflow",
        SRC_ROOT / "application",
        SRC_ROOT / "knowledge",
    ]
    for root in core_dirs:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            offenders = _imported_tops(path) & FORBIDDEN
            assert not offenders, (
                f"{path.relative_to(REPO_ROOT)} leaks {sorted(offenders)} into a core BM namespace."
            )
