"""Deterministic, source-preserving dirty-CAD *repair candidates*.

This module NEVER mutates DrawingIR, approves geometry, creates actual
topology passages, measures physical SI distance, or certifies a room.
Proposed segments are visual-only source-unit overlays. Their short gaps
might be intentional door openings, and user review is mandatory.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from enum import Enum
from hashlib import sha256
from itertools import combinations
from math import acos, degrees, dist, hypot, isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.ir import (
    CoordinateKind, DrawingIR, EvidenceOrigin, GeometryPrimitive,
    PrimitiveKind, SourceReference, SHA256_PATTERN,
)
from mimarllm.core.units import CalibrationState

Point = tuple[float, float]


class RepairInputError(ValueError):
    """Invalid source/frame/compute limit: do not produce a misleading overlay."""


class RepairKind(str, Enum):
    VIRTUAL_GAP_BRIDGE = "VIRTUAL_GAP_BRIDGE"
    ENDPOINT_SNAP_CANDIDATE = "ENDPOINT_SNAP_CANDIDATE"
    DUPLICATE_SEGMENT_CANDIDATE = "DUPLICATE_SEGMENT_CANDIDATE"
    OVERLAPPING_SEGMENT_CANDIDATE = "OVERLAPPING_SEGMENT_CANDIDATE"


class RepairIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    frame_id: str
    source_entity_ids: tuple[str, ...] = ()
    detail: str


class UnitHypothesis(BaseModel):
    """Read-only description of an existing scale header; never a new calibration."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str
    observed_calibration_state: str
    source_unit: str
    claimed_metres_per_source_unit: float | None = Field(
        default=None, gt=0, allow_inf_nan=False,
    )
    provenance: str
    overlay_calibration_status: Literal["NOT_VERIFIED_BY_REPAIR"] = (
        "NOT_VERIFIED_BY_REPAIR"
    )
    physical_measurement_approved: Literal[False] = False


