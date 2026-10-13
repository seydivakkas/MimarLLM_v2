"""Evidence-gated, single-plan spatial adjacency; NOT fire-escape routing.

Only explicitly reviewed FaceCandidate polygons and independently identified
native CAD/PDF opening markers can create graph edges. A connectivity path
means topological *potential passage*, not an unobstructed walked route.
"""
from __future__ import annotations

from enum import Enum
from math import isfinite
from typing import Literal

import networkx as nx
from pydantic import BaseModel, ConfigDict, Field, model_validator
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from mimarllm.core.ir import DrawingIR, EvidenceOrigin, PrimitiveKind
from mimarllm.geometry.spatial import GeometryAnalysis

EXTERIOR_ID = "__EXTERIOR__"


class TopologyInputError(ValueError):
    """Invalid or unsafe geometry/space provenance. No graph is published."""


class SpaceKind(str, Enum):
    ROOM = "ROOM"
    CORRIDOR = "CORRIDOR"
    BALCONY = "BALCONY"
    STAIR = "STAIR"
    LANDING = "LANDING"


class PassageKind(str, Enum):
    DOOR = "DOOR"
    ARCHWAY = "ARCHWAY"
    OPEN_PASSAGE = "OPEN_PASSAGE"
    EXTERIOR_DOOR = "EXTERIOR_DOOR"


class SpaceReview(BaseModel):
    """Explicit human semantic declaration tied to a Shapely face."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    space_id: str = Field(min_length=1)
    face_id: str = Field(min_length=1)
    kind: SpaceKind
    reviewer_id: str = Field(min_length=1)
    label: str | None = None
    floor_label: str | None = None


class PassageReview(BaseModel):
    """A manually reviewed crossing with a nearby ORIGINAL native source marker.

    The line represents a user's passage-centerline annotation; it is NOT
    drawn from room centroids or inferred from a layer/text label.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)
    passage_id: str = Field(min_length=1)
    from_space_id: str = Field(min_length=1)
    to_space_id: str = Field(min_length=1)
    kind: PassageKind
    reviewer_id: str = Field(min_length=1)
    supporting_entity_ids: tuple[str, ...] = Field(min_length=1)
    path_endpoints: tuple[tuple[float, float], tuple[float, float]]
    opening_reviewed: bool = True

    @model_validator(mode="after")
    def coherent(self) -> "PassageReview":
        if self.from_space_id == self.to_space_id:
            raise ValueError("A passage must join distinct spaces")
        if self.to_space_id == EXTERIOR_ID and self.kind != PassageKind.EXTERIOR_DOOR:
            raise ValueError("Exterior passage must be explicitly EXTERIOR_DOOR")
        if self.kind == PassageKind.EXTERIOR_DOOR and self.to_space_id != EXTERIOR_ID:
            raise ValueError("EXTERIOR_DOOR must terminate at exterior")
        if (not all(isfinite(v) for p in self.path_endpoints for v in p)
                or len(set(self.supporting_entity_ids)) != len(self.supporting_entity_ids)
                or any(not s.strip() for s in self.supporting_entity_ids)):
            raise ValueError("Invalid passage geometry or supporting IDs")
        return self


class TopologyIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    passage_id: str | None = None
    space_ids: tuple[str, ...] = ()
    detail: str


