"""Local, source-bound 2D review sidecar. NEVER mutate a DrawingIR or report.

Notes are unverified human observations, not approvals or regulatory evidence.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from threading import Lock
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ReviewError(ValueError):
    pass


class ReviewPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    entity_id: str = Field(min_length=1, max_length=160)
    frame_id: str = Field(min_length=1, max_length=160)
    reviewer_label: str = Field(min_length=1, max_length=80)
    note: str = Field(min_length=1, max_length=300)


class ReviewStore:
    """Atomic append + reversible tombstones, scoped to an existing run."""

    def __init__(self) -> None:
        self._lock = Lock()

    @staticmethod
    def _read(folder: Path, source_sha: str) -> list[dict]:
        path = folder / "review-notes.json"
        if path.is_symlink():
            raise ReviewError("Review sidecar symbolic link rejected")
        if not path.exists():
            return []
        if not path.is_file() or path.stat().st_size > 120_000:
            raise ReviewError("Review sidecar format/size invalid")
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ReviewError("Review sidecar unreadable") from exc
        if (not isinstance(blob, dict)
                or blob.get("schema_version") != 1
                or blob.get("source_sha256") != source_sha
                or not isinstance(blob.get("notes"), list)
                or len(blob["notes"]) > 100):
            raise ReviewError("Review sidecar identity mismatch")
        return blob["notes"]

    @staticmethod
    def _write(folder: Path, source_sha: str, notes: list[dict]) -> None:
        if len(notes) > 100:
            raise ReviewError("Maximum source review notes reached")
        blob = {"schema_version": 1, "source_sha256": source_sha, "notes": notes}
        encoded = json.dumps(blob, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > 120_000:
            raise ReviewError("Review sidecar exceeds storage budget")
        final = folder / "review-notes.json"
        if final.is_symlink():
            raise ReviewError("Review sidecar symbolic link rejected")
        temporary = folder / ("." + uuid4().hex + ".review-tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, final)
        finally:
            temporary.unlink(missing_ok=True)

    def list(self, folder: Path, source_sha: str) -> list[dict]:
        with self._lock:
            return [dict(n) for n in self._read(folder, source_sha)]

    def add(self, folder: Path, source_sha: str, drawing: dict, payload: ReviewPayload) -> dict:
        if payload.source_sha256 != source_sha or drawing.get("source_sha256") != source_sha:
            raise ReviewError("Drawing source identity mismatch")
        entities = drawing.get("entities")
        if not isinstance(entities, list):
            raise ReviewError("Drawing entities missing")
        matching = [
            entity for entity in entities
            if entity.get("entity_id") == payload.entity_id
            and entity.get("frame_id") == payload.frame_id
            and entity.get("origin") in ("CAD_NATIVE", "PDF_NATIVE")
            and entity.get("type_candidate") in ("LINE", "PDF_LINE")
            and entity.get("geometry", {}).get("kind") == "SEGMENT"
            and len(entity.get("geometry", {}).get("points", ())) == 2
        ]
        if len(matching) != 1:
            raise ReviewError("Unambiguous native line source required")
        record = {
            "review_id": uuid4().hex,
            "source_sha256": source_sha,
            "entity_id": payload.entity_id,
            "frame_id": payload.frame_id,
            "reviewer_label": payload.reviewer_label,
            "note": payload.note,
            "review_state": "UNVERIFIED_OBSERVATION",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "retracted_utc": None,
        }
        with self._lock:
            notes = self._read(folder, source_sha)
            self._write(folder, source_sha, notes + [record])
        return dict(record)

    def retract(self, folder: Path, source_sha: str, review_id: str) -> dict:
        with self._lock:
            notes = self._read(folder, source_sha)
            matching = [n for n in notes if n.get("review_id") == review_id]
            if len(matching) != 1:
                raise ReviewError("Review ID absent")
            if matching[0].get("retracted_utc") is not None:
                raise ReviewError("Review already retracted")
            # The original note text remains available for audit; no silent delete.
            matching[0]["retracted_utc"] = datetime.now(timezone.utc).isoformat()
            self._write(folder, source_sha, notes)
            return dict(matching[0])
