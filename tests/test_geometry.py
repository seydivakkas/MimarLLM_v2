"""Deterministic Shapely geometry tests: real source references, no legal PASS."""
from __future__ import annotations

from copy import deepcopy

import ezdxf
import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.ir import (
    CoordinateFrame, CoordinateKind, DrawingEntity, DrawingIR,
    EvidenceOrigin, GeometryPrimitive, PrimitiveKind, SourceKind,
    SourceReference, YDirection,
)
from mimarllm.core.units import UnitCalibration
from mimarllm.geometry.spatial import (
    GeometryInputError, GeometryReviewStatus, analyze_geometry, assess_area,
)
from mimarllm.geometry.walls import find_parallel_edge_gaps
from mimarllm.importers.dxf import parse_dxf
from mimarllm.importers.pdf_ir import parse_pdf_ir

HASH = "a" * 64
FRAME = "cad:Model"


def make_drawing(segments: list[tuple[tuple[float, float], tuple[float, float]]],
                 *, calibrated=False, frame_id=FRAME) -> DrawingIR:
    entities = []
    for i, (a, b) in enumerate(segments):
        eid = f"s{i}"
        entities.append(DrawingEntity(
            entity_id=eid, frame_id=frame_id,
            source=SourceReference(
                document_sha256=HASH, source_kind=SourceKind.DXF,
                frame_id=frame_id, view_id="Model", cad_handle=f"{i+10:X}",
            ),
            geometry=GeometryPrimitive(kind=PrimitiveKind.SEGMENT,
                                       points=(a, b)),
            layer="A-WALL", origin=EvidenceOrigin.CAD_NATIVE,
            type_candidate="LINE",
        ))
    calibration = (UnitCalibration.from_dxf_insunits(6, user_confirmed=True)
                   if calibrated else UnitCalibration.from_dxf_insunits(6))
    return DrawingIR(
        drawing_id="synthetic", source_sha256=HASH, source_kind=SourceKind.DXF,
        parser_version="synthetic-test", frames=[
            CoordinateFrame(frame_id=frame_id, kind=CoordinateKind.CAD_UNIT,
                            view_id="Model", y_direction=YDirection.UP)],
        calibration=calibration, calibration_frame_id=frame_id,
        entities=entities,
    )


@pytest.fixture()
def two_rooms():
    # Two separate 5 x 6 closed rectangles sharing one partition.
    segs = [
        ((0, 0), (5, 0)),   # s0 left bottom
        ((5, 0), (10, 0)),  # s1 right bottom
        ((10, 0), (10, 6)), # s2 right exterior
        ((10, 6), (5, 6)),  # s3 right top
        ((5, 6), (0, 6)),   # s4 left top
        ((0, 6), (0, 0)),   # s5 left exterior
        ((5, 0), (5, 6)),   # s6 partition
    ]
    return make_drawing(segs)


def test_two_closed_faces_from_shared_partition_are_only_candidates(two_rooms):
    result = analyze_geometry(two_rooms, FRAME)
    assert len(result.faces) == 2
    assert [f.source_area_squared for f in result.faces] == pytest.approx([30, 30])
    assert all(f.semantic_kind == "UNCLASSIFIED_FACE" for f in result.faces)
    assert all(f.status == "REVIEW_REQUIRED" for f in result.faces)
    assert all("s6" in f.boundary_entity_ids for f in result.faces)
    assert not two_rooms.findings
    assert not two_rooms.measurements


def test_closed_room_without_confirmation_has_only_source_area(two_rooms):
    room_ids = ["s0", "s4", "s5", "s6"]
    measured = assess_area(two_rooms, FRAME, room_ids, boundary_role="INTERIOR_ROOM")
    assert measured.status is GeometryReviewStatus.REVIEW_REQUIRED
    assert measured.reason_code == "BOUNDARY_UNREVIEWED"
    assert measured.source_area_squared == pytest.approx(30)
    assert measured.physical_area_m2 is None


