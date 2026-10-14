"""Process 017: DXF/PDF DrawingIR ↔ findings ↔ original legal PDF reports.

All PDFs and DXFs are synthetic and generated inside tests. No official
legislation or actual compliance decision is checked.
"""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import re

import ezdxf
import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.ir import DrawingIR, Finding, FindingStatus
from mimarllm.core.units import UnitCalibration
from mimarllm.geometry.spatial import analyze_geometry
from mimarllm.importers.dxf import parse_dxf
from mimarllm.importers.pdf_ir import parse_pdf_ir
from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import LegalDocumentMetadata, LegalNodeKind
from mimarllm.legal.applicability import ProjectLegalContext
from mimarllm.reports import (
    ReportInputError, ReportExportError, build_analysis_report,
    export_report, render_report_html,
)
from mimarllm.reports.models import AnalysisReport, ReportKind
from mimarllm.reports.visualizer import html_id, svg_frame
from mimarllm.rules.base import (
    Comparison, LegalSourceLocator, MetricKind, RuleDefinition,
    RuleDomain, RuleRequest, RuleResult, RuleStatus,
)
from mimarllm.rules.engine import RuleEngine
from mimarllm.rules.evidence import evaluate_regulatory_with_evidence
from mimarllm.core.ir import MeasurementEvidence


@pytest.fixture
def dxf_drawing(tmp_path):
    file=tmp_path/"synthetic_plan.dxf"
    doc=ezdxf.new("R2013")
    doc.header["$INSUNITS"]=6
    space=doc.modelspace()
    for a,b in [((0,0),(4,0)),((4,0),(4,3)),((4,3),(0,3)),((0,3),(0,0))]:
        space.add_line(a,b,dxfattribs={"layer":"0"})
    doc.saveas(file)
    drawing=parse_dxf(file).drawing
    assert drawing.entities
    return drawing,file


@pytest.fixture
def pdf_drawing(tmp_path):
    path=tmp_path/"drawing.pdf"
    c=Canvas(str(path),pagesize=(450,350))
    c.setFont("Helvetica",11)
    c.drawString(35,300,"A synthetic architectural drawing")
    c.line(30,250,310,250)
    c.rect(30,60,190,100)
    c.save()
    drawing=parse_pdf_ir(path).drawing
    assert drawing.entities
    return drawing,path


@pytest.fixture
def legal_doc(tmp_path):
    path=tmp_path/"synthetic_law.pdf"
    c=Canvas(str(path),pagesize=(440,310))
    c.setFont("Helvetica",11)
    c.drawString(25,280,"MADDE 7 - Example local and unverified legislation.")
    c.drawString(25,255,"(1) A synthetic clause, not applicable law.")
    c.save()
    doc=parse_legal_pdf(path,LegalDocumentMetadata(
        regulation_id="SYNTHETIC-NOT-OFFICIAL",
        document_kind="ORIGINAL",
        claimed_publication_date=date(2026,1,1),
    ))
    clause=next(n for n in doc.nodes if n.kind==LegalNodeKind.PARAGRAPH)
    return doc,path,clause


def one_finding(drawing):
    # Prefer a native line/polyline witness over a glyph/point observation.
    e=next((candidate for candidate in drawing.entities
            if candidate.geometry.kind.value in {"SEGMENT", "POLYLINE", "POLYGON"}),
           drawing.entities[0])
    drawing.findings.append(Finding(
        finding_id="inspection-one",
        check_id="synthetic.source-check",
        check_version="0.1",
        status=FindingStatus.REVIEW_REQUIRED,
        entity_ids=(e.entity_id,),
        evidence_ids=(),
        reason_code="SOURCE_REQUIRES_REVIEW",
    ))
    return drawing


def regulatory(drawing,doc,source):
    rule=RuleDefinition(
        rule_id="synthetic.law.candidate",version="v0",
        domain=RuleDomain.REGULATORY,
        metric=MetricKind.SEGMENT_LENGTH_M,
        description="This is NOT legal compliance",
        operator=Comparison.GE,threshold=1.2,
        legal_source=LegalSourceLocator(
            document_sha256=doc.document_sha256,
            page_index=source.spans[0].page_index,
            regulation_id=doc.metadata.regulation_id,
            article_id="7",clause_id="1",
            effective_from=date(2026,1,1),
        ),
    )
    result=RuleEngine([rule]).evaluate(rule.rule_id,RuleRequest(drawing=drawing))
    assert result.status==RuleStatus.INSUFFICIENT_EVIDENCE
    return rule,result


