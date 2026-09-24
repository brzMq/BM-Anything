"""P1-A exit test: BM core runs with LFX entirely absent.

Two properties:
  1. Importing the contract, native registry, a native provider AND the LFX
     adapter package must not load ``lfx`` (the adapter maps structurally; the
     only ``import lfx`` is lazy inside ``support`` and never triggered here).
  2. No core BM namespace depends on the adapter — so deleting
     ``bm/infrastructure/adapters/lfx/`` leaves BM intact (Adapter is removable).
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "bm"

CORE_DIRS = [
    SRC_ROOT / "domain",
    SRC_ROOT / "capability",
    SRC_ROOT / "workflow",
    SRC_ROOT / "application",
    SRC_ROOT / "knowledge",
]

# Probe in a FRESH interpreter so the result is order-independent and meaningful
# even when lfx is installed: importing BM core + the adapter package must not,
# by itself, pull in lfx/langflow.
_PROBE = """
import sys
import bm.capability.contract  # noqa: F401
import bm.capability.registry  # noqa: F401
import bm.capability.provider.text_reverse  # noqa: F401
import bm.infrastructure.adapters.lfx  # noqa: F401
loaded = sorted(m for m in sys.modules if m.split('.')[0] in ('lfx', 'langflow'))
print(loaded)
"""


def test_importing_bm_core_and_adapter_does_not_load_lfx() -> None:
    result = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "[]", (
        f"Importing BM core + adapter pulled in LFX/Langflow modules: {result.stdout!r}"
    )


def test_native_capability_works_without_lfx() -> None:
    from bm.capability.provider.text_reverse import TextReverseProvider
    from bm.capability.registry import NativeCapabilityRegistry

    reg = NativeCapabilityRegistry()
    reg.register_provider(TextReverseProvider())
    assert reg.invoke("text.reverse", {"text": "hello"}) == {"reversed": "olleh"}


def _imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    mods: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods.add(node.module)
    return mods


@pytest.mark.parametrize("root", CORE_DIRS, ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_core_never_imports_the_adapter(root: Path) -> None:
    """Adapter depends on contracts, never the reverse -> adapter is deletable."""
    if not root.exists():
        pytest.skip(f"{root} not present")
    for path in root.rglob("*.py"):
        offenders = {m for m in _imported_modules(path) if "adapters.lfx" in m}
        assert not offenders, (
            f"{path.relative_to(REPO_ROOT)} imports {sorted(offenders)}; core BM "
            f"must not depend on the LFX adapter."
        )
