"""Unit tests for LocalArtifactStore.

Covers P0 acceptance: "本地 Artifact 可写入、读取并校验 checksum".
Also verifies content-addressed layout, dedup, path-traversal guard, and
that blobs live under BM_HOME (never repo root / /tmp).
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path

import pytest

from bm.config.paths import resolve_paths
from bm.infrastructure.storage.local_artifact import ArtifactRef, LocalArtifactStore


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalArtifactStore:
    monkeypatch.setenv("BM_HOME", str(tmp_path / "bm"))
    monkeypatch.setenv("BM_CACHE_HOME", str(tmp_path / "cache"))
    paths = resolve_paths(create=True)
    return LocalArtifactStore(paths)


class TestPutRead:
    def test_put_bytes_roundtrip(self, store: LocalArtifactStore) -> None:
        data = b"hello bm-anything"
        ref = store.put_bytes(data, artifact_id="a1", media_type="text/plain")
        assert store.read_bytes(ref) == data

    def test_put_stream_roundtrip(self, store: LocalArtifactStore) -> None:
        data = b"stream content"
        ref = store.put(io.BytesIO(data), artifact_id="a2", media_type="application/octet-stream")
        with store.open(ref) as fh:
            assert fh.read() == data

    def test_put_file_roundtrip(self, store: LocalArtifactStore, tmp_path: Path) -> None:
        src = tmp_path / "src.bin"
        src.write_bytes(b"from file")
        ref = store.put_file(src, artifact_id="a3", media_type="application/octet-stream")
        assert store.read_bytes(ref) == b"from file"

    def test_checksum_is_sha256(self, store: LocalArtifactStore) -> None:
        data = b"checksum me"
        ref = store.put_bytes(data, artifact_id="a4", media_type="text/plain")
        expected = "sha256:" + hashlib.sha256(data).hexdigest()
        assert ref.checksum == expected

    def test_verify_ok(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(b"intact", artifact_id="a5", media_type="text/plain")
        assert store.verify(ref) is True

    def test_verify_detects_corruption(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(b"original", artifact_id="a6", media_type="text/plain")
        blob = store._resolve(ref)
        blob.write_bytes(b"tampered")
        assert store.verify(ref) is False

    def test_size_recorded(self, store: LocalArtifactStore) -> None:
        data = b"x" * 1234
        ref = store.put_bytes(data, artifact_id="a7", media_type="text/plain")
        assert ref.size == 1234


class TestContentAddressedLayout:
    def test_blob_path_uses_sha256_prefix(self, store: LocalArtifactStore) -> None:
        data = b"layout test"
        digest = hashlib.sha256(data).hexdigest()
        ref = store.put_bytes(data, artifact_id="b1", media_type="text/plain")
        expected_rel = f"artifacts/blobs/sha256/{digest[:2]}/{digest[2:4]}/{digest}"
        assert ref.storage_uri == f"local://{expected_rel}"

    def test_dedup_identical_content(self, store: LocalArtifactStore) -> None:
        data = b"same bytes"
        r1 = store.put_bytes(data, artifact_id="d1", media_type="text/plain")
        r2 = store.put_bytes(data, artifact_id="d2", media_type="text/plain")
        assert r1.checksum == r2.checksum
        assert r1.storage_uri == r2.storage_uri
        # Both manifests exist, one blob.
        blobs = list(store.paths.blobs.rglob("*"))
        blob_files = [p for p in blobs if p.is_file()]
        assert len(blob_files) == 1

    def test_delete_keeps_blob_when_referenced(self, store: LocalArtifactStore) -> None:
        data = b"shared blob"
        r1 = store.put_bytes(data, artifact_id="s1", media_type="text/plain")
        store.put_bytes(data, artifact_id="s2", media_type="text/plain")
        assert store.delete("s1") is True
        # s2 still references the blob.
        assert store.exists(r1) is True
        assert store.read_bytes(r1) == data

    def test_delete_removes_unreferenced_blob(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(b"lonely", artifact_id="l1", media_type="text/plain")
        blob = store._resolve(ref)
        assert store.delete("l1") is True
        assert not blob.exists()
        assert store.get_ref("l1") is None


class TestManifest:
    def test_get_ref_roundtrip(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(
            b"meta",
            artifact_id="m1",
            media_type="text/plain",
            metadata={"source": "test"},
        )
        loaded = store.get_ref("m1")
        assert loaded == ref
        assert loaded is not None
        assert loaded.metadata == {"source": "test"}

    def test_get_ref_missing_returns_none(self, store: LocalArtifactStore) -> None:
        assert store.get_ref("does-not-exist") is None

    def test_producer_and_lineage_persisted(self, store: LocalArtifactStore) -> None:
        store.put(
            io.BytesIO(b"x"),
            artifact_id="p1",
            media_type="text/plain",
            producer="test-suite",
            lineage={"parent": "none"},
        )
        loaded = store.get_ref("p1")
        assert loaded is not None
        assert loaded.producer == "test-suite"
        assert loaded.lineage == {"parent": "none"}


class TestSafety:
    def test_blob_lives_under_bm_home(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(b"home check", artifact_id="h1", media_type="text/plain")
        blob = store._resolve(ref)
        assert str(blob).startswith(str(store.paths.home))

    def test_blob_not_in_repo_root(self, store: LocalArtifactStore) -> None:
        repo_root = Path(__file__).resolve().parents[2]
        ref = store.put_bytes(b"repo check", artifact_id="h2", media_type="text/plain")
        blob = store._resolve(ref)
        assert not str(blob).startswith(str(repo_root))

    def test_path_traversal_rejected(self, store: LocalArtifactStore) -> None:
        evil = ArtifactRef(
            artifact_id="evil",
            media_type="text/plain",
            size=1,
            checksum="sha256:" + "0" * 64,
            storage_uri="local://../../etc/passwd",
        )
        with pytest.raises(ValueError, match="escapes BM_HOME"):
            store._resolve(evil)

    def test_wrong_scheme_rejected(self, store: LocalArtifactStore) -> None:
        bad = ArtifactRef(
            artifact_id="bad",
            media_type="text/plain",
            size=1,
            checksum="sha256:" + "0" * 64,
            storage_uri="s3://bucket/key",
        )
        with pytest.raises(ValueError, match="Unsupported storage_uri"):
            store._resolve(bad)

    def test_missing_blob_raises(self, store: LocalArtifactStore) -> None:
        ghost = ArtifactRef(
            artifact_id="ghost",
            media_type="text/plain",
            size=1,
            checksum="sha256:" + "a" * 64,
            storage_uri="local://artifacts/blobs/sha256/aa/aa/" + "a" * 64,
        )
        with pytest.raises(FileNotFoundError):
            store.read_bytes(ghost)

    def test_exists_false_for_missing(self, store: LocalArtifactStore) -> None:
        ghost = ArtifactRef(
            artifact_id="ghost2",
            media_type="text/plain",
            size=1,
            checksum="sha256:" + "b" * 64,
            storage_uri="local://artifacts/blobs/sha256/bb/bb/" + "b" * 64,
        )
        assert store.exists(ghost) is False


class TestArtifactRefIsFrozen:
    def test_ref_immutable(self, store: LocalArtifactStore) -> None:
        ref = store.put_bytes(b"immutable", artifact_id="i1", media_type="text/plain")
        with pytest.raises((AttributeError, TypeError, ValueError)):
            ref.artifact_id = "changed"  # type: ignore[misc]
