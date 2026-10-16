"""026: provenance-gated candidate massing, not an inferred architectural 3D model.

An explicit native CAD boundary selection and independently confirmed physical
scale are required. The returned footprint is a visual scenario ONLY.
"""
from __future__ import annotations

from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import Polygon

from mimarllm.core.ir import CoordinateKind, DrawingIR, EvidenceOrigin
from mimarllm.core.units import CalibrationState
from mimarllm.geometry.spatial import GeometryInputError, analyze_geometry


class MassingError(ValueError):
    """Unsafe, underdetermined or unsupported input: no geometry emitted."""


class MassingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str = Field(min_length=1, max_length=120)
    source_entity_ids: tuple[str, ...] = Field(min_length=3, max_length=64)
    declared_height_m: float = Field(gt=0, le=150, allow_inf_nan=False)
    reviewer_label: str = Field(min_length=1, max_length=80)

    @model_validator(mode="after")
    def unique_selection(self) -> "MassingRequest":
        if len(set(self.source_entity_ids)) != len(self.source_entity_ids):
            raise ValueError("Duplicate source entity ID")
        return self


class MassingCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["026-0.1"] = "026-0.1"
    status: Literal["UNVERIFIED_MASSING_SCENARIO"] = "UNVERIFIED_MASSING_SCENARIO"
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str
    face_id: str
    source_entity_ids: tuple[str, ...]
    source_cad_handles: tuple[str, ...]
    calibration_evidence_ids: tuple[str, ...]
    calibration_method: str
    reviewer_label: str
    footprint_metres: tuple[tuple[float, float], ...]  # no closing duplicate
    declared_height_m: float
    footprint_area_m2: float
    exterior_orientation: Literal["CCW"] = "CCW"
    coordinate_system: Literal["LOCAL_METRES_Y_UP"] = "LOCAL_METRES_Y_UP"
    height_kind: Literal["USER_DECLARED_SCENARIO"] = "USER_DECLARED_SCENARIO"
    legal_gate: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"
    certified_building: bool = False


def build_massing_candidate(drawing: DrawingIR, request: MassingRequest) -> MassingCandidate:
    if drawing.source_sha256 != request.source_sha256:
        raise MassingError("Source file SHA does not match request")
    if drawing.source_kind.value != "DXF":
        raise MassingError("Only physical-scale, native DXF modelspace is accepted in 026 v0.1")
    frame = next((f for f in drawing.frames if f.frame_id == request.frame_id), None)
    if (frame is None or frame.kind != CoordinateKind.CAD_UNIT
            or request.frame_id != "cad:Model"):
        raise MassingError("Only the original CAD modelspace frame may be extruded")
    calibration = drawing.calibration
    if (calibration.state != CalibrationState.CONFIRMED
            or drawing.calibration_frame_id != request.frame_id
            or calibration.metres_per_unit is None
            or calibration.metres_per_unit <= 0
            or not calibration.evidence_ids):
        raise MassingError("Independent confirmed source-to-metre calibration required")
    # HEADER_UNITS alone is not independent height/metric verification.
    if calibration.method is None or calibration.method.value == "HEADER_UNITS":
        raise MassingError("Header-only scale is insufficient for metric 2.5D")
    entities = {e.entity_id: e for e in drawing.entities}
    selected = [entities.get(eid) for eid in request.source_entity_ids]
    if any(entity is None for entity in selected):
        raise MassingError("Selected native geometry is missing")
    for entity in selected:
        assert entity is not None
        if (entity.frame_id != request.frame_id
                or entity.origin != EvidenceOrigin.CAD_NATIVE
                or entity.type_candidate != "LINE"
                or entity.geometry.kind.value != "SEGMENT"
                or entity.source.block_path
                or not entity.source.cad_handle):
            raise MassingError("Only direct source CAD LINE edges may support this footprint")
    if len({entity.source.cad_handle for entity in selected if entity}) != len(selected):
        raise MassingError("Ambiguous CAD handle selection")
    try:
        geometry = analyze_geometry(
            drawing, request.frame_id,
            entity_ids=request.source_entity_ids,
            max_segments=64, max_pairs=2016, max_intersections=256,
            max_faces=2, min_face_area=1e-8, snap_tolerance=0.0,
        )
    except GeometryInputError as exc:
        raise MassingError("Source boundary cannot be verified") from exc
    if geometry.issues or geometry.snapped_for_candidates_only or len(geometry.faces) != 1:
        raise MassingError("Open, repaired, overlapping or ambiguous boundary; no massing")
    face = geometry.faces[0]
    if (set(face.boundary_entity_ids) != set(request.source_entity_ids)
            or len(face.exterior) < 3 or len(face.exterior) > 64 or face.holes):
        raise MassingError("Footprint must be a single, exact, hole-free source face")
    polygon = Polygon(face.exterior)
    if (polygon.is_empty or not polygon.is_valid or polygon.area <= 1e-8
            or not isfinite(polygon.area)):
        raise MassingError("Invalid polygon topology")
    factor = calibration.metres_per_unit
    # Center-relative coordinates avoid excessive floating-point values in WebGL.
    center = polygon.centroid
    vertices = tuple(((x-center.x)*factor, (y-center.y)*factor)
                     for x,y in face.exterior)
    if not all(isfinite(v) and abs(v) <= 10_000 for point in vertices for v in point):
        raise MassingError("Footprint outside safe local coordinate range")
    # Make the winding deterministic for the downstream Three.js extrusion.
    area2 = sum((vertices[(i+1) % len(vertices)][0]-vertices[i][0]) *
                (vertices[(i+1) % len(vertices)][1]+vertices[i][1])
                for i in range(len(vertices)))
    if area2 > 0:  # clockwise -> reverse
        vertices = tuple(reversed(vertices))
    area_m2 = polygon.area * factor * factor
    if not isfinite(area_m2) or not 1e-6 <= area_m2 <= 1_000_000:
        raise MassingError("Metric footprint area exceeds preview bounds")
    return MassingCandidate(
        source_sha256=drawing.source_sha256,
        frame_id=request.frame_id, face_id=face.face_id,
        source_entity_ids=tuple(sorted(request.source_entity_ids)),
        source_cad_handles=tuple(sorted(e.source.cad_handle for e in selected if e)),
        calibration_evidence_ids=calibration.evidence_ids,
        calibration_method=calibration.method.value,
        reviewer_label=request.reviewer_label,
        footprint_metres=vertices,
        declared_height_m=request.declared_height_m,
        footprint_area_m2=area_m2,
    )
