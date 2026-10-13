"""Topology acceptance: reviewed faces and located openings only, no egress claim."""
from __future__ import annotations

import ezdxf
import pytest
from pydantic import ValidationError

from mimarllm.core.ir import (
    CoordinateFrame, CoordinateKind, DrawingEntity, DrawingIR, EvidenceOrigin,
    GeometryPrimitive, PrimitiveKind, SourceKind, SourceReference, YDirection,
)
from mimarllm.geometry.spatial import analyze_geometry
from mimarllm.geometry.topology import (
    EXTERIOR_ID, PassageKind, PassageReview, SpaceKind,
    SpaceReview, TopologyInputError, build_topology, shortest_passage_path,
)
from mimarllm.importers.dxf import parse_dxf

SHA = "a" * 64
FRAME = "cad:Model"


def scene():
    # Four continuous adjacent floor regions in a single source frame.
    pieces = []
    for index in range(4):
        x0, x1 = index * 5, (index + 1) * 5
        pieces.extend([((x0, 0), (x1, 0)), ((x1, 6), (x0, 6))])
    for index in range(5):
        x = index * 5
        pieces.append(((x, 0), (x, 6)))
    lines = [
        DrawingEntity(
            entity_id=f"wall{i}", frame_id=FRAME,
            geometry=GeometryPrimitive(kind=PrimitiveKind.SEGMENT, points=(a, b)),
            source=SourceReference(document_sha256=SHA, source_kind=SourceKind.DXF,
                                   frame_id=FRAME, view_id="Model",
                                   cad_handle=f"{i+10:X}"),
            origin=EvidenceOrigin.CAD_NATIVE,
            type_candidate="LINE",
        )
        for i, (a, b) in enumerate(pieces)
    ]
    markers = [
        DrawingEntity(
            entity_id=f"door{x}", frame_id=FRAME,
            geometry=GeometryPrimitive(kind=PrimitiveKind.POINT, points=((x, 3),)),
            source=SourceReference(document_sha256=SHA, source_kind=SourceKind.DXF,
                                   frame_id=FRAME, view_id="Model",
                                   cad_handle=f"A{x:X}"),
            origin=EvidenceOrigin.CAD_NATIVE, type_candidate="INSERT",
        )
        for x in (5, 10, 15, 20)
    ]
    drawing = DrawingIR(
        drawing_id="four-synthetic-cells", source_sha256=SHA,
        source_kind=SourceKind.DXF, parser_version="test-v0.1",
        frames=[CoordinateFrame(frame_id=FRAME, kind=CoordinateKind.CAD_UNIT,
                                y_direction=YDirection.UP, view_id="Model")],
        entities=lines + markers,
    )
    geometry = analyze_geometry(drawing, FRAME)
    assert len(geometry.faces) == 4
    reviews = [
        SpaceReview(space_id=sid, face_id=face.face_id, kind=kind,
                    reviewer_id="fixture-reviewer", label=sid)
        for sid, face, kind in zip(
            ("bedroom", "corridor", "landing", "balcony"),
            geometry.faces,
            (SpaceKind.ROOM, SpaceKind.CORRIDOR, SpaceKind.LANDING, SpaceKind.BALCONY),
        )
    ]
    return drawing, geometry, reviews


def portal(name: str, a: str, b: str, x: int,
           *, kind: PassageKind = PassageKind.DOOR) -> PassageReview:
    return PassageReview(
        passage_id=name, from_space_id=a, to_space_id=b,
        kind=kind, reviewer_id="fixture-reviewer",
        supporting_entity_ids=(f"door{x}",),
        path_endpoints=((x-1, 3), (x+1, 3)),
    )


def doors():
    return [
        portal("p1", "bedroom", "corridor", 5),
        portal("p2", "corridor", "landing", 10, kind=PassageKind.ARCHWAY),
        portal("p3", "landing", "balcony", 15, kind=PassageKind.OPEN_PASSAGE),
        portal("p4", "balcony", EXTERIOR_ID, 20, kind=PassageKind.EXTERIOR_DOOR),
    ]