class SpaceNode(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    space_id: str
    kind: str
    face_id: str | None = None
    boundary_entity_ids: tuple[str, ...] = ()
    reviewer_id: str | None = None
    label: str | None = None


class PassageEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    passage_id: str
    from_space_id: str
    to_space_id: str
    kind: PassageKind
    supporting_entity_ids: tuple[str, ...]
    reviewer_id: str
    boundary_crossing_point: tuple[float, float]
    status: Literal["REVIEWED_GEOMETRIC_ADJACENCY"] = "REVIEWED_GEOMETRIC_ADJACENCY"


class TopologyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drawing_sha256: str
    frame_id: str
    nodes: list[SpaceNode] = Field(default_factory=list)
    edges: list[PassageEdge] = Field(default_factory=list)
    issues: list[TopologyIssue] = Field(default_factory=list)
    components: list[tuple[str, ...]] = Field(default_factory=list)
    articulation_space_ids: list[str] = Field(default_factory=list)
    bridge_passage_ids: list[str] = Field(default_factory=list)
    exterior_reachable_space_ids: list[str] = Field(default_factory=list)
    no_confirmed_exterior_path_space_ids: list[str] = Field(default_factory=list)


class TopologyPath(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    from_space_id: str
    to_space_id: str
    space_ids: tuple[str, ...]
    passage_ids: tuple[str, ...]
    note: Literal["TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE"] = (
        "TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE"
    )


_NATIVE_SUPPORT = {
    "INSERT", "LINE", "LWPOLYLINE", "ARC",
    "PDF_LINE", "PDF_RECT", "PDF_CURVE",
}


def _network(result: TopologyResult) -> nx.MultiGraph:
    g = nx.MultiGraph()
    for node in result.nodes:
        g.add_node(node.space_id)
    for edge in result.edges:
        g.add_edge(edge.from_space_id, edge.to_space_id, key=edge.passage_id)
    return g


def shortest_passage_path(
    result: TopologyResult, source_space_id: str, target_space_id: str,
) -> TopologyPath | None:
    """Deterministic fewest-edges route; never a fire-escape metric."""
    graph = _network(result)
    if source_space_id not in graph or target_space_id not in graph:
        raise TopologyInputError("Unknown topology source/target")
    simple = nx.Graph(graph)
    try:
        space_ids = nx.shortest_path(simple, source_space_id, target_space_id)
    except nx.NetworkXNoPath:
        return None
    passages = tuple(
        min(graph[a][b].keys())
        for a, b in zip(space_ids, space_ids[1:])
    )
    return TopologyPath(
        from_space_id=source_space_id,
        to_space_id=target_space_id,
        space_ids=tuple(space_ids), passage_ids=passages,
    )


def build_topology(
    drawing: DrawingIR,
    geometry: GeometryAnalysis,
    spaces: list[SpaceReview],
    passages: list[PassageReview],
    *,
    include_exterior: bool = True,
    coordinate_tolerance: float = 1e-7,
    support_distance_source_units: float = .1,
    max_spaces: int = 300,
    max_passages: int = 1000,
    max_space_pairs: int = 45_000,
) -> TopologyResult:
    """Build a reviewed source-evidenced adjacency graph, no automatic doors.

    *Space* declarations bind exact Shapely face IDs; overlapping interiors,
    snapped faces, invalid coordinates and cross-frame source selections fail.
    Portal defects are returned as issues and **do not become graph edges**.
    """
    if (not (isfinite(coordinate_tolerance) and coordinate_tolerance > 0)
            or not (isfinite(support_distance_source_units)
                    and support_distance_source_units >= 0)
            or min(max_spaces, max_passages) < 1 or max_space_pairs < 0):
        raise TopologyInputError("Invalid topology limits")
    if len(spaces) > max_spaces or len(passages) > max_passages:
        raise TopologyInputError("Topology node/edge budget exceeded")
    if len(spaces) * (len(spaces) - 1) // 2 > max_space_pairs:
        raise TopologyInputError("Topology face pair-check budget exceeded")
    if geometry.source_sha256 != drawing.source_sha256:
        raise TopologyInputError("Geometry source hash differs from DrawingIR")
    if geometry.frame_id not in {f.frame_id for f in drawing.frames}:
        raise TopologyInputError("Geometry references unavailable coordinate frame")
    if geometry.snapped_for_candidates_only:
        raise TopologyInputError("Snapped candidate faces cannot create reviewed topology")

    faces = {face.face_id: face for face in geometry.faces}
    entities = {e.entity_id: e for e in drawing.entities}
    if len(faces) != len(geometry.faces):
        raise TopologyInputError("Duplicate geometry face IDs")

    ids = [space.space_id for space in spaces]
    if len(ids) != len(set(ids)) or EXTERIOR_ID in ids:
        raise TopologyInputError("Duplicate/reserved space ID")
    if len({s.face_id for s in spaces}) != len(spaces):
        raise TopologyInputError("Two reviewed spaces refer to the same face")
    if len({p.passage_id for p in passages}) != len(passages):
        raise TopologyInputError("Duplicate passage ID")

    reviewed: dict[str, Polygon] = {}
    face_for: dict[str, object] = {}
    for space in spaces:
        face = faces.get(space.face_id)
        if face is None:
            raise TopologyInputError(f"Space {space.space_id} is not a known face")
        if face.frame_id != geometry.frame_id or not face.boundary_entity_ids:
            raise TopologyInputError("Space face has unknown geometry/frame/source")
        for eid in face.boundary_entity_ids:
            if eid not in entities or entities[eid].frame_id != geometry.frame_id:
                raise TopologyInputError("Face cannot be traced to native drawing entities")
        polygon = Polygon(face.exterior, holes=face.holes)
        if not polygon.is_valid or polygon.is_empty or polygon.area <= coordinate_tolerance**2:
            raise TopologyInputError("Reviewed space polygon is invalid")
        reviewed[space.space_id] = polygon
        face_for[space.space_id] = face

    # No coincident, overlapping, or contained spaces: those imply ambiguous
    # room coverage and would create fictitious paths through the same floor.
    sorted_ids = sorted(reviewed)
    for index, a in enumerate(sorted_ids):
        for b in sorted_ids[index + 1:]:
            if reviewed[a].intersection(reviewed[b]).area > coordinate_tolerance**2:
                raise TopologyInputError(f"Overlapping reviewed interiors: {a}, {b}")

    selected_boundary_ids = {
        eid for space in spaces for eid in face_for[space.space_id].boundary_entity_ids
    }
    for issue in geometry.issues:
        if issue.code in {
            "OVERLAPPING_SEGMENTS", "SELF_INTERSECTING_SOURCE",
            "INVALID_RING", "BOUNDARY_SOURCE_UNRESOLVED",
            "SNAPPED_TOPOLOGY_UNVERIFIED",
        } and (not issue.entity_ids
               or set(issue.entity_ids) & selected_boundary_ids):
            raise TopologyInputError(
                f"Reviewed face includes ambiguous source geometry: {issue.code}"
            )

    result = TopologyResult(
        drawing_sha256=drawing.source_sha256,
        frame_id=geometry.frame_id,
        nodes=[
            SpaceNode(
                space_id=s.space_id, kind=s.kind.value, face_id=s.face_id,
                reviewer_id=s.reviewer_id, label=s.label,
                boundary_entity_ids=face_for[s.space_id].boundary_entity_ids,
            ) for s in sorted(spaces, key=lambda s: s.space_id)
        ],
    )
    if include_exterior:
        result.nodes.append(SpaceNode(space_id=EXTERIOR_ID, kind="EXTERIOR"))

    def reject(portal: PassageReview, code: str, detail: str) -> None:
        result.issues.append(TopologyIssue(
            code=code, passage_id=portal.passage_id,
            space_ids=(portal.from_space_id, portal.to_space_id),
            detail=detail,
        ))

    for passage in sorted(passages, key=lambda p: p.passage_id):
        is_exterior = passage.to_space_id == EXTERIOR_ID
        if (passage.from_space_id not in reviewed
                or (is_exterior and not include_exterior)
                or (not is_exterior and passage.to_space_id not in reviewed)):
            reject(passage, "UNKNOWN_SPACE", "Passage references unreviewed/unknown space")
            continue
        if not passage.opening_reviewed:
            reject(passage, "OPENING_UNREVIEWED", "Opening evidence not confirmed")
            continue
        supporting = [entities.get(eid) for eid in passage.supporting_entity_ids]
        if (any(entity is None for entity in supporting)
                or any(entity.frame_id != geometry.frame_id
                       for entity in supporting if entity is not None)
                or any(entity.origin not in {
                    EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE
                } or entity.type_candidate not in _NATIVE_SUPPORT
                       for entity in supporting if entity is not None)):
            reject(passage, "UNSUPPORTED_OPENING_SOURCE",
                   "Opening marker missing, from another frame, or non-native text/OCR")
            continue

        start, end = map(Point, passage.path_endpoints)
        travel = LineString(passage.path_endpoints)
        if travel.length <= coordinate_tolerance:
            reject(passage, "DEGENERATE_PASSAGE", "Path endpoints coincide")
            continue
        first = reviewed[passage.from_space_id]
        if not first.contains(start):
            reject(passage, "SOURCE_ENDPOINT_NOT_INTERIOR",
                   "Passage start must lie inside the reviewed source surface")
            continue
        if is_exterior:
            second = None
            if any(poly.covers(end) for poly in reviewed.values()):
                reject(passage, "EXTERIOR_ENDPOINT_NOT_OUTSIDE",
                       "Exterior endpoint must be outside every reviewed space")
                continue
            boundary = first.boundary
        else:
            second = reviewed[passage.to_space_id]
            if not second.contains(end):
                reject(passage, "TARGET_ENDPOINT_NOT_INTERIOR",
                       "Passage end must lie inside the reviewed destination surface")
                continue
            common = first.boundary.intersection(second.boundary)
            if common.length <= coordinate_tolerance:
                reject(passage, "NO_SHARED_BOUNDARY",
                       "Reviewed spaces do not have a positive-length common edge")
                continue
            boundary = common

        crossing = travel.intersection(boundary)
        if (crossing.geom_type != "Point"
                or travel.difference(
                    first.union(second) if second is not None else first
                ).length > (
                    coordinate_tolerance if second is not None
                    else max(coordinate_tolerance, travel.length)
                )):
            reject(passage, "INVALID_PASSAGE_CROSSING",
                   "Passage must cross exactly one suitable boundary point")
            continue
        if any(
            travel.intersection(polygon).length > coordinate_tolerance
            for sid, polygon in reviewed.items()
            if sid not in {passage.from_space_id, passage.to_space_id}
        ):
            reject(passage, "THIRD_SPACE_CROSSING",
                   "Opening path crosses an additional reviewed space")
            continue
        if not is_exterior:
            # Refuse a long nonlocal jump whose line crosses other boundary
            # components; a real shared-boundary passage stays in two surfaces.
            if travel.difference(first.union(second)).length > coordinate_tolerance:
                reject(passage, "PASSAGE_OUTSIDE_SPACES",
                       "Passage line leaves the reviewed adjacent surfaces")
                continue
        else:
            # Exactly one exit crossing of the source polygon. A simple
            # geometry witness, not an exit width, open-direction or code test.
            if travel.intersection(first.boundary).geom_type != "Point":
                reject(passage, "INVALID_EXTERIOR_CROSSING",
                       "Exit path crosses source boundary more than once")
                continue

        if any(
            # Source marker must be localized at the crossing and is still
            # only reviewer-declared proof of semantic opening.
            Point(entity.geometry.points[0]).distance(crossing)
            > support_distance_source_units
            if entity.geometry.kind == PrimitiveKind.POINT
            else LineString(
                list(entity.geometry.points)
                + ([entity.geometry.points[0]] if entity.geometry.closed else [])
            ).distance(crossing) > support_distance_source_units
            for entity in supporting if entity is not None
        ):
            reject(passage, "OPENING_SOURCE_TOO_FAR",
                   "A declared opening source does not lie at the boundary crossing")
            continue
        result.edges.append(PassageEdge(
            passage_id=passage.passage_id,
            from_space_id=passage.from_space_id,
            to_space_id=passage.to_space_id,
            kind=passage.kind, supporting_entity_ids=passage.supporting_entity_ids,
            reviewer_id=passage.reviewer_id,
            boundary_crossing_point=(float(crossing.x), float(crossing.y)),
        ))

    graph = _network(result)
    result.components = sorted(
        (tuple(sorted(group)) for group in nx.connected_components(graph)),
        key=lambda group: group[0],
    )
    simple = nx.Graph(graph)
    result.articulation_space_ids = sorted(nx.articulation_points(simple))
    # In MultiGraph, removing one of two parallel independent door edges
    # never disconnects the graph. nx.bridges handles multiedges correctly.
    result.bridge_passage_ids = sorted(
        next(iter(graph[a][b]))
        for a, b in nx.bridges(graph)
        if len(graph[a][b]) == 1
    )
    if include_exterior:
        reachable = nx.node_connected_component(graph, EXTERIOR_ID)
        result.exterior_reachable_space_ids = sorted(
            space_id for space_id in reachable if space_id != EXTERIOR_ID
        )
        result.no_confirmed_exterior_path_space_ids = sorted(
            space_id for space_id in reviewed if space_id not in reachable
        )
    return result
