"""Unreviewed visual-source inspection tasks, derived only from LegalAST.

No user-provided claim can turn a human's visual click into a legal approval.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from hashlib import sha256
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.legal.models import (
    LegalDocument, LegalSourceSpan, SHA_PATTERN,
)
from mimarllm.legal.versions import AmendmentClaim


class ReviewInputError(ValueError):
    pass


class TargetKind(str, Enum):
    NODE = "NODE"
    TABLE_CELL = "TABLE_CELL"
    CHANGE_MENTION = "CHANGE_MENTION"
    AMENDMENT_SIDE = "AMENDMENT_SIDE"


class AmendmentSide(str, Enum):
    TARGET = "TARGET"
    AMENDING = "AMENDING"


class ReviewChoice(str, Enum):
    UNREVIEWED = "UNREVIEWED"
    VISUALLY_MATCHED = "VISUALLY_MATCHED"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED"


class ReviewSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA_PATTERN)
    kind: TargetKind
    reference_id: str = Field(min_length=1)
    span_index: int = Field(default=0, ge=0)
    row_index: int | None = Field(default=None, ge=0)
    column_index: int | None = Field(default=None, ge=0)
    amendment_side: AmendmentSide | None = None

    @model_validator(mode="after")
    def shape(self):
        if self.kind == TargetKind.TABLE_CELL:
            if self.row_index is None or self.column_index is None:
                raise ValueError("Table cell needs row and column")
            if self.span_index != 0:
                raise ValueError("Table cell has one exact source polygon")
        elif self.row_index is not None or self.column_index is not None:
            raise ValueError("Row/column only apply to table cells")
        if (self.kind == TargetKind.AMENDMENT_SIDE) != (self.amendment_side is not None):
            raise ValueError("Amendment side only applies to amendment selection")
        if self.kind in {TargetKind.CHANGE_MENTION, TargetKind.AMENDMENT_SIDE} and self.span_index != 0:
            raise ValueError("Selected source has only one referenced span")
        return self


class ReviewTask(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    task_id: str = Field(pattern=SHA_PATTERN)
    document_sha256: str = Field(pattern=SHA_PATTERN)
    kind: TargetKind
    reference_id: str
    text: str
    source: LegalSourceSpan
    span_index: int = Field(ge=0)
    row_index: int | None = None
    column_index: int | None = None
    amendment_side: AmendmentSide | None = None
    related_claim_id: str | None = None
    claimed_relation: str | None = None
    claimed_effective_from: date | None = None
    legal_review_status: Literal["UNREVIEWED"] = "UNREVIEWED"
    claim_scope: Literal["VISUAL_SOURCE_INSPECTION_NOT_LEGAL_APPROVAL"] = (
        "VISUAL_SOURCE_INSPECTION_NOT_LEGAL_APPROVAL"
    )

    @model_validator(mode="after")
    def source_matches(self):
        if self.source.document_sha256 != self.document_sha256:
            raise ValueError("Visual inspection must cite its own original PDF")
        return self


class ReviewQueue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    queue_schema: Literal["0.1"] = "0.1"
    tasks: tuple[ReviewTask, ...] = Field(min_length=1)
    source_documents: tuple[str, ...]
    review_status: Literal["UNREVIEWED"] = "UNREVIEWED"
    approved_for_check: Literal[False] = False

    @model_validator(mode="after")
    def validate_queue(self):
        if len({x.task_id for x in self.tasks}) != len(self.tasks):
            raise ValueError("Duplicate review task ID")
        if set(x.document_sha256 for x in self.tasks) != set(self.source_documents):
            raise ValueError("Review queue source document identity mismatch")
        if len(set(self.source_documents)) != len(self.source_documents):
            raise ValueError("Duplicate source documents")
        return self


def _select_one(
    docs: dict[str, LegalDocument],
    selection: ReviewSelection,
    claims: dict[str, AmendmentClaim],
):
    doc = docs.get(selection.document_sha256)
    if doc is None:
        raise ReviewInputError("Selected original PDF not in LegalAST collection")
    kind = selection.kind
    claim = None
    if kind == TargetKind.NODE:
        obj = next((n for n in doc.nodes if n.node_id == selection.reference_id), None)
        if obj is None or selection.span_index >= len(obj.spans):
            raise ReviewInputError("Selected node/span does not exist in LegalAST")
        source, txt = obj.spans[selection.span_index], obj.text
    elif kind == TargetKind.TABLE_CELL:
        table = next((t for t in doc.tables if t.table_id == selection.reference_id), None)
        if table is None:
            raise ReviewInputError("Selected table not found")
        obj = next((c for c in table.cells if c.row_index == selection.row_index
                    and c.column_index == selection.column_index), None)
        if obj is None:
            raise ReviewInputError("Table cell row/column does not exist")
        source, txt = obj.source, obj.text
    elif kind == TargetKind.CHANGE_MENTION:
        obj = next((c for c in doc.changes if c.candidate_id == selection.reference_id), None)
        if obj is None:
            raise ReviewInputError("Change mention source not found")
        source, txt = obj.source, obj.text
    else:
        claim = claims.get(selection.reference_id)
        if claim is None:
            raise ReviewInputError("Amendment claim is not in selected source set")
        assert selection.amendment_side is not None
        if selection.amendment_side == AmendmentSide.TARGET:
            if doc.document_sha256 != claim.target_document_sha256:
                raise ReviewInputError("Amendment target PDF source mismatch")
            obj = next((n for n in doc.nodes if n.node_id == claim.target_node_id), None)
            if obj is None:
                raise ReviewInputError("Claim target node not in original PDF")
            source, txt = obj.spans[0], obj.text
        else:
            if doc.document_sha256 != claim.amending_document_sha256:
                raise ReviewInputError("Amending original PDF source mismatch")
            obj = next((n for n in doc.nodes if n.node_id == claim.amending_node_id), None)
            if obj is None or claim.source_span not in obj.spans:
                raise ReviewInputError("Claim source span not on selected amendment node")
            source, txt = claim.source_span, obj.text
    key = json.dumps(selection.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
    ident = sha256(key.encode("utf-8")).hexdigest()
    return ReviewTask(
        task_id=ident, document_sha256=doc.document_sha256,
        kind=kind, reference_id=selection.reference_id,
        text=txt, source=source, span_index=selection.span_index,
        row_index=selection.row_index, column_index=selection.column_index,
        amendment_side=selection.amendment_side,
        related_claim_id=claim.claim_id if claim else None,
        claimed_relation=claim.relation.value if claim else None,
        claimed_effective_from=claim.claimed_effective_from if claim else None,
    )


def build_review_queue(
    documents: list[LegalDocument],
    selections: list[ReviewSelection],
    *, amendment_claims: list[AmendmentClaim] | None = None,
    max_tasks: int = 24,
    max_documents: int = 24,
) -> ReviewQueue:
    """Create a bounded source-authentic selection, not an approval."""
    if not 1 <= len(selections) <= max_tasks <= 100 or not 1 <= len(documents) <= max_documents <= 100:
        raise ReviewInputError("Review queue safety budget exceeded")
    checked = [LegalDocument.model_validate(x.model_dump()) for x in documents]
    docs = {doc.document_sha256: doc for doc in checked}
    if len(docs) != len(checked):
        raise ReviewInputError("Duplicate PDF SHA in review set")
    claims_list = [AmendmentClaim.model_validate(c.model_dump())
                   for c in (amendment_claims or [])]
    claims = {c.claim_id: c for c in claims_list}
    if len(claims) != len(claims_list):
        raise ReviewInputError("Duplicate amendment claim ID")
    selected = [ReviewSelection.model_validate(x.model_dump()) for x in selections]
    tasks = [_select_one(docs, selection, claims) for selection in selected]
    if len({t.task_id for t in tasks}) != len(tasks):
        raise ReviewInputError("Duplicate selected review source")
    return ReviewQueue(
        tasks=tuple(tasks),
        source_documents=tuple(sorted({t.document_sha256 for t in tasks})),
    )


def task_digest(task: ReviewTask) -> str:
    """Content digest binds reviewer decisions to the exact source text/quad."""
    checked = ReviewTask.model_validate(task.model_dump())
    return sha256(checked.model_dump_json().encode("utf-8")).hexdigest()


class ReviewDecision(BaseModel):
    """A user-declared observation, not authenticated expert or signed approval."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    task_id: str = Field(pattern=SHA_PATTERN)
    task_digest: str = Field(pattern=SHA_PATTERN)
    choice: ReviewChoice
    reviewer_label: str = Field(min_length=1, max_length=120)
    observation: str = Field(min_length=1, max_length=2000)
    reviewed_at: datetime
    legal_approval: Literal[False] = False
    authentic_identity_verified: Literal[False] = False

    @model_validator(mode="after")
    def no_anonymous_submission(self):
        if (not self.reviewer_label.strip() or not self.observation.strip()
                or self.reviewed_at.tzinfo is None or self.reviewed_at.utcoffset() is None):
            raise ValueError("Review needs an observation, label and timezone-aware time")
        return self


def validate_decisions(
    queue: ReviewQueue,
    decisions: list[ReviewDecision],
    *, max_decisions: int = 100,
) -> tuple[ReviewDecision, ...]:
    queue = ReviewQueue.model_validate(queue.model_dump())
    if not 1 <= len(decisions) <= max_decisions:
        raise ReviewInputError("Review decision budget exceeded")
    tasks = {t.task_id: t for t in queue.tasks}
    seen = set()
    result = []
    for d in decisions:
        checked = ReviewDecision.model_validate(d.model_dump())
        if checked.task_id in seen or checked.task_id not in tasks:
            raise ReviewInputError("Duplicate or unknown review task ID")
        if checked.task_digest != task_digest(tasks[checked.task_id]):
            raise ReviewInputError("Review choice source text/polygon digest mismatch")
        seen.add(checked.task_id)
        result.append(checked)
    return tuple(result)
