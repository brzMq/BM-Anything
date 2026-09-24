"""The single sanctioned home for a real ``lfx`` import.

Everything here is lazy and guarded so that importing the rest of BM never
requires LFX to be installed. ``tests/architecture/test_lfx_only_in_adapter.py``
allows ``import lfx`` ONLY under this package.

Note on cost: importing ``lfx`` top-level is cheap, but pulling in the graph
engine (``lfx.graph``) is heavy (~16s cold / ~2260 modules, see
P1_LFX_POC_REPORT.md). This module therefore only touches the lightweight
``lfx.inputs`` surface needed to read component field metadata.
"""

from __future__ import annotations

import importlib.util
from typing import Any


def is_lfx_available() -> bool:
    """True if the ``lfx`` distribution is importable in this environment."""
    return importlib.util.find_spec("lfx") is not None


def require_lfx() -> None:
    if not is_lfx_available():
        raise RuntimeError(
            "lfx is not installed; this helper is only exercised in the LFX-gated "
            "PoC path. Install with `pip install lfx==1.12.3`."
        )


def make_input(kind: str, name: str, *, required: bool = True, info: str | None = None) -> Any:
    """Construct a real LFX input object (lazy import).

    ``kind`` is a short name mapped onto ``lfx.inputs`` classes, e.g. ``"str"``
    -> ``StrInput``. Used by the gated PoC test to prove the adapter maps real
    LFX objects, not just stubs.
    """
    require_lfx()
    import lfx.inputs as lfx_inputs  # local import: allowed only here

    cls_name = {
        "str": "StrInput",
        "bool": "BoolInput",
        "int": "IntInput",
        "float": "FloatInput",
        "dict": "DictInput",
        "dropdown": "DropdownInput",
    }.get(kind)
    if cls_name is None or not hasattr(lfx_inputs, cls_name):
        raise ValueError(f"unsupported lfx input kind: {kind!r}")
    cls = getattr(lfx_inputs, cls_name)
    kwargs: dict[str, Any] = {"name": name, "required": required}
    if info is not None:
        kwargs["info"] = info
    return cls(**kwargs)
