"""A pure-native example capability.

Proves the register / discover / invoke path works with zero LFX involvement.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from bm.capability.contract import CapabilitySpec, FieldSchema


class TextReverseProvider:
    """Structural ``Provider``: exposes ``spec`` + ``invoke`` (no inheritance)."""

    def __init__(self) -> None:
        self._spec = CapabilitySpec(
            capability_id="text.reverse",
            name="Text Reverse",
            version="0.1.0",
            description="Reverse a UTF-8 string (native reference capability).",
            inputs=[FieldSchema(name="text", type="string")],
            outputs=[FieldSchema(name="reversed", type="string")],
            source="native",
        )

    @property
    def spec(self) -> CapabilitySpec:
        return self._spec

    def invoke(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text", ""))
        return {"reversed": text[::-1]}


def provider() -> TextReverseProvider:
    """Entry-point factory (``text.reverse = "bm.capability.provider.text_reverse:provider"``)."""
    return TextReverseProvider()
