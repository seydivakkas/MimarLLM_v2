"""026: 2.5D source provenance, geometry safety and localhost API contracts."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import ezdxf
import pytest
from fastapi.testclient import TestClient

from mimarllm.app.server import create_app
from mimarllm.core.units import UnitCalibration, CalibrationMethod
from mimarllm.geometry.massing25d import (
    MassingError, MassingRequest, build_massing_candidate,
)
from mimarllm.importers.dxf import parse_dxf


@pytest.fixture
def source(tmp_path):
    file=tmp_path/"square.dxf"
    doc=ezdxf.new("R2013")
    doc.header["$INSUNITS"]=6
    model=doc.modelspace()
    for a,b in [
        ((0,0),(5,0)), ((5,0),(5,4)),
        ((5,4),(0,4)), ((0,4),(0,0)),
    ]:
        model.add_line(a,b)
    doc.saveas(file)
    drawing=parse_dxf(file).drawing
    entities=tuple(entity.entity_id for entity in drawing.entities)
    return file,drawing,entities


def calibrated(drawing, ids):
    drawing.calibration=UnitCalibration.from_reference(
        source_distance=5,known_distance_metres=5,
        evidence_id=ids[0],method=CalibrationMethod.USER_REFERENCE,
        user_confirmed=True,
    )
    drawing.calibration_frame_id="cad:Model"
    return drawing


def req(drawing, ids, height=3.4):
    return MassingRequest(
        source_sha256=drawing.source_sha256, frame_id="cad:Model",
        source_entity_ids=ids, declared_height_m=height,
        reviewer_label="synthetic reviewer",
    )


def test_native_rectangle_explicit_height_provenance_and_no_mutation(source):
    path, drawing, ids=source
    original=path.read_bytes()
    before=drawing.model_dump_json()
    with pytest.raises(MassingError,match="calibration"):
        build_massing_candidate(drawing,req(drawing,ids))
    drawing=calibrated(drawing,ids)
    frozen=drawing.model_dump_json()
    mass=build_massing_candidate(drawing,req(drawing,ids))
    assert mass.schema_version=="026-0.1"
    assert mass.source_sha256==sha256(original).hexdigest()
    assert mass.status=="UNVERIFIED_MASSING_SCENARIO"
    assert mass.legal_gate=="REGULATORY_LOCKED"
    assert mass.certified_building is False
    assert mass.height_kind=="USER_DECLARED_SCENARIO"
    assert mass.declared_height_m==3.4
    assert mass.footprint_area_m2==pytest.approx(20.0)
    assert set(mass.source_entity_ids)==set(ids)
    assert len(mass.source_cad_handles)==4
    assert mass.calibration_evidence_ids==(ids[0],)
    assert len(mass.footprint_metres)==4
    assert path.read_bytes()==original and drawing.model_dump_json()==frozen
    assert before != frozen  # only explicit calibration changed DrawingIR


def test_reject_nonclosed_wrong_source_wrong_frame_or_duplicate(source):
    path, drawing, ids=source
    calibrated(drawing,ids)
    cases=[
        (ids[:3],"boundary"),
        (ids[:2]+ids[:2],"boundary"),
    ]
    for subset,_ in cases:
        if len(set(subset))<len(subset):
            with pytest.raises(ValueError):
                req(drawing,subset)
        else:
            with pytest.raises(MassingError):
                build_massing_candidate(drawing,req(drawing,subset))
    with pytest.raises(MassingError,match="SHA"):
        build_massing_candidate(drawing,req(drawing.model_copy(update={"source_sha256":"f"*64}),ids))
    with pytest.raises(ValueError):
        req(drawing,ids,height=float("nan"))
    with pytest.raises(ValueError):
        req(drawing,ids,height=200)
    with pytest.raises(MassingError):
        build_massing_candidate(drawing,req(drawing,ids).model_copy(update={"frame_id":"cad:Other"}))
    drawing.calibration=UnitCalibration.from_dxf_insunits(6,user_confirmed=True)
    with pytest.raises(MassingError,match="Header-only"):
        build_massing_candidate(drawing,req(drawing,ids))


def test_nested_block_source_cannot_be_massing_boundary(tmp_path):
    file=tmp_path/"nested.dxf"
    doc=ezdxf.new()
    doc.header["$INSUNITS"]=6
    block=doc.blocks.new(name="X")
    for a,b in [((0,0),(4,0)),((4,0),(4,4)),((4,4),(0,4)),((0,4),(0,0))]:
        block.add_line(a,b)
    doc.modelspace().add_blockref("X",(0,0))
    doc.saveas(file)
    drawing=parse_dxf(file).drawing
    native=[e.entity_id for e in drawing.entities if e.type_candidate=="LINE"]
    assert len(native)==4
    calibrated(drawing,native)
    with pytest.raises(MassingError,match="direct source"):
        build_massing_candidate(drawing,req(drawing,tuple(native)))


def test_local_endpoint_requires_confirmed_scale_and_preserves_report(source,tmp_path):
    source_file,_,_=source
    workspace=tmp_path/"workspace"
    with TestClient(create_app(workspace),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        token=http.get("/api/session").json()["csrf"]
        response=http.post("/api/projects",content=source_file.read_bytes(),headers={
            "X-Mimar-CSRF":token,"X-Mimar-Extension":"dxf",
        })
        assert response.status_code==201
        project=response.json()
        pid=project["project_id"]
        def analyze(config):
            return http.post(f"/api/projects/{pid}/runs",
                             json={"config":config,"formats":["json","html"]},
                             headers={"X-Mimar-CSRF":token})
        first=analyze({})
        assert first.status_code==201,first.text
        rid=first.json()["run_id"]
        first_read=http.get(f"/api/projects/{pid}/runs/{rid}").json()
        native=first_read["native_lines"]
        assert len(native)==4
        endpoint=f"/api/projects/{pid}/runs/{rid}/massing25d"
        payload={
            "source_sha256":project["source_sha256"], "frame_id":"cad:Model",
            "source_entity_ids":[n["entity_id"] for n in native],
            "declared_height_m":3.4,"reviewer_label":"Review",
        }
        assert http.post(endpoint,json=payload).status_code==403
        denied=http.post(endpoint,json=payload,headers={"X-Mimar-CSRF":token})
        assert denied.status_code==409
        ref=native[0]
        from math import dist
        scale={"calibration":{
            "entity_id":ref["entity_id"],
            "known_length_metres":dist(*ref["points"]),
            "reviewer_id":"Reviewer","method":"USER_REFERENCE",
        }}
        second=analyze(scale)
        assert second.status_code==201,second.text
        rid2=second.json()["run_id"]
        endpoint=f"/api/projects/{pid}/runs/{rid2}/massing25d"
        original_ir=(workspace/"projects"/pid/"runs"/rid2/"drawingir.json").read_bytes()
        result=http.post(endpoint,json=payload,headers={"X-Mimar-CSRF":token})
        assert result.status_code==200,result.text
        obj=result.json()
        assert obj["footprint_area_m2"]==pytest.approx(20)
        assert obj["legal_gate"]=="REGULATORY_LOCKED"
        assert obj["height_kind"]=="USER_DECLARED_SCENARIO"
        assert (workspace/"projects"/pid/"runs"/rid2/"drawingir.json").read_bytes()==original_ir
        assert http.post(endpoint,json={**payload,"source_sha256":"f"*64},
                         headers={"X-Mimar-CSRF":token}).status_code==409
        assert http.post(endpoint,json={**payload,"source_entity_ids":payload["source_entity_ids"][:3]},
                         headers={"X-Mimar-CSRF":token}).status_code==409
        assert http.post(endpoint,content=b"x"*12001,
                         headers={"X-Mimar-CSRF":token}).status_code==413
        assert http.post(endpoint,json={**payload,"declared_height_m":-10},
                         headers={"X-Mimar-CSRF":token}).status_code==422
        assert http.get(f"/api/projects/{pid}/runs/{rid2}/files/scene25d.js").status_code==404


def test_026_static_is_offline_only_and_no_unapproved_semantics(source,tmp_path):
    with TestClient(create_app(tmp_path/"ui"),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        page=http.get("/").text
        ui=http.get("/static/dashboard.js").text
        scene=http.get("/static/scene25d.js")
        assert scene.status_code==200
        assert 'id="massing-height"' in page
        assert 'id="massing-build"' in page
        assert 'id="massing-canvas"' in page
        assert "import * as THREE" in scene.text
        assert 'from "./three.module.js"' in scene.text
        assert 'import("/static/scene25d.js")' in ui
        assert "UNVERIFIED_MASSING_SCENARIO" in ui
        assert "https://" not in page
        assert "innerHTML" not in ui and "eval(" not in ui
        assert "script-src 'self'" in http.get("/").headers["content-security-policy"]
