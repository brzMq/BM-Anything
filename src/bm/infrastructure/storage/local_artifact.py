"""LocalArtifactStore: content-addressed local filesystem artifact storage.

Implements v0.3 §8.3 and v0.3.1 §6:

- Durable root: ``BMPaths.artifacts`` (under BM_HOME, never repo root / /tmp).
- Content-addressed blob layout: ``blobs/sha256/ab/cd/abcdef...``.
- Sidecar manifest JSON next to the blob (``manifests/``) for metadata.
- Domain code only sees ``ArtifactRef``; absolute paths never cross module
  boundaries as protocol.

This is a P0 minimal implementation. The interface is designed so a future
S3ArtifactStore can replace it without domain changes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

from bm.config.paths import BMPaths, get_paths


@dataclass(frozen=True)
class ArtifactRef:
    """Domain-facing artifact reference. No absolute paths."""

    artifact_id: str
    media_type: str
    size: int
    checksum: str  # sha256:<hex>
    storage_uri: str  # e.g. "local://artifacts/blobs/sha256/ab/cd/abcdef..."
    metadata: dict[str, Any] = field(default_factory=dict)
    producer: str | None = None
    lineage: dict[str, Any] | None = None


def _sha256_stream(stream: BinaryIO, chunk_size: int = 1 << 20) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(chunk_size)
        if not chunk:
            break
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size


def _blob_path(paths: BMPaths, checksum_hex: str) -> Path:
    return paths.blobs / "sha256" / checksum_hex[:2] / checksum_hex[2:4] / checksum_hex


def _manifest_path(paths: BMPaths, artifact_id: str) -> Path:
    return paths.manifests / f"{artifact_id}.json"


class LocalArtifactStore:
    """Minimal content-addressed local artifact store."""

    scheme = "local"

    def __init__(self, paths: BMPaths | None = None) -> None:
        self._paths = paths or get_paths()
        self._paths.blobs.mkdir(parents=True, exist_ok=True)
        self._paths.manifests.mkdir(parents=True, exist_ok=True)

    @property
    def paths(self) -> BMPaths:
        return self._paths

    # ------------------------------------------------------------------ write
    def put(
        self,
        stream: BinaryIO,
        *,
        artifact_id: str,
        media_type: str,
        metadata: dict[str, Any] | None = None,
        producer: str | None = None,
        lineage: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        """Persist a stream as a content-addressed blob. Returns ArtifactRef."""
        # Buffer to a temp file in the same filesystem so the final move is atomic.
        tmp = self._paths.temp / f".bm-artifact-{artifact_id}.part"
        tmp.parent.mkdir(parents=True, exist_ok=True)
        with tmp.open("wb") as fh:
            shutil.copyfileobj(stream, fh)
        with tmp.open("rb") as fh:
            checksum_hex, size = _sha256_stream(fh)

        blob = _blob_path(self._paths, checksum_hex)
        blob.parent.mkdir(parents=True, exist_ok=True)
        if not blob.exists():
            # Atomic move within the same filesystem (temp -> blobs).
            shutil.move(str(tmp), str(blob))
        else:
            # Dedup: identical content already stored.
            tmp.unlink(missing_ok=True)

        ref = ArtifactRef(
            artifact_id=artifact_id,
            media_type=media_type,
            size=size,
            checksum=f"sha256:{checksum_hex}",
            storage_uri=f"{self.scheme}://{blob.relative_to(self._paths.home).as_posix()}",
            metadata=metadata or {},
            producer=producer,
            lineage=lineage,
        )
        _manifest_path(self._paths, artifact_id).write_text(
            json.dumps(asdict(ref), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return ref

    def put_bytes(
        self,
        data: bytes,
        *,
        artifact_id: str,
        media_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        import io

        return self.put(
            io.BytesIO(data),
            artifact_id=artifact_id,
            media_type=media_type,
            metadata=metadata,
        )

    def put_file(
        self,
        src: str | Path,
        *,
        artifact_id: str,
        media_type: str,
        metadata: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        with Path(src).open("rb") as fh:
            return self.put(fh, artifact_id=artifact_id, media_type=media_type, metadata=metadata)

    # ------------------------------------------------------------------- read
    def open(self, ref: ArtifactRef) -> BinaryIO:
        """Return a read-only binary stream for the blob."""
        blob = self._resolve(ref)
        return blob.open("rb")

    def read_bytes(self, ref: ArtifactRef) -> bytes:
        return self._resolve(ref).read_bytes()

    def get_ref(self, artifact_id: str) -> ArtifactRef | None:
        mp = _manifest_path(self._paths, artifact_id)
        if not mp.exists():
            return None
        data = json.loads(mp.read_text(encoding="utf-8"))
        return ArtifactRef(**data)

    def verify(self, ref: ArtifactRef) -> bool:
        """Re-hash the blob and compare against ref.checksum."""
        blob = self._resolve(ref)
        with blob.open("rb") as fh:
            actual, _ = _sha256_stream(fh)
        expected = ref.checksum.split(":", 1)[1]
        return actual == expected

    def exists(self, ref: ArtifactRef) -> bool:
        try:
            return self._resolve(ref).exists()
        except FileNotFoundError:
            return False

    # ----------------------------------------------------------------- delete
    def delete(self, artifact_id: str) -> bool:
        """Remove manifest and (if unreferenced) the blob. Returns True if removed."""
        ref = self.get_ref(artifact_id)
        mp = _manifest_path(self._paths, artifact_id)
        if ref is None or not mp.exists():
            return False
        mp.unlink()
        blob = self._resolve(ref)
        # Only delete blob if no other manifest references the same checksum.
        if blob.exists() and not self._blob_referenced_elsewhere(ref.checksum, artifact_id):
            blob.unlink()
        return True

    # --------------------------------------------------------------- internal
    def _resolve(self, ref: ArtifactRef) -> Path:
        prefix = f"{self.scheme}://"
        if not ref.storage_uri.startswith(prefix):
            raise ValueError(f"Unsupported storage_uri scheme: {ref.storage_uri}")
        rel = ref.storage_uri[len(prefix) :]
        # Guard against path traversal.
        candidate = (self._paths.home / rel).resolve()
        if not str(candidate).startswith(str(self._paths.home.resolve())):
            raise ValueError(f"storage_uri escapes BM_HOME: {ref.storage_uri}")
        if not candidate.exists():
            raise FileNotFoundError(f"Artifact blob missing: {ref.storage_uri}")
        return candidate

    def _blob_referenced_elsewhere(self, checksum: str, exclude_id: str) -> bool:
        for mp in self._paths.manifests.glob("*.json"):
            if mp.stem == exclude_id:
                continue
            try:
                data = json.loads(mp.read_text(encoding="utf-8"))
                if data.get("checksum") == checksum:
                    return True
            except (json.JSONDecodeError, OSError):
                continue
        return False
