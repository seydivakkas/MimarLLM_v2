"""Opt-in, immutable DXF revision writer; never overwrite uploaded originals.

Only direct modelspace LINE handles may be edited. Every commit emits a new DXF
and an audited revision entry. No automatic analysis or regulatory certification.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from math import hypot, isfinite
import json
import os
from pathlib import Path
import re
import shutil
from threading import Lock
from uuid import uuid4

import ezdxf
from pydantic import BaseModel, ConfigDict, Field, field_validator


_ID = re.compile(r"^[a-f0-9]{32}$")
_HANDLE = re.compile(r"^[0-9A-Fa-f]{1,32}$")
_MAX_REVISIONS = 24
_MAX_DXF_BYTES = 25_000_000


class EditError(ValueError):
    """Fail closed on unsupported geometry or source mismatch."""


class EditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_head: str = Field(min_length=1, max_length=32)
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    entity_id: str = Field(min_length=1, max_length=180)
    frame_id: str
    cad_handle: str = Field(min_length=1, max_length=32)
    expected_start: tuple[float, float]
    expected_end: tuple[float, float]
    new_start: tuple[float, float]
    new_end: tuple[float, float]
    reviewer_label: str = Field(min_length=1, max_length=80)

    @field_validator("expected_head")
    @classmethod
    def validate_head(cls, value: str) -> str:
        if value != "original" and not _ID.fullmatch(value):
            raise ValueError("Invalid revision ID")
        return value

    @field_validator("frame_id")
    @classmethod
    def validate_frame(cls, value: str) -> str:
        if value != "cad:Model":
            raise ValueError("Only direct modelspace is editable")
        return value

    @field_validator("cad_handle")
    @classmethod
    def validate_handle(cls, value: str) -> str:
        if not _HANDLE.fullmatch(value):
            raise ValueError("Invalid CAD handle")
        return value.upper()

    @field_validator("expected_start", "expected_end", "new_start", "new_end")
    @classmethod
    def validate_points(cls, value: tuple[float, float]) -> tuple[float, float]:
        if any(not isfinite(number) or abs(number) > 1_000_000 for number in value):
            raise ValueError("Non-finite or oversized coordinate")
        return value


class UndoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_head: str = Field(pattern=r"^[a-f0-9]{32}$")
    expected_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _valid_file(path: Path, digest: str) -> None:
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= _MAX_DXF_BYTES:
        raise EditError("Revision source missing, linked or too large")
    if _digest(path) != digest:
        raise EditError("Revision source SHA mismatch")


class DxfRevisions:
    """Single-process serialization with immutable per-revision output folders."""

    def __init__(self) -> None:
        self._lock = Lock()

    @staticmethod
    def _storage(project_dir: Path) -> Path:
        store = project_dir / "edits"
        if store.is_symlink():
            raise EditError("Edits directory cannot be a symlink")
        store.mkdir(mode=0o700, exist_ok=True)
        if not store.is_dir():
            raise EditError("Invalid edits storage")
        return store

    @staticmethod
    def _state(store: Path, original_sha: str) -> dict:
        current = store / "head.json"
        if current.is_symlink():
            raise EditError("Revision head symlink forbidden")
        if not current.exists():
            return {"original_sha256": original_sha, "head": "original",
                    "head_sha256": original_sha, "history": []}
        if not current.is_file() or current.stat().st_size > 24_000:
            raise EditError("Invalid revision head")
        try:
            state = json.loads(current.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise EditError("Revision journal corrupt") from exc
        if (not isinstance(state, dict) or state.get("original_sha256") != original_sha
                or not isinstance(state.get("history"), list)
                or len(state["history"]) > _MAX_REVISIONS
                or not isinstance(state.get("head_sha256"), str)
                or not re.fullmatch(r"[a-f0-9]{64}", state["head_sha256"])):
            raise EditError("Revision journal identity mismatch")
        history = state["history"]
        for entry in history:
            if (not isinstance(entry, dict)
                    or not _ID.fullmatch(str(entry.get("revision_id", "")))
                    or not re.fullmatch(r"[a-f0-9]{64}", str(entry.get("sha256", "")))
                    or entry.get("operation") not in ("MOVE_LINE", "UNDO")
                    or not isinstance(entry.get("parent_id"), str)):
                raise EditError("Malformed revision record")
        head = state.get("head")
        if head != "original" and not any(e["revision_id"] == head for e in history):
            raise EditError("Revision head missing from journal")
        expected_sha = (original_sha if head == "original" else
                        next(e["sha256"] for e in history if e["revision_id"] == head))
        if state["head_sha256"] != expected_sha:
            raise EditError("Head hash mismatch")
        return state

    @staticmethod
    def _path(store: Path, project_dir: Path, original_sha: str, state: dict, revision_id: str) -> tuple[Path, str]:
        if revision_id == "original":
            path = project_dir / "input.dxf"
            digest = original_sha
        else:
            matching = [r for r in state["history"] if r["revision_id"] == revision_id]
            if len(matching) != 1:
                raise EditError("Unknown revision")
            folder = store / revision_id
            if folder.is_symlink() or not folder.is_dir():
                raise EditError("Revision directory invalid")
            path = folder / "drawing.dxf"
            digest = matching[0]["sha256"]
        _valid_file(path, digest)
        return path, digest

    @staticmethod
    def _publish(store: Path, state: dict, revision: dict, source_file: Path) -> dict:
        if len(state["history"]) >= _MAX_REVISIONS:
            raise EditError("Revision limit reached")
        revision_id = revision["revision_id"]
        temp = store / ("." + revision_id + ".tmp")
        final = store / revision_id
        if final.exists() or temp.exists():
            raise EditError("Revision collision")
        temp.mkdir(mode=0o700)
        try:
            output = temp / "drawing.dxf"
            shutil.copyfile(source_file, output)
            revision["sha256"] = _digest(output)
            _valid_file(output, revision["sha256"])
            (temp / "revision.json").write_text(
                json.dumps(revision, ensure_ascii=False, sort_keys=True),
                encoding="utf-8")
            os.rename(temp, final)
            next_state = {"original_sha256": state["original_sha256"],
                          "head": revision_id, "head_sha256": revision["sha256"],
                          "history": [*state["history"], revision]}
            marker = store / ("." + uuid4().hex + ".head-tmp")
            try:
                marker.write_text(json.dumps(next_state, sort_keys=True), encoding="utf-8")
                os.replace(marker, store / "head.json")
            finally:
                marker.unlink(missing_ok=True)
            return dict(revision)
        finally:
            if temp.exists():
                shutil.rmtree(temp)

    def status(self, project_dir: Path, original_sha: str) -> dict:
        with self._lock:
            store = self._storage(project_dir)
            state = self._state(store, original_sha)
            self._path(store, project_dir, original_sha, state, state["head"])
            return state

    def revise(self, project_dir: Path, original_sha: str, payload: EditRequest) -> dict:
        if payload.source_sha256 != original_sha:
            raise EditError("Original SHA mismatch")
        with self._lock:
            store = self._storage(project_dir)
            state = self._state(store, original_sha)
            if payload.expected_head != state["head"] or payload.expected_sha256 != state["head_sha256"]:
                raise EditError("Stale edit head; refresh and retry")
            parent, digest = self._path(store, project_dir, original_sha, state, state["head"])
            try:
                doc = ezdxf.readfile(parent)
                if doc.audit().has_errors:
                    raise EditError("Source DXF audit failed")
            except (ezdxf.DXFError, OSError, UnicodeError) as exc:
                raise EditError("DXF cannot be read safely") from exc
            entities = [e for e in doc.modelspace().query("LINE")
                        if str(e.dxf.handle).upper() == payload.cad_handle]
            if len(entities) != 1 or payload.entity_id != "Model|" + payload.cad_handle + "|LINE":
                raise EditError("Only unique direct modelspace LINE handles allowed")
            entity = entities[0]
            def point(v):
                if any(not isfinite(float(n)) for n in v[:3]) or abs(float(v[2])) > 1e-7:
                    raise EditError("Unsupported 3D/elevated CAD line")
                return float(v[0]), float(v[1])
            old_start, old_end = point(entity.dxf.start), point(entity.dxf.end)
            if (any(abs(a-b) > 1e-6 for a,b in zip(old_start, payload.expected_start))
                    or any(abs(a-b) > 1e-6 for a,b in zip(old_end, payload.expected_end))):
                raise EditError("Stale/mismatched entity coordinates")
            if not 1e-8 <= hypot(payload.new_end[0]-payload.new_start[0],
                                payload.new_end[1]-payload.new_start[1]) <= 1_000_000:
                raise EditError("Degenerate or oversized line")
            entity.dxf.start = (*payload.new_start, 0)
            entity.dxf.end = (*payload.new_end, 0)
            draft = store / ("." + uuid4().hex + ".draft.dxf")
            try:
                doc.saveas(draft)
                if draft.stat().st_size > _MAX_DXF_BYTES:
                    raise EditError("Revised DXF exceeds upload limit")
                verify = ezdxf.readfile(draft)
                if verify.audit().has_errors:
                    raise EditError("Revised DXF audit failed")
                matching = [e for e in verify.modelspace().query("LINE")
                            if str(e.dxf.handle).upper() == payload.cad_handle]
                if len(matching) != 1 or point(matching[0].dxf.start) != payload.new_start or point(matching[0].dxf.end) != payload.new_end:
                    raise EditError("Roundtrip handle or geometry changed unexpectedly")
                entry = {
                    "revision_id": uuid4().hex,
                    "operation": "MOVE_LINE", "parent_id": state["head"],
                    "parent_sha256": digest, "source_sha256": original_sha,
                    "frame_id": payload.frame_id, "entity_id": payload.entity_id,
                    "cad_handle": payload.cad_handle,
                    "old_start": old_start, "old_end": old_end,
                    "new_start": payload.new_start, "new_end": payload.new_end,
                    "reviewer_label": payload.reviewer_label,
                    "created_utc": datetime.now(timezone.utc).isoformat(),
                    "legal_gate": "REGULATORY_LOCKED",
                }
                return self._publish(store, state, entry, draft)
            finally:
                draft.unlink(missing_ok=True)

    def undo(self, project_dir: Path, original_sha: str, payload: UndoRequest) -> dict:
        if payload.source_sha256 != original_sha:
            raise EditError("Original SHA mismatch")
        with self._lock:
            store = self._storage(project_dir)
            state = self._state(store, original_sha)
            if payload.expected_head != state["head"] or payload.expected_sha256 != state["head_sha256"]:
                raise EditError("Stale undo request")
            if state["head"] == "original":
                raise EditError("No revision to undo")
            latest = next(e for e in state["history"] if e["revision_id"] == state["head"])
            if latest["operation"] != "MOVE_LINE":
                raise EditError("Already undone; redo unsupported")
            parent, parent_sha = self._path(
                store, project_dir, original_sha, state, latest["parent_id"])
            entry = {"revision_id": uuid4().hex, "operation": "UNDO",
                     "parent_id": state["head"], "parent_sha256": state["head_sha256"],
                     "restored_id": latest["parent_id"], "restored_sha256": parent_sha,
                     "source_sha256": original_sha, "undone_revision": latest["revision_id"],
                     "created_utc": datetime.now(timezone.utc).isoformat(),
                     "legal_gate": "REGULATORY_LOCKED"}
            return self._publish(store, state, entry, parent)

    def download(self, project_dir: Path, original_sha: str, revision_id: str) -> bytes:
        if not _ID.fullmatch(revision_id):
            raise EditError("Invalid revision")
        with self._lock:
            store = self._storage(project_dir)
            state = self._state(store, original_sha)
            path, digest = self._path(store, project_dir, original_sha, state, revision_id)
            data = path.read_bytes()
            if sha256(data).hexdigest() != digest:
                raise EditError("Revision changed during read")
            return data
