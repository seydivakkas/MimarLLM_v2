"""028: pure deterministic draft rubric scoring, strictly separate from VLM/rules.

Never infer scores from drawing geometry or AI commentary. The local user
declares a human review, not a cryptographically authenticated instructor.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from mimarllm.core.ir import DrawingIR, EvidenceOrigin
from mimarllm.pedagogy.rubric import Axis, DEFAULT_CATALOG, RUBRIC_VERSION, profile


class RubricError(ValueError):
    """Unverifiable references or unapproved scope, no scoring result."""


class CriterionReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    criterion_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]{3,64}$")
    human_level: int = Field(ge=0, le=4, strict=True)
    source_entity_ids: tuple[str, ...] = Field(min_length=1, max_length=12)
    reviewer_note: str = Field(min_length=15, max_length=500)
    human_review_attested: Literal[True]

    @model_validator(mode="after")
    def unique_source(self) -> "CriterionReview":
        if len(set(self.source_entity_ids)) != len(self.source_entity_ids):
            raise ValueError("Duplicate source IDs within criterion")
        return self


class RubricSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str = Field(min_length=1, max_length=120)
    rubric_version: Literal["028.0.1"] = RUBRIC_VERSION
    academic_year: int = Field(ge=1, le=4, strict=True)
    reviewer_label: str = Field(min_length=2, max_length=80)
    human_review_attested: Literal[True]
    reviews: tuple[CriterionReview, ...] = Field(max_length=24)

    @model_validator(mode="after")
    def no_duplicate_reviews(self) -> "RubricSubmission":
        ids=[item.criterion_id for item in self.reviews]
        if len(ids)!=len(set(ids)):
            raise ValueError("A criterion must be reviewed at most once")
        return self


class AxisOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    axis: Axis
    title_tr: str
    active: bool
    weight_original: int = Field(ge=0)
    active_criteria: tuple[str, ...]
    reviewed_criteria: tuple[str, ...]
    missing_criteria: tuple[str, ...]
    status: Literal["NOT_APPLICABLE_BY_LEVEL", "REVIEW_REQUIRED", "LOCAL_DRAFT_REVIEWED"]
    draft_axis_percent: Decimal | None = None


class RubricOutcome(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rubric_version: Literal["028.0.1"] = RUBRIC_VERSION
    status: Literal["NOT_SCORED", "LOCAL_DRAFT_ONLY"]
    academic_year: int
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str
    reviewer_label: str
    assessment_type: Literal["USER_ATTESTED_HUMAN_REVIEW_NOT_VERIFIED"] = (
        "USER_ATTESTED_HUMAN_REVIEW_NOT_VERIFIED"
    )
    active_criterion_count: int
    reviewed_criterion_count: int
    missing_criterion_ids: tuple[str, ...]
    excluded_higher_year_criteria: tuple[str, ...]
    axes: tuple[AxisOutcome, ...]
    draft_points_out_of_100: Decimal | None
    official_grade: Literal[False] = False
    regulatory_status: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"
    vlm_derived_scores: Literal[False] = False
    can_modify_drawing: Literal[False] = False


def evaluate_rubric(drawing: DrawingIR, submitted: RubricSubmission) -> RubricOutcome:
    """Return all axes plus optional *local draft* weighted score.

    The official course rubric, pedagogical suitability, and assessor identity
    remain unverified; this is not a transcript grade or grading authority.
    """
    try:
        drawing=DrawingIR.model_validate(drawing.model_dump(mode="json"))
        submitted=RubricSubmission.model_validate(submitted.model_dump(mode="json"))
    except (ValidationError, TypeError, ValueError) as exc:
        raise RubricError("RUBRIC_UNTRUSTED_REQUEST_OR_IR") from exc
    if drawing.source_sha256 != submitted.source_sha256:
        raise RubricError("RUBRIC_SOURCE_SHA_MISMATCH")
    if submitted.frame_id not in {f.frame_id for f in drawing.frames}:
        raise RubricError("RUBRIC_SOURCE_FRAME_UNKNOWN")
    plan=profile(submitted.academic_year)
    applicable={c.criterion_id:c for c in DEFAULT_CATALOG.criteria
                if c.min_year<=submitted.academic_year<=c.max_year}
    reviews={r.criterion_id:r for r in submitted.reviews}
    if not set(reviews)<=set(applicable):
        raise RubricError("RUBRIC_CRITERION_NOT_APPLICABLE_OR_UNKNOWN")
    sources={e.entity_id:e for e in drawing.entities}
    for review in reviews.values():
        for source_id in review.source_entity_ids:
            entity=sources.get(source_id)
            if entity is None or entity.frame_id!=submitted.frame_id:
                raise RubricError("RUBRIC_SOURCE_ENTITY_NOT_FOUND_IN_FRAME")
            if (entity.source.document_sha256!=drawing.source_sha256
                    or entity.source.source_kind!=drawing.source_kind
                    or entity.source.frame_id!=submitted.frame_id
                    or entity.origin not in {
                        EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE
                    }):
                raise RubricError("RUBRIC_SOURCE_NOT_NATIVE_AND_VERIFIED")
    axes=[]
    total_weighted=Decimal("0")
    total_active_weight=0
    for definition in DEFAULT_CATALOG.axes:
        group=tuple(c for c in applicable.values() if c.axis==definition.axis)
        ids=tuple(c.criterion_id for c in group)
        reviewed_ids=tuple(x for x in ids if x in reviews)
        missing=tuple(x for x in ids if x not in reviews)
        if not group:
            status="NOT_APPLICABLE_BY_LEVEL"
            pct=None
        elif missing:
            status="REVIEW_REQUIRED"
            pct=None
        else:
            status="LOCAL_DRAFT_REVIEWED"
            weighted_sum=sum(
                (Decimal(reviews[c.criterion_id].human_level)*Decimal(c.internal_weight)
                 for c in group),Decimal("0"))
            denominator=sum(c.internal_weight for c in group)
            pct=(weighted_sum/Decimal(denominator)*Decimal("25")).quantize(
                Decimal("0.01"),rounding=ROUND_HALF_UP)
            total_weighted+=(
                weighted_sum/Decimal(denominator)*Decimal(definition.default_weight)
            )
        if group:
            total_active_weight+=definition.default_weight
        axes.append(AxisOutcome(
            axis=definition.axis,title_tr=definition.title_tr,active=bool(group),
            weight_original=definition.default_weight,
            active_criteria=ids,reviewed_criteria=reviewed_ids,
            missing_criteria=missing,status=status,draft_axis_percent=pct,
        ))
    missing_all=tuple(c.criterion_id for c in applicable.values() if c.criterion_id not in reviews)
    complete=not missing_all and bool(applicable)
    overall=(total_weighted/Decimal(total_active_weight)*Decimal("25")).quantize(
        Decimal("0.01"),rounding=ROUND_HALF_UP) if complete else None
    return RubricOutcome(
        status="LOCAL_DRAFT_ONLY" if complete else "NOT_SCORED",
        academic_year=submitted.academic_year,
        source_sha256=drawing.source_sha256,frame_id=submitted.frame_id,
        reviewer_label=submitted.reviewer_label,
        active_criterion_count=len(applicable),
        reviewed_criterion_count=len(reviews),
        missing_criterion_ids=missing_all,
        excluded_higher_year_criteria=tuple(plan["excluded_higher_year_criteria"]),
        axes=tuple(axes),
        draft_points_out_of_100=overall,
    )
