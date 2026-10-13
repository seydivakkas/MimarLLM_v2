"""Shapely geometry observations for one DrawingIR coordinate frame.

Geometric faces are UNVERIFIED candidates. A physical room/net or exterior
footprint area is only emitted for a separately confirmed, exact, closed
source-entity selection with a confirmed frame-bound calibration.
"""
from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field
from shapely.geometry import LineString, MultiLineString
from shapely.ops import polygonize_full, snap, unary_union

from mimarllm.core.ir import (
    CoordinateKind, DrawingIR, DrawingEntity, EvidenceOrigin, PrimitiveKind,
)
from mimarllm.core.units import CalibrationState


class GeometryInputError(ValueError):
    """Malformed request, unsafe geometry count or cross-frame selection."""


class GeometryReviewStatus(str, Enum):
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    MEASURED = "MEASURED"


class GeometryIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    frame_id: str
    entity_ids: tuple[str, ...] = ()
    detail: str


class FaceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    face_id: str
    frame_id: str
    exterior: tuple[tuple[float, float], ...]
    holes: tuple[tuple[tuple[float, float], ...], ...] = ()
    source_area_squared: float = Field(ge=0, allow_inf_nan=False)
    boundary_entity_ids: tuple[str, ...]
    status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    semantic_kind: Literal["UNCLASSIFIED_FACE"] = "UNCLASSIFIED_FACE"


class GeometryAnalysis(BaseModel):
    frame_id: str
    source_sha256: str
    faces: list[FaceCandidate] = Field(default_factory=list)
    issues: list[GeometryIssue] = Field(default_factory=list)
    input_entity_ids: list[str] = Field(default_factory=list)
    snapped_for_candidates_only: bool = False


class AreaAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    boundary_role: Literal["INTERIOR_ROOM", "EXTERIOR_ENVELOPE"]
    frame_id: str
    source_entity_ids: tuple[str, ...]
    reviewer_id: str | None = None
    status: GeometryReviewStatus
    reason_code: str
    source_area_squared: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    physical_area_m2: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    physical_area_semantics: str | None = None


# Native source linework only, no OCR polygons, glyph bounding rectangles,
# candidate classifications or tessellated DXF circles as room boundaries.
_ADMITTED = {"LINE", "LWPOLYLINE", "PDF_LINE", "PDF_RECT"}


def _entities(
    drawing: DrawingIR, frame_id: str,
    ids: Sequence[str] | None = None,
) -> list[DrawingEntity]:
    frames = {f.frame_id: f for f in drawing.frames}
    if frame_id not in frames:
        raise GeometryInputError("Unknown coordinate frame")
    if frames[frame_id].kind not in {CoordinateKind.CAD_UNIT, CoordinateKind.PDF_POINT}:
        raise GeometryInputError("This v0.1 engine accepts only CAD or PDF frames")
    entities = {e.entity_id: e for e in drawing.entities}
    if ids is not None:
        if not ids or len(ids) != len(set(ids)):
            raise GeometryInputError("Source selection requires unique entity IDs")
        if any(entity_id not in entities for entity_id in ids):
            raise GeometryInputError("Unknown selected source entity")
        if any(entities[entity_id].frame_id != frame_id for entity_id in ids):
            raise GeometryInputError("Selection mixes PDF pages or CAD layouts")
        return [entities[entity_id] for entity_id in ids]
    return [e for e in drawing.entities if e.frame_id == frame_id]


def _linework(
    selected: Sequence[DrawingEntity],
    *,
    frame_id: str,
    max_segments: int,
    report_ignored: bool = False,
) -> tuple[list[tuple[str, LineString]], list[GeometryIssue]]:
    lines: list[tuple[str, LineString]] = []
    issues: list[GeometryIssue] = []
    for entity in selected:
        p = entity.geometry
        if (entity.origin not in {EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE}
                or entity.type_candidate not in _ADMITTED
                or p.kind not in {PrimitiveKind.SEGMENT, PrimitiveKind.POLYLINE,
                                  PrimitiveKind.POLYGON}):
            # A broad PDF pass can contain tens of thousands of glyphs.
            # Ignore unrelated text/points silently during discovery; when
            # the caller *selects* an invalid boundary, expose the mistake.
            if report_ignored:
                issues.append(GeometryIssue(
                    code="UNSUPPORTED_BOUNDARY_SOURCE", frame_id=frame_id,
                    entity_ids=(entity.entity_id,),
                    detail="Selected entity is not native linear boundary geometry",
                ))
            continue
        pts = list(p.points)
        if p.closed:
            pts.append(pts[0])
        for start, end in zip(pts, pts[1:]):
            if len(lines) >= max_segments:
                raise GeometryInputError("Geometry segment safety budget exceeded")
            line = LineString((start, end))
            if line.length <= 1e-12:
                issues.append(GeometryIssue(
                    code="DEGENERATE_SEGMENT", frame_id=frame_id,
                    entity_ids=(entity.entity_id,), detail="Zero-length source segment",
                ))
                continue
            lines.append((entity.entity_id, line))
    return lines, issues


