"""Unreviewed, source-located regulation PDF AST contracts, never legal approval."""
from __future__ import annotations

from datetime import date
from enum import Enum
from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA_PATTERN = r"^[0-9a-f]{64}$"
Point = tuple[float, float]
Quad = tuple[Point, Point, Point, Point]


class TextOrigin(str, Enum):
    NATIVE_PDF = "NATIVE_PDF"
    RAPIDOCR_CPU = "RAPIDOCR_CPU"


class LegalNodeKind(str, Enum):
    SECTION = "SECTION"
    ARTICLE = "ARTICLE"
    TEMPORARY_ARTICLE = "TEMPORARY_ARTICLE"
    PARAGRAPH = "PARAGRAPH"
    ITEM = "ITEM"
    TEXT = "TEXT"


class ChangeKind(str, Enum):
    AMENDMENT_MENTION = "AMENDMENT_MENTION"
    REPEAL_MENTION = "REPEAL_MENTION"
    EFFECTIVITY_MENTION = "EFFECTIVITY_MENTION"
    EXCEPTION_MENTION = "EXCEPTION_MENTION"


class LegalSourceSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA_PATTERN)
    page_index: int = Field(ge=0)
    polygon: Quad
    extraction: TextOrigin
    printed_page_number: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    reference_type: Literal["NATIVE_BBOX", "OCR_DETECTION_QUAD", "TABLE_CELL_BBOX"] = "NATIVE_BBOX"

    @model_validator(mode="after")
    def valid_span(self) -> "LegalSourceSpan":
        if not all(isfinite(v) for xy in self.polygon for v in xy):
            raise ValueError("Nonfinite source polygon")
        if (self.extraction == TextOrigin.RAPIDOCR_CPU
                and self.reference_type != "OCR_DETECTION_QUAD"):
            raise ValueError("OCR source must retain OCR detection quad")
        if (self.extraction == TextOrigin.NATIVE_PDF
                and self.reference_type == "OCR_DETECTION_QUAD"):
            raise ValueError("Native source cannot impersonate OCR quadrilateral")
        return self


class LegalDocumentMetadata(BaseModel):
    """Externally asserted publication information, NOT verified officiality."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    regulation_id: str = Field(min_length=1)
    document_kind: Literal["ORIGINAL", "AMENDMENT", "CONSOLIDATION", "UNKNOWN"] = "UNKNOWN"
    claimed_title: str | None = None
    claimed_source_url: str | None = None
    claimed_publication_date: date | None = None
    claimed_gazette_number: str | None = None
    claimed_effective_from: date | None = None
    claimed_effective_until: date | None = None
    claimed_jurisdiction: str | None = None
    provenance_status: Literal["USER_ASSERTED_UNVERIFIED"] = "USER_ASSERTED_UNVERIFIED"

    @model_validator(mode="after")
    def valid_interval(self) -> "LegalDocumentMetadata":
        if (self.claimed_effective_from and self.claimed_effective_until
                and self.claimed_effective_until < self.claimed_effective_from):
            raise ValueError("Claimed effectivity date interval is inverted")
        if not self.regulation_id.strip():
            raise ValueError("Regulation identifier cannot be blank")
        return self


class LegalLine(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    line_id: str = Field(min_length=1)
    text: str
    source: LegalSourceSpan
    reading_index: int = Field(ge=0)


class LegalNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    node_id: str = Field(min_length=1)
    parent_node_id: str | None = None
    kind: LegalNodeKind
    order_index: int = Field(ge=0)
    text: str
    spans: tuple[LegalSourceSpan, ...] = Field(min_length=1)
    article_number: str | None = None
    paragraph_number: str | None = None
    item_key: str | None = None


class LegalTableCell(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    row_index: int = Field(ge=0)
    column_index: int = Field(ge=0)
    text: str
    source: LegalSourceSpan


class LegalTable(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    table_id: str = Field(min_length=1)
    page_index: int = Field(ge=0)
    source: LegalSourceSpan
    cells: list[LegalTableCell]
    suggested_parent_node_id: str | None = None
    review_required: Literal[True] = True


class LegalChangeCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str = Field(min_length=1)
    kind: ChangeKind
    source: LegalSourceSpan
    text: str
    related_node_id: str | None = None
    review_required: Literal[True] = True


class LegalReviewIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str = Field(min_length=1)
    page_index: int | None = Field(default=None, ge=0)
    source_line_id: str | None = None
    detail: str


class LegalDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    document_sha256: str = Field(pattern=SHA_PATTERN)
    page_count: int = Field(ge=1)
    metadata: LegalDocumentMetadata
    lines: list[LegalLine] = Field(default_factory=list)
    nodes: list[LegalNode] = Field(default_factory=list)
    tables: list[LegalTable] = Field(default_factory=list)
    changes: list[LegalChangeCandidate] = Field(default_factory=list)
    issues: list[LegalReviewIssue] = Field(default_factory=list)
    review_status: Literal["UNREVIEWED"] = "UNREVIEWED"
    legal_compliance_certified: Literal[False] = False

    @model_validator(mode="after")
    def validate_trace(self) -> "LegalDocument":
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate LegalAST node identity")
        seen: set[str] = set()
        for n in self.nodes:
            if n.parent_node_id and n.parent_node_id not in seen:
                raise ValueError("LegalAST parent must precede its children")
            seen.add(n.node_id)
        if len({x.line_id for x in self.lines}) != len(self.lines):
            raise ValueError("Duplicate LegalAST line identity")
        if len({x.table_id for x in self.tables}) != len(self.tables):
            raise ValueError("Duplicate legal table")
        if len({x.candidate_id for x in self.changes}) != len(self.changes):
            raise ValueError("Duplicate legal change candidate")
        spans = [x.source for x in self.lines]
        spans += [s for n in self.nodes for s in n.spans]
        spans += [x.source for x in self.tables]
        spans += [c.source for table in self.tables for c in table.cells]
        spans += [c.source for c in self.changes]
        if any(s.document_sha256 != self.document_sha256
               or s.page_index >= self.page_count for s in spans):
            raise ValueError("Legal source span does not match original PDF")
        for table in self.tables:
            if table.source.page_index != table.page_index:
                raise ValueError("Legal table source page mismatch")
            if table.suggested_parent_node_id is not None and table.suggested_parent_node_id not in seen:
                raise ValueError("Legal table references unknown parent candidate")
        for change in self.changes:
            if change.related_node_id is not None and change.related_node_id not in seen:
                raise ValueError("Legal change references unknown node")
        return self