def test_confirmed_interior_boundary_unconfirmed_scale_is_not_m2(two_rooms):
    measured = assess_area(
        two_rooms, FRAME, ["s0", "s4", "s5", "s6"],
        boundary_role="INTERIOR_ROOM", reviewer_id="architect-review-01",
    )
    assert measured.status is GeometryReviewStatus.INSUFFICIENT_EVIDENCE
    assert measured.reason_code == "CONFIRMED_PHYSICAL_SCALE_MISSING"
    assert measured.physical_area_m2 is None


def test_confirmed_boundary_and_frame_scale_give_physical_area(two_rooms):
    verified = two_rooms.model_copy(update={
        "calibration": UnitCalibration.from_dxf_insunits(6, user_confirmed=True)
    })
    measured = assess_area(
        verified, FRAME, ["s0", "s4", "s5", "s6"],
        boundary_role="INTERIOR_ROOM", reviewer_id="architect-review-01",
    )
    assert measured.status is GeometryReviewStatus.MEASURED
    assert measured.source_area_squared == pytest.approx(30)
    assert measured.physical_area_m2 == pytest.approx(30)
    assert measured.physical_area_semantics == "INTERIOR_ROOM_AREA_M2"
    assert not verified.findings


def test_external_outline_is_footprint_not_total_gross_floor(two_rooms):
    drawing = make_drawing([
        ((0, 0), (10, 0)), ((10, 0), (10, 6)),
        ((10, 6), (0, 6)), ((0, 6), (0, 0)),
    ], calibrated=True)
    result = assess_area(drawing, FRAME, ["s0", "s1", "s2", "s3"],
                         boundary_role="EXTERIOR_ENVELOPE",
                         reviewer_id="architect-review-01")
    assert result.status is GeometryReviewStatus.MEASURED
    assert result.source_area_squared == pytest.approx(60)
    assert result.physical_area_m2 == pytest.approx(60)
    assert result.physical_area_semantics == "EXTERIOR_FOOTPRINT_M2"


def test_open_boundary_refuses_area_and_reports_dangle():
    drawing = make_drawing([
        ((0, 0), (10, 0)), ((10, 0), (10, 5)),
        ((10, 5), (0, 5)),
    ], calibrated=True)
    geometry = analyze_geometry(drawing, FRAME)
    assert not geometry.faces
    assert any(issue.code in {"DANGLING_OR_OPEN_EDGE", "UNASSIGNED_CUT_EDGE"}
               for issue in geometry.issues)
    measurement = assess_area(drawing, FRAME, ["s0", "s1", "s2"],
                              boundary_role="INTERIOR_ROOM",
                              reviewer_id="architect")
    assert measurement.status is GeometryReviewStatus.REVIEW_REQUIRED
    assert measurement.physical_area_m2 is None


def test_overlap_blocks_measured_even_with_valid_outer_cycle():
    drawing = make_drawing([
        ((0, 0), (10, 0)), ((10, 0), (10, 5)),
        ((10, 5), (0, 5)), ((0, 5), (0, 0)),
        ((0, 0), (10, 0)),  # duplicate wall line
    ], calibrated=True)
    geometry = analyze_geometry(drawing, FRAME)
    assert any(issue.code == "OVERLAPPING_SEGMENTS" for issue in geometry.issues)
    measurement = assess_area(drawing, FRAME, [f"s{i}" for i in range(5)],
                              boundary_role="INTERIOR_ROOM",
                              reviewer_id="architect")
    assert measurement.status is GeometryReviewStatus.REVIEW_REQUIRED
    assert measurement.physical_area_m2 is None