def test_chained_rooms_balcony_landing_exterior_and_provenance():
    drawing, geometry, rooms = scene()
    out = build_topology(drawing, geometry, rooms, doors())
    assert len(out.nodes) == 5
    assert len(out.edges) == 4
    assert out.drawing_sha256 == SHA
    assert out.frame_id == FRAME
    assert out.exterior_reachable_space_ids == sorted(s.space_id for s in rooms)
    assert out.no_confirmed_exterior_path_space_ids == []
    assert all(n.boundary_entity_ids for n in out.nodes if n.kind != "EXTERIOR")
    path = shortest_passage_path(out, "bedroom", EXTERIOR_ID)
    assert path is not None
    assert path.space_ids == ("bedroom", "corridor", "landing", "balcony", EXTERIOR_ID)
    assert path.passage_ids == ("p1", "p2", "p3", "p4")
    assert path.note == "TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE"
    assert {edge.boundary_crossing_point for edge in out.edges} == {
        (5, 3), (10, 3), (15, 3), (20, 3)
    }
    assert out.articulation_space_ids == ["balcony", "corridor", "landing"]
    assert out.bridge_passage_ids == ["p1", "p2", "p3", "p4"]


def test_nearby_rooms_are_not_assumed_connected_without_reviewed_door():
    drawing, geometry, rooms = scene()
    out = build_topology(drawing, geometry, rooms, [])
    assert out.edges == []
    assert shortest_passage_path(out, "bedroom", "corridor") is None
    assert out.exterior_reachable_space_ids == []
    assert out.no_confirmed_exterior_path_space_ids == sorted(s.space_id for s in rooms)


def test_missing_exit_does_not_claim_fire_failure():
    drawing, geometry, rooms = scene()
    out = build_topology(drawing, geometry, rooms, doors()[:3])
    assert len(out.edges) == 3
    assert not out.exterior_reachable_space_ids
    assert set(out.no_confirmed_exterior_path_space_ids) == set(s.space_id for s in rooms)
    assert not hasattr(out, "escape_distance_metres")
    assert not hasattr(out, "compliant")


def test_unreviewed_portal_has_explicit_issue_no_edge():
    drawing, geometry, rooms = scene()
    passage = doors()[0].model_copy(update={"opening_reviewed": False})
    out = build_topology(drawing, geometry, rooms, [passage])
    assert not out.edges
    assert any(issue.code == "OPENING_UNREVIEWED" for issue in out.issues)


def test_wrong_door_location_never_creates_ghost_passage():
    drawing, geometry, rooms = scene()
    wrongly_marked = doors()[0].model_copy(
        update={"supporting_entity_ids": ("door15",)}
    )
    out = build_topology(drawing, geometry, rooms, [wrongly_marked])
    assert out.edges == []
    assert [i.code for i in out.issues] == ["OPENING_SOURCE_TOO_FAR"]


def test_false_corner_and_nonadjacent_room_portals_are_rejected():
    drawing, geometry, rooms = scene()
    jump = PassageReview(
        passage_id="ghost", from_space_id="bedroom", to_space_id="landing",
        kind=PassageKind.DOOR, reviewer_id="reviewer",
        supporting_entity_ids=("door10",),
        path_endpoints=((4, 3), (11, 3)),
    )
    out = build_topology(drawing, geometry, rooms, [jump])
    assert not out.edges
    assert [x.code for x in out.issues] == ["NO_SHARED_BOUNDARY"]


def test_ocr_or_text_never_counts_as_opening_marker():
    drawing, geometry, rooms = scene()
    fake = drawing.entities[-4].model_copy(update={
        "entity_id": "ocr-ghost", "origin": EvidenceOrigin.OCR_CANDIDATE,
        "type_candidate": "PDF_OCR_TEXT_QUAD",
    })
    drawing.entities.append(fake)
    out = build_topology(drawing, geometry, rooms, [
        doors()[0].model_copy(update={"supporting_entity_ids": ("ocr-ghost",)})
    ])
    assert not out.edges
    assert [i.code for i in out.issues] == ["UNSUPPORTED_OPENING_SOURCE"]


def test_missing_marker_and_wrong_frame_rejected():
    drawing, geometry, rooms = scene()
    out = build_topology(drawing, geometry, rooms, [
        doors()[0].model_copy(update={"supporting_entity_ids": ("missing",)})
    ])
    assert not out.edges
    assert [i.code for i in out.issues] == ["UNSUPPORTED_OPENING_SOURCE"]
    new_frame = CoordinateFrame(frame_id="cad:Paper", kind=CoordinateKind.CAD_UNIT,
                                y_direction=YDirection.UP, view_id="Paper")
    drawing.frames.append(new_frame)
    marker = drawing.entities[-1]
    source = marker.source.model_copy(update={
        "frame_id": "cad:Paper", "view_id": "Paper"
    })
    drawing.entities[-1] = marker.model_copy(
        update={"source": source, "frame_id": "cad:Paper"}
    )
    out = build_topology(drawing, geometry, rooms, [
        doors()[3]
    ])
    assert not out.edges
    assert [i.code for i in out.issues] == ["UNSUPPORTED_OPENING_SOURCE"]


