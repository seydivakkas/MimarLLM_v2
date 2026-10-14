"""Process 018 CLI integration: local files only, bounded config, output safety."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import ezdxf
import pytest
from reportlab.pdfgen.canvas import Canvas

from mimarllm.cli import main
from mimarllm.pipeline import PipelineConfig


@pytest.fixture
def dxf(tmp_path):
    p=tmp_path/"local-plan.dxf"
    doc=ezdxf.new("R2013")
    m=doc.modelspace()
    m.add_line((0,0),(5,0))
    m.add_line((5,0),(5,4))
    m.add_line((5,4),(0,4))
    m.add_line((0,4),(0,0))
    doc.saveas(p)
    return p


@pytest.fixture
def pdf(tmp_path):
    p=tmp_path/"drawing.pdf"
    c=Canvas(str(p),pagesize=(430,330))
    c.drawString(35,270,"Synthetic architectural evidence only")
    c.line(40,230,320,230)
    c.save()
    return p


def test_cli_dxf_default_emits_html_json_manifest_with_source_sha(dxf,tmp_path,capsys):
    out=tmp_path/"output"
    out.mkdir()
    status=main(["analyze",str(dxf),"--output-dir",str(out)])
    captured=capsys.readouterr()
    assert status==0 and not captured.err
    assert "MIMARLLM_COMPLETED_WITH_REVIEW_GATES" in captured.out
    assert "REGULATORY_LOCKED" in captured.out
    assert (out/"analysis.json").is_file()
    assert (out/"analysis.html").is_file()
    manifest=json.loads((out/"pipeline-manifest.json").read_text("utf-8"))
    report=json.loads((out/"analysis.json").read_text("utf-8"))
    assert report["drawing_sha256"]==manifest["source_sha256"]
    assert report["legal_gate"]=="REGULATORY_LOCKED"
    assert manifest["completion"]=="COMPLETED_WITH_REVIEW_GATES"
    assert any(stage["stage"]=="CALIBRATION"
               and stage["status"]=="REVIEW_REQUIRED" for stage in manifest["stages"])


def test_cli_python_module_entrypoint_works_offline(dxf,tmp_path):
    out=tmp_path/"cli"
    out.mkdir()
    proc=subprocess.run([
        sys.executable,"-m","mimarllm.cli","analyze",str(dxf),
        "--output-dir",str(out),"--format","json",
    ],capture_output=True,text=True,timeout=45)
    assert proc.returncode==0,(proc.stderr[-500:])
    assert (out/"analysis.json").exists()
    assert not (out/"analysis.html").exists()
    assert (out/"pipeline-manifest.json").exists()


def test_cli_pdf_embeds_real_verified_page_image(pdf,tmp_path):
    out=tmp_path/"out"
    out.mkdir()
    rc=main(["analyze",str(pdf),"--output-dir",str(out),"--format","html"])
    assert rc==0
    html=(out/"analysis.html").read_text("utf-8")
    assert "data:image/png;base64," in html
    assert "REGULATORY_LOCKED" in html


def test_cli_existing_report_rejected_and_untouched(dxf,tmp_path,capsys):
    out=tmp_path/"out"
    out.mkdir()
    (out/"analysis.json").write_text("IMPORTANT",encoding="utf-8")
    rc=main(["analyze",str(dxf),"--output-dir",str(out)])
    assert rc==2
    assert (out/"analysis.json").read_text("utf-8")=="IMPORTANT"
    assert not (out/"analysis.html").exists()
    assert not (out/"pipeline-manifest.json").exists()
    assert "overwrite" in capsys.readouterr().err


def test_cli_invalid_json_and_unknown_config_field_rejected(dxf,tmp_path,capsys):
    out=tmp_path/"out"
    out.mkdir()
    cfg=tmp_path/"bad.json"
    cfg.write_text('{"remote_api_key":"forbidden"}',encoding="utf-8")
    rc=main(["analyze",str(dxf),"--output-dir",str(out),
             "--config",str(cfg)])
    assert rc==2
    assert "invalid" in capsys.readouterr().err.lower()
    assert list(out.iterdir())==[]


def test_cli_bad_source_no_stacktrace(dxf,tmp_path,capsys):
    out=tmp_path/"out"
    out.mkdir()
    rc=main(["analyze",str(tmp_path/"nope.dxf"),"--output-dir",str(out)])
    stderr=capsys.readouterr().err
    assert rc==2
    assert "Traceback" not in stderr
    assert list(out.iterdir())==[]


def test_cli_missing_output_directory_and_pdf_format(dxf,tmp_path):
    out=tmp_path/"missing"
    assert main(["analyze",str(dxf),"--output-dir",str(out)])==2
    out.mkdir()
    assert main(["analyze",str(dxf),"--output-dir",str(out),
                 "--format","pdf","--format","md"])==0
    assert (out/"analysis.pdf").read_bytes().startswith(b"%PDF")
    assert (out/"analysis.md").exists()


def test_cli_config_with_regulatory_rule_remains_insufficient(dxf,tmp_path):
    out=tmp_path/"out"
    out.mkdir()
    config=tmp_path/"config.json"
    config.write_text(json.dumps({
        "rules":[{
            "definition":{
                "rule_id":"fake.regulation","version":"0.1",
                "domain":"REGULATORY","metric":"SEGMENT_LENGTH_M",
                "description":"UNVERIFIED law",
                "operator":">=","threshold":1.2,
                "legal_source":{
                    "document_sha256":"0"*64,"page_index":0,
                    "regulation_id":"FAKE","article_id":"7",
                    "effective_from":"2026-01-01",
                },
            },
        }]
    }),encoding="utf-8")
    assert main(["analyze",str(dxf),"--output-dir",str(out),
                 "--config",str(config)])==0
    report=json.loads((out/"analysis.json").read_text("utf-8"))
    found=next(f for f in report["findings"]
               if f["kind"]=="REGULATORY_CANDIDATE")
    assert found["status"]=="INSUFFICIENT_EVIDENCE"
    assert found["legal_evidence"] is None
    assert report["legal_gate"]=="REGULATORY_LOCKED"


def test_cli_ocr_roi_needs_local_cpu_only_or_explicit_error(dxf,tmp_path,capsys):
    out=tmp_path/"out"
    out.mkdir()
    cfg=tmp_path/"roi.json"
    cfg.write_text(json.dumps({
        "ocr_regions":{"0":[[10,10,100,90]]}
    }),encoding="utf-8")
    result=main(["analyze",str(dxf),"--output-dir",str(out),
                 "--config",str(cfg)])
    assert result != 0
    assert not list(out.iterdir())
    assert "Traceback" not in capsys.readouterr().err


def test_cli_format_order_and_duplicate_format_not_duplicate_outputs(dxf,tmp_path):
    out=tmp_path/"out"
    out.mkdir()
    assert main(["analyze",str(dxf),"--output-dir",str(out),
                 "--format","json","--format","json","--format","md"])==0
    assert sorted(p.name for p in out.iterdir())==[
        "analysis.json","analysis.md","pipeline-manifest.json",
    ]
