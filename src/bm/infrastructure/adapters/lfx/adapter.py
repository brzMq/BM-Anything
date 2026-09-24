"""LfxCapabilityAdapter — translate LFX component metadata into BM contracts.

Design: BM -> Adapter -> LFX (never the reverse). This module performs a pure,
*structural* mapping over duck-typed LFX input objects (reading only ``.name``,
``.required`` and ``.info``), so it does NOT import ``lfx`` itself. The concrete
``import lfx`` lives only in ``support``. That keeps the mapping unit-testable
with a stub and means removing LFX never breaks this file's imports.

Verified against real LFX 1.12.3 attributes (``lfx.inputs.StrInput`` etc. expose
``.name`` / ``.required`` / ``.info``). The full LFX input taxonomy is broader;
this PoC maps the common scalar cases and falls back to ``string``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from bm.capability.contract import CapabilitySpec, FieldSchema

# LFX input class name -> BM field type. Keyed on the concrete class name so we
# never need to import or subclass the LFX type.
_TYPE_MAP: dict[str, str] = {
    "StrInput": "string",
    "MultilineInput": "string",
    "SecretStrInput": "string",
    "MultilineSecretInput": "string",
    "CodeInput": "string",
    "PromptInput": "string",
    "MessageInput": "string",
    "QueryInput": "string",
    "LinkInput": "string",
    "TabInput": "string",
    "BoolInput": "boolean",
    "IntInput": "integer",
    "SliderInput": "integer",
    "FloatInput": "number",
    "DropdownInput": "string",
    "MultiselectInput": "array",
    "SortableListInput": "array",
    "DictInput": "object",
    "NestedDictInput": "object",
    "JSONInput": "object",
    "FileInput": "string",
    "DataInput": "object",
}


class LfxCapabilityAdapter:
    """Stateless translator from an LFX component's declared inputs to a spec."""

    @staticmethod
    def _bm_type(lfx_input: Any) -> str:
        return _TYPE_MAP.get(type(lfx_input).__name__, "string")

    @staticmethod
    def _to_field(lfx_input: Any) -> FieldSchema:
        name = getattr(lfx_input, "name", None)
        if not isinstance(name, str) or not name:
            raise ValueError("LFX input object is missing a string .name attribute")
        return FieldSchema(
            name=name,
            type=LfxCapabilityAdapter._bm_type(lfx_input),
            required=bool(getattr(lfx_input, "required", True)),
            description=getattr(lfx_input, "info", None),
        )

    @classmethod
    def to_capability_spec(
        cls,
        *,
        capability_id: str,
        name: str,
        inputs: Iterable[Any],
        version: str = "0.1.0",
        description: str | None = None,
        outputs: Iterable[FieldSchema] | None = None,
    ) -> CapabilitySpec:
        """Build a BM ``CapabilitySpec`` from LFX-style input objects.

        The returned object is a plain BM ``CapabilitySpec`` — no LFX type is
        stored on it, so downstream BM code stays LFX-agnostic.
        """
        fields = [cls._to_field(i) for i in inputs]
        out_fields = list(outputs) if outputs is not None else []
        return CapabilitySpec(
            capability_id=capability_id,
            name=name,
            version=version,
            description=description,
            inputs=fields,
            outputs=out_fields,
            source="lfx",
            metadata={"adapter": "lfx"},
        )

    @classmethod
    def register(
        cls,
        registry: Any,
        *,
        capability_id: str,
        name: str,
        inputs: Iterable[Any],
        invoke: Any,
        version: str = "0.1.0",
        description: str | None = None,
        outputs: Iterable[FieldSchema] | None = None,
    ) -> CapabilitySpec:
        """Adapt an LFX component and register it into a native BM registry."""
        spec = cls.to_capability_spec(
            capability_id=capability_id,
            name=name,
            inputs=inputs,
            version=version,
            description=description,
            outputs=outputs,
        )
        registry.register(spec, invoke)
        return spec
