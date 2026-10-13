"""Deterministic rule contracts — technical observations are NOT legal conclusions.

The regulatory source gate is deliberately LOCKED in v0.1: a user-written PDF
hash, legal citation, or approval flag cannot authorize compliance verdicts.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.ir import DrawingIR, SHA256_PATTERN
from mimarllm.geometry.spatial import AreaAssessment, GeometryAnalysis
from mimarllm.geometry.topology import PassageReview, SpaceReview


class RuleDomain(str, Enum):
    TECHNICAL = "TECHNICAL"
    REGULATORY = "REGULATORY"


class RuleStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class MetricKind(str, Enum):
    SEGMENT_LENGTH_M = "SEGMENT_LENGTH_M"
    REVIEWED_INTERIOR_AREA_M2 = "REVIEWED_INTERIOR_AREA_M2"
    REVIEWED_FOOTPRINT_M2 = "REVIEWED_FOOTPRINT_M2"
    REVIEWED_TOPOLOGY_PATH = "REVIEWED_TOPOLOGY_PATH"


class Comparison(str, Enum):
    GE = ">="
    GT = ">"
    LE = "<="
    LT = "<"
    EQ = "=="


class ApplicabilityStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    APPLICABLE = "APPLICABLE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LegalSourceLocator(BaseModel):
    """Unverified candidate legislation metadata; never permission to certify."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA256_PATTERN)
    page_index: int = Field(ge=0)
    regulation_id: str = Field(min_length=1)
    article_id: str = Field(min_length=1)
    clause_id: str | None = None
    amendment_id: str | None = None
    effective_from: date
    effective_until: date | None = None

    @model_validator(mode="after")
    def valid_dates(self) -> "LegalSourceLocator":
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError("Legal source effectivity interval is inverted")
        return self


class RuleDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    domain: RuleDomain
    metric: MetricKind
    description: str = Field(min_length=1)
    operator: Comparison | None = None
    threshold: float | None = Field(default=None, allow_inf_nan=False)
    legal_source: LegalSourceLocator | None = None

    @model_validator(mode="after")
    def valid_rule(self) -> "RuleDefinition":
        if not all(x.strip() for x in (self.rule_id, self.version, self.description)):
            raise ValueError("Rule ID, version, description must contain text")
        if self.metric == MetricKind.REVIEWED_TOPOLOGY_PATH:
            if self.operator is not None or self.threshold is not None:
                raise ValueError("Topological path is a qualitative existence check")
        else:
            if self.operator is None or self.threshold is None:
                raise ValueError("Numeric rule requires a comparator and threshold")
            if not isfinite(self.threshold) or self.threshold < 0:
                raise ValueError("Invalid physical comparison threshold")
        if self.domain == RuleDomain.TECHNICAL and self.legal_source is not None:
            raise ValueError("A technical-only scenario cannot claim a legal citation")
        if self.domain == RuleDomain.REGULATORY and self.legal_source is None:
            raise ValueError("Regulatory candidates must identify a legislation locator")
        return self


class ApplicabilityReview(BaseModel):
    """Technical-scenario scope declaration; not an authenticated legal finding."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    status: ApplicabilityStatus = ApplicabilityStatus.UNKNOWN
    reviewed_by: str | None = None
    reason: str | None = None
    drawing_sha256: str | None = Field(default=None, pattern=SHA256_PATTERN)
    supporting_entity_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def require_reviewed_scope(self) -> "ApplicabilityReview":
        if self.status == ApplicabilityStatus.NOT_APPLICABLE:
            if (not self.reviewed_by or not self.reviewed_by.strip()
                    or not self.reason or not self.reason.strip()
                    or not self.drawing_sha256 or not self.supporting_entity_ids):
                raise ValueError("Scope exclusion needs reviewer, reason, drawing and source entities")
        return self


class RuleRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drawing: DrawingIR
    measurement_evidence_id: str | None = None
    area_assessment: AreaAssessment | None = None
    geometry_analysis: GeometryAnalysis | None = None
    spaces: list[SpaceReview] = Field(default_factory=list)
    passages: list[PassageReview] = Field(default_factory=list)
    path_from_space_id: str | None = None
    path_to_space_id: str | None = None
    applicability: ApplicabilityReview | None = None


class RuleResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_id: str
    rule_version: str
    status: RuleStatus
    domain: RuleDomain
    metric: MetricKind
    drawing_sha256: str = Field(pattern=SHA256_PATTERN)
    reason_code: str = Field(min_length=1)
    frame_id: str | None = None
    entity_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    observed_value: float | None = Field(default=None, allow_inf_nan=False)
    threshold: float | None = Field(default=None, allow_inf_nan=False)
    operator: Comparison | None = None
    unit: str | None = None
    calculated_tolerance: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    legal_source: LegalSourceLocator | None = None
    legal_compliance_certified: bool = False
    claim_scope: str = "TECHNICAL_ONLY_NOT_LEGAL"

    @model_validator(mode="after")
    def deny_legal_certification(self) -> "RuleResult":
        if self.legal_compliance_certified:
            raise ValueError("RuleEngine v0.1 cannot certify legal compliance")
        if self.domain == RuleDomain.REGULATORY and self.status in {
            RuleStatus.COMPLIANT, RuleStatus.NON_COMPLIANT, RuleStatus.NOT_APPLICABLE,
        }:
            raise ValueError("Unverified regulatory results must remain on HOLD")
        return self
