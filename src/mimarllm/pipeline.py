"""Single-file offline DXF/PDF -> DrawingIR -> geometry/topology/rules -> report.

There is NO automatic room/door recognition, scale confirmation or regulatory
approval. Every calibrated measurement and reviewed transition must have an
explicit native-source reference and human declaration. Geometry candidates
are never legal or physical construction conclusions.
"""
from __future__ import annotations

from enum import Enum
from math import dist
from pathlib import Path
from typing import Literal, Mapping, Protocol, Sequence

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.ir import (
    DrawingIR, EvidenceOrigin, MeasurementEvidence, PrimitiveKind, SourceKind,
)
from mimarllm.core.units import CalibrationMethod, UnitCalibration
from mimarllm.geometry.spatial import (
    AreaAssessment, GeometryAnalysis, GeometryInputError, analyze_geometry,
    assess_area,
)
from mimarllm.geometry.topology import (
    PassageReview, SpaceReview, TopologyInputError, TopologyResult,
    build_topology,
)
from mimarllm.importers.dxf import DxfInputError, parse_dxf
from mimarllm.importers.pdf_ir import PdfIrResult, PdfIrIssue, parse_pdf_ir, OcrReader
from mimarllm.importers.pdf import PdfInputError
from mimarllm.reports.builder import ReportInputError, build_analysis_report
from mimarllm.reports.models import AnalysisReport
from mimarllm.rules.base import (
    ApplicabilityReview, MetricKind, RuleDefinition, RuleRequest, RuleResult,
)
from mimarllm.rules.engine import RuleEngine


class PipelineInputError(ValueError):
    """Invalid local input/config; no report or legal claim is issued."""


class StageStatus(str, Enum):
    COMPLETE = "COMPLETE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


class StageRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    stage: Literal["IMPORT", "CALIBRATION", "GEOMETRY", "TOPOLOGY", "RULES", "REPORT"]
    status: StageStatus
    reason_code: str = Field(min_length=1)
    frame_id: str | None = None
    details: tuple[str, ...] = ()


