"""Process 018 full offline orchestration — synthetic DXF, PDF, evidence gates."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import ezdxf
import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.ir import DrawingIR
from mimarllm.core.units import CalibrationState
from mimarllm.geometry.topology import SpaceKind, SpaceReview
from mimarllm.pipeline import (
    CalibrationReference, PipelineConfig, PipelineInputError,
    ReviewedArea, ReviewedTopology, RuleRun, StageStatus, run_local_pipeline,
)
from mimarllm.rules.base import (
    Comparison, LegalSourceLocator, MetricKind, RuleDefinition, RuleDomain,
    RuleStatus,
)


@pytest.fixture
def local_dxf(tmp_path):
    path=tmp_path/"test_plan.dxf"
    doc=ezdxf.new("R2013")
    doc.header["$INSUNITS"]=6
    model=doc.modelspace()
    for a,b in [((0,0),(4,0)),((4,0),(4,3)),((4,3),(0,3)),((0,3),(0,0))]:
        model.add_line(a,b)
    model.add_text("TEST",dxfattribs={"height":.2})
    doc.saveas(path)
    return path


@pytest.fixture
def local_pdf(tmp_path):
    path=tmp_path/"two-pages.pdf"
    c=Canvas(str(path),pagesize=(420,320))
    c.setFont("Helvetica",12)
    c.drawString(40,275,"Synthetic PDF page zero")
    c.line(30,200,230,200)
    c.rect(30,50,120,90)
    c.showPage()
    c.drawString(40,275,"Synthetic PDF page one")
    c.line(30,180,120,180)
    c.save()
    return path


def _segment(config_path):
    return next(e for e in run_local_pipeline(config_path).drawing.entities
                if e.geometry.kind.value=="SEGMENT" and e.type_candidate=="LINE")


def _technical(threshold=3.5):
    return RuleDefinition(
        rule_id="synthetic.length",version="v1",
        domain=RuleDomain.TECHNICAL,
        metric=MetricKind.SEGMENT_LENGTH_M,
        description="Synthetic native segment length, not a statute",
        operator=Comparison.GE,threshold=threshold,
    )


def _law():
    return RuleDefinition(
        rule_id="fake.law",version="draft",
        domain=RuleDomain.REGULATORY,
        metric=MetricKind.SEGMENT_LENGTH_M,
        description="Never certify laws based on drawings",
        operator=Comparison.GE,threshold=1,
        legal_source=LegalSourceLocator(
            document_sha256="b"*64,page_index=0,
            regulation_id="FAKE-NOT-OFFICIAL",article_id="7",
            effective_from=date(2026,1,1),
        ),
    )


def test_default_dxf_all_stages_with_explicit_review_holds(local_dxf):
    result=run_local_pipeline(local_dxf)
    assert result.manifest.source_sha256==result.drawing.source_sha256
    assert result.manifest.calibration_state in {"INFERRED","UNKNOWN"}
    assert result.drawing.calibration.state != CalibrationState.CONFIRMED
    assert len(result.geometries)==1
    assert result.manifest.face_candidate_count>=1
    assert len(result.topologies)==0
    assert len(result.rules)==0
    assert result.report.legal_gate=="REGULATORY_LOCKED"
    assert result.manifest.legal_gate=="REGULATORY_LOCKED"
    assert any(x.stage=="TOPOLOGY" and x.status==StageStatus.SKIPPED
               for x in result.manifest.stages)
    assert any(x.stage=="CALIBRATION" and x.status==StageStatus.REVIEW_REQUIRED
               for x in result.manifest.stages)
    assert all(x.status!="COMPLIANT" for x in result.report.findings)


def test_technical_rule_without_calibration_cannot_pass(local_dxf):
    line=_segment(local_dxf)
    opts=PipelineConfig(rules=(RuleRun(
        definition=_technical(), measurement_entity_id=line.entity_id,
    ),))
    result=run_local_pipeline(local_dxf,opts)
    assert result.rules[0].status==RuleStatus.INSUFFICIENT_EVIDENCE
    assert result.rules[0].reason_code=="CONFIRMED_SCALE_OR_SI_MISSING"
    assert result.report.findings[0].technical_domain != RuleDomain.REGULATORY
    assert result.drawing.measurements[0].physical_value is None


def test_explicit_native_segment_human_reference_allows_technical_only(local_dxf):
    line=_segment(local_dxf)
    opts=PipelineConfig(
        calibration=CalibrationReference(
            entity_id=line.entity_id,known_length_metres=4,
            reviewer_id="synthetic reviewer",
        ),
        rules=(RuleRun(
            definition=_technical(),measurement_entity_id=line.entity_id,
        ),),
    )
    result=run_local_pipeline(local_dxf,opts)
    assert result.drawing.calibration.state==CalibrationState.CONFIRMED
    assert result.rules[0].status==RuleStatus.COMPLIANT
    assert result.rules[0].legal_compliance_certified is False
    assert result.manifest.calibration_state=="CONFIRMED"
    assert result.drawing.calibration_frame_id==line.frame_id
    assert result.drawing.measurements[0].entity_ids==(line.entity_id,)
    assert result.report.findings[1 if result.report.findings[0].kind.value!="TECHNICAL_RULE" else 0].technical_domain != RuleDomain.REGULATORY


def test_wrong_reference_entity_rejected_instead_of_assuming_scale(local_dxf):
    with pytest.raises(PipelineInputError,match="reference"):
        run_local_pipeline(local_dxf,PipelineConfig(
            calibration=CalibrationReference(
                entity_id="FAKE_HANDLE",known_length_metres=5,reviewer_id="Human",
            ),
        ))
    with pytest.raises(ValidationError):
        CalibrationReference(entity_id="x",known_length_metres=-2,
                             reviewer_id="Reviewer")
    with pytest.raises(ValidationError):
        CalibrationReference(entity_id="x",known_length_metres=4,
                             reviewer_id="  ")


def test_distinct_source_segment_dimension_disagreement_can_be_reviewed(local_dxf):
    line=_segment(local_dxf)
    result=run_local_pipeline(local_dxf,PipelineConfig(
        calibration=CalibrationReference(
            entity_id=line.entity_id,known_length_metres=2,reviewer_id="User"
        ),
        rules=(RuleRun(definition=_technical(3.5),measurement_entity_id=line.entity_id),),
    ))
    assert result.rules[0].status==RuleStatus.NON_COMPLIANT
    assert result.rules[0].claim_scope=="TECHNICAL_ONLY_NOT_LEGAL"
    assert result.report.disclaimer=="TECHNICAL_ANALYSIS_NOT_LEGAL_COMPLIANCE"


def test_regulatory_rule_always_held_even_after_user_calibration(local_dxf):
    line=_segment(local_dxf)
    result=run_local_pipeline(local_dxf,PipelineConfig(
        calibration=CalibrationReference(
            entity_id=line.entity_id,known_length_metres=4,reviewer_id="User",
        ),
        rules=(RuleRun(definition=_law(),measurement_entity_id=line.entity_id),),
    ))
    assert result.rules[0].status==RuleStatus.INSUFFICIENT_EVIDENCE
    assert result.rules[0].legal_compliance_certified is False
    assert result.report.findings[0].status=="INSUFFICIENT_EVIDENCE"
    assert result.report.findings[0].legal_evidence is None
    assert result.report.legal_gate=="REGULATORY_LOCKED"


def test_multi_page_pdf_keeps_two_frame_geometry_and_source_sha(local_pdf):
    result=run_local_pipeline(local_pdf)
    assert len(result.drawing.frames)==2
    assert len(result.geometries)==2
    assert {g.frame_id for g in result.geometries}=={
        "pdf:page0","pdf:page1",
    }
    assert result.report.source_kind=="PDF"
    assert all(g.source_sha256==result.drawing.source_sha256 for g in result.geometries)
    assert len({f.finding_id for f in result.report.findings})==len(result.report.findings)
    assert all(f.frame_id in {"pdf:page0","pdf:page1"} for f in result.report.findings)
    assert result.manifest.completion=="COMPLETED_WITH_REVIEW_GATES"


def test_frame_selection_not_first_page_guess_and_reference_invalid(local_pdf):
    result=run_local_pipeline(local_pdf,PipelineConfig(
        geometry_frame_ids=("pdf:page1",),
    ))
    assert [g.frame_id for g in result.geometries]==["pdf:page1"]
    with pytest.raises(PipelineInputError,match="frame"):
        run_local_pipeline(local_pdf,PipelineConfig(
            geometry_frame_ids=("pdf:page42",),
        ))


def test_topology_only_when_explicitly_reviewed_and_wrong_face_no_graph(local_dxf):
    base=run_local_pipeline(local_dxf)
    frame=base.geometries[0].frame_id
    bad=ReviewedTopology(frame_id=frame,spaces=(
        SpaceReview(space_id="R1",face_id="nonexistent",kind=SpaceKind.ROOM,
                    reviewer_id="Human"),
    ))
    result=run_local_pipeline(local_dxf,PipelineConfig(topology=(bad,)))
    assert len(result.topologies)==0
    assert any(s.stage=="TOPOLOGY" and s.status==StageStatus.ERROR
               for s in result.manifest.stages)
    assert result.manifest.topology_edge_count==0


def test_topology_correct_review_is_not_fire_egress_route(local_dxf):
    base=run_local_pipeline(local_dxf)
    frame=base.geometries[0].frame_id
    face=base.geometries[0].faces[0]
    reviewed=ReviewedTopology(frame_id=frame,spaces=(
        SpaceReview(space_id="R1",face_id=face.face_id,kind=SpaceKind.ROOM,
                    reviewer_id="Human",label="Synthetic"),
    ))
    result=run_local_pipeline(local_dxf,PipelineConfig(topology=(reviewed,)))
    assert len(result.topologies)==1
    assert result.topologies[0].frame_id==frame
    assert result.manifest.topology_edge_count==0
    assert result.report.legal_gate=="REGULATORY_LOCKED"


def test_technical_path_no_space_reviews_no_guess(local_dxf):
    path_rule=RuleDefinition(
        rule_id="synthetic.path",version="v1",
        domain=RuleDomain.TECHNICAL,metric=MetricKind.REVIEWED_TOPOLOGY_PATH,
        description="Topological review only",
    )
    result=run_local_pipeline(local_dxf,PipelineConfig(
        rules=(RuleRun(definition=path_rule),),
    ))
    assert result.rules[0].status==RuleStatus.INSUFFICIENT_EVIDENCE
    assert "TOPOLOGY_WITNESS" in result.rules[0].reason_code


def test_area_candidate_not_measured_without_user_scale(local_dxf):
    base=run_local_pipeline(local_dxf)
    face=base.geometries[0].faces[0]
    opts=PipelineConfig(rules=(RuleRun(
        definition=RuleDefinition(
            rule_id="synthetic.area",version="v1",
            domain=RuleDomain.TECHNICAL,
            metric=MetricKind.REVIEWED_INTERIOR_AREA_M2,
            description="Synthetic area, not a room or gross floor area",
            operator=Comparison.GE,threshold=1,
        ),
        area=ReviewedArea(frame_id=face.frame_id,
            source_entity_ids=face.boundary_entity_ids,
            boundary_role="INTERIOR_ROOM",reviewer_id="Human"
        ),
    ),))
    result=run_local_pipeline(local_dxf,opts)
    assert result.rules[0].status!=RuleStatus.COMPLIANT
    assert result.rules[0].legal_compliance_certified is False


def test_source_file_missing_broken_and_extension_rejected(tmp_path):
    with pytest.raises(PipelineInputError,match="does not exist"):
        run_local_pipeline(tmp_path/"absent.dxf")
    strange=tmp_path/"malware.exe"
    strange.write_bytes(b"not drawing")
    with pytest.raises(PipelineInputError,match="Only .dxf"):
        run_local_pipeline(strange)
    bad=tmp_path/"bad.dxf"
    bad.write_text("This is not DXF",encoding="utf-8")
    with pytest.raises(PipelineInputError,match="Import rejected"):
        run_local_pipeline(bad)


def test_ocr_is_never_implicit_and_dxf_ocr_rejected(local_dxf,local_pdf):
    no_ocr=run_local_pipeline(local_pdf)
    assert no_ocr.drawing.source_kind.value=="PDF"
    requested=PipelineConfig(ocr_regions={0:((15.,15.,100.,100.),)})
    with pytest.raises(PipelineInputError,match="local CPU OCR reader"):
        run_local_pipeline(local_pdf,requested)
    with pytest.raises(PipelineInputError,match="never DXF"):
        run_local_pipeline(local_dxf,requested)
    with pytest.raises(ValidationError):
        PipelineConfig(ocr_regions={0:((50,50,20,100),)})


def test_report_all_geometry_frames_without_cross_page_join(local_pdf):
    result=run_local_pipeline(local_pdf)
    assert len(result.geometries)==2
    report=result.report
    for f in report.findings:
        if not f.entity_ids:
            continue
        assert {next(s.frame_id for s in report.sources if s.entity_id==eid)
                for eid in f.entity_ids}=={f.frame_id}


def test_malicious_config_extra_and_conflicting_rule_selection_rejected():
    with pytest.raises(ValidationError,match="extra"):
        PipelineConfig.model_validate({"network_api_key":"no"})
    with pytest.raises(ValidationError,match="Boundary evidence requires"):
        RuleRun(definition=_technical(),area=ReviewedArea(
            frame_id="f",source_entity_ids=("x",),
            boundary_role="INTERIOR_ROOM",reviewer_id="u",
        ))

def test_exceeded_shapely_segment_budget_is_explicit_partial_not_pass(local_dxf):
    result=run_local_pipeline(local_dxf,PipelineConfig(max_segments_per_frame=1))
    assert result.manifest.completion=="PARTIAL_WITH_ERRORS"
    assert result.geometries==()
    assert any(s.stage=="GEOMETRY" and s.status==StageStatus.ERROR
               for s in result.manifest.stages)
    assert result.report.legal_gate=="REGULATORY_LOCKED"
    assert all(f.status!="COMPLIANT" for f in result.report.findings)

def test_calibration_cannot_mislabel_unverified_dimension_or_scale(local_dxf):
    with pytest.raises(ValidationError):
        CalibrationReference(
            entity_id=_segment(local_dxf).entity_id,
            known_length_metres=4,reviewer_id="Human",method="DIMENSION"
        )
