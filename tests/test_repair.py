"""Synthetic source-preserving CAD repair candidates, never adopted into DrawingIR."""
from __future__ import annotations

import ezdxf
import pytest
from pydantic import ValidationError

from mimarllm.importers.dxf import parse_dxf
from mimarllm.importers.pdf_ir import parse_pdf_ir
from mimarllm.geometry.repair import (
    RepairInputError, RepairKind, propose_repair_overlay,
)
from mimarllm.geometry.spatial import analyze_geometry
from reportlab.pdfgen.canvas import Canvas


def dxf_lines(tmp_path, lines, *, layers=None, units=6):
    file=tmp_path/"dirty.dxf"
    doc=ezdxf.new("R2013")
    doc.header["$INSUNITS"]=units
    for idx,(a,b) in enumerate(lines):
        attrib={"layer": (layers or ["0"]*len(lines))[idx]}
        doc.modelspace().add_line(a,b,dxfattribs=attrib)
    doc.saveas(file)
    return parse_dxf(file).drawing


def test_short_endpoint_gap_generates_virtual_bridge_without_source_mutation(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))])
    before=d.model_dump_json()
    frame=d.frames[0].frame_id
    overlay=propose_repair_overlay(d,frame)
    bridges=[c for c in overlay.candidates if c.kind==RepairKind.VIRTUAL_GAP_BRIDGE]
    assert len(bridges)==1
    c=bridges[0]
    assert c.proposed_geometry.points==((1,0),(1.08,0))
    assert c.gap_source_units==pytest.approx(.08)
    assert c.source_sha256==d.source_sha256
    assert c.source_references[0].cad_handle
    assert c.source_references[1].cad_handle
    assert c.review_status=="REVIEW_REQUIRED"
    assert c.may_be_intentional_opening is True
    assert c.modifies_original is False
    assert c.legal_compliance_certified is False
    assert c.physical_value_metres is None
    assert overlay.can_feed_topology is False and overlay.can_feed_ruleengine is False
    assert d.model_dump_json()==before
    # The true Shapely source geometry remains OPEN.
    real=analyze_geometry(d,frame)
    assert len(real.faces)==0


def test_snap_candidate_is_not_actual_drawing_mutation(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.006,0),(2,0))])
    c=propose_repair_overlay(d,d.frames[0].frame_id).candidates[0]
    assert c.kind==RepairKind.ENDPOINT_SNAP_CANDIDATE
    assert c.proposed_geometry.points==((1,0),(1.006,0))
    assert d.entities[0].geometry.points[-1]==(1.,0.)


def test_exactly_connected_endpoint_does_not_generate_bridge(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1,0),(2,0))])
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    assert overlay.candidates==()


def test_reversed_duplicate_line_is_candidate_but_not_deleted(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(3,0)),((3,0),(0,0))])
    before=d.model_dump_json()
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    assert len(overlay.candidates)==1
    c=overlay.candidates[0]
    assert c.kind==RepairKind.DUPLICATE_SEGMENT_CANDIDATE
    assert c.proposed_geometry is None
    assert len(c.source_references)==2
    assert len(d.entities)==2
    assert d.model_dump_json()==before


def test_partial_collinear_overlap_is_never_auto_removed(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(3,0)),((2,0),(5,0))])
    c=propose_repair_overlay(d,d.frames[0].frame_id).candidates[0]
    assert c.kind==RepairKind.OVERLAPPING_SEGMENT_CANDIDATE
    assert c.modifies_original is False
    assert c.proposed_geometry is None


def test_cross_layer_bridging_is_not_offered(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))],
                layers=["WALL","DOOR"])
    o=propose_repair_overlay(d,d.frames[0].frame_id)
    assert not o.candidates


def test_ambiguous_endpoint_does_not_receive_arbitrary_connector(tmp_path):
    d=dxf_lines(tmp_path,[
        ((0,0),(1,0)),
        ((1.08,0),(2,0)),
        ((1.09,.02),(1.09,2)),
    ])
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    assert "AMBIGUOUS_ENDPOINT_MATCH" in {i.code for i in overlay.issues}
    assert not any(c.source_entity_ids[0]==d.entities[0].entity_id
                   and c.kind==RepairKind.VIRTUAL_GAP_BRIDGE
                   for c in overlay.candidates)


def test_frame_cannot_be_wrong_or_not_cad(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0))])
    with pytest.raises(RepairInputError,match="CAD coordinate frame"):
        propose_repair_overlay(d,"pdf:page0")
    pdf=tmp_path/"page.pdf"
    c=Canvas(str(pdf),pagesize=(400,300))
    c.line(20,150,220,150)
    c.save()
    p=parse_pdf_ir(pdf).drawing
    with pytest.raises(RepairInputError,match="CAD coordinate frame"):
        propose_repair_overlay(p,p.frames[0].frame_id)


def test_dxf_header_unit_inferred_never_confirms_physical_scale(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0))],units=6)
    assert d.calibration.state.value=="INFERRED"
    o=propose_repair_overlay(d,d.frames[0].frame_id)
    assert o.unit_hypothesis.observed_calibration_state=="INFERRED"
    assert o.unit_hypothesis.claimed_metres_per_source_unit==pytest.approx(1)
    assert o.unit_hypothesis.physical_measurement_approved is False
    assert o.physical_conclusions_approved is False
    assert d.calibration.state.value=="INFERRED"