def test_cross_frame_page_or_layout_cannot_be_mixed(two_rooms):
    extra = CoordinateFrame(
        frame_id="cad:Layout1", kind=CoordinateKind.CAD_UNIT,
        y_direction=YDirection.UP, view_id="Layout1",
    )
    entity = DrawingEntity(
        entity_id="extra", frame_id="cad:Layout1",
        source=SourceReference(document_sha256=HASH, source_kind=SourceKind.DXF,
                               view_id="Layout1", cad_handle="F0", frame_id="cad:Layout1"),
        geometry=GeometryPrimitive(kind=PrimitiveKind.SEGMENT,
                                   points=((0, 0), (1, 0))),
        origin=EvidenceOrigin.CAD_NATIVE, type_candidate="LINE",
    )
    doc = two_rooms.model_copy(update={"frames": [*two_rooms.frames, extra],
                                        "entities": [*two_rooms.entities, entity]})
    with pytest.raises(GeometryInputError, match="mixes"):
        analyze_geometry(doc, FRAME, entity_ids=["s0", "extra"])
    with pytest.raises(GeometryInputError, match="mixes"):
        assess_area(doc, FRAME, ["s0", "extra"], boundary_role="INTERIOR_ROOM",
                    reviewer_id="architect")


def test_other_frame_calibration_does_not_leak(two_rooms):
    extra = CoordinateFrame(
        frame_id="cad:Layout1", kind=CoordinateKind.CAD_UNIT,
        y_direction=YDirection.UP, view_id="Layout1",
    )
    doc = two_rooms.model_copy(update={
        "frames": [*two_rooms.frames, extra],
        "calibration": UnitCalibration.from_dxf_insunits(6, user_confirmed=True),
        "calibration_frame_id": "cad:Layout1",
    })
    result = assess_area(doc, FRAME, ["s0", "s4", "s5", "s6"],
                         boundary_role="INTERIOR_ROOM", reviewer_id="architect")
    assert result.status is GeometryReviewStatus.INSUFFICIENT_EVIDENCE
    assert result.physical_area_m2 is None


def test_source_selection_requires_unique_real_ids(two_rooms):
    with pytest.raises(GeometryInputError, match="unique"):
        analyze_geometry(two_rooms, FRAME, entity_ids=["s0", "s0"])
    with pytest.raises(GeometryInputError, match="Unknown selected"):
        analyze_geometry(two_rooms, FRAME, entity_ids=["ghost"])


def test_unsupported_ocr_candidate_never_makes_room():
    native = make_drawing([((0, 0), (10, 0))])
    false_entity = native.entities[0].model_copy(update={
        "entity_id": "fake-ocr", "origin": EvidenceOrigin.OCR_CANDIDATE,
    })
    native.entities.append(false_entity)
    result = analyze_geometry(native, FRAME)
    assert any(issue.code == "UNSUPPORTED_BOUNDARY_SOURCE" for issue in result.issues)
    assert not result.faces


def test_safety_budgets_reject_large_inputs(two_rooms):
    with pytest.raises(GeometryInputError, match="segment safety"):
        analyze_geometry(two_rooms, FRAME, max_segments=2)
    with pytest.raises(GeometryInputError, match="pair-check"):
        analyze_geometry(two_rooms, FRAME, max_pairs=2)
    with pytest.raises(GeometryInputError, match="Face safety"):
        analyze_geometry(two_rooms, FRAME, max_faces=1)


def test_zero_snap_default_and_nonzero_snap_never_certifies(two_rooms):
    original = analyze_geometry(two_rooms, FRAME)
    snapped = analyze_geometry(two_rooms, FRAME, snap_tolerance=0.01)
    assert not original.snapped_for_candidates_only
    assert snapped.snapped_for_candidates_only
    assert any(issue.code == "SNAPPED_TOPOLOGY_UNVERIFIED" for issue in snapped.issues)
    assert all(face.status == "REVIEW_REQUIRED" for face in snapped.faces)
    with pytest.raises(GeometryInputError, match="Invalid"):
        analyze_geometry(two_rooms, FRAME, snap_tolerance=-1)


