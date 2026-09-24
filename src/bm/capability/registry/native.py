"""Native BM capability registry — the LFX-independent discovery path.

This module MUST NOT import ``lfx`` / ``langflow`` (enforced by
tests/architecture/test_lfx_only_in_adapter.py). It demonstrates that BM keeps
a minimal, self-sufficient registry path based on:

  1. in-process registration (used by native providers and tests), and
  2. Python ``importlib.metadata`` entry points (group ``bm.capabilities``),
     the packaging-native discovery mechanism, plus
  3. a tiny JSON manifest loader.

An LFX-backed registry, if ever adopted, would sit *beside* this as another
adapter backend — never underneath it.
"""

from __future__ import annotations

import importlib.metadata
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from bm.capability.contract import CapabilitySpec

CapabilityInvoker = Callable[[Mapping[str, Any]], dict[str, Any]]


@runtime_checkable
class Provider(Protocol):
    """Structural contract every capability provider satisfies.

    Deliberately a ``Protocol`` (not a base class) so third-party component
    types can be adapted to it without inheritance.
    """

    @property
    def spec(self) -> CapabilitySpec: ...

    def invoke(self, payload: Mapping[str, Any]) -> dict[str, Any]: ...


class NativeCapabilityRegistry:
    """In-process registry keyed by ``capability_id``."""

    def __init__(self) -> None:
        self._specs: dict[str, CapabilitySpec] = {}
        self._invokers: dict[str, CapabilityInvoker] = {}

    def register(self, spec: CapabilitySpec, invoker: CapabilityInvoker) -> None:
        if spec.capability_id in self._specs:
            raise ValueError(f"duplicate capability_id: {spec.capability_id}")
        self._specs[spec.capability_id] = spec
        self._invokers[spec.capability_id] = invoker

    def register_provider(self, provider: Provider) -> None:
        self.register(provider.spec, provider.invoke)

    def get(self, capability_id: str) -> CapabilitySpec:
        return self._specs[capability_id]

    def list(self) -> list[CapabilitySpec]:
        return [self._specs[k] for k in sorted(self._specs)]

    def invoke(self, capability_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self._invokers[capability_id](payload)


def load_capability_manifest(path: str | Path) -> CapabilitySpec:
    """Parse a minimal BM capability manifest (JSON) into a CapabilitySpec."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return CapabilitySpec.model_validate(data)


def discover_entry_point_capabilities(
    group: str = "bm.capabilities",
) -> dict[str, CapabilitySpec]:
    """Discover capabilities advertised via Python entry points.

    Each entry point must resolve to either a ``Provider`` or a zero-arg
    callable returning one. Returns ``capability_id -> spec``. This is the
    packaging-native, dependency-free discovery path BM keeps for itself.
    """
    found: dict[str, CapabilitySpec] = {}
    for ep in importlib.metadata.entry_points(group=group):
        obj = ep.load()
        # Entry point may resolve to a Provider instance or a factory returning one.
        if not hasattr(obj, "spec"):
            obj = obj()
        if not isinstance(obj, Provider):
            raise TypeError(f"entry point {ep.name!r} did not resolve to a Provider")
        found[obj.spec.capability_id] = obj.spec
    return found
