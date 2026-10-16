"""Process 019: local-only FastAPI dashboard synthetic E2E contract tests."""
from __future__ import annotations
from datetime import date
from math import dist
import json

import ezdxf
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen.canvas import Canvas

from mimarllm.app.server import create_app
from mimarllm.app.launch import main as launch_main


@pytest.fixture
def cli(tmp_path):
    app=create_app(tmp_path/"workspace")
    with TestClient(app,base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        yield http,http.get("/api/session").json()["csrf"],tmp_path/"workspace"


@pytest.fixture
def dxf(tmp_path):
    p=tmp_path/"synthetic.dxf"
    cad=ezdxf.new("R2013")
    cad.header["$INSUNITS"]=6
    m=cad.modelspace()
    for a,b in [((0,0),(5,0)),((5,0),(5,4)),((5,4),(0,4)),((0,4),(0,0))]:
        m.add_line(a,b)
    cad.saveas(p)
    return p.read_bytes()


@pytest.fixture
def pdf(tmp_path):
    p=tmp_path/"synthetic.pdf"
    c=Canvas(str(p),pagesize=(430,340))
    c.drawString(30,290,"First synthetic page")
    c.line(30,220,220,220)
    c.showPage()
    c.drawString(30,290,"Second synthetic page")
    c.line(30,220,200,220)
    c.save()
    return p.read_bytes()


def upload(http,csrf,body,ext="dxf"):
    return http.post("/api/projects",content=body,headers={
        "X-Mimar-CSRF":csrf,"X-Mimar-Extension":ext,
        "Content-Type":"application/octet-stream",
    })


def run(http,csrf,pid,config=None,formats=None):
    return http.post(f"/api/projects/{pid}/runs",
        json={"config":config or {},"formats":formats or ["json","html"]},
        headers={"X-Mimar-CSRF":csrf})


def details(http,pid,rid):
    return http.get(f"/api/projects/{pid}/runs/{rid}").json()


def test_turkish_ui_assets_and_csp(cli):
    http,csrf,_=cli
    page=http.get("/")
    assert page.status_code==200
    assert "Proje inceleme paneli" in page.text
    assert 'id="upload-button"' in page.text
    assert "Hukukî doğrulama kilitli" in page.text
    assert page.headers["x-frame-options"]=="DENY"
    assert "script-src 'self'" in page.headers["content-security-policy"]
    assert "no-store" in page.headers["cache-control"]
    for asset in ("dashboard.js","dashboard.css"):
        resp=http.get("/static/"+asset)
        assert resp.status_code==200 and len(resp.content)>1000
        assert "cdn." not in resp.text.lower()
    assert http.get("/static/sneaky.js").status_code==404
    assert len(csrf)>32


def test_dxf_upload_pipeline_report_source_and_sha(cli,dxf):
    http,csrf,workspace=cli
    created=upload(http,csrf,dxf)
    assert created.status_code==201,created.text
    project=created.json()
    pid=project["project_id"]
    assert project["source_kind"]=="DXF"
    assert project["source_name"]=="input.dxf"
    assert len(project["source_sha256"])==64
    assert (workspace/"projects"/pid/"input.dxf").read_bytes()==dxf
    result=run(http,csrf,pid)
    assert result.status_code==201,result.text
    rid=result.json()["run_id"]
    summary=details(http,pid,rid)
    assert summary["manifest"]["legal_gate"]=="REGULATORY_LOCKED"
    assert summary["manifest"]["source_sha256"]==project["source_sha256"]
    assert summary["manifest"]["calibration_state"]!="CONFIRMED"
    assert summary["native_lines"]
    assert summary["sources"]
    assert "analysis.html" in summary["reports"]
    resp=http.get(f"/api/projects/{pid}/runs/{rid}/files/analysis.html")
    assert resp.status_code==200
    assert "source-svg" in resp.text
    assert "style-src 'unsafe-inline'" in resp.headers["content-security-policy"]


def test_pdf_two_pages_true_source_background(cli,pdf):
    http,csrf,_=cli
    pid=upload(http,csrf,pdf,"pdf").json()["project_id"]
    resp=run(http,csrf,pid)
    assert resp.status_code==201,resp.text
    rid=resp.json()["run_id"]
    data=details(http,pid,rid)
    assert len(data["frames"])==2
    assert data["manifest"]["legal_gate"]=="REGULATORY_LOCKED"
    html=http.get(f"/api/projects/{pid}/runs/{rid}/files/analysis.html").text
    assert "data:image/png;base64," in html
    assert "Gerçek orijinal PDF" in html


def test_native_line_calibration_reanalysis_is_only_technical(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    first=run(http,csrf,pid).json()["run_id"]
    line=details(http,pid,first)["native_lines"][0]
    length=dist(*line["points"])
    cfg={
      "calibration":{"entity_id":line["entity_id"],"known_length_metres":length,
                     "reviewer_id":"Human test","method":"USER_REFERENCE"},
      "rules":[{"definition":{
          "rule_id":"synthetic.length","version":"v1",
          "domain":"TECHNICAL","metric":"SEGMENT_LENGTH_M",
          "description":"Not official legal rule",
          "operator":">=","threshold":length-0.01,
      },"measurement_entity_id":line["entity_id"]}]
    }
    resp=run(http,csrf,pid,cfg,["json","html","md"])
    assert resp.status_code==201,resp.text
    second=resp.json()["run_id"]
    assert first!=second
    data=details(http,pid,second)
    assert data["manifest"]["calibration_state"]=="CONFIRMED"
    assert any(f["kind"]=="TECHNICAL_RULE" and f["status"]=="COMPLIANT"
               for f in data["findings"])
    assert data["manifest"]["legal_gate"]=="REGULATORY_LOCKED"
    assert "analysis.md" in data["reports"]
    runs=http.get(f"/api/projects/{pid}").json()["runs"]
    assert {x["run_id"] for x in runs}=={first,second}


def test_regulatory_candidate_stays_hold(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    config={"rules":[{"definition":{
        "rule_id":"fake-law","version":"draft","domain":"REGULATORY",
        "metric":"SEGMENT_LENGTH_M","description":"Unverified law",
        "operator":">=","threshold":1,
        "legal_source":{"document_sha256":"a"*64,"page_index":0,
                        "regulation_id":"FAKE","article_id":"7",
                        "effective_from":"2026-01-01"},
    }}]}
    resp=run(http,csrf,pid,config)
    assert resp.status_code==201,resp.text
    data=details(http,pid,resp.json()["run_id"])
    assert any(f["kind"]=="REGULATORY_CANDIDATE" and
               f["status"]=="INSUFFICIENT_EVIDENCE" and
               f["legal_evidence"] is None for f in data["findings"])


def test_local_csrf_origin_and_foreign_host_rejected(cli,dxf,tmp_path):
    http,csrf,_=cli
    no=http.post("/api/projects",content=dxf,headers={"X-Mimar-Extension":"dxf"})
    assert no.status_code==403
    evil=upload(http,"bad-token",dxf)
    assert evil.status_code==403
    cross=http.post("/api/projects",content=dxf,headers={
        "X-Mimar-Extension":"dxf","X-Mimar-CSRF":csrf,
        "Origin":"http://malicious.invalid"})
    assert cross.status_code==403
    app=create_app(tmp_path/"newworkspace")
    with TestClient(app,base_url="http://malicious.invalid:8765",
                    client=("127.0.0.1",12345)) as remote:
        assert remote.get("/api/session").status_code==403
    with TestClient(app,base_url="http://127.0.0.1:8765",
                    client=("8.8.8.8",54321)) as remote:
        assert remote.get("/").status_code==403


def test_upload_limits_invalid_extension_and_empty(cli,dxf):
    http,csrf,_=cli
    assert upload(http,csrf,dxf,"exe").status_code==415
    assert upload(http,csrf,b"").status_code==422
    huge=http.post("/api/projects",content=b"x",headers={
        "X-Mimar-Extension":"dxf","X-Mimar-CSRF":csrf,
        "Content-Length":"26000000"})
    assert huge.status_code==413


def test_unknown_project_run_and_download_path_rejected(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    assert http.get("/api/projects/not-a-valid-id").status_code==404
    assert http.get(f"/api/projects/{pid}/runs/notvalid").status_code==404
    assert http.get(f"/api/projects/{pid}/runs/{rid}/files/secret.env").status_code==404
    good=http.get(f"/api/projects/{pid}/runs/{rid}/files/analysis.json")
    assert good.status_code==200
    assert "attachment" in good.headers["content-disposition"]


def test_modified_original_pdf_or_dxf_cannot_be_reused(cli,dxf):
    http,csrf,workspace=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    (workspace/"projects"/pid/"input.dxf").write_bytes(dxf+b"\nmodified")
    assert run(http,csrf,pid).status_code==422
    assert http.get(f"/api/projects/{pid}").json()["runs"]==[]


def test_invalid_json_unknown_config_no_fake_output(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    assert run(http,csrf,pid,{"remote_api_key":"forbidden"}).status_code==422
    bad=http.post(f"/api/projects/{pid}/runs",content=b"{BROKEN",
        headers={"X-Mimar-CSRF":csrf,"Content-Type":"application/json"})
    assert bad.status_code==422
    assert not http.get(f"/api/projects/{pid}").json()["runs"]


def test_geometry_budget_partial_retained_with_hold(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    resp=run(http,csrf,pid,{"max_segments_per_frame":1})
    assert resp.status_code==201,resp.text
    assert resp.json()["completion"]=="PARTIAL_WITH_ERRORS"
    assert any(s["status"]=="ERROR" for s in resp.json()["manifest"]["stages"])
    assert resp.json()["manifest"]["legal_gate"]=="REGULATORY_LOCKED"


def test_dashboard_static_text_escape_and_offline_only(cli):
    http,_,_=cli
    script=http.get("/static/dashboard.js").text
    assert "innerHTML" not in script
    assert "eval(" not in script
    assert "textContent" in script
    assert "fetch(" in script
    assert "https://" not in http.get("/").text


def test_launcher_uses_loopback_and_disables_proxy_headers(tmp_path,monkeypatch):
    import uvicorn
    calls=[]
    monkeypatch.setattr(uvicorn,"run",lambda app,**kw:calls.append(kw))
    assert launch_main(["--workspace",str(tmp_path/"private"),"--port","9001"])==0
    assert calls[0]["host"]=="127.0.0.1"
    assert calls[0]["proxy_headers"] is False
    assert calls[0]["port"]==9001


def test_oversized_analysis_json_rejected_before_parse(cli,dxf):
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    oversized=b"x"*256001
    result=http.post(f"/api/projects/{pid}/runs",content=oversized,headers={
        "X-Mimar-CSRF":csrf,
        "Content-Type":"application/json",
    })
    assert result.status_code==413
    assert not http.get(f"/api/projects/{pid}").json()["runs"]


def test_run_summary_rejects_mismatched_source_sha(cli,dxf):
    http,csrf,workspace=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    stored=workspace/"projects"/pid/"runs"/rid/"analysis.json"
    report=json.loads(stored.read_text("utf-8"))
    report["drawing_sha256"]="f"*64
    stored.write_text(json.dumps(report),encoding="utf-8")
    resp=http.get(f"/api/projects/{pid}/runs/{rid}")
    assert resp.status_code==409


def test_tampered_project_metadata_cannot_redirect_source_path(cli,dxf):
    http,csrf,workspace=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    stored=workspace/"projects"/pid/"project.json"
    meta=json.loads(stored.read_text("utf-8"))
    meta["source_name"]="../../not_a_drawing.pdf"
    stored.write_text(json.dumps(meta),encoding="utf-8")
    assert http.get(f"/api/projects/{pid}").status_code==409
    assert run(http,csrf,pid).status_code==409
    assert not http.get("/api/projects").json()["projects"]


def test_async_job_pipeline_preserves_source_and_regulatory_hold(cli,dxf):
    from time import sleep
    http,csrf,_=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    source_sha=http.get(f"/api/projects/{pid}").json()["project"]["source_sha256"]
    resp=http.post(f"/api/projects/{pid}/jobs",
                   json={"config":{},"formats":["json","html"]},
                   headers={"X-Mimar-CSRF":csrf})
    assert resp.status_code==202,resp.text
    job=resp.json()
    assert job["project_id"]==pid and job["source_sha256"]==source_sha
    assert job["state"] in ("QUEUED","RUNNING")
    for _ in range(200):
        state=http.get(f"/api/projects/{pid}/jobs/{job['job_id']}")
        assert state.status_code==200
        job=state.json()
        if job["state"] in ("COMPLETED","FAILED"):
            break
        sleep(.025)
    assert job["state"]=="COMPLETED",job
    assert job["run_id"] and len(job["run_id"])==32
    result=details(http,pid,job["run_id"])
    assert result["source_sha256"]==source_sha
    assert result["manifest"]["legal_gate"]=="REGULATORY_LOCKED"
    assert result["native_lines"]
    assert all(item["origin"] in ("CAD_NATIVE","PDF_NATIVE")
               for item in result["native_lines"])
    assert all(item["frame_id"] for item in result["native_lines"])


def test_async_jobs_obey_csrf_id_body_and_ownership(cli,dxf):
    http,csrf,_=cli
    p1=upload(http,csrf,dxf).json()["project_id"]
    p2=upload(http,csrf,dxf).json()["project_id"]
    endpoint=f"/api/projects/{p1}/jobs"
    assert http.post(endpoint,json={"config":{}}).status_code==403
    assert http.post(endpoint,content=b"x"*256001,
                     headers={"X-Mimar-CSRF":csrf}).status_code==413
    assert http.post(endpoint,json={"config":{"remote_api_key":"x"}},
                     headers={"X-Mimar-CSRF":csrf}).status_code==422
    job=http.post(endpoint,json={"config":{}},
                  headers={"X-Mimar-CSRF":csrf}).json()
    assert http.get(f"/api/projects/{p2}/jobs/{job['job_id']}").status_code==404
    assert http.get(f"/api/projects/{p1}/jobs/not-valid").status_code==404


def test_2d_ui_source_inspector_offline_and_escaped(cli):
    http,_,_=cli
    html=http.get("/").text
    js=http.get("/static/dashboard.js").text
    assert 'id="drawing-2d"' in html
    assert 'id="frame-filter"' in html and 'id="layer-filter"' in html
    assert 'id="job-status"' in html
    assert 'renderDrawing(data)' in js
    assert 'data.source_sha256' in js
    assert 'document.createElementNS' in js
    assert 'innerHTML' not in js
    assert 'eval(' not in js
    assert "https://" not in html
    assert "script-src 'self'" in http.get("/").headers["content-security-policy"]


def test_2d_review_note_sidecar_audited_and_original_unchanged(cli,dxf):
    http,csrf,workspace=cli
    project=upload(http,csrf,dxf).json()
    pid=project["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    data=details(http,pid,rid)
    source=data["native_lines"][0]
    base=f"/api/projects/{pid}/runs/{rid}"
    input_file=workspace/"projects"/pid/"input.dxf"
    drawing_file=workspace/"projects"/pid/"runs"/rid/"drawingir.json"
    original_drawing=drawing_file.read_bytes()
    payload={
      "source_sha256":project["source_sha256"],
      "entity_id":source["entity_id"],"frame_id":source["frame_id"],
      "reviewer_label":"Studio reviewer",
      "note":"Kaynak çizgisi manuel kontrol gerektirir."
    }
    add=http.post(base+"/reviews",json=payload,headers={"X-Mimar-CSRF":csrf})
    assert add.status_code==201,add.text
    note=add.json()
    assert note["review_state"]=="UNVERIFIED_OBSERVATION"
    assert note["retracted_utc"] is None
    assert len(note["review_id"])==32
    listed=http.get(base+"/reviews").json()
    assert listed["source_sha256"]==project["source_sha256"]
    assert len(listed["notes"])==1
    assert listed["notes"][0]["entity_id"]==source["entity_id"]
    assert input_file.read_bytes()==dxf
    assert drawing_file.read_bytes()==original_drawing
    assert details(http,pid,rid)["manifest"]["legal_gate"]=="REGULATORY_LOCKED"
    assert http.get(base+"/files/review-notes.json").status_code==404
    assert http.delete(base+"/reviews/"+note["review_id"]).status_code==403
    erased=http.delete(base+"/reviews/"+note["review_id"],
                       headers={"X-Mimar-CSRF":csrf})
    assert erased.status_code==200,erased.text
    assert erased.json()["retracted_utc"] is not None
    assert http.delete(base+"/reviews/"+note["review_id"],
                       headers={"X-Mimar-CSRF":csrf}).status_code==409
    assert len(http.get(base+"/reviews").json()["notes"])==1
    assert drawing_file.read_bytes()==original_drawing
    app=create_app(workspace)
    with TestClient(app,base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as another_process:
        retained=another_process.get(base+"/reviews").json()["notes"]
        assert len(retained)==1 and retained[0]["retracted_utc"]


def test_review_source_forgery_budget_and_payload_rejected(cli,dxf):
    http,csrf,workspace=cli
    project=upload(http,csrf,dxf).json()
    pid=project["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    source=details(http,pid,rid)["native_lines"][0]
    url=f"/api/projects/{pid}/runs/{rid}/reviews"
    payload={
      "source_sha256":project["source_sha256"],
      "entity_id":source["entity_id"],"frame_id":source["frame_id"],
      "reviewer_label":"Reviewer","note":"Manuel gözlem."
    }
    headers={"X-Mimar-CSRF":csrf}
    assert http.post(url,json=payload).status_code==403
    assert http.post(url,content=b"x"*4097,headers=headers).status_code==413
    assert http.post(url,json={**payload,"source_sha256":"f"*64},
                     headers=headers).status_code==409
    assert http.post(url,json={**payload,"entity_id":"fabricated-id"},
                     headers=headers).status_code==409
    assert http.post(url,json={**payload,"unexpected":"malicious"},
                     headers=headers).status_code==422
    assert http.get(url).json()["notes"]==[]
    (workspace/"projects"/pid/"input.dxf").write_bytes(dxf+b"\\nmodified")
    assert http.post(url,json=payload,headers=headers).status_code==409
    assert http.get(url).status_code==409


def test_dxf_revision_edits_persist_and_undo_is_lossless(cli,dxf):
    import hashlib
    http,csrf,workspace=cli
    project=upload(http,csrf,dxf).json()
    pid=project["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    line=details(http,pid,rid)["native_lines"][0]
    assert line["origin"]=="CAD_NATIVE" and line["frame_id"]=="cad:Model"
    base=f"/api/projects/{pid}/edits"
    status=http.get(base)
    assert status.status_code==200
    assert status.json()["head"]=="original"
    assert status.json()["head_sha256"]==project["source_sha256"]
    req={
        "source_sha256":project["source_sha256"],"expected_head":"original",
        "expected_sha256":project["source_sha256"],
        "entity_id":line["entity_id"],"frame_id":line["frame_id"],
        "cad_handle":line["cad_handle"],
        "expected_start":line["points"][0],"expected_end":line["points"][1],
        "new_start":[1,2],"new_end":[6,2],"reviewer_label":"CAD reviewer",
    }
    orig=workspace/"projects"/pid/"input.dxf"
    initial=orig.read_bytes()
    drawing=workspace/"projects"/pid/"runs"/rid/"drawingir.json"
    initial_ir=drawing.read_bytes()
    response=http.post(base,json=req,headers={"X-Mimar-CSRF":csrf})
    assert response.status_code==201,response.text
    first=response.json()
    assert first["operation"]=="MOVE_LINE"
    assert first["legal_gate"]=="REGULATORY_LOCKED"
    assert first["cad_handle"]==line["cad_handle"].upper()
    rid1=first["revision_id"]
    download=http.get(base+f"/{rid1}/download")
    assert download.status_code==200
    assert hashlib.sha256(download.content).hexdigest()==first["sha256"]
    assert orig.read_bytes()==initial
    assert drawing.read_bytes()==initial_ir
    exported=workspace/"first-revision.dxf"
    exported.write_bytes(download.content)
    doc=ezdxf.readfile(exported)
    assert not doc.audit().has_errors
    modified=[e for e in doc.modelspace().query("LINE")
              if e.dxf.handle==line["cad_handle"]][0]
    assert tuple(modified.dxf.start) == (1,2,0)
    assert tuple(modified.dxf.end) == (6,2,0)
    assert len(list(doc.modelspace().query("LINE")))==4
    bad=http.post(base,json=req,headers={"X-Mimar-CSRF":csrf})
    assert bad.status_code==409  # optimistic stale edit rejected
    next_req=dict(req,expected_head=rid1,expected_sha256=first["sha256"],
                  expected_start=[1,2],expected_end=[6,2],
                  new_start=[2,2],new_end=[7,2])
    nxt=http.post(base,json=next_req,headers={"X-Mimar-CSRF":csrf})
    assert nxt.status_code==201,nxt.text
    second=nxt.json()
    assert second["parent_id"]==rid1
    undo=http.post(base+"/undo",json={
        "source_sha256":project["source_sha256"],
        "expected_head":second["revision_id"],"expected_sha256":second["sha256"]
    },headers={"X-Mimar-CSRF":csrf})
    assert undo.status_code==201,undo.text
    restored=undo.json()
    assert restored["operation"]=="UNDO"
    assert restored["sha256"]==first["sha256"]
    assert http.get(base+f"/{restored['revision_id']}/download").content == download.content
    assert http.get(base).json()["head"]==restored["revision_id"]
    assert len(http.get(base).json()["history"])==3
    assert http.get(base+f"/{second['revision_id']}/download").status_code==200
    assert orig.read_bytes()==initial and drawing.read_bytes()==initial_ir
    new_app=create_app(workspace)
    with TestClient(new_app,base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as after_restart:
        state=after_restart.get(base).json()
        assert state["head"]==restored["revision_id"]
        assert len(state["history"])==3
        assert after_restart.get(base+f"/{rid1}/download").content==download.content


def test_dxf_edit_security_and_pdf_rejected(cli,dxf,pdf):
    http,csrf,workspace=cli
    pid=upload(http,csrf,dxf).json()["project_id"]
    rid=run(http,csrf,pid).json()["run_id"]
    item=details(http,pid,rid)["native_lines"][0]
    project=http.get(f"/api/projects/{pid}").json()["project"]
    url=f"/api/projects/{pid}/edits"
    req={
        "source_sha256":project["source_sha256"],
        "expected_head":"original","expected_sha256":project["source_sha256"],
        "entity_id":item["entity_id"],"frame_id":item["frame_id"],
        "cad_handle":item["cad_handle"],
        "expected_start":item["points"][0],"expected_end":item["points"][1],
        "new_start":[1,1],"new_end":[2,1],"reviewer_label":"review",
    }
    assert http.post(url,json=req).status_code==403
    assert http.post(url,content=b"x"*4097,headers={"X-Mimar-CSRF":csrf}).status_code==413
    assert http.post(url,json={**req,"frame_id":"cad:Other"},
                     headers={"X-Mimar-CSRF":csrf}).status_code==422
    assert http.post(url,json={**req,"new_start":[2_000_000,1]},
                     headers={"X-Mimar-CSRF":csrf}).status_code==422
    assert http.post(url,json={**req,"new_end":[1,1]},
                     headers={"X-Mimar-CSRF":csrf}).status_code==409
    assert http.post(url,json={**req,"cad_handle":"BADBEEF"},
                     headers={"X-Mimar-CSRF":csrf}).status_code==409
    assert http.post(url,json={**req,"entity_id":"Model|FAKE|LINE"},
                     headers={"X-Mimar-CSRF":csrf}).status_code==409
    assert http.post(url,json={**req,"expected_end":[222,222]},
                     headers={"X-Mimar-CSRF":csrf}).status_code==409
    assert http.get(url+"/not-id/download").status_code==404
    assert http.get(url).json()["history"]==[]
    pdfpid=upload(http,csrf,pdf,"pdf").json()["project_id"]
    assert http.get(f"/api/projects/{pdfpid}/edits").status_code==415
    (workspace/"projects"/pid/"input.dxf").write_bytes(dxf+b"\nchanged")
    assert http.get(url).status_code==409
    assert http.post(url,json=req,headers={"X-Mimar-CSRF":csrf}).status_code==409


def test_dxf_edit_ui_offline_provenance(cli):
    http,_,_=cli
    page=http.get("/").text
    script=http.get("/static/dashboard.js").text
    assert 'id="edit-start-x"' in page
    assert 'id="edit-run"' in page
    assert 'id="edit-undo"' in page
    assert '"/edits"' in script
    assert 'download' in script
    assert "innerHTML" not in script