def test_dxf_entity_handle_and_layout_source_bidirectional(dxf_drawing):
    drawing,_=dxf_drawing
    report=build_analysis_report(one_finding(drawing))
    assert report.legal_gate=="REGULATORY_LOCKED"
    assert report.drawing_sha256==drawing.source_sha256
    assert len(report.sources)==1
    source=report.sources[0]
    assert source.origin_reference.cad_handle
    assert source.frame_id==drawing.entities[0].frame_id
    html=render_report_html(report)
    assert html_id("source",source.entity_id) in html
    assert html_id("finding","drawing:inspection-one") in html
    assert source.origin_reference.cad_handle in html
    assert 'class="source-svg"' in html
    assert "tam CAD baskı" in html
    assert 'href="#'+html_id("finding","drawing:inspection-one")+'"' in html
    assert 'href="#'+html_id("source",source.entity_id)+'"' in html
    assert "REGULATORY_LOCKED" in html


def test_pdf_render_true_original_background_and_source_overlay(pdf_drawing):
    drawing,pdf=pdf_drawing
    report=build_analysis_report(one_finding(drawing))
    html=render_report_html(report,drawing_pdf_path=pdf)
    assert "data:image/png;base64," in html
    assert 'viewBox="0.000000 0.000000 450.000000 350.000000"' in html
    assert "Gerçek orijinal PDF" in html
    assert "<polyline points=" in html or "<polygon points=" in html
    assert html_id("finding","drawing:inspection-one") in html


def test_pdf_background_not_invented_when_original_missing(pdf_drawing):
    drawing,_=pdf_drawing
    report=build_analysis_report(one_finding(drawing))
    html=render_report_html(report)
    assert "Orijinal PDF dosyası sağlanmadı" in html
    assert "data:image/png;base64," not in html
    assert "Yalnız DrawingIR" not in html  # explicit missing original message


def test_foreign_pdf_path_rejected_before_export(pdf_drawing,legal_doc,tmp_path):
    drawing,_=pdf_drawing
    _,other,_=legal_doc
    report=build_analysis_report(one_finding(drawing))
    with pytest.raises(ReportExportError,match="SHA256 mismatch"):
        export_report(report,tmp_path/"not_created.html",drawing_pdf_path=other)
    assert not (tmp_path/"not_created.html").exists()


def test_technical_rule_real_ruleengine_preserves_measurement_and_numeric_value(dxf_drawing):
    drawing,_=dxf_drawing
    entity=drawing.entities[0]
    length=((entity.geometry.points[1][0]-entity.geometry.points[0][0])**2
        +(entity.geometry.points[1][1]-entity.geometry.points[0][1])**2)**.5
    frame=entity.frame_id
    drawing.calibration=UnitCalibration.from_dxf_insunits(6,user_confirmed=True)
    drawing.calibration_frame_id=frame
    drawing.measurements.append(MeasurementEvidence(
        evidence_id="native-line-length",entity_ids=(entity.entity_id,),
        source_value=length,quantity="length",source_frame_id=frame,
        method_id="segment_length",tolerance_source_units=0.,
        physical_value=length,physical_unit="m",
    ))
    rule=RuleDefinition(
        rule_id="technical.synthetic.length",version="0.1",
        domain=RuleDomain.TECHNICAL,metric=MetricKind.SEGMENT_LENGTH_M,
        description="Synthetic technical threshold not building code",
        operator=Comparison.GE,threshold=3.5,
    )
    result=RuleEngine([rule]).evaluate(rule.rule_id,RuleRequest(
        drawing=drawing,measurement_evidence_id="native-line-length",
    ))
    assert result.status==RuleStatus.COMPLIANT
    report=build_analysis_report(drawing,rules=[result])
    f=report.findings[0]
    assert f.kind==ReportKind.TECHNICAL_RULE
    assert f.measurement_ids==("native-line-length",)
    assert f.evidence_ids==("native-line-length",)
    assert f.observed_value==pytest.approx(length)
    assert f.technical_domain==RuleDomain.TECHNICAL
    assert report.legal_gate=="REGULATORY_LOCKED"


