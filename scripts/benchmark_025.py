"""Synthetic, reproducible Windows/Linux CAD performance profile (not field UAT)."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
from statistics import median
import tempfile
from time import perf_counter, process_time
import tracemalloc

import ezdxf

from mimarllm.app.dxf_edits import DxfRevisions, EditRequest, UndoRequest
from mimarllm.importers.dxf import parse_dxf


def timed(fn):
    start = perf_counter()
    result = fn()
    return result, round((perf_counter()-start)*1000, 3)


def profile(output_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="mimar-perf-025-") as td:
        root=Path(td)
        project=root/"project"
        project.mkdir()
        drawing=ezdxf.new("R2013")
        model=drawing.modelspace()
        first=None
        for x in range(500):
            entity=model.add_line((float(x),0),(float(x),10))
            if first is None:
                first=entity.dxf.handle
        original=project/"input.dxf"
        drawing.saveas(original)
        content=original.read_bytes()
        sha=sha256(content).hexdigest()

        tracemalloc.start()
        cpu_start=process_time()
        parsed_ms=[]
        for _ in range(5):
            result,ms=timed(lambda:parse_dxf(original))
            if result.drawing.source_sha256!=sha or len(result.drawing.entities)!=500:
                raise RuntimeError("Synthetic DXF parser output not provenance-consistent")
            parsed_ms.append(ms)
        store=DxfRevisions()
        command=EditRequest(
            source_sha256=sha, expected_head="original",expected_sha256=sha,
            entity_id=f"Model|{first}|LINE",frame_id="cad:Model",cad_handle=first,
            expected_start=(0,0),expected_end=(0,10),
            new_start=(1,1),new_end=(1,11),reviewer_label="synthetic-benchmark")
        revision,edit_ms=timed(lambda:store.revise(project,sha,command))
        if original.read_bytes()!=content:
            raise RuntimeError("Original DXF mutated")
        undo,undo_ms=timed(lambda:store.undo(project,sha,UndoRequest(
            source_sha256=sha,expected_head=revision["revision_id"],
            expected_sha256=revision["sha256"])))
        if undo["sha256"]!=sha:
            raise RuntimeError("Undo not byte-exact")
        current,peak_bytes=tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cpu_ms=(process_time()-cpu_start)*1000
        ordered=sorted(parsed_ms)
        report={
            "schema_version":1,
            "kind":"SYNTHETIC_025_NOT_FIELD_ACCEPTANCE",
            "platform":platform.platform(),
            "python":platform.python_version(),
            "processor":platform.processor(),
            "cpu_count":os.cpu_count(),
            "source_bytes":len(content),
            "cad_line_entities":500,
            "parse_wall_ms_samples":parsed_ms,
            "parse_wall_ms_median":round(median(parsed_ms),3),
            "parse_wall_ms_max":max(ordered),
            "edit_wall_ms":edit_ms,
            "undo_wall_ms":undo_ms,
            "cpu_ms_total":round(cpu_ms,3),
            "python_tracemalloc_peak_bytes":peak_bytes,
            "memory_scope":"PYTHON_ALLOCATIONS_ONLY_NOT_NATIVE_DLL_RSS",
            "original_sha256":sha,
            "source_mutated":False,
            "legal_gate":"REGULATORY_LOCKED",
            "measurement_limits":"Runner variability; not 95th percentile, physical machine or A0/A1/real CAD acceptance",
        }
        output_path.parent.mkdir(parents=True,exist_ok=True)
        output_path.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
        return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    arguments=parser.parse_args()
    data=profile(arguments.output)
    print(json.dumps({"synthetic":data["kind"],"parse_ms":data["parse_wall_ms_samples"],
                      "edit_ms":data["edit_wall_ms"],"undo_ms":data["undo_wall_ms"],
                      "python_peak_bytes":data["python_tracemalloc_peak_bytes"]}))
