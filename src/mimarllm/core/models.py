"""Source-aware PDF observation types. Coordinates use page-top-left PDF points.

These observations are NOT a semantic claim that a line is a wall or that text
is a physical measurement. The future DrawingIR parser can consume them.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Point = tuple[float, float]
Quad = tuple[Point, Point, Point, Point]
BBox = tuple[float, float, float, float]


class TextCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_id: str
    page_index: int = Field(ge=0)
    text: str
    method: Literal["native_pdf", "rapidocr_cpu"]
    polygon: Quad
    coordinate_system: Literal["pdf_top_left_pt"] = "pdf_top_left_pt"
    confidence: float | None = Field(default=None, ge=0, le=1)
    font_name: str | None = None
    font_size_pt: float | None = None
    text_matrix: tuple[float, float, float, float, float, float] | None = None
    review_required: bool = False


class VectorObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    page_index: int = Field(ge=0)
    kind: Literal["line", "curve", "rect"]
    bounds: BBox
    line_width_pt: float | None = None
    coordinate_system: Literal["pdf_top_left_pt"] = "pdf_top_left_pt"


class PageObservation(BaseModel):
    page_index: int = Field(ge=0)
    width_pt: float = Field(gt=0)
    height_pt: float = Field(gt=0)
    rotation_degrees: int = 0
    text: list[TextCandidate] = Field(default_factory=list)
    vectors: list[VectorObservation] = Field(default_factory=list)


class PdfObservation(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_count: int = Field(ge=1)
    pages: list[PageObservation]

    @model_validator(mode="after")
    def check_count(self):
        if len(self.pages) != self.page_count:
            raise ValueError("page_count and pages disagree")
        return self
