"""028 rubric regression: class-scoped pedagogy, manual source review, never AI grades."""
from __future__ import annotations

import json
from hashlib import sha256

import ezdxf
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from mimarllm.app.server import create_app
from mimarllm.importers.dxf import parse_dxf
from mimarllm.pedagogy.rubric import Axis, DEFAULT_CATALOG, RUBRIC_VERSION, profile
from mimarllm.pedagogy.scoring import (
    RubricError, RubricSubmission, CriterionReview, evaluate_rubric,
)


@pytest.fixture
def drawing(tmp_path):
    file=tmp_path/"studio.dxf"
    doc=ezdxf.new("R2013")
    m=doc.modelspace()
    for start,end in (
        ((0,0),(5,0)),((5,0),(5,4)),
        ((5,4),(0,4)),((0,4),(0,0)),
    ):
        m.add_line(start,end)
    doc.saveas(file)
    ir=parse_dxf(file).drawing
    return file,ir,tuple(x.entity_id for x in ir.entities)


def human_review(criterion, source, level=3):
    return CriterionReview(
        criterion_id=criterion, human_level=level,
        source_entity_ids=(source,),
        reviewer_note="İncelemeci çizimdeki ilgili kararı insan gözüyle değerlendirdi.",
        human_review_attested=True,
    )


def submission(ir, year, reviews):
    return RubricSubmission(
        source_sha256=ir.source_sha256,frame_id="cad:Model",
        academic_year=year,reviewer_label="Pilot incelemeci",
        human_review_attested=True,reviews=tuple(reviews),
    )


def test_catalog_eight_axes_and_progressive_first_year():
    assert len(DEFAULT_CATALOG.axes)==8
    assert sum(axis.default_weight for axis in DEFAULT_CATALOG.axes)==100
    assert len(set(axis.axis for axis in DEFAULT_CATALOG.axes))==8
    first=profile(1)
    second=profile(2)
    third=profile(3)
    fourth=profile(4)
    assert [len(p["criteria"]) for p in [first,second,third,fourth]] == [6,10,14,16]
    assert not [x for x in first["criteria"] if x["axis"] in
                {"STRUCTURE","ENVIRONMENT"}]
    assert [x for x in first["axes"] if x["axis"]=="STRUCTURE"][0]["active"] is False
    assert "STRUCTURE_CONCEPT" in first["excluded_higher_year_criteria"]
    assert "STRUCTURE_COORDINATION" in second["excluded_higher_year_criteria"]
    assert third["official_grade"] is False
    assert all(p["rubric_version"]==RUBRIC_VERSION for p in
               (first,second,third,fourth))
    with pytest.raises(ValueError):
        profile(5)


def test_missing_review_never_generates_total_or_fake_fail(drawing):
    file,ir,ids=drawing
    orig=file.read_bytes(),ir.model_dump_json()
    result=evaluate_rubric(ir,submission(ir,1,()))
    assert result.status=="NOT_SCORED"
    assert result.draft_points_out_of_100 is None
    assert result.active_criterion_count==6
    assert result.reviewed_criterion_count==0
    assert len(result.missing_criterion_ids)==6
    assert result.official_grade is False
    axes={a.axis:a for a in result.axes}
    assert axes[Axis.STRUCTURE].status=="NOT_APPLICABLE_BY_LEVEL"
    assert axes[Axis.STRUCTURE].draft_axis_percent is None
    assert axes[Axis.ENVIRONMENT].status=="NOT_APPLICABLE_BY_LEVEL"
    assert axes[Axis.CONTEXT].status=="REVIEW_REQUIRED"
    partial=evaluate_rubric(ir,submission(ir,1,[human_review("CONCEPT_INTENT",ids[0],4)]))
    assert partial.draft_points_out_of_100 is None
    assert partial.reviewed_criterion_count==1
    assert orig==(file.read_bytes(),ir.model_dump_json())


def test_approved_human_draft_is_deterministic_exact_decimal(drawing):
    file,ir,ids=drawing
    start=file.read_bytes(),ir.model_dump_json()
    keys=[c["criterion_id"] for c in profile(1)["criteria"]]
    reviews=[human_review(key,ids[0],level=3) for key in keys]
    result=evaluate_rubric(ir,submission(ir,1,reviews))
    assert result.status=="LOCAL_DRAFT_ONLY"
    assert str(result.draft_points_out_of_100)=="75.00"
    assert result.official_grade is False
    assert result.vlm_derived_scores is False
    assert result.can_modify_drawing is False
    assert all(a.draft_axis_percent==75 for a in result.axes if a.active)
    assert all(a.draft_axis_percent is None for a in result.axes if not a.active)
    assert result.missing_criterion_ids==()
    # Reordering manual evidence never alters computed decimal scenario.
    reversed_result=evaluate_rubric(ir,submission(ir,1,tuple(reversed(reviews))))
    assert reversed_result.draft_points_out_of_100==result.draft_points_out_of_100
    all_good=evaluate_rubric(ir,submission(ir,1,[human_review(k,ids[0],4) for k in keys]))
    assert str(all_good.draft_points_out_of_100)=="100.00"
    zeros=evaluate_rubric(ir,submission(ir,1,[human_review(k,ids[0],0) for k in keys]))
    assert str(zeros.draft_points_out_of_100)=="0.00"
    assert start==(file.read_bytes(),ir.model_dump_json())