def _quality(
    parts: list[tuple[str, LineString]], frame_id: str, *, max_pairs: int,
    overlap_epsilon: float = 1e-8,
) -> list[GeometryIssue]:
    n = len(parts)
    if n * (n - 1) // 2 > max_pairs:
        raise GeometryInputError("Overlap pair-check safety budget exceeded")
    issues: list[GeometryIssue] = []
    for i in range(n):
        for j in range(i + 1, n):
            # Adjacent edges that share ONLY an endpoint are not overlaps.
            intersection = parts[i][1].intersection(parts[j][1])
            if intersection.length > overlap_epsilon:
                ids = tuple(sorted({parts[i][0], parts[j][0]}))
                issues.append(GeometryIssue(
                    code="OVERLAPPING_SEGMENTS", frame_id=frame_id,
                    entity_ids=ids, detail="Coincident linear source overlap; review required",
                ))
    return issues


def _polygon_faces(
    lines: list[tuple[str, LineString]],
    frame_id: str,
    *,
    min_face_area: float,
    max_faces: int,
    snap_tolerance: float,
) -> tuple[list[FaceCandidate], list[GeometryIssue]]:
    issues: list[GeometryIssue] = []
    if not lines:
        return [], [GeometryIssue(
            code="NO_BOUNDARY_GEOMETRY", frame_id=frame_id,
            detail="No accepted native source linework",
        )]
    original = MultiLineString([line for _, line in lines])
    topology = original if snap_tolerance == 0 else snap(original, original, snap_tolerance)
    noded = unary_union(topology)
    polygon_shapes, cuts, dangles, invalid = polygonize_full(noded)
    for code, collection in (
        ("DANGLING_OR_OPEN_EDGE", dangles),
        ("UNASSIGNED_CUT_EDGE", cuts),
        ("INVALID_RING", invalid),
    ):
        if not collection.is_empty:
            issues.append(GeometryIssue(
                code=code, frame_id=frame_id,
                detail=f"Polygonization has {len(collection.geoms)} unresolved components",
            ))
    if snap_tolerance > 0:
        issues.append(GeometryIssue(
            code="SNAPPED_TOPOLOGY_UNVERIFIED", frame_id=frame_id,
            detail="Snapping may alter boundaries; candidates cannot be certified",
        ))
    raw = [poly for poly in polygon_shapes.geoms
           if poly.is_valid and poly.area >= min_face_area and not poly.is_empty]
    if len(raw) > max_faces:
        raise GeometryInputError("Face safety budget exceeded")
    # Sorting stabilizes synthetic ordering; semantic identity still unverified.
    raw.sort(key=lambda poly: (round(poly.bounds[0], 9), round(poly.bounds[1], 9),
                               round(poly.area, 9)))
    faces: list[FaceCandidate] = []
    for idx, poly in enumerate(raw):
        boundary = poly.boundary
        sources = sorted({entity_id for entity_id, line in lines
                          if boundary.intersection(line).length > 1e-8})
        if not sources:
            issues.append(GeometryIssue(
                code="BOUNDARY_SOURCE_UNRESOLVED", frame_id=frame_id,
                detail=f"Face {idx} cannot be mapped back to source lines",
            ))
        faces.append(FaceCandidate(
            face_id=f"{frame_id}:face:{idx}",
            frame_id=frame_id,
            exterior=tuple((float(x), float(y)) for x, y in list(poly.exterior.coords)[:-1]),
            holes=tuple(tuple((float(x), float(y)) for x, y in list(ring.coords)[:-1])
                        for ring in poly.interiors),
            source_area_squared=float(poly.area),
            boundary_entity_ids=tuple(sources),
        ))
    return faces, issues


