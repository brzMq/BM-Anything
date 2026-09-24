"""P1-A PoC: LfxCapabilityAdapter maps LFX component metadata -> BM spec.

Runs two ways:
  * always, against stubs whose class names mirror real LFX inputs (no install),
  * additionally, against REAL ``lfx.inputs`` objects when LFX is installed
    (skipped otherwise, so CI stays green without the heavy dependency).
"""

from __future__ import annotations

import pytest

from bm.capability.registry import NativeCapabilityRegistry
from bm.infrastructure.adapters.lfx import LfxCapabilityAdapter
from bm.infrastructure.adapters.lfx.support import is_lfx_available


class StrInput:  # mirrors lfx.inputs.StrInput shape
    def __init__(self, name: str, required: bool = True, info: str | None = None) -> None:
        self.name, self.required, self.info = name, required, info


class BoolInput:
    def __init__(self, name: str, required: bool = True, info: str | None = None) -> None:
        self.name, self.required, self.info = name, required, info


def test_maps_stub_inputs_to_bm_fields() -> None:
    spec = LfxCapabilityAdapter.to_capability_spec(
        capability_id="lfx.demo",
        name="Demo",
        inputs=[StrInput("text", True, "the text"), BoolInput("flag", False)],
    )
    assert spec.source == "lfx"
    assert spec.metadata["adapter"] == "lfx"
    by_name = {f.name: f for f in spec.inputs}
    assert by_name["text"].type == "string"
    assert by_name["text"].required is True
    assert by_name["text"].description == "the text"
    assert by_name["flag"].type == "boolean"
    assert by_name["flag"].required is False


def test_unknown_input_type_falls_back_to_string() -> None:
    class WeirdInput:
        name = "w"

    spec = LfxCapabilityAdapter.to_capability_spec(
        capability_id="lfx.w", name="W", inputs=[WeirdInput()]
    )
    assert spec.inputs[0].type == "string"


def test_missing_name_rejected() -> None:
    class Nameless:
        required = True

    with pytest.raises(ValueError, match="missing a string .name"):
        LfxCapabilityAdapter.to_capability_spec(capability_id="x", name="x", inputs=[Nameless()])


def test_adapted_capability_invokes_through_native_registry() -> None:
    reg = NativeCapabilityRegistry()
    spec = LfxCapabilityAdapter.register(
        reg,
        capability_id="lfx.echo",
        name="Echo",
        inputs=[StrInput("text")],
        invoke=lambda payload: {"echo": payload.get("text", "")},
    )
    assert spec.source == "lfx"
    assert reg.invoke("lfx.echo", {"text": "hi"}) == {"echo": "hi"}


@pytest.mark.skipif(not is_lfx_available(), reason="real lfx not installed")
def test_maps_real_lfx_inputs() -> None:
    from bm.infrastructure.adapters.lfx.support import make_input

    spec = LfxCapabilityAdapter.to_capability_spec(
        capability_id="lfx.real",
        name="Real",
        inputs=[
            make_input("str", "text", info="the text"),
            make_input("bool", "flag", required=False),
            make_input("int", "count"),
        ],
    )
    by_name = {f.name: f for f in spec.inputs}
    assert by_name["text"].type == "string"
    assert by_name["text"].description == "the text"
    assert by_name["flag"].type == "boolean"
    assert by_name["count"].type == "integer"