def test_class_specific_criteria_and_higher_level_dont_penalize_first_year(drawing):
    _,ir,ids=drawing
    first=profile(1)
    with pytest.raises(RubricError,match="NOT_APPLICABLE"):
        evaluate_rubric(ir,submission(ir,1,[human_review("STRUCTURE_CONCEPT",ids[0])]))
    with pytest.raises(RubricError,match="NOT_APPLICABLE"):
        evaluate_rubric(ir,submission(ir,1,[human_review("FUNCTION_ACCESS",ids[0])]))
    fourth=profile(4)
    full=[human_review(c["criterion_id"],ids[0],4) for c in fourth["criteria"]]
    result=evaluate_rubric(ir,submission(ir,4,full))
    assert result.active_criterion_count==16
    assert str(result.draft_points_out_of_100)=="100.00"
    assert set(a.axis for a in result.axes if a.active)==set(Axis)
    assert not result.excluded_higher_year_criteria


def test_source_spoof_and_model_injected_score_rejected(drawing):
    _,ir,ids=drawing
    r=human_review("CONCEPT_INTENT",ids[0])
    with pytest.raises(RubricError,match="SHA"):
        evaluate_rubric(ir,submission(ir,1,[r]).model_copy(
            update={"source_sha256":"f"*64}))
    with pytest.raises(RubricError,match="FRAME"):
        evaluate_rubric(ir,submission(ir,1,[r]).model_copy(
            update={"frame_id":"cad:Other"}))
    with pytest.raises(RubricError,match="ENTITY"):
        evaluate_rubric(ir,submission(ir,1,[
            human_review("CONCEPT_INTENT","Model|FAKE|LINE")]))
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **submission(ir,1,[r]).model_dump(),
            "vlm_score":100,
        })
    with pytest.raises(ValidationError):
        CriterionReview.model_validate({
            **r.model_dump(),"ai_generated":True,
        })
    with pytest.raises(ValidationError):
        CriterionReview.model_validate({
            **r.model_dump(),"human_level":4.5,
        })
    with pytest.raises(ValidationError):
        CriterionReview.model_validate({
            **r.model_dump(),"human_review_attested":False,
        })
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **submission(ir,1,[r]).model_dump(),"human_review_attested":False,
        })
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **submission(ir,1,[r]).model_dump(),
            "reviews":[r.model_dump(),r.model_dump()],
        })


def test_rubric_rest_is_readonly_and_scope_checked(tmp_path,drawing):
    file,ir,ids=drawing
    root=tmp_path/"app"
    with TestClient(create_app(root),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        csrf=http.get("/api/session").json()["csrf"]
        assert http.get("/api/rubric/profile/1").status_code==200
        assert http.get("/api/rubric/profile/5").status_code==404
        created=http.post("/api/projects",content=file.read_bytes(),
            headers={"X-Mimar-CSRF":csrf,"X-Mimar-Extension":"dxf"})
        assert created.status_code==201,created.text
        project=created.json()
        pid=project["project_id"]
        executed=http.post(f"/api/projects/{pid}/runs",
            json={"config":{},"formats":["json","html"]},
            headers={"X-Mimar-CSRF":csrf})
        assert executed.status_code==201,executed.text
        rid=executed.json()["run_id"]
        url=f"/api/projects/{pid}/runs/{rid}/rubric/evaluate"
        source=http.get(f"/api/projects/{pid}/runs/{rid}").json()
        ref=source["native_lines"][0]["entity_id"]
        payload={
            "source_sha256":project["source_sha256"],
            "frame_id":"cad:Model","academic_year":1,
            "reviewer_label":"Yerel öğretici","human_review_attested":True,
            "rubric_version":"028.0.1","reviews":[{
                "criterion_id":"CONCEPT_INTENT","human_level":3,
                "source_entity_ids":[ref],
                "reviewer_note":"Yapılan tasarım kararını kaynak çizgiden insan olarak inceledim.",
                "human_review_attested":True,
            }]
        }
        original_drawing=(root/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()
        original_report=(root/"projects"/pid/"runs"/rid/"analysis.json").read_bytes()
        assert http.post(url,json=payload).status_code==403
        response=http.post(url,json=payload,headers={"X-Mimar-CSRF":csrf})
        assert response.status_code==200,response.text
        result=response.json()
        assert result["status"]=="NOT_SCORED"
        assert result["draft_points_out_of_100"] is None
        assert result["official_grade"] is False
        assert result["regulatory_status"]=="REGULATORY_LOCKED"
        assert result["reviewed_criterion_count"]==1
        assert len(result["axes"])==8
        assert http.post(url,json={**payload,"source_sha256":"f"*64},
            headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(url,json={**payload,"reviews":[{
            **payload["reviews"][0],"source_entity_ids":["fake"]
        }]},headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(url,json={**payload,"reviews":[{
            **payload["reviews"][0],"criterion_id":"STRUCTURE_CONCEPT"
        }]},headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(url,json={**payload,"human_review_attested":False},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(url,json={**payload,"ai_grade":99},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(url,content=b"x"*32769,
            headers={"X-Mimar-CSRF":csrf}).status_code==413
        assert (root/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()==original_drawing
        assert (root/"projects"/pid/"runs"/rid/"analysis.json").read_bytes()==original_report
        assert not (root/"projects"/pid/"runs"/rid/"rubric-grade.json").exists()


def test_rubric_ui_is_native_and_avoids_llm_or_official_grade(tmp_path):
    with TestClient(create_app(tmp_path/"ui"),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        page=http.get("/").text
        js=http.get("/static/dashboard.js").text
        for node in ("rubric-year","rubric-frame","rubric-reviewer",
                     "rubric-human-confirm","rubric-criteria",
                     "rubric-evaluate","rubric-outcome"):
            assert f'id="{node}"' in page
        assert "NOT_SCORED" in js
        assert '"/api/rubric/profile/"' in js
        assert '"human_review_attested"' not in page  # no hidden forged authority
        assert "innerHTML" not in js
        assert "eval(" not in js
        assert "RESMÎ NOT" in page
        assert http.get("/api/rubric/profile/1").json()["official_grade"] is False
