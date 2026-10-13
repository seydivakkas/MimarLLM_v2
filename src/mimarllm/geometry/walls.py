"""Parallel-source-segment gap observations; NEVER definitive wall thickness.

No layer label, midpoint spacing or pair distance alone proves two lines are
opposing wall faces. Returned candidates are review-only source-unit gaps.
"""
from __future__ import annotations

from math import acos, degrees, hypot, isfinite
from typing import Sequence

from pydantic import BaseModel, ConfigDict, Field

from mimarllm.core.ir import DrawingIR
from mimarllm.geometry.spatial import (
    GeometryInputError, GeometryIssue, _entities, _linework,
)


class WallGapCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    frame_id: str
    first_entity_id: str
    second_entity_id: str
    gap_source_units: float = Field(gt=0, allow_inf_nan=False)
    overlap_source_units: float = Field(gt=0, allow_inf_nan=False)
    angular_deviation_degrees: float = Field(ge=0, le=90, allow_inf_nan=False)
    status: str = "REVIEW_REQUIRED"
    semantic_kind: str = "PARALLEL_EDGE_GAP_CANDIDATE"


class WallGapResult(BaseModel):
    source_sha256: str
    frame_id: str
    candidates: list[WallGapCandidate] = Field(default_factory=list)
    issues: list[GeometryIssue] = Field(default_factory=list)


def find_parallel_edge_gaps(
    drawing: DrawingIR, frame_id: str,
    *,
    entity_ids: Sequence[str] | None = None,
    min_gap: float = 0.001,
    max_gap: float = 500,
    min_overlap: float = 1.0,
    max_segments: int = 650,
    max_pairs: int = 210_000,
    max_candidates: int = 1000,
    angle_tolerance_degrees: float = 2,
) -> WallGapResult:
    """Candidate distances between projected overlapping parallel source segments.

    Distances, widths and overlap are expressed in the selected frame's
    *original units* (CAD units or PDF points). No automatic physical metre
    value is created, regardless of page scale.
    """
    if (not all(isfinite(v) for v in (min_gap, max_gap, min_overlap, angle_tolerance_degrees))
            or min_gap <= 0 or max_gap <= min_gap or min_overlap <= 0
            or angle_tolerance_degrees < 0 or angle_tolerance_degrees > 30
            or max_segments < 1 or max_pairs < 0 or max_candidates < 1):
        raise GeometryInputError("Invalid wall-gap source-unit budgets")
    entities = _entities(drawing, frame_id, entity_ids)
    pieces, issues = _linework(
        entities, frame_id=frame_id, max_segments=max_segments,
        report_ignored=entity_ids is not None,
    )
    n = len(pieces)
    if n * (n - 1) // 2 > max_pairs:
        raise GeometryInputError("Wall-gap pair-check safety budget exceeded")

    results: list[WallGapCandidate] = []
    for i in range(n):
        eid_a, line_a = pieces[i]
        ax0, ay0 = line_a.coords[0]
        ax1, ay1 = line_a.coords[-1]
        length_a = hypot(ax1 - ax0, ay1 - ay0)
        ux, uy = (ax1 - ax0) / length_a, (ay1 - ay0) / length_a
        for j in range(i + 1, n):
            eid_b, line_b = pieces[j]
            if eid_a == eid_b:
                # Edges of the same source polyline are not independent wall faces.
                continue
            bx0, by0 = line_b.coords[0]
            bx1, by1 = line_b.coords[-1]
            length_b = hypot(bx1 - bx0, by1 - by0)
            vx, vy = (bx1 - bx0) / length_b, (by1 - by0) / length_b
            dot = min(1., abs(ux * vx + uy * vy))
            angle = degrees(acos(dot))
            if angle > angle_tolerance_degrees:
                continue
            signed0 = ux * (by0 - ay0) - uy * (bx0 - ax0)
            signed1 = ux * (by1 - ay0) - uy * (bx1 - ax0)
            # Require near-parallel, essentially constant perpendicular distance
            # so slanted/intersecting edges do not create a false thickness.
            gap = abs((signed0 + signed1) / 2)
            if not min_gap <= gap <= max_gap:
                continue
            if abs(signed0 - signed1) > max(min_gap, gap * 0.10):
                continue
            t0 = ux * (bx0 - ax0) + uy * (by0 - ay0)
            t1 = ux * (bx1 - ax0) + uy * (by1 - ay0)
            overlap = min(length_a, max(t0, t1)) - max(0, min(t0, t1))
            if overlap < min_overlap:
                continue
            if len(results) >= max_candidates:
                raise GeometryInputError("Wall-gap candidate budget exceeded")
            results.append(WallGapCandidate(
                frame_id=frame_id, first_entity_id=eid_a, second_entity_id=eid_b,
                gap_source_units=gap, overlap_source_units=overlap,
                angular_deviation_degrees=angle,
            ))
    results.sort(key=lambda c: (c.first_entity_id, c.second_entity_id,
                                c.gap_source_units))
    return WallGapResult(source_sha256=drawing.source_sha256, frame_id=frame_id,
                         candidates=results, issues=issues)