def analyze_geometry(
    drawing: DrawingIR,
    frame_id: str,
    *,
    entity_ids: Sequence[str] | None = None,
    max_segments: int = 1200,
    max_pairs: int = 250_000,
    max_faces: int = 300,
    min_face_area: float = 1e-9,
    snap_tolerance: float = 0.0,
) -> GeometryAnalysis:
    """Return unclassified 2D planar faces, never certified rooms or areas."""
    if (not isinstance(max_segments, int) or max_segments < 1 or
        not isinstance(max_pairs, int) or max_pairs < 0 or
        not isinstance(max_faces, int) or max_faces < 1 or
        not all(isfinite(x) for x in (min_face_area, snap_tolerance)) or
        min_face_area <= 0 or snap_tolerance < 0):
        raise GeometryInputError("Invalid geometry safety limits")
    chosen = _entities(drawing, frame_id, entity_ids)
    parts, issues = _linework(
        chosen, frame_id=frame_id, max_segments=max_segments,
        report_ignored=entity_ids is not None,
    )
    issues.extend(_quality(parts, frame_id, max_pairs=max_pairs))
    faces, polygon_issues = _polygon_faces(
        parts, frame_id, min_face_area=min_face_area,
        max_faces=max_faces, snap_tolerance=snap_tolerance,
    )
    issues.extend(polygon_issues)
    return GeometryAnalysis(
        frame_id=frame_id, source_sha256=drawing.source_sha256,
        faces=faces, issues=issues,
        input_entity_ids=[e.entity_id for e in chosen],
        snapped_for_candidates_only=snap_tolerance > 0,
    )


def assess_area(
    drawing: DrawingIR,
    frame_id: str,
    source_entity_ids: Sequence[str],
    *,
    boundary_role: Literal["INTERIOR_ROOM", "EXTERIOR_ENVELOPE"],
    reviewer_id: str | None = None,
    max_segments: int = 1200,
) -> AreaAssessment:
    """Strict single-face surface measurement of *explicitly selected* source edges.

    INTERIOR_ROOM requires someone independently checked *interior wall faces*.
    EXTERIOR_ENVELOPE measures only footprint, NOT legal gross building area.
    An unavailable/unknown scale leaves physical_area_m2=None.
    """
    selected = tuple(source_entity_ids)
    # Validates source existence, frame and duplicates, even if not reviewed.
    _entities(drawing, frame_id, selected)
    result = analyze_geometry(
        drawing, frame_id, entity_ids=selected,
        max_segments=max_segments, snap_tolerance=0.0,
    )
    reason = "BOUNDARY_UNREVIEWED"
    status = GeometryReviewStatus.REVIEW_REQUIRED
    source_area = None
    physical = None
    semantics = None
    disqualifying = bool(result.issues)
    if len(result.faces) != 1 or disqualifying or result.faces[0].holes:
        reason = "NOT_ONE_UNAMBIGUOUS_CLOSED_BOUNDARY"
    else:
        source_area = result.faces[0].source_area_squared
        if not reviewer_id or not reviewer_id.strip():
            reason = "BOUNDARY_UNREVIEWED"
        elif (drawing.calibration.state != CalibrationState.CONFIRMED or
              drawing.calibration_frame_id != frame_id):
            reason = "CONFIRMED_PHYSICAL_SCALE_MISSING"
            status = GeometryReviewStatus.INSUFFICIENT_EVIDENCE
        else:
            physical = drawing.calibration.area_square_metres(source_area)
            reason = "INTERIOR_BOUNDARY_GEOMETRY_MEASURED" if boundary_role == "INTERIOR_ROOM" else "EXTERIOR_FOOTPRINT_GEOMETRY_MEASURED"
            semantics = "INTERIOR_ROOM_AREA_M2" if boundary_role == "INTERIOR_ROOM" else "EXTERIOR_FOOTPRINT_M2"
            status = GeometryReviewStatus.MEASURED
    return AreaAssessment(
        boundary_role=boundary_role, frame_id=frame_id,
        source_entity_ids=selected, reviewer_id=reviewer_id,
        status=status, reason_code=reason,
        source_area_squared=source_area, physical_area_m2=physical,
        physical_area_semantics=semantics,
    )
