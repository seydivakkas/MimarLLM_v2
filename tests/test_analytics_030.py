"""030: opt-in local history, minimization, delete/revoke and nonofficial trends."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import sqlite3

import ezdxf
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from mimarllm.analytics.models import (
    AddSnapshot, CreateCollection, DeleteSnapshot, RevokeCollection,
    HistoryError, CompareSnapshots,
)
from mimarllm.analytics.store import PrivateHistory
from mimarllm.analytics.trends import compare_drafts
from mimarllm.app.server import create_app
from mimarllm.importers.dxf import parse_dxf
from mimarllm.pedagogy.rubric import profile
from mimarllm.pedagogy.scoring import (
    RubricSubmission, CriterionReview, evaluate_rubric,
)


@pytest.fixture
def drawing(tmp_path):
    p=tmp_path/"synthetic-studio.dxf"
    d=ezdxf.new("R2013")
    for p1,p2 in [
        ((0,0),(5,0)),((5,0),(5,4)),
        ((5,4),(0,4)),((0,4),(0,0)),
    ]:
        d.modelspace().add_line(p1,p2)
    d.saveas(p)
    ir=parse_dxf(p).drawing
    return p,ir,ir.entities[0].entity_id


def assessment(ir,entity,year=2,level=3,complete=True):
    criteria=[x["criterion_id"] for x in profile(year)["criteria"]]
    if not complete:
        criteria=criteria[:2]
    reviews=tuple(CriterionReview(
        criterion_id=key,human_level=level,
        source_entity_ids=(entity,),
        reviewer_note="Bu çizimde ilgili kararı kaynak konumundan insan olarak inceledim.",
        human_review_attested=True,
    ) for key in criteria)
    return RubricSubmission(
        source_sha256=ir.source_sha256,frame_id="cad:Model",
        academic_year=year,reviewer_label="TEST INCELEMECI",
        human_review_attested=True,reviews=reviews,
    )


def make_history(tmp_path, now=None):
    hist=PrivateHistory(tmp_path)
    assert not hist.db.exists()
    data=hist.create(30,now=now)
    assert len(data["collection_token"])==32
    assert hist.db.exists()
    return hist,data["collection_token"]


def test_no_database_created_until_explicit_consent(tmp_path):
    folder=tmp_path/"app";folder.mkdir()
    hist=PrivateHistory(folder)
    assert not hist.db.exists()
    with pytest.raises(HistoryError,match="NOT_ENABLED"):
        hist.list("a"*32)
    assert not hist.db.exists()
    with pytest.raises(ValidationError):
        CreateCollection.model_validate({"consent":False,"retention_days":90})
    assert not hist.db.exists()
    with pytest.raises(ValidationError):
        CreateCollection.model_validate({"retention_days":90})


def test_minimal_local_database_token_hashed_and_no_raw_notes(drawing,tmp_path):
    file,ir,entity=drawing
    hist,token=make_history(tmp_path)
    original=file.read_bytes(),ir.model_dump_json()
    source=evaluate_rubric(ir,assessment(ir,entity))
    item=hist.add(token,"2026-GUZ","a"*32,"b"*32,source)
    assert item["schema_version"]=="030.0.1"
    assert item["official_grade"] is False
    assert item["pedagogical_progress_verified"] is False
    assert item["draft_total"]==75
    assert len(item["axes"])==8
    assert all(item["axes"][a] is not None for a in item["axes"])
    assert "reviewer_note" not in str(item)
    db=hist.db.read_bytes()
    assert token.encode() not in db
    assert source.source_sha256.encode() not in db
    assert "TEST INCELEMECI".encode() not in db
    assert "Bu çizimde ilgili kararı".encode() not in db
    listing=hist.list(token)
    assert listing["count"]==1
    assert "collection_token" not in str(listing)
    assert listing["snapshots"][0]["snapshot_id"]==item["snapshot_id"]
    with pytest.raises(HistoryError):
        hist.list("f"*32)
    assert original==(file.read_bytes(),ir.model_dump_json())


def test_same_level_draft_delta_eight_axis_and_no_progress_verdict(drawing,tmp_path):
    _,ir,entity=drawing
    hist,token=make_history(tmp_path)
    a=hist.add(token,"2026-GUZ","a"*32,"b"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=2,level=2)))
    b=hist.add(token,"2026-BAHAR","a"*32,"c"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=2,level=3)))
    out=compare_drafts(*hist.pair(token,a["snapshot_id"],b["snapshot_id"]))
    assert out.status=="COMPARABLE_DRAFT_ONLY"
    assert out.reason=="SAME_LEVEL_AND_RUBRIC"
    assert out.total_draft_delta==25
    assert len(out.axes)==8
    assert all(axis.comparable and axis.delta_points==25 for axis in out.axes)
    assert not out.pedagogical_progress_verified
    assert not out.official_grade and not out.independent_assessor_verified
    assert out.legal_gate=="REGULATORY_LOCKED"


def test_first_year_missing_axes_are_null_not_zero(drawing,tmp_path):
    _,ir,entity=drawing
    hist,token=make_history(tmp_path)
    a=hist.add(token,"2027-GUZ","a"*32,"b"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=1,level=3)))
    b=hist.add(token,"2027-BAHAR","a"*32,"c"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=1,level=4)))
    cmp=compare_drafts(*hist.pair(token,a["snapshot_id"],b["snapshot_id"]))
    assert cmp.status=="COMPARABLE_DRAFT_ONLY"
    assert cmp.total_draft_delta==25
    by_axis={axis.axis.value:axis for axis in cmp.axes}
    assert len(by_axis)==8
    for name in ("STRUCTURE","ENVIRONMENT"):
        assert by_axis[name].before_percent is None
        assert by_axis[name].after_percent is None
        assert by_axis[name].delta_points is None
        assert by_axis[name].comparable is False


def test_cross_year_and_partial_data_refuse_delta(drawing,tmp_path):
    _,ir,entity=drawing
    hist,token=make_history(tmp_path)
    a=hist.add(token,"2028-GUZ","a"*32,"b"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=1)))
    b=hist.add(token,"2028-BAHAR","a"*32,"c"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=2)))
    c=hist.add(token,"2027-GUZ","a"*32,"d"*32,
               evaluate_rubric(ir,assessment(ir,entity,year=1,complete=False)))
    diff=compare_drafts(*hist.pair(token,a["snapshot_id"],b["snapshot_id"]))
    assert diff.status=="NOT_COMPARABLE" and diff.reason=="LEVEL_OR_RUBRIC_DIFFER"
    assert diff.total_draft_delta is None
    assert all(x.before_percent is None and x.delta_points is None for x in diff.axes)
    partial=compare_drafts(*hist.pair(token,a["snapshot_id"],c["snapshot_id"]))
    assert partial.status=="NOT_COMPARABLE"
    assert partial.reason=="INSUFFICIENT_REVIEW_COVERAGE"
    assert partial.total_draft_delta is None
    assert all(x.after_percent is None for x in partial.axes)


def test_expiration_delete_record_revocation_minimized_storage(drawing,tmp_path):
    _,ir,entity=drawing
    start=datetime(2030,1,1,tzinfo=timezone.utc)
    hist,token=make_history(tmp_path,now=start)
    source=evaluate_rubric(ir,assessment(ir,entity))
    first=hist.add(token,"2026-GUZ","a"*32,"b"*32,source,now=start)
    second=hist.add(token,"2026-BAHAR","a"*32,"c"*32,source,now=start)
    assert hist.list(token,now=start)["count"]==2
    hist.remove(token,first["snapshot_id"],now=start)
    assert hist.list(token,now=start)["count"]==1
    with pytest.raises(HistoryError,match="SNAPSHOT_NOT_FOUND"):
        hist.remove(token,first["snapshot_id"],now=start)
    hist.revoke(token,now=start)
    with pytest.raises(HistoryError,match="COLLECTION_UNKNOWN"):
        hist.list(token,now=start)
    with pytest.raises(HistoryError,match="COLLECTION_UNKNOWN"):
        hist.revoke(token,now=start)
    new=hist.create(30,now=start)
    with pytest.raises(HistoryError,match="COLLECTION_UNKNOWN"):
        hist.list(new["collection_token"],now=start+timedelta(days=31))


def test_analytics_rest_consent_token_source_scope_csrf_and_no_writes(drawing,tmp_path):
    path,ir,entity=drawing
    root=tmp_path/"dashboard"
    with TestClient(create_app(root),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        csrf=http.get("/api/session").json()["csrf"]
        assert not (root/"private-analytics-030.sqlite3").exists()
        create="/api/analytics/history/create"
        assert http.post(create,json={"consent":True}).status_code==403
        assert http.post(create,json={"consent":False},
                         headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert not (root/"private-analytics-030.sqlite3").exists()
        response=http.post(create,json={"consent":True,"retention_days":90},
                           headers={"X-Mimar-CSRF":csrf})
        assert response.status_code==201,response.text
        token=response.json()["collection_token"]
        assert len(token)==32
        savedir=root/"private-analytics-030.sqlite3"
        assert savedir.exists()
        project=http.post("/api/projects",content=path.read_bytes(),headers={
            "X-Mimar-CSRF":csrf,"X-Mimar-Extension":"dxf",
        })
        assert project.status_code==201,project.text
        pid=project.json()["project_id"]
        run=http.post(f"/api/projects/{pid}/runs",
            json={"config":{},"formats":["json","html"]},
            headers={"X-Mimar-CSRF":csrf})
        assert run.status_code==201,run.text
        rid=run.json()["run_id"]
        before=(root/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()
        manifest_before=(root/"projects"/pid/"runs"/rid/"analysis.json").read_bytes()
        payload={
            "collection_token":token,"consent":True,"project_id":pid,"run_id":rid,
            "period_label":"2026-GUZ",
            "assessment":assessment(ir,entity,year=1).model_dump(mode="json"),
        }
        add="/api/analytics/history/add"
        assert http.post(add,json={**payload,"consent":False},
                         headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(add,json={**payload,"assessment":{
            **payload["assessment"],"vlm_score":99
        }},headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(add,json={**payload,"assessment":{
            **payload["assessment"],"source_sha256":"f"*64,
        }},headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(add,content=b"x"*32769,
                         headers={"X-Mimar-CSRF":csrf}).status_code==413
        assert http.post(add,json={**payload,"collection_token":"f"*32},
                         headers={"X-Mimar-CSRF":csrf}).status_code==404
        first=http.post(add,json=payload,headers={"X-Mimar-CSRF":csrf})
        assert first.status_code==201,first.text
        snap=first.json()["snapshot_id"]
        listing=http.post("/api/analytics/history/list",
            json={"collection_token":token},headers={"X-Mimar-CSRF":csrf})
        assert listing.status_code==200 and listing.json()["count"]==1
        assert http.post("/api/analytics/history/compare",
            json={"collection_token":token,"before_id":snap,"after_id":snap},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        deleted=http.post("/api/analytics/history/delete",
            json={"collection_token":token,"snapshot_id":snap,"confirm_delete":True},
            headers={"X-Mimar-CSRF":csrf})
        assert deleted.status_code==200 and deleted.json()["status"]=="SNAPSHOT_DELETED"
        assert http.post("/api/analytics/history/list",
            json={"collection_token":token},headers={"X-Mimar-CSRF":csrf}).json()["count"]==0
        assert http.post("/api/analytics/history/revoke",
            json={"collection_token":token,"confirm_delete":False},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post("/api/analytics/history/revoke",
            json={"collection_token":token,"confirm_delete":True},
            headers={"X-Mimar-CSRF":csrf}).status_code==200
        assert http.post("/api/analytics/history/list",
            json={"collection_token":token},headers={"X-Mimar-CSRF":csrf}).status_code==404
        assert (root/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()==before
        assert (root/"projects"/pid/"runs"/rid/"analysis.json").read_bytes()==manifest_before
        assert not (root/"projects"/pid/"runs"/rid/"student-grade.json").exists()


def test_period_does_not_accept_free_text_personal_identifiers():
    with pytest.raises(ValidationError):
        AddSnapshot.model_validate({
            "collection_token":"a"*32,"consent":True,
            "project_id":"b"*32,"run_id":"c"*32,
            "period_label":"Student Full Name",
            "assessment":{},
        })
    # Under-specified and named fields cannot become an analytics record.
    with pytest.raises(ValidationError):
        CreateCollection.model_validate({"consent":True,"retention_days":999})


def test_private_radar_ui_is_offline_svg_with_empty_default(tmp_path):
    root=tmp_path/"browser"
    with TestClient(create_app(root),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        page=http.get("/").text
        js=http.get("/static/dashboard.js").text
        for element in (
            "analytics-030","analytics-retention","analytics-consent-create",
            "analytics-collection-token","analytics-create","analytics-load",
            "analytics-period","analytics-save-consent","analytics-save",
            "analytics-before","analytics-after","analytics-compare",
            "analytics-delete","analytics-revoke","analytics-radar",
            "analytics-axis-table",
        ):
            assert f'id="{element}"' in page
        assert "window.confirm" in js
        assert '"/api/analytics/history/create"' in js
        assert '"/api/analytics/history/revoke"' in js
        assert "NOT_COMPARABLE" in js
        assert "allPresent" in js
        assert 'if(allPresent)' in js
        assert "innerHTML" not in js
        assert "eval(" not in js
        assert "https://" not in page
        assert not (root/"private-analytics-030.sqlite3").exists()
