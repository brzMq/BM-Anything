"""BM Capability Registry package (P1 PoC subset).

Native, LFX-independent discovery path. Full registry semantics land in P2.
"""

from __future__ import annotations

from bm.capability.registry.native import (
    NativeCapabilityRegistry,
    Provider,
    discover_entry_point_capabilities,
    load_capability_manifest,
)

__all__ = [
    "NativeCapabilityRegistry",
    "Provider",
    "discover_entry_point_capabilities",
    "load_capability_manifest",
]
