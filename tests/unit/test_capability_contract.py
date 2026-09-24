"""P1-A PoC: the BM capability contract is framework-neutral."""

from __future__ import annotations

import sys

from bm.capability.contract import CapabilitySpec, FieldSchema


def test_default_spec_is_native_sourced() -> None:
    spec = CapabilitySpec(capability_id="a.b", name="A B")
    assert spec.source == "native"
    assert spec.inputs == []
    assert spec.outputs == []
    assert spec.metadata == {}


def test_field_schema_defaults() -> None:
    f = FieldSchema(name="x")
    assert f.type == "string"
    assert f.required is True
    assert f.description is None


def test_spec_stores_only_plain_data_not_lfx_types() -> None:
    spec = CapabilitySpec(
        capability_id="t.r",
        name="T",
        inputs=[FieldSchema(name="text", type="string")],
        source="lfx",
        metadata={"adapter": "lfx"},
    )
    # Provenance is a string tag, never a class relationship.
    assert isinstance(spec.source, str)
    dumped = spec.model_dump()
    assert dumped["source"] == "lfx"


def test_importing_contract_does_not_load_lfx() -> None:
    import bm.capability.contract  # noqa: F401

    assert "lfx" not in sys.modules
