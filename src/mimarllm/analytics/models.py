"""030: typed non-identifying local learning-history snapshots.

Never store reviewer notes, student identity, filenames, native drawing content,
GGUF/VLM output, source SHA or an official educational grade.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.pedagogy.rubric import Axis, RUBRIC_VERSION
from mimarllm.pedagogy.scoring import RubricSubmission


class HistoryError(ValueError):
    """Private history missing, invalid or not authorized."""


class CreateCollection(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    consent: Literal[True]
    retention_days: Literal[30,90,180] = 90


class TokenRequest(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    collection_token: str=Field(pattern=r"^[a-f0-9]{32}$")


class AddSnapshot(TokenRequest):
    consent: Literal[True]
    project_id: str=Field(pattern=r"^[a-f0-9]{32}$")
    run_id: str=Field(pattern=r"^[a-f0-9]{32}$")
    period_label: str=Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9 _.-]{0,31}$")
    assessment: RubricSubmission


class DeleteSnapshot(TokenRequest):
    confirm_delete: Literal[True]
    snapshot_id: str=Field(pattern=r"^[a-f0-9]{32}$")


class RevokeCollection(TokenRequest):
    confirm_delete: Literal[True]


class CompareSnapshots(TokenRequest):
    before_id: str=Field(pattern=r"^[a-f0-9]{32}$")
    after_id: str=Field(pattern=r"^[a-f0-9]{32}$")

    @model_validator(mode="after")
    def distinct(self) -> "CompareSnapshots":
        if self.before_id==self.after_id:
            raise ValueError("Different snapshots required")
        return self


class AxisSeries(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    axis: Axis
    label_tr: str
    before_percent: float | None=None
    after_percent: float | None=None
    delta_points: float | None=None
    comparable: bool=False


class TrendComparison(BaseModel):
    model_config=ConfigDict(extra="forbid", frozen=True)
    status: Literal["COMPARABLE_DRAFT_ONLY","NOT_COMPARABLE"]
    reason: Literal["SAME_LEVEL_AND_RUBRIC", "LEVEL_OR_RUBRIC_DIFFER",
                    "INSUFFICIENT_REVIEW_COVERAGE"]
    before_id: str
    after_id: str
    before_period: str
    after_period: str
    academic_year_before: int
    academic_year_after: int
    rubric_version_before: str
    rubric_version_after: str
    axes: tuple[AxisSeries, ...]
    total_draft_delta: float | None=None
    official_grade: Literal[False]=False
    independent_assessor_verified: Literal[False]=False
    pedagogical_progress_verified: Literal[False]=False
    legal_gate: Literal["REGULATORY_LOCKED"]="REGULATORY_LOCKED"