class Layer0SemanticCandidate(BaseModel):
    """Layer0 membership is NOT architectural semantics."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    entity_id: str
    source: SourceReference
    geometry_kind: PrimitiveKind
    hypothesis: Literal["LAYER0_UNCLASSIFIED_BOUNDARY_OR_ANNOTATION"] = (
        "LAYER0_UNCLASSIFIED_BOUNDARY_OR_ANNOTATION"
    )
    review_status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    is_verified_wall_or_door: Literal[False] = False


class RepairCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    candidate_id: str = Field(pattern=SHA256_PATTERN)
    source_sha256: str = Field(pattern=SHA256_PATTERN)
    frame_id: str
    kind: RepairKind
    source_entity_ids: tuple[str, ...] = Field(min_length=2, max_length=2)
    source_references: tuple[SourceReference, ...] = Field(min_length=2, max_length=2)
    proposed_geometry: GeometryPrimitive | None = None
    gap_source_units: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    reason_code: str
    review_status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    overlay_kind: Literal["VIRTUAL_CANDIDATE"] = "VIRTUAL_CANDIDATE"
    may_be_intentional_opening: bool = False
    modifies_original: Literal[False] = False
    physical_value_metres: None = None
    legal_compliance_certified: Literal[False] = False

    @model_validator(mode="after")
    def consistent_source(self):
        if len(set(self.source_entity_ids)) != 2:
            raise ValueError("A proposed connection must trace two distinct entities")
        if any(ref.document_sha256 != self.source_sha256
               or ref.frame_id != self.frame_id
               or ref.source_kind.value != "DXF"
               for ref in self.source_references):
            raise ValueError("Repair source must trace the same original DXF frame")
        connecting = self.kind in {
            RepairKind.VIRTUAL_GAP_BRIDGE,
            RepairKind.ENDPOINT_SNAP_CANDIDATE,
        }
        if connecting and (
            self.proposed_geometry is None
            or self.proposed_geometry.kind != PrimitiveKind.SEGMENT
            or not self.may_be_intentional_opening
        ):
            raise ValueError("Gap/snap connector is visual-only and may be intentional")
        if not connecting and self.proposed_geometry is not None:
            raise ValueError("Duplicate/overlap cannot silently delete original linework")
        return self


class RepairOverlay(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["0.1"] = "0.1"
    source_sha256: str = Field(pattern=SHA256_PATTERN)
    frame_id: str
    candidates: tuple[RepairCandidate, ...] = ()
    layer0_candidates: tuple[Layer0SemanticCandidate, ...] = ()
    unit_hypothesis: UnitHypothesis
    issues: tuple[RepairIssue, ...] = ()
    approval_status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"
    changes_drawing_ir: Literal[False] = False
    can_feed_ruleengine: Literal[False] = False
    can_feed_topology: Literal[False] = False
    physical_conclusions_approved: Literal[False] = False

    @model_validator(mode="after")
    def identity(self):
        if len({c.candidate_id for c in self.candidates}) != len(self.candidates):
            raise ValueError("Duplicate repair candidate ID")
        if any(c.frame_id != self.frame_id or c.source_sha256 != self.source_sha256
               for c in self.candidates):
            raise ValueError("Overlay mixes CAD coordinate frames")
        if any(c.source.frame_id != self.frame_id
               or c.source.document_sha256 != self.source_sha256
               for c in self.layer0_candidates):
            raise ValueError("Layer0 evidence from different source")
        if self.unit_hypothesis.frame_id != self.frame_id:
            raise ValueError("Unit hypothesis refers to another frame")
        return self


def _id(digest: str, frame: str, kind: RepairKind,
        entities: tuple[str, str], coordinates: tuple[Point, ...]) -> str:
    payload = "|".join((
        digest, frame, kind.value, entities[0], entities[1],
        ";".join(f"{x:.12g},{y:.12g}" for x, y in coordinates),
    ))
    return sha256(payload.encode("utf-8")).hexdigest()


def _segment_pairs(
    drawing: DrawingIR, frame: str, max_segments: int
) -> list[tuple[str, SourceReference, str, Point, Point]]:
    parts: list[tuple[str, SourceReference, str, Point, Point]] = []
    for e in drawing.entities:
        if e.frame_id != frame or e.origin != EvidenceOrigin.CAD_NATIVE:
            continue
        if e.geometry.kind not in {
            PrimitiveKind.SEGMENT, PrimitiveKind.POLYLINE, PrimitiveKind.POLYGON
        }:
            continue
        if e.source.source_kind.value != "DXF" or not e.source.cad_handle:
            raise RepairInputError("Native DXF part lost its original CAD handle")
        p = list(e.geometry.points)
        pairs = list(zip(p[:-1], p[1:]))
        if e.geometry.closed and p[-1] != p[0]:
            pairs.append((p[-1], p[0]))
        for a, b in pairs:
            if dist(a, b) < 1e-12:
                continue
            parts.append((e.entity_id, e.source, e.layer or "0", a, b))
            if len(parts) > max_segments:
                raise RepairInputError("Native repair segment safety budget exceeded")
    return parts


def _collinear(a: Point, b: Point, c: Point, d: Point,
               angle_degrees: float, cross_tolerance: float) -> bool:
    ab = (b[0]-a[0], b[1]-a[1])
    cd = (d[0]-c[0], d[1]-c[1])
    len_ab, len_cd = hypot(*ab), hypot(*cd)
    dot = abs((ab[0]*cd[0]+ab[1]*cd[1])/(len_ab*len_cd))
    if degrees(acos(min(1, max(0, dot)))) > angle_degrees:
        return False
    distance0 = abs(ab[0]*(c[1]-a[1]) - ab[1]*(c[0]-a[0]))/len_ab
    distance1 = abs(ab[0]*(d[1]-a[1]) - ab[1]*(d[0]-a[0]))/len_ab
    return max(distance0, distance1) <= cross_tolerance


def propose_repair_overlay(
    drawing: DrawingIR,
    frame_id: str,
    *,
    snap_tolerance: float = 0.01,
    max_gap_source_units: float = 0.15,
    angle_tolerance_degrees: float = 3.0,
    max_segments: int = 800,
    max_pairs: int = 250_000,
    max_candidates: int = 300,
    max_layer0: int = 800,
) -> RepairOverlay:
    """Return detached candidates; never adopt them into the physical geometry.

    Finds native source-unit endpoint gaps and duplicate/overlapping segments.
    No geometry is changed and no inference about doors/rooms is made.
    """
    if (not all(isfinite(x) for x in (
            snap_tolerance, max_gap_source_units, angle_tolerance_degrees))
            or not 0 < snap_tolerance < max_gap_source_units
            or angle_tolerance_degrees < 0 or angle_tolerance_degrees > 25
            or max_segments < 1 or max_segments > 5000
            or max_pairs < 0 or max_pairs > 1_000_000
            or not 1 <= max_candidates <= 5000
            or not 1 <= max_layer0 <= 5000):
        raise RepairInputError("Invalid source-unit tolerance or safety budget")
    drawing = DrawingIR.model_validate(drawing.model_dump())
    frame = next((f for f in drawing.frames if f.frame_id == frame_id), None)
    if frame is None or frame.kind != CoordinateKind.CAD_UNIT:
        raise RepairInputError("Repair overlay is only for an original CAD coordinate frame")
    parts = _segment_pairs(drawing, frame_id, max_segments)
    if len(parts) * (len(parts)-1)//2 > max_pairs:
        raise RepairInputError("Repair pair-check safety budget exceeded")

    layer0 = [
        Layer0SemanticCandidate(
            entity_id=e.entity_id, source=e.source,
            geometry_kind=e.geometry.kind,
        )
        for e in drawing.entities
        if e.frame_id == frame_id and e.origin == EvidenceOrigin.CAD_NATIVE
        and (e.layer or "0").strip().casefold() == "0"
        and e.geometry.kind in {PrimitiveKind.SEGMENT, PrimitiveKind.POLYLINE,
                                 PrimitiveKind.POLYGON}
    ]
    if len(layer0) > max_layer0:
        raise RepairInputError("Layer0 evidence safety budget exceeded")
    unit = UnitHypothesis(
        frame_id=frame_id,
        observed_calibration_state=drawing.calibration.state.value,
        source_unit=drawing.calibration.source_unit.value,
        claimed_metres_per_source_unit=(
            drawing.calibration.metres_per_unit
            if drawing.calibration.state == CalibrationState.INFERRED else None
        ),
        provenance=(
            drawing.calibration.method.value if drawing.calibration.method
            else "UNKNOWN_SOURCE_UNITS"
        ),
    )
    proposals: list[RepairCandidate] = []
    issues: list[RepairIssue] = []
    # First isolate duplicate/collinear overlapping native segments, which
    # must NOT be considered a short free endpoint gap.
    blocked: set[tuple[int, int]] = set()
    pending: list[tuple[float, int, int, int, int]] = []
    for i, j in combinations(range(len(parts)), 2):
        ei, ri, li, a, b = parts[i]
        ej, rj, lj, c, d = parts[j]
        if ei == ej or li.casefold() != lj.casefold():
            continue
        if _collinear(a, b, c, d, angle_tolerance_degrees, snap_tolerance):
            ab = (b[0]-a[0], b[1]-a[1])
            ln = hypot(*ab)
            ux, uy = ab[0]/ln, ab[1]/ln
            t0, t1 = sorted((
                (c[0]-a[0])*ux+(c[1]-a[1])*uy,
                (d[0]-a[0])*ux+(d[1]-a[1])*uy,
            ))
            overlap = max(0.0, min(ln, t1) - max(0.0, t0))
            if overlap > max(snap_tolerance, 1e-10):
                duplicate = (
                    (dist(a,c) <= snap_tolerance and dist(b,d) <= snap_tolerance)
                    or (dist(a,d) <= snap_tolerance and dist(b,c) <= snap_tolerance)
                )
                kind = (
                    RepairKind.DUPLICATE_SEGMENT_CANDIDATE if duplicate else
                    RepairKind.OVERLAPPING_SEGMENT_CANDIDATE
                )
                refs = (ri, rj)
                ids = (ei, ej)
                proposals.append(RepairCandidate(
                    candidate_id=_id(drawing.source_sha256, frame_id, kind, ids, (a,b,c,d)),
                    source_sha256=drawing.source_sha256,
                    frame_id=frame_id, kind=kind,
                    source_entity_ids=ids, source_references=refs,
                    reason_code="ORIGINAL_SEGMENTS_OVERLAP_KEEP_BOTH_UNTIL_HUMAN_REVIEW",
                ))
                blocked.update({(i,0),(i,1),(j,0),(j,1)})
                if len(proposals) > max_candidates:
                    raise RepairInputError("Repair candidate budget exceeded")
                continue
        for end_i, pi in enumerate((a, b)):
            for end_j, pj in enumerate((c, d)):
                gap = dist(pi, pj)
                if 1e-12 < gap <= max_gap_source_units:
                    pending.append((gap, i, end_i, j, end_j))

    # An endpoint already touching ANY other original segment is not free.
    # This avoids snapping extra bridges onto already connected corners.
    from shapely.geometry import LineString, Point
    attached: set[tuple[int,int]] = set(blocked)
    for i, (_, _, _, a, b) in enumerate(parts):
        for side, p in enumerate((a,b)):
            witness = Point(p)
            for j, (other_id, _, _, c,d) in enumerate(parts):
                if i == j:
                    continue
                if other_id == parts[i][0]:
                    continue
                if witness.distance(LineString([c,d])) <= 1e-10:
                    attached.add((i,side))
                    break

    choices: dict[tuple[int,int], list[tuple[float,int,int,int,int]]] = defaultdict(list)
    for entry in pending:
        gap,i,ai,j,aj=entry
        if (i,ai) in attached or (j,aj) in attached:
            continue
        choices[(i,ai)].append(entry)
        choices[(j,aj)].append(entry)
    ambiguous = {key for key, entries in choices.items() if len(entries) > 1}
    for key in sorted(ambiguous):
        i,side=key
        issues.append(RepairIssue(
            code="AMBIGUOUS_ENDPOINT_MATCH", frame_id=frame_id,
            source_entity_ids=(parts[i][0],),
            detail="Multiple equally plausible CAD neighbours; no virtual connector inserted",
        ))
    used_endpoints: set[tuple[int,int]] = set()
    for gap,i,ai,j,aj in sorted(pending):
        left,right=(i,ai),(j,aj)
        if left in attached or right in attached or left in ambiguous or right in ambiguous:
            continue
        if left in used_endpoints or right in used_endpoints:
            continue
        ei,ri,_,a,b=parts[i]
        ej,rj,_,c,d=parts[j]
        p=(a,b)[ai];q=(c,d)[aj]
        kind = (
            RepairKind.ENDPOINT_SNAP_CANDIDATE if gap <= snap_tolerance else
            RepairKind.VIRTUAL_GAP_BRIDGE
        )
        proposals.append(RepairCandidate(
            candidate_id=_id(drawing.source_sha256,frame_id,kind,(ei,ej),(p,q)),
            source_sha256=drawing.source_sha256,frame_id=frame_id,
            kind=kind, source_entity_ids=(ei,ej),
            source_references=(ri,rj),
            proposed_geometry=GeometryPrimitive(
                kind=PrimitiveKind.SEGMENT,points=(p,q),
            ),
            gap_source_units=gap,
            may_be_intentional_opening=True,
            reason_code="VIRTUAL_CONNECTION_MAY_BE_INTENTIONAL_DOOR_OR_UNDRAWN_OPENING",
        ))
        used_endpoints.update({left,right})
        if len(proposals) > max_candidates:
            raise RepairInputError("Repair candidate budget exceeded")
    proposals.sort(key=lambda c: (c.kind.value,c.source_entity_ids,c.candidate_id))
    return RepairOverlay(
        source_sha256=drawing.source_sha256,frame_id=frame_id,
        candidates=tuple(proposals),
        layer0_candidates=tuple(layer0),
        unit_hypothesis=unit,issues=tuple(issues),
    )