def test_wrong_geometry_hash_rejected():
    drawing, geometry, rooms = scene()
    modified = geometry.model_copy(update={"source_sha256": "f" * 64})
    with pytest.raises(TopologyInputError, match="hash"):
        build_topology(drawing, modified, rooms, doors())


def test_wrong_face_and_reserved_ids_and_duplicate_passage_rejected():
    drawing, geometry, rooms = scene()
    invalid = rooms[0].model_copy(update={"face_id": "not-found"})
    with pytest.raises(TopologyInputError, match="known face"):
        build_topology(drawing, geometry, [invalid, *rooms[1:]], [])
    reserved = rooms[0].model_copy(update={"space_id": EXTERIOR_ID})
    with pytest.raises(TopologyInputError, match="reserved"):
        build_topology(drawing, geometry, [reserved, *rooms[1:]], [])
    with pytest.raises(TopologyInputError, match="Duplicate passage"):
        build_topology(drawing, geometry, rooms, [doors()[0], doors()[0]])


def test_snapped_faces_are_unverifiable_topology_source():
    drawing, geometry, rooms = scene()
    altered = geometry.model_copy(update={"snapped_for_candidates_only": True})
    with pytest.raises(TopologyInputError, match="Snapped"):
        build_topology(drawing, altered, rooms, doors())


def test_overlapping_room_interiors_rejected():
    drawing, geometry, rooms = scene()
    faces = [face.model_copy() for face in geometry.faces]
    faces[1] = faces[1].model_copy(update={
        "exterior": faces[0].exterior,
        "source_area_squared": faces[0].source_area_squared,
    })
    overlapping = geometry.model_copy(update={"faces": faces})
    with pytest.raises(TopologyInputError, match="source geometry"):
        build_topology(drawing, overlapping, rooms, [])


def test_two_parallel_doors_are_independent_not_bridges():
    drawing, geometry, rooms = scene()
    second = portal("another", "bedroom", "corridor", 5)
    out = build_topology(drawing, geometry, rooms, [doors()[0], second])
    assert len(out.edges) == 2
    assert out.bridge_passage_ids == []
    assert shortest_passage_path(out, "bedroom", "corridor").passage_ids == ("another",)


def test_marked_stair_is_only_single_frame_space_not_three_d_egress():
    drawing, geometry, rooms = scene()
    altered = rooms[2].model_copy(update={"kind": SpaceKind.STAIR})
    out = build_topology(drawing, geometry, [*rooms[:2], altered, rooms[3]], doors())
    assert next(n.kind for n in out.nodes if n.space_id == "landing") == "STAIR"
    assert out.frame_id == FRAME
    assert not hasattr(out, "interfloor_path")
    assert not hasattr(out, "walking_distance_m")


def test_door_to_outside_requires_explicit_geometry_and_type():
    drawing, geometry, rooms = scene()
    with pytest.raises(ValidationError, match="EXTERIOR_DOOR"):
        PassageReview(
            passage_id="bad", from_space_id="balcony", to_space_id=EXTERIOR_ID,
            kind=PassageKind.DOOR, reviewer_id="reviewer",
            supporting_entity_ids=("door20",),
            path_endpoints=((19, 3), (21, 3)),
        )
    false_exit = doors()[3].model_copy(update={
        "path_endpoints": ((18, 3), (19, 3)),
    })
    out = build_topology(drawing, geometry, rooms, [false_exit])
    assert not out.edges
    assert [issue.code for issue in out.issues] == ["EXTERIOR_ENDPOINT_NOT_OUTSIDE"]


def test_invalid_portal_crossing_and_degenerate_endpoints_fail_closed():
    drawing, geometry, rooms = scene()
    wrong = doors()[0].model_copy(update={
        "path_endpoints": ((4, 1), (6, 3))
    })
    out = build_topology(drawing, geometry, rooms, [wrong])
    assert out.edges == []
    assert out.issues[0].code in {"OPENING_SOURCE_TOO_FAR", "INVALID_PASSAGE_CROSSING"}

    degenerate = doors()[0].model_copy(update={
        "path_endpoints": ((4, 3), (4, 3))
    })
    out = build_topology(drawing, geometry, rooms, [degenerate])
    assert not out.edges
    assert [issue.code for issue in out.issues] == ["DEGENERATE_PASSAGE"]