def test_regulatory_binding_real_original_pdf_in_html_and_backlink(dxf_drawing,legal_doc):
    drawing,_=dxf_drawing
    legal,pdf,node=legal_doc
    rule,rr=regulatory(drawing,legal,node)
    review=evaluate_regulatory_with_evidence(
        RuleEngine([rule]),rule,RuleRequest(drawing=drawing),
        [legal],source_node_id=node.node_id,local_pdf_path=pdf,
        project=ProjectLegalContext(drawing_sha256=drawing.source_sha256),
    )
    report=build_analysis_report(
        drawing,rules=[rr],regulatory_evaluations=[review],
    )
    assert report.findings[0].kind==ReportKind.REGULATORY_CANDIDATE
    assert report.findings[0].status==RuleStatus.INSUFFICIENT_EVIDENCE.value
    assert report.findings[0].legal_evidence.document_sha256==legal.document_sha256
    html=render_report_html(
        report,legal_documents=[legal],
        legal_pdf_paths={legal.document_sha256:pdf},
    )
    assert html.count("data:image/png;base64,")>=1
    assert "<polygon points=" in html
    assert "HUKUKI_HOLD" in html
    assert node.node_id in html
    assert html_id("legal",report.findings[0].finding_id) in html
    assert 'href="#'+html_id("finding",report.findings[0].finding_id)+'"' in html


def test_regulatory_report_missing_source_pdf_no_fake_background(dxf_drawing,legal_doc):
    drawing,_=dxf_drawing
    legal,pdf,node=legal_doc
    rule,rr=regulatory(drawing,legal,node)
    bound=evaluate_regulatory_with_evidence(
        RuleEngine([rule]),rule,RuleRequest(drawing=drawing),[legal],
        source_node_id=node.node_id,local_pdf_path=pdf,
    )
    report=build_analysis_report(
        drawing,rules=[rr],regulatory_evaluations=[bound],
    )
    html=render_report_html(report,legal_documents=[legal])
    assert "Orijinal mevzuat PDF yerel dosyası mevcut değil" in html
    assert "data:image/png;base64," not in html
    no_ast=render_report_html(report)
    assert "LegalAST/orijinal PDF sağlanmadı" in no_ast


def test_legal_original_wrong_pdf_file_rejected(dxf_drawing,legal_doc,tmp_path):
    drawing,_=dxf_drawing
    legal,pdf,node=legal_doc
    rule,rr=regulatory(drawing,legal,node)
    bound=evaluate_regulatory_with_evidence(
        RuleEngine([rule]),rule,RuleRequest(drawing=drawing),[legal],
        source_node_id=node.node_id,local_pdf_path=pdf,
    )
    report=build_analysis_report(drawing,rules=[rr],regulatory_evaluations=[bound])
    altered=tmp_path/"altered.pdf"
    altered.write_bytes(pdf.read_bytes()+b"\\n%unsafe\\n")
    with pytest.raises(ReportExportError,match="SHA/page/geometry"):
        render_report_html(report,legal_documents=[legal],
                           legal_pdf_paths={legal.document_sha256:altered})


def test_forged_legal_node_span_rejected_even_with_matching_pdf(dxf_drawing,legal_doc):
    drawing,_=dxf_drawing
    legal,pdf,node=legal_doc
    rule,rr=regulatory(drawing,legal,node)
    bound=evaluate_regulatory_with_evidence(
        RuleEngine([rule]),rule,RuleRequest(drawing=drawing),[legal],
        source_node_id=node.node_id,local_pdf_path=pdf,
    )
    report=build_analysis_report(drawing,rules=[rr],regulatory_evaluations=[bound])
    link=report.findings[0].legal_evidence
    assert link
    bad=link.model_copy(update={"node_id":"made-up-node"})
    bad_f=report.findings[0].model_copy(update={"legal_evidence":bad})
    forged=report.model_copy(update={"findings":(bad_f,)})
    with pytest.raises(ReportExportError,match="LegalAST"):
        render_report_html(forged,legal_documents=[legal],
                           legal_pdf_paths={legal.document_sha256:pdf})


def test_regulatory_no_binding_cannot_generate_verified_original_link(dxf_drawing,legal_doc):
    drawing,_=dxf_drawing
    legal,_,node=legal_doc
    _,r=regulatory(drawing,legal,node)
    report=build_analysis_report(drawing,rules=[r])
    assert report.findings[0].legal_evidence is None
    html=render_report_html(report)
    assert "Doğrulanmış mevzuat PDF bağlantısı yok" in html
    assert "data:image/png;base64," not in html


def test_rule_foreign_drawing_sha_and_evidence_rejected(dxf_drawing):
    drawing,_=dxf_drawing
    rule=RuleResult(
        rule_id="sample",rule_version="1",
        domain=RuleDomain.REGULATORY,
        metric=MetricKind.SEGMENT_LENGTH_M,
        status=RuleStatus.INSUFFICIENT_EVIDENCE,
        drawing_sha256="f"*64,
        reason_code="REGULATORY_SOURCE_AND_APPLICABILITY_UNVERIFIED",
    )
    with pytest.raises(ReportInputError,match="SHA"):
        build_analysis_report(drawing,rules=[rule])
    bad=RuleResult.model_validate(rule.model_dump() | {
        "drawing_sha256":drawing.source_sha256,
        "entity_ids":("forged",),
    })
    with pytest.raises(ReportInputError,match="unknown"):
        build_analysis_report(drawing,rules=[bad])


