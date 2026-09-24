"""LFX adapter package (BM -> Adapter -> LFX).

This is the sanctioned home for any ``lfx`` / ``langflow`` reference in the
codebase. ``adapter`` holds the pure, import-free structural mapping; ``support``
is the single module that actually imports ``lfx`` (lazily, guarded).

Enforced by tests/architecture/test_lfx_only_in_adapter.py.
"""

from __future__ import annotations

from bm.infrastructure.adapters.lfx.adapter import LfxCapabilityAdapter

__all__ = ["LfxCapabilityAdapter"]
