"""DrawingIR v0.1: source-traceable observations, not architectural conclusions.

This module does not determine walls, rooms, fire compliance, or net areas.
Coordinate frames and physical calibration are explicit and fail closed.
"""
from __future__ import annotations

from enum import Enum
from math import isfinite, isclose

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.units import UnitCalibration

Point = tuple[float, float]
Quad = tuple[Point, Point, Point, Point]
SHA256_PATTERN = r"^[0-9a-f]{64}$"


class SourceKind(str, Enum):
    DXF = "DXF"
    PDF = "PDF"
    IMAGE = "IMAGE"


class CoordinateKind(str, Enum):
    CAD_UNIT = "CAD_UNIT"
    PDF_POINT = "PDF_POINT"
    PIXEL = "PIXEL"
    METRE = "METRE"


class YDirection(str, Enum):
    UP = "UP"
    DOWN = "DOWN"


class EvidenceOrigin(str, Enum):
    CAD_NATIVE = "CAD_NATIVE"
    PDF_NATIVE = "PDF_NATIVE"
    OCR_CANDIDATE = "OCR_CANDIDATE"
    VLM_CANDIDATE = "VLM_CANDIDATE"
    USER_CONFIRMED = "USER_CONFIRMED"


class PrimitiveKind(str, Enum):
    POINT = "POINT"
    SEGMENT = "SEGMENT"
    POLYLINE = "POLYLINE"
    POLYGON = "POLYGON"


class FindingStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ERROR = "ERROR"


