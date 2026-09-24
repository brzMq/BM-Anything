"""BM Capability Contract package.

Re-exports the framework-neutral contract types. See ``spec`` for the hard
LFX-independence constraints (enforced by tests/architecture/).
"""

from __future__ import annotations

from bm.capability.contract.spec import CapabilitySpec, FieldSchema

__all__ = ["CapabilitySpec", "FieldSchema"]
