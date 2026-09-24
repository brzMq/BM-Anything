"""BM Capability Contract — P1 PoC subset.

HARD CONSTRAINTS (enforced by tests/architecture/):

- This package MUST NOT import ``lfx.*`` or ``langflow.*`` types.
- ``CapabilitySpec`` MUST NOT inherit from any third-party Component class.
- LFX integration is allowed ONLY via ``bm.infrastructure.adapters.lfx``
  (Adapter pattern: BM -> Adapter -> LFX). Never the reverse.

SCOPE NOTE: This is the *minimal* contract needed to prove the decoupling
property in P1 (BM core usable without LFX). The full contract — resources,
permissions, side effects, idempotency, execution, errors, observability —
lands in P2 (Capability Foundation). Do not treat these fields as final.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FieldSchema(BaseModel):
    """A single input/output field descriptor.

    Deliberately structural (name + json-ish type) so it can be populated
    either by a native BM provider or translated from an LFX component field
    by the adapter — without either framework leaking its own types here.
    """

    name: str
    type: str = "string"
    required: bool = True
    description: str | None = None


class CapabilitySpec(BaseModel):
    """Framework-neutral description of a capability.

    ``source`` is provenance metadata (a plain string such as ``"native"`` or
    ``"lfx"``), NOT a class hierarchy. A capability whose ``source`` is ``lfx``
    is still a plain ``CapabilitySpec`` — LFX never becomes a base type of the
    BM contract.
    """

    capability_id: str
    name: str
    version: str = "0.0.0"
    description: str | None = None
    inputs: list[FieldSchema] = Field(default_factory=list)
    outputs: list[FieldSchema] = Field(default_factory=list)
    source: str = "native"
    metadata: dict[str, Any] = Field(default_factory=dict)


__all__ = ["CapabilitySpec", "FieldSchema"]