class CoordinateFrame(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str = Field(min_length=1)
    kind: CoordinateKind
    y_direction: YDirection
    view_id: str | None = None
    page_index: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def check_page(self) -> "CoordinateFrame":
        if self.kind == CoordinateKind.PDF_POINT and self.page_index is None:
            raise ValueError("PDF_POINT frame needs page index")
        if self.kind == CoordinateKind.CAD_UNIT and not self.view_id:
            raise ValueError("CAD_UNIT frame needs view/layout identifier")
        return self


class Transform2D(BaseModel):
    """Affine source->target: x'=ax+by+c; y'=dx+ey+f."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    source_frame_id: str = Field(min_length=1)
    target_frame_id: str = Field(min_length=1)
    coefficients: tuple[float, float, float, float, float, float]

    @model_validator(mode="after")
    def check_invertible(self) -> "Transform2D":
        a, b, c, d, e, f = self.coefficients
        if not all(isfinite(x) for x in self.coefficients):
            raise ValueError("Nonfinite coordinate transform")
        if a * e - b * d == 0:
            raise ValueError("Singular coordinate transform")
        return self

    def apply(self, xy: Point) -> Point:
        if not all(isfinite(v) for v in xy):
            raise ValueError("Nonfinite source coordinate")
        a, b, c, d, e, f = self.coefficients
        out = (a * xy[0] + b * xy[1] + c, d * xy[0] + e * xy[1] + f)
        if not all(isfinite(v) for v in out):
            raise ValueError("Nonfinite transformed coordinate")
        return out

    def inverse(self) -> "Transform2D":
        a, b, c, d, e, f = self.coefficients
        determinant = a * e - b * d
        result = (e / determinant, -b / determinant,
                  (b * f - e * c) / determinant,
                  -d / determinant, a / determinant,
                  (d * c - a * f) / determinant)
        return Transform2D(
            source_frame_id=self.target_frame_id,
            target_frame_id=self.source_frame_id,
            coefficients=result,
        )


class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA256_PATTERN)
    source_kind: SourceKind
    frame_id: str = Field(min_length=1)
    page_index: int | None = Field(default=None, ge=0)
    view_id: str | None = None
    cad_handle: str | None = None
    block_path: tuple[str, ...] = ()
    source_polygon: Quad | None = None

    @model_validator(mode="after")
    def check_origin(self) -> "SourceReference":
        if self.source_kind == SourceKind.DXF:
            if not self.view_id or not self.cad_handle:
                raise ValueError("DXF reference needs view and CAD handle")
            if self.page_index is not None:
                raise ValueError("DXF reference cannot claim a PDF page")
        else:
            if self.page_index is None:
                raise ValueError("PDF/image reference needs page index")
            if self.cad_handle is not None or self.block_path:
                raise ValueError("PDF/image reference cannot claim CAD handles")
        if self.source_polygon is not None:
            if not all(isfinite(v) for p in self.source_polygon for v in p):
                raise ValueError("Invalid source polygon")
        return self


class GeometryPrimitive(BaseModel):
    """Unclassified geometric observation in its declared coordinate frame."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: PrimitiveKind
    points: tuple[Point, ...]
    closed: bool = False

    @model_validator(mode="after")
    def check_shape(self) -> "GeometryPrimitive":
        count = len(self.points)
        expected = {
            PrimitiveKind.POINT: 1,
            PrimitiveKind.SEGMENT: 2,
            PrimitiveKind.POLYLINE: 2,
            PrimitiveKind.POLYGON: 3,
        }[self.kind]
        if count < expected or (self.kind in {PrimitiveKind.POINT, PrimitiveKind.SEGMENT} and count != expected):
            raise ValueError("Geometry contains wrong number of points")
        if self.kind == PrimitiveKind.POLYGON and not self.closed:
            raise ValueError("Polygon must explicitly be closed")
        if not all(isfinite(value) for point in self.points for value in point):
            raise ValueError("Nonfinite geometry")
        return self


class DrawingEntity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    entity_id: str = Field(min_length=1)
    frame_id: str = Field(min_length=1)
    geometry: GeometryPrimitive
    source: SourceReference
    layer: str | None = None
    origin: EvidenceOrigin
    type_candidate: str = "UNCLASSIFIED"
    is_verified_semantics: bool = False

    @model_validator(mode="after")
    def check_semantic(self) -> "DrawingEntity":
        if self.frame_id != self.source.frame_id:
            raise ValueError("Entity and source coordinate frames differ")
        if self.is_verified_semantics and self.origin in {
            EvidenceOrigin.OCR_CANDIDATE, EvidenceOrigin.VLM_CANDIDATE
        }:
            raise ValueError("Probabilistic semantic candidate is not verified")
        return self


class MeasurementEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    evidence_id: str = Field(min_length=1)
    entity_ids: tuple[str, ...] = Field(min_length=1)
    source_value: float = Field(ge=0, allow_inf_nan=False)
    quantity: str = Field(pattern=r"^(length|area)$")
    source_frame_id: str = Field(min_length=1)
    method_id: str = Field(min_length=1)
    tolerance_source_units: float = Field(ge=0, allow_inf_nan=False)
    physical_value: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    physical_unit: str | None = None

    @model_validator(mode="after")
    def check_physical(self) -> "MeasurementEvidence":
        if (self.physical_value is None) != (self.physical_unit is None):
            raise ValueError("Physical measurement needs value AND unit")
        if self.physical_unit is not None:
            if self.physical_unit != ("m" if self.quantity == "length" else "m2"):
                raise ValueError("Invalid physical measurement unit")
        return self


class Finding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    finding_id: str = Field(min_length=1)
    check_id: str = Field(min_length=1)
    check_version: str = Field(min_length=1)
    status: FindingStatus
    entity_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    reason_code: str = Field(min_length=1)
    legal_compliance_certified: bool = False

    @model_validator(mode="after")
    def check_evidence(self) -> "Finding":
        if self.legal_compliance_certified:
            raise ValueError("Legal compliance certification is not part of DrawingIR v0.1")
        if self.status in {FindingStatus.PASS, FindingStatus.FAIL}:
            if not self.entity_ids or not self.evidence_ids:
                raise ValueError("Definitive result needs entity and evidence IDs")
        return self


class DrawingIR(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = Field(default="0.1", pattern=r"^0\.1$")
    drawing_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=SHA256_PATTERN)
    source_kind: SourceKind
    parser_version: str = Field(min_length=1)
    frames: list[CoordinateFrame] = Field(min_length=1)
    calibration: UnitCalibration = Field(default_factory=UnitCalibration)
    calibration_frame_id: str | None = None
    transforms: list[Transform2D] = Field(default_factory=list)
    entities: list[DrawingEntity] = Field(default_factory=list)
    measurements: list[MeasurementEvidence] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_graph(self) -> "DrawingIR":
        ids = [frame.frame_id for frame in self.frames]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate coordinate frame IDs")
        frames = {frame.frame_id: frame for frame in self.frames}
        if self.calibration_frame_id is not None and self.calibration_frame_id not in frames:
            raise ValueError("Calibration references unknown coordinate frame")
        if self.calibration.metres_per_unit is not None and self.calibration_frame_id is None:
            raise ValueError("Scale-bearing calibration must be bound to a coordinate frame")
        entity_ids = [entity.entity_id for entity in self.entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("Duplicate entity IDs")
        for entity in self.entities:
            if entity.frame_id not in frames:
                raise ValueError("Entity references missing coordinate frame")
            src = entity.source
            if src.document_sha256 != self.source_sha256 or src.source_kind != self.source_kind:
                raise ValueError("Entity provenance does not match drawing file")
            frame = frames[src.frame_id]
            if src.source_kind == SourceKind.DXF:
                if frame.kind != CoordinateKind.CAD_UNIT or frame.view_id != src.view_id:
                    raise ValueError("DXF source coordinate frame does not match layout")
            elif src.source_kind == SourceKind.PDF:
                if frame.kind != CoordinateKind.PDF_POINT or frame.page_index != src.page_index:
                    raise ValueError("PDF source frame/page mismatch")
            elif frame.kind != CoordinateKind.PIXEL or frame.page_index != src.page_index:
                raise ValueError("Raster source frame/page mismatch")
        for transform in self.transforms:
            if transform.source_frame_id not in frames or transform.target_frame_id not in frames:
                raise ValueError("Transform references unknown frame")
        evidence_ids = [measure.evidence_id for measure in self.measurements]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("Duplicate measurement evidence IDs")
        known_entities = set(entity_ids)
        for measure in self.measurements:
            if measure.source_frame_id not in frames:
                raise ValueError("Measurement frame missing")
            if not set(measure.entity_ids) <= known_entities:
                raise ValueError("Measurement references unknown entity")
            if any(next(e for e in self.entities if e.entity_id == entity_id).frame_id
                   != measure.source_frame_id for entity_id in measure.entity_ids):
                raise ValueError("Measurement mixes coordinate frames")
            if measure.physical_value is not None:
                if self.calibration.state.value != "CONFIRMED":
                    raise ValueError("Physical measurement requires confirmed calibration")
                if measure.source_frame_id != self.calibration_frame_id:
                    raise ValueError("Physical measurement uses a different calibration frame")
                expected = (
                    self.calibration.length_metres(measure.source_value)
                    if measure.quantity == "length"
                    else self.calibration.area_square_metres(measure.source_value)
                )
                if not isclose(measure.physical_value, expected, rel_tol=1e-9, abs_tol=1e-12):
                    raise ValueError("Physical measurement disagrees with validated calibration")
        known_evidence = set(evidence_ids)
        findings = [finding.finding_id for finding in self.findings]
        if len(findings) != len(set(findings)):
            raise ValueError("Duplicate finding IDs")
        for finding in self.findings:
            if not set(finding.entity_ids) <= known_entities:
                raise ValueError("Finding references unknown entity")
            if not set(finding.evidence_ids) <= known_evidence:
                raise ValueError("Finding references unknown measurement evidence")
        return self
