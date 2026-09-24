"""BM Capability Contract (v0.3.1 §4).

HARD CONSTRAINTS (enforced by tests/architecture/):

- This package MUST NOT import ``lfx.*`` or ``langflow.*`` types.
- ``CapabilitySpec`` MUST NOT inherit from any third-party Component class.
- LFX integration is allowed ONLY via ``bm.infrastructure.adapters.lfx``
  (Adapter pattern: BM → Adapter → LFX). Never the reverse.

P0 ships an empty shell. The concrete CapabilitySpec / InputSpec / OutputSpec /
ResourceSpec / PermissionSpec / ExecutionSpec / SideEffectSpec / IdempotencySpec
models land in P2 (Capability Foundation).
"""

from __future__ import annotations

# Intentionally empty in P0. See P2 prompt in CODEX_PROMPTS_v0.3.md.