def test_unknown_header_no_metre_hypothesis(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0))],units=0)
    o=propose_repair_overlay(d,d.frames[0].frame_id)
    assert o.unit_hypothesis.claimed_metres_per_source_unit is None
    assert o.unit_hypothesis.overlay_calibration_status=="NOT_VERIFIED_BY_REPAIR"


def test_layer0_only_unclassified_semantic_candidates(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((0,2),(2,2))],
                layers=["0","DUVAR"])
    o=propose_repair_overlay(d,d.frames[0].frame_id)
    assert len(o.layer0_candidates)==1
    assert o.layer0_candidates[0].entity_id==d.entities[0].entity_id
    assert o.layer0_candidates[0].hypothesis=="LAYER0_UNCLASSIFIED_BOUNDARY_OR_ANNOTATION"
    assert o.layer0_candidates[0].is_verified_wall_or_door is False


def test_large_pair_budget_rejected_before_search(tmp_path):
    d=dxf_lines(tmp_path,[((i*3.,0),(i*3.+1,0)) for i in range(15)])
    with pytest.raises(RepairInputError,match="pair-check safety budget"):
        propose_repair_overlay(d,d.frames[0].frame_id,max_pairs=5)
    with pytest.raises(RepairInputError,match="segment safety budget"):
        propose_repair_overlay(d,d.frames[0].frame_id,max_segments=2)


def test_invalid_tolerance_and_empty_or_unsafe_models_are_rejected(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0))])
    for kwargs in (
        {"snap_tolerance":0},
        {"snap_tolerance":1,"max_gap_source_units":.5},
        {"max_candidates":0},
        {"max_segments":0},
        {"snap_tolerance":float("nan")},
    ):
        with pytest.raises(RepairInputError):
            propose_repair_overlay(d,d.frames[0].frame_id,**kwargs)
    o=propose_repair_overlay(d,d.frames[0].frame_id)
    with pytest.raises(ValidationError):
        o.model_copy(update={"changes_drawing_ir":True}).model_validate(
            o.model_dump()|{"changes_drawing_ir":True})


def test_output_reproducible_json_and_original_sha_mapping(tmp_path):
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))])
    a=propose_repair_overlay(d,d.frames[0].frame_id)
    b=propose_repair_overlay(d,d.frames[0].frame_id)
    assert a.model_dump_json()==b.model_dump_json()
    assert type(a).model_validate_json(a.model_dump_json())==a
    refs={e.entity_id:e.source for e in d.entities}
    for c in a.candidates:
        for eid,ref in zip(c.source_entity_ids,c.source_references):
            assert refs[eid]==ref
            assert ref.document_sha256==d.source_sha256


def test_nested_insert_block_path_kept(tmp_path):
    file=tmp_path/"nested.dxf"
    doc=ezdxf.new("R2013")
    deep=doc.blocks.new(name="LEAF")
    deep.add_line((0,0),(1,0))
    deep.add_line((1.08,0),(2,0))
    parent=doc.blocks.new(name="PARENT")
    parent.add_blockref("LEAF",(0,0))
    doc.modelspace().add_blockref("PARENT",(5,5))
    doc.saveas(file)
    d=parse_dxf(file).drawing
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    bridge=next(c for c in overlay.candidates
                if c.kind==RepairKind.VIRTUAL_GAP_BRIDGE)
    assert all(ref.cad_handle and ref.block_path for ref in bridge.source_references)
    assert bridge.source_sha256==d.source_sha256
    original_by_id={entity.entity_id:entity.source for entity in d.entities}
    for eid,source in zip(bridge.source_entity_ids,bridge.source_references):
        assert original_by_id[eid] == source
        assert source.block_path


def test_repair_svg_overlay_uses_true_original_and_dashed_virtual_source(tmp_path):
    from mimarllm.geometry.repair_viewer import render_repair_overlay_svg
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))])
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    svg=render_repair_overlay_svg(d,overlay)
    assert svg.startswith("<svg ")
    assert "VIRTUAL CANDIDATE - NOT ACCEPTED" in svg
    assert 'stroke-dasharray="5,4"' in svg
    assert "ORIGINAL CAD" in svg
    assert d.entities[0].source.cad_handle in svg
    assert overlay.candidates[0].candidate_id not in d.model_dump_json()


def test_repair_svg_rejects_alien_hash_or_wrong_cad_source_ref(tmp_path):
    from mimarllm.geometry.repair_viewer import render_repair_overlay_svg
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))])
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    forged=overlay.model_copy(update={"source_sha256":"1"*64})
    with pytest.raises(RepairInputError,match="SHA"):
        render_repair_overlay_svg(d,forged)
    changed_source=overlay.candidates[0].source_references[0].model_copy(
        update={"cad_handle":"FAKE"}
    )
    changed_candidate=overlay.candidates[0].model_copy(update={
        "source_references":(changed_source,overlay.candidates[0].source_references[1])
    })
    forged=overlay.model_copy(update={"candidates":(changed_candidate,)})
    with pytest.raises(RepairInputError,match="handle"):
        render_repair_overlay_svg(d,forged)


def test_repair_svg_vertex_limit_fails_closed(tmp_path):
    from mimarllm.geometry.repair_viewer import render_repair_overlay_svg
    d=dxf_lines(tmp_path,[((0,0),(1,0)),((1.08,0),(2,0))])
    overlay=propose_repair_overlay(d,d.frames[0].frame_id)
    with pytest.raises(RepairInputError,match="vertex render budget"):
        render_repair_overlay_svg(d,overlay,max_vertices=2)
