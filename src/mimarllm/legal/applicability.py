"""Project-specific legal applicability *evidence*, no statutory decision."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.legal.models import SHA_PATTERN


class ExceptionReview(str, Enum):
    UNKNOWN = "UNKNOWN"
    USER_ASSERTED_NONE = "USER_ASSERTED_NONE"
    USER_ASSERTED_PRESENT = "USER_ASSERTED_PRESENT"


class ProjectLegalContext(BaseModel):
    """Explicit facts; neither the permit date nor use is auto-inferred."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    drawing_sha256: str = Field(pattern=SHA_PATTERN)
    jurisdiction_country: Literal["TR"] = "TR"
    province: str | None = None
    district: str | None = None
    municipality: str | None = None
    use_classification: str | None = None
    building_class: str | None = None
    permit_or_application_date: date | None = None
    evaluation_date: date | None = None
    exception_review: ExceptionReview = ExceptionReview.UNKNOWN
    exception_source_ids: tuple[str, ...] = ()
    reviewer_id: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if any(s is not None and not s.strip()
               for s in (self.province, self.district, self.municipality,
                         self.use_classification, self.building_class,
                         self.reviewer_id)):
            raise ValueError("Project applicability fields cannot contain blank text")
        if self.exception_review == ExceptionReview.USER_ASSERTED_PRESENT and (
            not self.exception_source_ids or not self.reviewer_id):
            raise ValueError("Claimed legal exception requires source IDs and reviewer")
        if (len(set(self.exception_source_ids)) != len(self.exception_source_ids)
                or any(not x.strip() for x in self.exception_source_ids)):
            raise ValueError("Invalid exception reference IDs")
        return self


class ApplicabilityEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    drawing_sha256: str = Field(pattern=SHA_PATTERN)
    relevant_date: date | None
    unknown_fields: tuple[str, ...]
    exception_review: ExceptionReview
    status: Literal["INSUFFICIENT_EVIDENCE", "REVIEW_REQUIRED"]
    reason_code: str
    claim_scope: Literal["PROJECT_CONTEXT_UNVERIFIED_NOT_LEGAL_APPLICABILITY"] = (
        "PROJECT_CONTEXT_UNVERIFIED_NOT_LEGAL_APPLICABILITY"
    )


def assess_project_context(context: ProjectLegalContext) -> ApplicabilityEvidence:
    """Even a complete submitted form is not independently verified law."""
    ctx = ProjectLegalContext.model_validate(context.model_dump())
    missing = tuple(
        name for name, value in (
            ("province", ctx.province),
            ("district", ctx.district),
            ("municipality", ctx.municipality),
            ("use_classification", ctx.use_classification),
            ("building_class", ctx.building_class),
            ("permit_or_application_date", ctx.permit_or_application_date),
            ("reviewer_id", ctx.reviewer_id),
        ) if value is None
    )
    if ctx.exception_review == ExceptionReview.UNKNOWN:
        missing += ("exception_review",)
    elif ctx.exception_review == ExceptionReview.USER_ASSERTED_PRESENT:
        return ApplicabilityEvidence(
            drawing_sha256=ctx.drawing_sha256,
            relevant_date=ctx.permit_or_application_date,
            unknown_fields=missing,
            exception_review=ctx.exception_review,
            status="REVIEW_REQUIRED",
            reason_code="CLAIMED_EXCEPTION_MUST_BE_REVIEWED_AGAINST_LEGAL_TEXT",
        )
    return ApplicabilityEvidence(
        drawing_sha256=ctx.drawing_sha256,
        relevant_date=ctx.permit_or_application_date,
        unknown_fields=missing, exception_review=ctx.exception_review,
        status="INSUFFICIENT_EVIDENCE",
        reason_code=(
            "PROJECT_APPLICABILITY_FIELDS_MISSING" if missing
            else "PROJECT_CONTEXT_USER_ASSERTED_NOT_INDEPENDENTLY_VALIDATED"
        ),
    )
