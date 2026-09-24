"""P1-A PoC: native registry discovery + invocation, zero LFX."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bm.capability.contract import FieldSchema
from bm.capability.provider.text_reverse import TextReverseProvider, provider
from bm.capability.registry import (
    NativeCapabilityRegistry,
    discover_entry_point_capabilities,
    load_capability_manifest,
)


def test_register_list_get_invoke() -> None:
    reg = NativeCapabilityRegistry()
    reg.register_provider(TextReverseProvider())
    assert [s.capability_id for s in reg.list()] == ["text.reverse"]
    assert reg.get("text.reverse").source == "native"
    assert reg.invoke("text.reverse", {"text": "abc"}) == {"reversed": "cba"}


def test_duplicate_registration_rejected() -> None:
    reg = NativeCapabilityRegistry()
    reg.register_provider(TextReverseProvider())
    with pytest.raises(ValueError, match="duplicate"):
        reg.register_provider(TextReverseProvider())


def test_load_capability_manifest(tmp_path: Path) -> None:
    manifest = {
        "capability_id": "doc.parse",
        "name": "Document Parse",
        "version": "0.2.0",
        "inputs": [{"name": "path", "type": "string", "required": True}],
        "outputs": [{"name": "text", "type": "string", "required": True}],
        "source": "native",
    }
    p = tmp_path / "doc.parse.json"
    p.write_text(json.dumps(manifest), encoding="utf-8")
    spec = load_capability_manifest(p)
    assert spec.capability_id == "doc.parse"
    assert spec.inputs[0] == FieldSchema(name="path", type="string", required=True)


def test_discover_entry_point_capabilities(monkeypatch: pytest.MonkeyPatch) -> None:
    ep = SimpleNamespace(name="text.reverse", load=lambda: provider)
    monkeypatch.setattr(
        "bm.capability.registry.native.importlib.metadata.entry_points",
        lambda group=None: [ep],
    )
    found = discover_entry_point_capabilities()
    assert set(found) == {"text.reverse"}
    assert found["text.reverse"].source == "native"


def test_discover_accepts_provider_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    inst = TextReverseProvider()
    ep = SimpleNamespace(name="text.reverse", load=lambda: inst)
    monkeypatch.setattr(
        "bm.capability.registry.native.importlib.metadata.entry_points",
        lambda group=None: [ep],
    )
    found = discover_entry_point_capabilities()
    assert set(found) == {"text.reverse"}


def test_discover_rejects_non_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    ep = SimpleNamespace(name="bad", load=lambda: lambda: object())
    monkeypatch.setattr(
        "bm.capability.registry.native.importlib.metadata.entry_points",
        lambda group=None: [ep],
    )
    with pytest.raises(TypeError, match="did not resolve to a Provider"):
        discover_entry_point_capabilities()