def test_limits_and_space_id_validation():
    drawing, geometry, rooms = scene()
    with pytest.raises(TopologyInputError, match="budget"):
        build_topology(drawing, geometry, rooms, doors(), max_spaces=2)
    with pytest.raises(TopologyInputError, match="pair-check"):
        build_topology(drawing, geometry, rooms, doors(), max_space_pairs=2)
    with pytest.raises(TopologyInputError, match="budget"):
        build_topology(drawing, geometry, rooms, doors(), max_passages=1)
    with pytest.raises(TopologyInputError, match="Unknown topology"):
        shortest_passage_path(
            build_topology(drawing, geometry, rooms, []), "ghost", "bedroom"
        )


def test_topology_json_roundtrip():
    drawing, geometry, rooms = scene()
    out = build_topology(drawing, geometry, rooms, doors())
    assert type(out).model_validate_json(out.model_dump_json()) == out


def test_real_ezdxf_saved_loaded_then_reviewed_adjacency(tmp_path):
    doc = ezdxf.new("R2013")
    space = doc.modelspace()
    for x0, x1 in ((0, 5), (5, 10)):
        space.add_line((x0, 0), (x1, 0))
        space.add_line((x0, 6), (x1, 6))
    for x in (0, 5, 10):
        space.add_line((x, 0), (x, 6))
    marker_block = doc.blocks.new("MANUALLY_REVIEWED_OPENING")
    # Empty block placement is a geometric marker, not automatic door proof.
    space.add_blockref("MANUALLY_REVIEWED_OPENING", (5, 3))
    filename = tmp_path / "two_spatial_rooms.dxf"
    doc.saveas(filename)
    imported = parse_dxf(filename)
    analysis = analyze_geometry(imported.drawing, "cad:Model")
    assert len(analysis.faces) == 2
    reviews = [
        SpaceReview(space_id=sid, face_id=face.face_id,
                    kind=SpaceKind.ROOM if index == 0 else SpaceKind.CORRIDOR,
                    reviewer_id="human-reviewed-synthetic")
        for index, (sid, face) in enumerate(zip(("room", "hall"), analysis.faces))
    ]
    marker = next(e for e in imported.drawing.entities
                  if e.type_candidate == "INSERT")
    edge = PassageReview(
        passage_id="d1", from_space_id="room", to_space_id="hall",
        kind=PassageKind.DOOR, reviewer_id="human-reviewed-synthetic",
        supporting_entity_ids=(marker.entity_id,),
        path_endpoints=((4, 3), (6, 3)),
    )
    graph = build_topology(imported.drawing, analysis, reviews, [edge])
    assert len(graph.edges) == 1
    assert graph.edges[0].supporting_entity_ids == (marker.entity_id,)
    assert graph.drawing_sha256 == imported.drawing.source_sha256
    assert shortest_passage_path(graph, "room", "hall").passage_ids == ("d1",)


def test_forged_geometry_face_with_correct_hash_still_rejected():
    drawing, geometry, rooms = scene()
    faces = list(geometry.faces)
    changed = [(x + .25, y) for x, y in faces[0].exterior]
    faces[0] = faces[0].model_copy(update={"exterior": tuple(changed)})
    forged = geometry.model_copy(update={"faces": faces})
    assert forged.source_sha256 == drawing.source_sha256
    with pytest.raises(TopologyInputError, match="source geometry"):
        build_topology(drawing, forged, rooms, doors())


def test_floor_labels_from_different_levels_are_not_connected_by_2d_plan():
    drawing, geometry, rooms = scene()
    labeled = [
        s.model_copy(update={"floor_label": "floor-1" if i < 2 else "floor-2"})
        for i, s in enumerate(rooms)
    ]
    with pytest.raises(TopologyInputError, match="floor labels"):
        build_topology(drawing, geometry, labeled, doors())


def test_forged_face_source_ids_are_rejected():
    drawing, geometry, rooms = scene()
    faces = list(geometry.faces)
    faces[0] = faces[0].model_copy(
        update={"boundary_entity_ids": ("door5",)}
    )
    forged = geometry.model_copy(update={"faces": faces})
    with pytest.raises(TopologyInputError, match="source geometry"):
        build_topology(drawing, forged, rooms, doors())
