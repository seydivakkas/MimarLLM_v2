"""027 synthetic trust gates: no actual GGUF weights or physical GPU needed."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import os

import ezdxf
import pytest
from fastapi.testclient import TestClient

from mimarllm.app.server import create_app
from mimarllm.importers.dxf import parse_dxf
from mimarllm.vlm.budget import HardwareSnapshot, BudgetError, plan_budget
from mimarllm.vlm.local_engine import (
    LocalVlmConfig, VlmFailure, preflight, command, chat_request,
    config_from_local_file,
)
from mimarllm.vlm.models import VlmRequest, VlmResult, parse_model_response
from mimarllm.vlm.source import selected_line_preview
from scripts.windows.configure_vlm_027 import configure


@pytest.fixture
def drawing(tmp_path):
    file=tmp_path/"native.dxf"
    doc=ezdxf.new("R2013")
    model=doc.modelspace()
    for a,b in [
        ((0,0),(6,0)), ((6,0),(6,3)),
        ((6,3),(0,3)), ((0,3),(0,0)),
    ]:
        model.add_line(a,b)
    doc.saveas(file)
    ir=parse_dxf(file).drawing
    return file,ir,tuple(e.entity_id for e in ir.entities)


def selection(ir, ids):
    return VlmRequest(
        source_sha256=ir.source_sha256, frame_id="cad:Model",
        entity_ids=ids, question="Yalnız kaynaklı çizgilerdeki belirsizliği belirt.",
        reviewer_label="synthetic reviewer", consent=True,
    )


def local_artifacts(tmp_path):
    runner=tmp_path/"llama-server"
    runner.write_bytes(b"fake offline llama server binary")
    runner.chmod(0o700)
    model=tmp_path/"model.gguf"
    model.write_bytes(b"GGUF" + b"M"*200)
    mmproj=tmp_path/"mmproj.gguf"
    mmproj.write_bytes(b"GGUF" + b"P"*200)
    return runner,model,mmproj


def config_for(tmp_path, **kwargs):
    exe,model,mmproj=local_artifacts(tmp_path)
    def digest(path):return sha256(path.read_bytes()).hexdigest()
    params=dict(
        llama_server_path=exe,llama_server_sha256=digest(exe),
        model_path=model,model_sha256=digest(model),
        mmproj_path=mmproj,mmproj_sha256=digest(mmproj),
    )
    params.update(kwargs)
    return LocalVlmConfig(**params)


def test_source_line_preview_provenance_and_non_mutation(drawing):
    file,ir,ids=drawing
    original=ir.model_dump_json(),file.read_bytes()
    output=selected_line_preview(ir,selection(ir,ids))
    assert output.startswith(b"\x89PNG\r\n\x1a\n")
    assert 500 < len(output) <= 350_000
    assert original==(ir.model_dump_json(),file.read_bytes())
    with pytest.raises(VlmFailure,match="SHA"):
        selected_line_preview(ir,selection(ir,ids).model_copy(update={"source_sha256":"f"*64}))
    with pytest.raises(VlmFailure,match="NATIVE"):
        selected_line_preview(ir,selection(ir,("Model|not-present|LINE",)))
    with pytest.raises(ValueError):
        selection(ir,(ids[0],ids[0]))


def test_untrusted_model_only_schema_rejects_overwrite_legal_numeric_and_new_sources(drawing):
    _,ir,ids=drawing
    accepted={"suggestions":[{"entity_ids":[ids[0]],"kind":"NEEDS_HUMAN_REVIEW",
                              "commentary":"Çizgilerin türü insan tarafından incelenmeli."}]}
    result=parse_model_response(json.dumps(accepted),ids)
    assert result.suggestions[0].entity_ids==(ids[0],)
    for tampered in [
        {"suggestions":[{"entity_ids":[ids[0]],"kind":"LEGAL_PASS","commentary":"confirmed"}]},
        {"suggestions":[{"entity_ids":["FAKE"],"kind":"WALL_CANDIDATE","commentary":"unknown"}]},
        {"suggestions":[{"entity_ids":[ids[0]],"kind":"WALL_CANDIDATE",
                         "commentary":"guess","physical_area_m2":100.0}]},
        {"suggestions":[{"entity_ids":[ids[0]],"kind":"WALL_CANDIDATE",
                         "commentary":"guess"}],"can_modify_drawing":True},
        {"suggestions":[{"entity_ids":[ids[0]],"kind":"WALL_CANDIDATE",
                         "commentary":"guess","status":"PASS"}]},
        {"suggestions":[{"entity_ids":[ids[0],ids[0]],"kind":"WALL_CANDIDATE",
                         "commentary":"guess"}]},
    ]:
        with pytest.raises(VlmFailure):
            parse_model_response(json.dumps(tampered),ids)
    with pytest.raises(VlmFailure):
        parse_model_response("X"*8200,ids)


def test_budget_fails_closed_gpu_unknown_and_reserves_memory():
    snapshot=HardwareSnapshot(available_ram_mib=7000)
    cpu=plan_budget(1_000_000_000,300_000_000,snapshot,gpu_requested=True)
    assert cpu.execution_mode=="CPU_FALLBACK" and cpu.n_gpu_layers==0
    assert cpu.estimate_only
    with pytest.raises(BudgetError,match="GPU"):
        plan_budget(1_000_000_000,300_000_000,snapshot,
                    gpu_requested=True,allow_cpu_fallback=False)
    with pytest.raises(BudgetError,match="RAM"):
        plan_budget(1_000_000_000,300_000_000,HardwareSnapshot(),gpu_requested=False)
    with pytest.raises(BudgetError,match="INSUFFICIENT"):
        plan_budget(1_000_000_000,300_000_000,
                    HardwareSnapshot(available_ram_mib=400),gpu_requested=False)
    available=HardwareSnapshot(
        available_ram_mib=8000,available_vram_mib=8192,
        gpu_probe="NVIDIA_SMI_SINGLE_DEVICE",
    )
    gpu=plan_budget(1_000_000_000,300_000_000,available,gpu_requested=True)
    assert gpu.execution_mode=="GPU_BUDGETED" and gpu.n_gpu_layers==99
    assert gpu.estimated_vram_required_mib<=8192
    low=plan_budget(1_000_000_000,300_000_000,
        HardwareSnapshot(available_ram_mib=8000,available_vram_mib=256,
                         gpu_probe="NVIDIA_SMI_SINGLE_DEVICE"),gpu_requested=True)
    assert low.execution_mode=="CPU_FALLBACK"


def test_local_gguf_mmproj_hash_gate_and_no_remote_url(drawing,tmp_path):
    _,ir,ids=drawing
    config=config_for(tmp_path,gpu_requested=True)
    hardware=HardwareSnapshot(available_ram_mib=8192)
    budget=preflight(config,hardware)
    assert budget.execution_mode=="CPU_FALLBACK"
    args=command(config,18283,budget)
    assert args[args.index("--host")+1]=="127.0.0.1"
    assert args[args.index("--fit")+1]=="off"
    assert "--mmproj" in args and "--no-mmproj-offload" in args
    assert "--hf-repo" not in args and "--mmproj-url" not in args
    prompt=chat_request(selected_line_preview(ir,selection(ir,ids)),
                        selection(ir,ids),config)
    assert prompt["response_format"]["type"]=="json_schema"
    assert prompt["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    config.mmproj_path.write_bytes(b"TAMPERED")
    with pytest.raises(VlmFailure,match="SHA"):
        preflight(config,hardware)


def test_trusted_local_setup_refuses_overwrite_and_is_not_browser_model_path(tmp_path):
    workspace=tmp_path/"work"
    workspace.mkdir()
    runner,model,mmproj=local_artifacts(tmp_path)
    target=configure(workspace,llama_server=runner,model=model,mmproj=mmproj,
                     gpu=False,cpu_fallback=True)
    configured=config_from_local_file(workspace)
    assert target==workspace/"vlm-runtime.json"
    assert configured.model_path==model and not configured.gpu_requested
    with pytest.raises(ValueError,match="Existing"):
        configure(workspace,llama_server=runner,model=model,mmproj=mmproj,
                  gpu=False,cpu_fallback=True)
    target.write_bytes(b"{}")
    with pytest.raises(VlmFailure,match="INVALID"):
        config_from_local_file(workspace)


def test_vlm_api_model_missing_and_strict_provenance(tmp_path,drawing,monkeypatch):
    input_file,ir,ids=drawing
    workspace=tmp_path/"dashboard"
    with TestClient(create_app(workspace),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        session=http.get("/api/session").json()
        csrf=session["csrf"]
        status=http.get("/api/vlm/status")
        assert status.status_code==200 and not status.json()["configured"]
        created=http.post("/api/projects",content=input_file.read_bytes(),headers={
            "X-Mimar-CSRF":csrf,"X-Mimar-Extension":"dxf",
        })
        assert created.status_code==201,created.text
        pid=created.json()["project_id"]
        run=http.post(f"/api/projects/{pid}/runs",
            json={"config":{},"formats":["json","html"]},
            headers={"X-Mimar-CSRF":csrf})
        assert run.status_code==201,run.text
        rid=run.json()["run_id"]
        details=http.get(f"/api/projects/{pid}/runs/{rid}").json()
        native=details["native_lines"]
        payload={
            "source_sha256":created.json()["source_sha256"],"frame_id":"cad:Model",
            "entity_ids":[n["entity_id"] for n in native],
            "question":"Lütfen yalnız olası çizim belirsizliklerini özetle.",
            "reviewer_label":"Reviewer","consent":True,
        }
        url=f"/api/projects/{pid}/runs/{rid}/vlm/suggest"
        assert http.post(url,json=payload).status_code==403
        assert http.post(url,json={k:v for k,v in payload.items() if k!="consent"},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(url,json=payload,headers={"X-Mimar-CSRF":csrf}).status_code==503
        modeldir=tmp_path/"models"
        modeldir.mkdir()
        config=config_for(modeldir)
        (workspace/"vlm-runtime.json").write_text(config.model_dump_json())
        assert http.get("/api/vlm/status").json()["configured"]
        assert http.post(url,json={**payload,"source_sha256":"f"*64},
            headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(url,json={**payload,"entity_ids":["BAD_SOURCE"]},
            headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert http.post(url,json={**payload,"question":"x"*321},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert http.post(url,content=b"x"*8193,
            headers={"X-Mimar-CSRF":csrf}).status_code==413
        before=(workspace/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()
        from mimarllm.vlm import local_engine
        def stub_infer(drawing,request,config):
            selected_line_preview(drawing,request)
            suggestions=parse_model_response(json.dumps({"suggestions":[{
                "entity_ids":[request.entity_ids[0]],"kind":"NEEDS_HUMAN_REVIEW",
                "commentary":"Semantik insan tarafından doğrulanmalı."
            }]}),request.entity_ids)
            return VlmResult(source_sha256=request.source_sha256,frame_id=request.frame_id,
                source_entity_ids=request.entity_ids,reviewer_label=request.reviewer_label,
                model_sha256=config.model_sha256,mmproj_sha256=config.mmproj_sha256,
                execution_mode="CPU_FALLBACK",suggestions=suggestions.suggestions)
        monkeypatch.setattr(local_engine,"infer",stub_infer)
        success=http.post(url,json=payload,headers={"X-Mimar-CSRF":csrf})
        assert success.status_code==200,success.text
        response=success.json()
        assert response["status"]=="UNVERIFIED_VLM_SUGGESTION"
        assert response["can_modify_drawing"] is False
        assert response["can_approve_regulations"] is False
        assert response["legal_gate"]=="REGULATORY_LOCKED"
        assert (workspace/"projects"/pid/"runs"/rid/"drawingir.json").read_bytes()==before
        assert not (workspace/"projects"/pid/"runs"/rid/"vlm-result.json").exists()


def test_vlm_panel_not_a_certification(tmp_path):
    with TestClient(create_app(tmp_path/"u"),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as http:
        page=http.get("/").text
        js=http.get("/static/dashboard.js").text
        assert 'id="vlm-opt-in"' in page and 'id="vlm-infer"' in page
        assert 'id="vlm-results"' in page
        assert '"/api/vlm/status"' in js
        assert '"/vlm/suggest"' in js
        assert "innerHTML" not in js
        assert "https://" not in page