def test_geometry_faces_remain_review_candidates_not_rooms(dxf_drawing):
    drawing,_=dxf_drawing
    geo=analyze_geometry(drawing,drawing.entities[0].frame_id)
    assert geo.source_sha256==drawing.source_sha256
    report=build_analysis_report(drawing,geometry=geo)
    assert all(f.status!="COMPLIANT" for f in report.findings)
    for f in report.findings:
        if f.kind==ReportKind.FACE_CANDIDATE:
            assert f.reason_code=="UNCLASSIFIED_FACE_NOT_CONFIRMED_ROOM"
    bad=geo.model_copy(update={"source_sha256":"0"*64})
    with pytest.raises(ReportInputError,match="different drawing"):
        build_analysis_report(drawing,geometry=bad)


def test_report_json_md_html_pdf_export_offline_and_no_overwrite(dxf_drawing,tmp_path):
    drawing,_=dxf_drawing
    report=build_analysis_report(one_finding(drawing))
    for suffix in (".json",".md",".html",".pdf"):
        target=tmp_path/("export"+suffix)
        export_report(report,target)
        assert target.stat().st_size>100
        with pytest.raises(ReportExportError,match="overwrite"):
            export_report(report,target)
    text=(tmp_path/"export.md").read_text("utf-8")
    assert "inspection" in text.lower() or "synthetic.source-check" in text
    loaded=AnalysisReport.model_validate_json((tmp_path/"export.json").read_text("utf-8"))
    assert loaded==report
    assert (tmp_path/"export.pdf").read_bytes().startswith(b"%PDF")


def test_sources_and_cross_links_escape_malicious_layer_or_check_id(dxf_drawing):
    drawing,_=dxf_drawing
    e=drawing.entities[0]
    drawing.entities[0]=e.model_copy(update={"layer":'<script>alert("x")</script>'})
    drawing.findings.append(Finding(
        finding_id="unsafe",check_id='<img src=x onerror=alert(1)>',
        check_version="0.1",status=FindingStatus.REVIEW_REQUIRED,
        entity_ids=(e.entity_id,),reason_code="HTML_ESCAPING",
    ))
    report=build_analysis_report(drawing)
    html=render_report_html(report)
    assert "&lt;img src=x onerror=alert(1)&gt;" in html
    assert '<img src=x onerror=alert(1)>' not in html
    assert "<script>alert" not in html


def test_report_forged_source_document_cannot_pass_schema(dxf_drawing):
    drawing,_=dxf_drawing
    report=build_analysis_report(one_finding(drawing))
    entity=report.sources[0]
    forged=entity.model_copy(update={"drawing_sha256":"0"*64})
    altered=report.model_copy(update={"sources":(forged,)})
    with pytest.raises(ValidationError,match="provenance"):
        AnalysisReport.model_validate(altered.model_dump())


def test_report_rejects_duplicate_rule_and_frame_mismatch(dxf_drawing):
    drawing,_=dxf_drawing
    r=RuleResult(
        rule_id="s",rule_version="1",domain=RuleDomain.TECHNICAL,
        metric=MetricKind.SEGMENT_LENGTH_M,status=RuleStatus.REVIEW_REQUIRED,
        reason_code="SENTETIC",drawing_sha256=drawing.source_sha256,
    )
    with pytest.raises(ReportInputError,match="Duplicate"):
        build_analysis_report(drawing,rules=[r,r])
    frame=r.model_copy(update={
        "entity_ids":(drawing.entities[0].entity_id,),
        "frame_id":"unknown",
    })
    with pytest.raises(ReportInputError,match="frame"):
        build_analysis_report(drawing,rules=[frame])


def test_report_page_limit_and_external_legal_pdf_requires_ast(pdf_drawing,legal_doc):
    drawing,path=pdf_drawing
    report=build_analysis_report(one_finding(drawing))
    with pytest.raises(ReportExportError,match="budgets"):
        render_report_html(report,drawing_pdf_path=path,max_pages=0)
    legal,pdf,_=legal_doc
    with pytest.raises(ReportExportError,match="Legal PDFs require"):
        render_report_html(report,legal_pdf_paths={legal.document_sha256:pdf})
