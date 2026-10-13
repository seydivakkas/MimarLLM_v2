"""Single-writer local review JSONL audit history with a SHA chain.

Tamper-evident only if last hash is independently anchored; anyone with
write access can rewrite the entire chain. NOT digital signatures or identity.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.legal.review import (
    ReviewDecision, ReviewInputError, ReviewQueue, validate_decisions,
)
from mimarllm.legal.models import SHA_PATTERN

GENESIS = "0" * 64


class ReviewLedgerError(ReviewInputError):
    pass


class LedgerEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    sequence: int = Field(ge=1)
    previous_sha256: str = Field(pattern=SHA_PATTERN)
    decision: ReviewDecision
    record_sha256: str = Field(pattern=SHA_PATTERN)
    approval_status: Literal["HUKUKI_HOLD"] = "HUKUKI_HOLD"

    @model_validator(mode="after")
    def valid_self_hash(self):
        if self.record_sha256 != _digest(
            self.sequence, self.previous_sha256, self.decision
        ):
            raise ValueError("Ledger entry digest mismatch")
        return self


def _digest(sequence: int, previous: str, decision: ReviewDecision) -> str:
    payload = json.dumps(
        {"sequence":sequence, "previous_sha256":previous,
         "decision":decision.model_dump(mode="json")},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def read_review_ledger(
    path: str | Path, *, max_bytes: int = 8_000_000,
    max_records: int = 15_000,
) -> tuple[LedgerEntry, ...]:
    path = Path(path)
    if not path.exists():
        return ()
    if not path.is_file() or path.stat().st_size > max_bytes:
        raise ReviewLedgerError("Review ledger exceeds size limit")
    previous = GENESIS
    entries = []
    try:
        with path.open("r", encoding="utf-8") as reader:
            for line in reader:
                if len(entries) >= max_records:
                    raise ReviewLedgerError("Review ledger record budget exceeded")
                if not line.strip():
                    raise ReviewLedgerError("Blank ledger record")
                item = LedgerEntry.model_validate_json(line)
                if item.sequence != len(entries) + 1 or item.previous_sha256 != previous:
                    raise ReviewLedgerError("Review ledger hash chain or sequence broken")
                entries.append(item)
                previous = item.record_sha256
    except (OSError, UnicodeError, ValueError) as exc:
        raise ReviewLedgerError("Review ledger verification failed") from exc
    return tuple(entries)


def append_review_decisions(
    path: str | Path,
    queue: ReviewQueue,
    decisions: list[ReviewDecision],
    *, max_ledger_bytes: int = 8_000_000,
) -> tuple[LedgerEntry, ...]:
    """Validate exact ReviewTask digests before appending a local review.

    One writer at a time only. This has no cross-process locking or signatures.
    A full rewrite of a writable ledger cannot be detected without anchoring.
    """
    checked = validate_decisions(queue, decisions)
    existing = read_review_ledger(path, max_bytes=max_ledger_bytes)
    target = Path(path).expanduser().resolve(strict=False)
    if target.suffix.lower() != ".jsonl" or not target.parent.is_dir():
        raise ReviewLedgerError("Ledger requires .jsonl in an existing directory")
    previous = existing[-1].record_sha256 if existing else GENESIS
    new = []
    for decision in checked:
        seq = len(existing) + len(new) + 1
        item = LedgerEntry(
            sequence=seq, previous_sha256=previous, decision=decision,
            record_sha256=_digest(seq, previous, decision),
        )
        new.append(item)
        previous = item.record_sha256
    encoded = "".join(x.model_dump_json() + "\n" for x in new).encode("utf-8")
    if target.exists() and target.stat().st_size + len(encoded) > max_ledger_bytes:
        raise ReviewLedgerError("Review ledger would exceed byte limit")
    if not target.exists() and len(encoded) > max_ledger_bytes:
        raise ReviewLedgerError("Review ledger would exceed byte limit")
    # Single-process append; opening with exclusive mode for a new ledger.
    try:
        if target.exists():
            with target.open("ab") as writer:
                writer.write(encoded)
        else:
            with target.open("xb") as writer:
                writer.write(encoded)
    except OSError as exc:
        raise ReviewLedgerError("Review ledger could not be written") from exc
    return tuple(new)


def import_exported_review_json(
    json_path: str | Path, *,
    max_json_bytes: int = 500_000,
) -> list[ReviewDecision]:
    """Import browser draft; final append still needs source queue validation."""
    p = Path(json_path).expanduser().resolve(strict=True)
    if not p.is_file() or p.stat().st_size > max_json_bytes:
        raise ReviewLedgerError("Browser decision JSON outside limit")
    try:
        content = json.loads(p.read_text("utf-8"))
        if not isinstance(content, list) or not 1 <= len(content) <= 100:
            raise ValueError("Invalid decision list")
        return [ReviewDecision.model_validate(d) for d in content]
    except (ValueError, TypeError) as exc:
        raise ReviewLedgerError("Browser review JSON is invalid") from exc
