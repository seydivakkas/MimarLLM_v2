"""Analysis report contract: traceable technical observations, NOT legal approval."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.ir import (
    GeometryPrimitive, SourceReference, SHA256_PATTERN,
)
from mimarllm.legal.models import LegalSourceSpan
from mimarllm.rules.base import RuleDomain, RuleStatus


class ReportKind(str, Enum):
    DRAWING_FINDING = "DRAWING_FINDING"
    TECHNICAL_RULE = "TECHNICAL_RULE"
    REGULATORY_CANDIDATE = "REGULATORY_CANDIDATE"
    GEOMETRY_ISSUE = "GEOMETRY_ISSUE"
    FACE_CANDIDATE = "FACE_CANDIDATE"
    TOPOLOGY_ISSUE = "TOPOLOGY_ISSUE"


class ReportSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    entity_id: str = Field(min_length=1)
    drawing_sha256: str = Field(pattern=SHA256_PATTERN)
    frame_id: str = Field(min_length=1)
    geometry: GeometryPrimitive
    origin_reference: SourceReference
    layer: str | None = None


class LegalEvidenceLink(BaseModel):
    """A legal candidate source; never effectivity or officiality certification."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA256_PATTERN)
    node_id: str = Field(min_length=1)
    spans: tuple[LegalSourceSpan, ...] = Field(min_length=1)
    binding_status: str
    reason_codes: tuple[str, ...]
    original_local_audit: str | None = None
    officiality: Literal["NOT_VERIFIED"] = "NOT_VERIFIED"
    effectivity: Literal["NOT_VERIFIED"] = "NOT_VERIFIED"
    legal_compliance_certified: Literal[False] = False

    @model_validator(mode="after")
    def source_consistency(self):
        if any(span.document_sha256 != self.document_sha256 for span in self.spans):
            raise ValueError("Legal evidence spans from foreign PDF")
        return self


class ReportFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    finding_id: str = Field(min_length=1)
    kind: ReportKind
    check_id: str
    status: str
    reason_code: str
    frame_id: str | None = None
    entity_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    measurement_ids: tuple[str, ...] = ()
    technical_domain: RuleDomain | None = None
    observed_value: float | None = Field(default=None, allow_inf_nan=False)
    threshold: float | None = Field(default=None, allow_inf_nan=False)
    unit: str | None = None
    legal_evidence: LegalEvidenceLink | None = None
    claim_scope: Literal["TECHNICAL_OBSERVATION_NOT_LEGAL_VERDICT"] = (
        "TECHNICAL_OBSERVATION_NOT_LEGAL_VERDICT"
    )


class ReportFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str
    coordinate_kind: str
    view_id: str | None = None
    page_index: int | None = None


class AnalysisReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: Literal["0.1"] = "0.1"
    drawing_id: str
    drawing_sha256: str = Field(pattern=SHA256_PATTERN)
    source_kind: str
    frames: tuple[ReportFrame, ...]
    sources: tuple[ReportSource, ...]
    findings: tuple[ReportFinding, ...]
    calibration_state: str
    legal_gate: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"
    disclaimer: Literal["TECHNICAL_ANALYSIS_NOT_LEGAL_COMPLIANCE"] = (
        "TECHNICAL_ANALYSIS_NOT_LEGAL_COMPLIANCE"
    )

    @model_validator(mode="after")
    def check_references(self):
        if len({f.frame_id for f in self.frames}) != len(self.frames):
            raise ValueError("Duplicate report frame")
        frames = {f.frame_id for f in self.frames}
        src_ids = [s.entity_id for s in self.sources]
        if len(set(src_ids)) != len(src_ids):
            raise ValueError("Duplicate report entity")
        sources = {s.entity_id: s for s in self.sources}
        for src in self.sources:
            if (src.drawing_sha256 != self.drawing_sha256
                    or src.frame_id not in frames
                    or src.origin_reference.frame_id != src.frame_id
                    or src.origin_reference.document_sha256 != self.drawing_sha256):
                raise ValueError("Report source provenance/frame mismatch")
        ids = [f.finding_id for f in self.findings]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate report finding")
        for item in self.findings:
            if not set(item.entity_ids).issubset(sources):
                raise ValueError("Report finding points to missing source entity")
            if item.frame_id is not None and item.frame_id not in frames:
                raise ValueError("Report finding frame missing")
            if item.frame_id is not None and any(
                    sources[eid].frame_id != item.frame_id for eid in item.entity_ids):
                raise ValueError("Report finding mixes coordinate frames")
            if item.kind == ReportKind.REGULATORY_CANDIDATE:
                if item.technical_domain != RuleDomain.REGULATORY:
                    raise ValueError("Regulatory report kind must not be technical")
                if item.status in {"COMPLIANT", "NON_COMPLIANT", "NOT_APPLICABLE"}:
                    raise ValueError("Report cannot declare legal compliance")
            if item.kind == ReportKind.TECHNICAL_RULE:
                if item.technical_domain != RuleDomain.TECHNICAL:
                    raise ValueError("Technical scenario needs technical domain")
        return self