class CalibrationReference(BaseModel):
    """Explicit physical reference length on an actual native SEGMENT entity."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    entity_id: str = Field(min_length=1)
    known_length_metres: float = Field(gt=0, allow_inf_nan=False)
    reviewer_id: str = Field(min_length=1, max_length=120)
    method: Literal["USER_REFERENCE", "DIMENSION", "GRAPHIC_SCALE"] = "USER_REFERENCE"

    @model_validator(mode="after")
    def validated_reviewer(self):
        if not self.reviewer_id.strip():
            raise ValueError("Physical calibration requires a nonblank human reviewer label")
        return self


class ReviewedTopology(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str = Field(min_length=1)
    spaces: tuple[SpaceReview, ...] = Field(min_length=1)
    passages: tuple[PassageReview, ...] = ()


class ReviewedArea(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str = Field(min_length=1)
    source_entity_ids: tuple[str, ...] = Field(min_length=1)
    boundary_role: Literal["INTERIOR_ROOM", "EXTERIOR_ENVELOPE"]
    reviewer_id: str = Field(min_length=1)


class RuleRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    definition: RuleDefinition
    measurement_entity_id: str | None = None
    measurement_tolerance_source_units: float = Field(default=0, ge=0, allow_inf_nan=False)
    area: ReviewedArea | None = None
    topology_frame_id: str | None = None
    path_from_space_id: str | None = None
    path_to_space_id: str | None = None
    applicability: ApplicabilityReview | None = None

    @model_validator(mode="after")
    def selection_matches_metric(self):
        metric = self.definition.metric
        if self.measurement_entity_id is not None and metric != MetricKind.SEGMENT_LENGTH_M:
            raise ValueError("Segment evidence is only allowed for SEGMENT_LENGTH_M")
        if self.area is not None and metric not in {
            MetricKind.REVIEWED_INTERIOR_AREA_M2,
            MetricKind.REVIEWED_FOOTPRINT_M2,
        }:
            raise ValueError("Boundary evidence requires an area scenario")
        if any(v is not None for v in (
            self.topology_frame_id, self.path_from_space_id, self.path_to_space_id,
        )) and metric != MetricKind.REVIEWED_TOPOLOGY_PATH:
            raise ValueError("Path fields only apply to topology path rule")
        return self


class PipelineConfig(BaseModel):
    """Bounded offline orchestration config; no network, inferential semantics."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    geometry_frame_ids: tuple[str, ...] = ()
    # OCR is never implicit. Values are bounded source-PDF-point rectangles.
    ocr_regions: dict[int, tuple[tuple[float, float, float, float], ...]] = Field(default_factory=dict)
    calibration: CalibrationReference | None = None
    topology: tuple[ReviewedTopology, ...] = ()
    rules: tuple[RuleRun, ...] = ()
    max_geometry_frames: int = Field(default=20, ge=1, le=50)
    max_segments_per_frame: int = Field(default=1200, ge=1, le=8000)
    max_import_entities: int = Field(default=20000, ge=1, le=100000)

    @model_validator(mode="after")
    def limits(self):
        if len(self.rules) > 128 or len(self.topology) > 20:
            raise ValueError("Pipeline rule/topology configuration budget exceeded")
        if (sum(len(v) for v in self.ocr_regions.values()) > 64
                or any(page < 0 for page in self.ocr_regions)):
            raise ValueError("OCR source rectangle budget or page index invalid")
        from math import isfinite
        if any(not all(isfinite(x) for x in rect)
               or not (rect[0] < rect[2] and rect[1] < rect[3])
               for regions in self.ocr_regions.values() for rect in regions):
            raise ValueError("OCR regions require finite nonempty rectangles")
        if len(self.geometry_frame_ids) != len(set(self.geometry_frame_ids)):
            raise ValueError("Duplicate geometry frame selector")
        if len({t.frame_id for t in self.topology}) != len(self.topology):
            raise ValueError("Duplicate reviewed topology for one frame")
        keys = [(r.definition.rule_id, r.definition.version) for r in self.rules]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate rule ID/version")
        return self


class PipelineManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["0.1"] = "0.1"
    source_sha256: str
    drawing_id: str
    source_kind: SourceKind
    frame_ids: tuple[str, ...]
    entity_count: int = Field(ge=0)
    face_candidate_count: int = Field(ge=0)
    topology_edge_count: int = Field(ge=0)
    rule_count: int = Field(ge=0)
    report_finding_count: int = Field(ge=0)
    calibration_state: str
    stages: tuple[StageRecord, ...]
    import_issue_codes: tuple[str, ...]
    completion: Literal["COMPLETED_WITH_REVIEW_GATES"] = "COMPLETED_WITH_REVIEW_GATES"
    legal_gate: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"


class PipelineResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drawing: DrawingIR
    geometries: tuple[GeometryAnalysis, ...]
    topologies: tuple[TopologyResult, ...]
    rules: tuple[RuleResult, ...]
    report: AnalysisReport
    manifest: PipelineManifest


def _apply_calibration(drawing: DrawingIR, selection: CalibrationReference) -> None:
    matches = [e for e in drawing.entities if e.entity_id == selection.entity_id]
    if len(matches) != 1:
        raise PipelineInputError("Physical reference must identify one native entity")
    e = matches[0]
    if (e.geometry.kind != PrimitiveKind.SEGMENT
            or e.origin not in {EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE}
            or e.type_candidate not in {"LINE", "PDF_LINE"}):
        raise PipelineInputError("Physical reference must be an original native line segment")
    length = dist(*e.geometry.points)
    if length <= 0:
        raise PipelineInputError("Cannot calibrate using a zero-length native segment")
    calibration = UnitCalibration.from_reference(
        source_distance=length,
        known_distance_metres=selection.known_length_metres,
        evidence_id=e.entity_id,
        method=CalibrationMethod(selection.method),
        user_confirmed=True,
    )
    drawing.calibration = calibration
    drawing.calibration_frame_id = e.frame_id


