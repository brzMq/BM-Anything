"""Architecture guard: BM Capability Contract MUST NOT import LFX / Langflow.

Enforces v0.3.1 §4 (修正三) and ARCHITECTURE_v0.3.md §10.1:

- ``bm.capability.contract`` 不允许 import ``lfx.*`` / ``langflow.*`` 任何类型。
- ``CapabilitySpec`` 不得继承第三方 Component 类。
- LFX 只能通过 ``bm.infrastructure.adapters.lfx`` 接入（Adapter-only）。

P0 ships an empty contract shell; this test ensures the shell stays clean and
that the guard is already wired before P2 lands real models.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_ROOT = REPO_ROOT / "src" / "bm" / "capability" / "contract"

FORBIDDEN_TOP_LEVEL = {"lfx", "langflow"}


def _contract_py_files() -> list[Path]:
    if not CONTRACT_ROOT.exists():
        return []
    return sorted(p for p in CONTRACT_ROOT.rglob("*.py") if p.is_file())


def _imports_in(path: Path) -> set[str]:
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


def _class_bases_in(path: Path) -> list[tuple[str, str]]:
    """Return (class_name, base_name) pairs for every class definition."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name):
                    out.append((node.name, base.id))
                elif isinstance(base, ast.Attribute):
                    # e.g. lfx.Component — capture the root name
                    root = base
                    while isinstance(root, ast.Attribute):
                        root = root.value
                    if isinstance(root, ast.Name):
                        out.append((node.name, f"{root.id}.{base.attr}"))
    return out


@pytest.mark.parametrize("path", _contract_py_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_contract_file_has_no_lfx_imports(path: Path) -> None:
    offenders = _imports_in(path) & FORBIDDEN_TOP_LEVEL
    assert not offenders, (
        f"{path.relative_to(REPO_ROOT)} imports forbidden LFX/Langflow module(s): "
        f"{sorted(offenders)}. bm.capability.contract must be independent of LFX; "
        f"use bm.infrastructure.adapters.lfx instead."
    )


@pytest.mark.parametrize("path", _contract_py_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_contract_classes_do_not_inherit_lfx(path: Path) -> None:
    for cls, base in _class_bases_in(path):
        root = base.split(".")[0]
        assert root not in FORBIDDEN_TOP_LEVEL, (
            f"{path.relative_to(REPO_ROOT)}: class {cls} inherits from {base}. "
            f"BM Capability MUST NOT inherit LFX Component (v0.3.1 §4.1)."
        )


def test_contract_root_exists() -> None:
    assert CONTRACT_ROOT.exists(), f"Expected capability contract package at {CONTRACT_ROOT}"


def test_no_lfx_adapter_leaks_into_contract_namespace() -> None:
    """The string 'lfx' must not appear as an import target anywhere under contract/."""
    for path in _contract_py_files():
        text = path.read_text(encoding="utf-8").lower()
        # Allow the word inside comments/docstrings explaining the rule,
        # but forbid actual import statements.
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
                continue
            assert "import lfx" not in stripped and "from lfx" not in stripped, (
                f"{path.relative_to(REPO_ROOT)} contains an lfx import: {line!r}"
            )
            assert "import langflow" not in stripped and "from langflow" not in stripped, (
                f"{path.relative_to(REPO_ROOT)} contains a langflow import: {line!r}"
            )