def test_parallel_edges_are_only_gap_candidates():
    drawing = make_drawing([
        ((0, 0), (10, 0)),
        ((0, .24), (10, .24)),
        ((2, -4), (2, 4)),  # crossing, not near-parallel
    ])
    result = find_parallel_edge_gaps(
        drawing, FRAME, min_gap=.1, max_gap=.4, min_overlap=3)
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert {candidate.first_entity_id, candidate.second_entity_id} == {"s0", "s1"}
    assert candidate.gap_source_units == pytest.approx(.24)
    assert candidate.overlap_source_units == pytest.approx(10)
    assert candidate.status == "REVIEW_REQUIRED"
    assert candidate.semantic_kind == "PARALLEL_EDGE_GAP_CANDIDATE"


def test_parallel_edges_with_no_overlap_are_not_thickness():
    drawing = make_drawing([
        ((0, 0), (10, 0)), ((11, .24), (20, .24))
    ])
    result = find_parallel_edge_gaps(
        drawing, FRAME, min_gap=.1, max_gap=.4, min_overlap=1)
    assert not result.candidates


def test_duplicate_coincident_edges_are_not_wall_thickness():
    drawing = make_drawing([
        ((0, 0), (10, 0)), ((0, 0), (10, 0))
    ])
    result = find_parallel_edge_gaps(drawing, FRAME, max_gap=1, min_overlap=1)
    assert not result.candidates


def test_wall_safety_budgets_and_negative_tolerances(two_rooms):
    with pytest.raises(GeometryInputError, match="pair-check"):
        find_parallel_edge_gaps(two_rooms, FRAME, max_pairs=1)
    with pytest.raises(GeometryInputError, match="Invalid"):
        find_parallel_edge_gaps(two_rooms, FRAME, min_gap=-1)


def test_real_ezdxf_two_room_source_identity_and_inferred_scale(tmp_path):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 6
    m = doc.modelspace()
    lines = [
        ((0, 0), (5, 0)), ((5, 0), (10, 0)),
        ((10, 0), (10, 6)), ((10, 6), (5, 6)),
        ((5, 6), (0, 6)), ((0, 6), (0, 0)),
        ((5, 0), (5, 6)),
    ]
    refs = [m.add_line(a, b) for a, b in lines]
    filename = tmp_path / "two_rooms.dxf"
    doc.saveas(filename)
    drawing = parse_dxf(filename).drawing
    analysis = analyze_geometry(drawing, "cad:Model")
    assert len(analysis.faces) == 2
    assert all(face.source_area_squared == pytest.approx(30)
               for face in analysis.faces)
    assert all(face.boundary_entity_ids for face in analysis.faces)
    assert drawing.calibration.state.value == "INFERRED"
    assert drawing.source_sha256 == analysis.source_sha256
    left_ids = [drawing.entities[i].entity_id for i in (0, 4, 5, 6)]
    assessment = assess_area(drawing, "cad:Model", left_ids,
                             boundary_role="INTERIOR_ROOM",
                             reviewer_id="synthetic-review")
    assert assessment.status is GeometryReviewStatus.INSUFFICIENT_EVIDENCE
    assert assessment.physical_area_m2 is None
    assert all(r.dxf.handle in {ent.source.cad_handle for ent in drawing.entities}
               for r in refs)


def test_real_pdf_rect_is_face_candidate_not_physical_room(tmp_path):
    pdf_file = tmp_path / "rect.pdf"
    page = Canvas(str(pdf_file), pagesize=(400, 300))
    page.rect(35, 65, 100, 60)
    page.drawString(10, 240, "ROOM")
    page.save()
    pdf_drawing = parse_pdf_ir(pdf_file).drawing
    result = analyze_geometry(pdf_drawing, "pdf:page0")
    assert any(face.source_area_squared == pytest.approx(6000)
               for face in result.faces)
    assert all(face.semantic_kind == "UNCLASSIFIED_FACE" for face in result.faces)
    assert pdf_drawing.calibration.metres_per_unit is None
    assert not pdf_drawing.findings