def _native_segment_measurement(
    drawing: DrawingIR, entity_id: str, tolerance: float,
) -> MeasurementEvidence:
    matches = [e for e in drawing.entities if e.entity_id == entity_id]
    if len(matches) != 1:
        raise PipelineInputError("Selected measurement entity is absent")
    e = matches[0]
    if (e.geometry.kind != PrimitiveKind.SEGMENT
            or e.origin not in {EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE}
            or e.type_candidate not in {"LINE", "PDF_LINE"}):
        raise PipelineInputError("Only source-native line segments can create length evidence")
    length = dist(*e.geometry.points)
    if length <= 0:
        raise PipelineInputError("Zero-length entity cannot provide length evidence")
    physical = (
        drawing.calibration.length_metres(length)
        if drawing.calibration.state.value == "CONFIRMED"
        and drawing.calibration_frame_id == e.frame_id else None
    )
    return MeasurementEvidence(
        evidence_id=f"pipeline:segment:{entity_id}",
        entity_ids=(entity_id,), source_value=length, quantity="length",
        source_frame_id=e.frame_id, method_id="segment_length",
        tolerance_source_units=tolerance,
        physical_value=physical, physical_unit="m" if physical is not None else None,
    )


def run_local_pipeline(
    path: str | Path,
    config: PipelineConfig | None = None,
    *,
    ocr_regions: Mapping[int, Sequence[tuple[float, float, float, float]]] | None = None,
    ocr_reader: OcrReader | None = None,
) -> PipelineResult:
    """Run a bounded single-file local pipeline; nonfatal analysis errors are HOLD.

    There is no "pass" status for whole-building approval. The manifest only
    means the source-aware pipeline produced a report with candid exclusions.
    """
    opts = PipelineConfig.model_validate((config or PipelineConfig()).model_dump())
    try:
        file = Path(path).expanduser().resolve(strict=True)
    except (ValueError, OSError) as exc:
        raise PipelineInputError("Local source drawing does not exist") from exc
    if not file.is_file():
        raise PipelineInputError("Only a local regular drawing file is supported")
    suffix = file.suffix.lower()
    if suffix not in {".dxf", ".pdf"}:
        raise PipelineInputError("Only .dxf and .pdf drawings are supported")
    effective_ocr = ocr_regions if ocr_regions is not None else opts.ocr_regions
    if suffix == ".dxf" and (effective_ocr or ocr_reader is not None):
        raise PipelineInputError("OCR is only applicable to PDF, never DXF")
    if effective_ocr and ocr_reader is None:
        raise PipelineInputError("OCR regions require explicit local CPU OCR reader")
    try:
        if suffix == ".dxf":
            imported = parse_dxf(file, max_entities=opts.max_import_entities)
            drawing = imported.drawing
            import_codes = tuple(i.code for i in imported.issues)
        else:
            imported_pdf: PdfIrResult = parse_pdf_ir(
                file, ocr_regions=effective_ocr, ocr_engine=ocr_reader,
            )
            drawing = imported_pdf.drawing
            import_codes = tuple(i.code for i in imported_pdf.issues)
    except (DxfInputError, PdfInputError, OSError, ValueError) as exc:
        # External input must not leak full source text through a CLI traceback.
        raise PipelineInputError(
            f"Import rejected: {type(exc).__name__}"
        ) from exc

    drawing = DrawingIR.model_validate(drawing.model_dump())
    stages: list[StageRecord] = [StageRecord(
        stage="IMPORT", status=(
            StageStatus.REVIEW_REQUIRED if import_codes else StageStatus.COMPLETE
        ),
        reason_code="SOURCE_IMPORTED_WITH_ISSUES" if import_codes else "SOURCE_IMPORTED",
        details=import_codes[:100],
    )]
    if opts.calibration is not None:
        _apply_calibration(drawing, opts.calibration)
        stages.append(StageRecord(
            stage="CALIBRATION", status=StageStatus.COMPLETE,
            reason_code="HUMAN_REFERENCED_NATIVE_LINE_SCALE_NOT_LEGAL_APPROVAL",
            frame_id=drawing.calibration_frame_id,
            details=(opts.calibration.entity_id,),
        ))
    else:
        stages.append(StageRecord(
            stage="CALIBRATION", status=StageStatus.REVIEW_REQUIRED,
            reason_code="SOURCE_PHYSICAL_SCALE_NOT_USER_CONFIRMED",
        ))
    drawing = DrawingIR.model_validate(drawing.model_dump())
    frames = {f.frame_id for f in drawing.frames}
    requested_frames = opts.geometry_frame_ids or tuple(f.frame_id for f in drawing.frames)
    if not set(requested_frames).issubset(frames):
        raise PipelineInputError("Geometry frame selection is not in DrawingIR")
    if len(requested_frames) > opts.max_geometry_frames:
        raise PipelineInputError("Geometry frame count exceeds configured safety limit")
    geometries: list[GeometryAnalysis] = []
    by_frame: dict[str, GeometryAnalysis] = {}
    for frame in requested_frames:
        try:
            geometry = analyze_geometry(
                drawing, frame,
                max_segments=opts.max_segments_per_frame,
            )
        except (GeometryInputError, ValueError):
            stages.append(StageRecord(
                stage="GEOMETRY", status=StageStatus.ERROR, frame_id=frame,
                reason_code="GEOMETRY_ANALYSIS_REJECTED_NO_CONCLUSION",
            ))
            continue
        geometries.append(geometry)
        by_frame[frame] = geometry
        stages.append(StageRecord(
            stage="GEOMETRY", frame_id=frame,
            status=(StageStatus.REVIEW_REQUIRED
                    if geometry.issues or geometry.faces
                    else StageStatus.COMPLETE),
            reason_code=(
                "UNCLASSIFIED_FACES_OR_GEOMETRY_ISSUES_REQUIRE_REVIEW"
                if geometry.issues or geometry.faces
                else "NATIVE_LINEWORK_INSPECTED_NO_ROOM_SEMANTICS"
            ),
            details=tuple(i.code for i in geometry.issues[:40]),
        ))

    topologies: list[TopologyResult] = []
    for selection in opts.topology:
        if selection.frame_id not in requested_frames:
            raise PipelineInputError("Reviewed topology frame not included in geometry selection")
        geo = by_frame.get(selection.frame_id)
        if geo is None:
            stages.append(StageRecord(
                stage="TOPOLOGY", frame_id=selection.frame_id,
                status=StageStatus.SKIPPED,
                reason_code="GEOMETRY_NOT_AVAILABLE_CANNOT_BUILD_TOPOLOGY",
            ))
            continue
        try:
            topo = build_topology(
                drawing, geo, list(selection.spaces), list(selection.passages),
            )
        except (TopologyInputError, GeometryInputError, ValueError):
            stages.append(StageRecord(
                stage="TOPOLOGY", frame_id=selection.frame_id,
                status=StageStatus.ERROR,
                reason_code="REVIEWED_TOPOLOGY_SOURCE_REJECTED_NO_GRAPH",
            ))
            continue
        topologies.append(topo)
        stages.append(StageRecord(
            stage="TOPOLOGY", frame_id=selection.frame_id,
            status=StageStatus.REVIEW_REQUIRED if topo.issues else StageStatus.COMPLETE,
            reason_code="REVIEWED_ADJACENCY_NOT_WALKING_EGRESS_ROUTE",
            details=tuple(i.code for i in topo.issues[:40]),
        ))
    if not opts.topology:
        stages.append(StageRecord(
            stage="TOPOLOGY", status=StageStatus.SKIPPED,
            reason_code="NO_EXPLICIT_SPACE_AND_DOOR_REVIEWS_NO_GRAPH_INFERRED",
        ))
    topo_by_frame = {t.frame_id: t for t in topologies}
    declarations = {t.frame_id: t for t in opts.topology}
    engine = RuleEngine([r.definition for r in opts.rules]) if opts.rules else None
    rule_results: list[RuleResult] = []
    for selected in opts.rules:
        definition = selected.definition
        measurement_id = None
        if selected.measurement_entity_id is not None:
            evidence = _native_segment_measurement(
                drawing, selected.measurement_entity_id,
                selected.measurement_tolerance_source_units,
            )
            # Duplicate references by multiple technical checks share one ID.
            known = {m.evidence_id: m for m in drawing.measurements}
            if evidence.evidence_id in known and known[evidence.evidence_id] != evidence:
                raise PipelineInputError("Same segment referenced with different tolerance")
            if evidence.evidence_id not in known:
                drawing.measurements.append(evidence)
            measurement_id = evidence.evidence_id
        area: AreaAssessment | None = None
        if selected.area is not None:
            a = selected.area
            if a.frame_id not in requested_frames or a.frame_id not in by_frame:
                raise PipelineInputError("Area review frame has no validated geometry")
            try:
                area = assess_area(
                    drawing, a.frame_id, a.source_entity_ids,
                    boundary_role=a.boundary_role, reviewer_id=a.reviewer_id,
                )
            except (GeometryInputError, ValueError) as exc:
                raise PipelineInputError("Explicit area source review was rejected") from exc
        topo_frame = selected.topology_frame_id
        declaration = declarations.get(topo_frame) if topo_frame is not None else None
        topology_present = topo_frame in topo_by_frame if topo_frame is not None else False
        request = RuleRequest(
            drawing=drawing,
            measurement_evidence_id=measurement_id,
            area_assessment=area,
            geometry_analysis=by_frame.get(topo_frame) if topology_present else None,
            spaces=list(declaration.spaces) if topology_present and declaration else [],
            passages=list(declaration.passages) if topology_present and declaration else [],
            path_from_space_id=selected.path_from_space_id,
            path_to_space_id=selected.path_to_space_id,
            applicability=selected.applicability,
        )
        assert engine is not None
        outcome = engine.evaluate(definition.rule_id, request)
        # Safety gate remains in the existing RuleEngine, not this pipeline.
        rule_results.append(outcome)
        stages.append(StageRecord(
            stage="RULES", frame_id=outcome.frame_id,
            status=(
                StageStatus.REVIEW_REQUIRED
                if outcome.status.value not in {"COMPLIANT", "NON_COMPLIANT"}
                or definition.domain.value == "REGULATORY"
                else StageStatus.COMPLETE
            ),
            reason_code=outcome.reason_code,
            details=(definition.rule_id, outcome.status.value),
        ))
    if not opts.rules:
        stages.append(StageRecord(
            stage="RULES", status=StageStatus.SKIPPED,
            reason_code="NO_EXPLICIT_RULE_DEFINITIONS_NO_THRESHOLDS_INFERRED",
        ))
    drawing = DrawingIR.model_validate(drawing.model_dump())
    try:
        report = build_analysis_report(
            drawing, rules=rule_results,
            geometries=geometries, topologies=topologies,
            max_entities=min(opts.max_import_entities, 20_000),
            include_unlinked_sources=True,
        )
    except (ReportInputError, ValueError) as exc:
        raise PipelineInputError(
            f"Report/source integrity rejected: {type(exc).__name__}"
        ) from exc
    stages.append(StageRecord(
        stage="REPORT", status=StageStatus.COMPLETE,
        reason_code="SOURCE_LINKED_REPORT_CREATED_WITH_EXPLICIT_REVIEW_GATES",
    ))
    manifest = PipelineManifest(
        source_sha256=drawing.source_sha256,
        drawing_id=drawing.drawing_id,
        source_kind=drawing.source_kind,
        frame_ids=tuple(f.frame_id for f in drawing.frames),
        entity_count=len(drawing.entities),
        face_candidate_count=sum(len(g.faces) for g in geometries),
        topology_edge_count=sum(len(t.edges) for t in topologies),
        rule_count=len(rule_results), report_finding_count=len(report.findings),
        calibration_state=drawing.calibration.state.value,
        stages=tuple(stages), import_issue_codes=import_codes[:100],
    )
    return PipelineResult(
        drawing=drawing, geometries=tuple(geometries),
        topologies=tuple(topologies), rules=tuple(rule_results),
        report=report, manifest=manifest,
    )
