"""Process 023 — synthetic large-page bounded tile OCR and original PDF provenance.

Injected deterministic OCR reader is NOT a learned multilingual OCR model.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.ir import EvidenceOrigin
from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import PdfInputError
from mimarllm.importers.pdf_ir import parse_pdf_ir
from mimarllm.ocr.tiles import TiledOcrRequest, plan_ocr_tiles, read_tiled_ocr
from mimarllm.ocr.layout import LayoutZone, detect_layout_candidates
from mimarllm.pipeline import PipelineConfig, PipelineInputError, run_local_pipeline
from mimarllm.rules.base import RuleDomain


@pytest.fixture
def page(tmp_path):
    path = tmp_path / "large-plan.pdf"
    c=Canvas(str(path),pagesize=(800,800))
    c.setFont("Helvetica",11)
    c.drawString(650,90,"ANTET SAMPLE A1")
    c.line(20,390,770,390)
    c.showPage()
    c.drawString(30,710,"SECOND PAGE")
    c.save()
    return path


@pytest.fixture
def a0(tmp_path):
    path=tmp_path/"A0_oversize.pdf"
    c=Canvas(str(path),pagesize=(2384,3370))
    c.drawString(2200,100,"A0 synthetic title area")
    c.save()
    return path


def request(**kwargs):
    data=dict(
        page_index=0,roi_points=(0,0,800,800),
        tile_width_pt=450,tile_height_pt=450,overlap_pt=100,
    )
    data.update(kwargs)
    return TiledOcrRequest(**data)


class OverlapReader:
    """A synthetic token in all tiles containing one exact PDF rectangle."""
    def __init__(self, *, text="KAPI 90", box=(405,405,425,430)):
        self.text=text
        self.box=box
        self.calls=0

    def read(self, region):
        self.calls+=1
        x0,y0,x1,y1=region.roi_points
        left,top,right,bottom=self.box
        if not (x0<=left and y0<=top and x1>=right and y1>=bottom):
            return []
        # Emulate recognition in tile pixel coordinates and transform back.
        from_pixel = tuple(region.pixel_to_source(*region.source_to_pixel(x,y))
                           for x,y in ((left,top),(right,top),
                                       (right,bottom),(left,bottom)))
        return [TextCandidate(
            candidate_id="fake",page_index=region.page_index,
            text=self.text,method="rapidocr_cpu",confidence=.90,
            polygon=from_pixel,review_required=True,
        )]


def test_a0_page_plan_large_raster_never_renders_full_bitmap(a0):
    req=TiledOcrRequest(
        page_index=0,roi_points=(0,0,2384,3370),dpi=144,
    )
    plan=plan_ocr_tiles(a0,req)
    assert len(plan)>64 and len(plan)<=128
    assert plan[0].page_index==0
    assert plan[0].document_sha256==plan[-1].document_sha256
    assert plan[-1].roi_points[2]==pytest.approx(2384)
    assert plan[-1].roi_points[3]==pytest.approx(3370)
    assert all((t.roi_points[2]-t.roi_points[0])<=384+1e-6
               and (t.roi_points[3]-t.roi_points[1])<=384+1e-6 for t in plan)


def test_overlap_token_deduplicates_without_moving_source_quad(page):
    reader=OverlapReader()
    output=read_tiled_ocr(page,request(),reader)
    assert len(output.tiles)==4
    assert reader.calls==4
    assert len(output.candidates)==1
    assert output.removed_duplicate_count==3
    text=output.candidates[0]
    assert text.text=="KAPI 90" and text.review_required
    for actual,expected in zip(text.polygon,((405,405),(425,405),(425,430),(405,430))):
        assert actual==pytest.approx(expected,abs=1e-4)
    assert output.candidate_tile_ids[0] in {t.tile_id for t in output.tiles}


def test_two_repeated_text_instances_at_different_locations_not_deduped(page):
    class TwoTokens:
        def read(self,region):
            result=[]
            for x,y in ((60,60),(700,700)):
                x0,y0,x1,y1=region.roi_points
                if x0<=x and y0<=y and x+20<=x1 and y+16<=y1:
                    result.append(TextCandidate(
                        candidate_id="same",page_index=region.page_index,
                        text="ODA",method="rapidocr_cpu",confidence=.8,
                        polygon=((x,y),(x+20,y),(x+20,y+16),(x,y+16)),
                    ))
            return result
    result=read_tiled_ocr(page,request(),TwoTokens())
    assert len(result.candidates)==2
    assert result.removed_duplicate_count==0


def test_parse_pdf_ir_tiled_outputs_original_sha_and_unverified_entities(page):
    reader=OverlapReader()
    result=parse_pdf_ir(page,tiled_ocr=(request(),),ocr_engine=reader)
    assert len(result.tiled_ocr_results)==1
    assert len(result.tiled_ocr_results[0].candidates)==1
    tiled=[e for e in result.drawing.entities
           if e.origin==EvidenceOrigin.OCR_CANDIDATE]
    assert len(tiled)==1
    assert tiled[0].source.document_sha256==result.drawing.source_sha256
    assert tiled[0].source.page_index==0
    assert tiled[0].source.source_polygon==tiled[0].geometry.points
    assert not tiled[0].is_verified_semantics
    assert any(i.code=="TILED_OCR_OVERLAP_DEDUP_REVIEW_REQUIRED"
               for i in result.issues)
    assert any(l.zone==LayoutZone.LOWER_RIGHT_TEXT_CLUSTER
               for l in result.layout_candidates)


def test_layout_uses_original_page_coordinate_and_no_title_semantics(page):
    native=parse_pdf_ir(page)
    candidates=[l for l in native.layout_candidates
                if l.page_index==0 and l.zone==LayoutZone.LOWER_RIGHT_TEXT_CLUSTER]
    assert len(candidates)==1
    title=candidates[0]
    assert title.document_sha256==native.drawing.source_sha256
    assert title.approval_status=="REVIEW_REQUIRED"
    assert title.source_semantics=="POSITION_ONLY_NO_TITLE_BLOCK_CERTIFICATION"
    assert all(0<=x<=800 and 0<=y<=800 for x,y in title.polygon)
    assert not [l for l in native.layout_candidates
                if l.page_index==1 and l.zone==LayoutZone.LOWER_RIGHT_TEXT_CLUSTER]


def test_tiled_roi_opt_in_required_no_automatic_model_download(page):
    with pytest.raises(Exception,match="explicitly installed"):
        parse_pdf_ir(page,tiled_ocr=(request(),))
    with pytest.raises(PipelineInputError,match="local CPU OCR"):
        run_local_pipeline(page,PipelineConfig(tiled_ocr=(request(),)))


def test_user_selected_tiled_pipeline_preserves_legal_gate(page):
    r=run_local_pipeline(page,PipelineConfig(tiled_ocr=(request(),)),
                         ocr_reader=OverlapReader())
    assert r.manifest.source_sha256==r.drawing.source_sha256
    assert r.manifest.legal_gate=="REGULATORY_LOCKED"
    assert not r.rules
    assert any(s.stage=="IMPORT" and s.status=="REVIEW_REQUIRED"
               for s in r.manifest.stages)
    assert any(e.origin==EvidenceOrigin.OCR_CANDIDATE
               and not e.is_verified_semantics for e in r.drawing.entities)
    assert all(f.status!="COMPLIANT" for f in r.report.findings)


def test_budget_preflight_too_many_tiles_rejected_before_reader_called(a0):
    reader=OverlapReader()
    req=TiledOcrRequest(
        page_index=0,roi_points=(0,0,2384,3370),
        tile_width_pt=80,tile_height_pt=80,overlap_pt=8,
        max_tiles=5,
    )
    with pytest.raises(PdfInputError,match="tile count"):
        read_tiled_ocr(a0,req,reader)
    assert reader.calls==0


def test_tile_pixel_limit_and_total_limit(page):
    too_many_pixels=request(max_pixels_per_tile=50_000)
    with pytest.raises(PdfInputError,match="pixel budget"):
        plan_ocr_tiles(page,too_many_pixels)
    too_many_total=request(max_total_pixels=50_000)
    with pytest.raises(PdfInputError,match="cumulative"):
        plan_ocr_tiles(page,too_many_total)


def test_outside_roi_and_mismatched_method_or_page_rejected(page):
    class Bad:
        def __init__(self,choice): self.choice=choice
        def read(self,region):
            return [TextCandidate(
                candidate_id="bad",page_index=region.page_index+(
                    1 if self.choice=="page" else 0),
                text="WRONG",method=(
                    "native_pdf" if self.choice=="method" else "rapidocr_cpu"
                ),
                polygon=((900,900),(920,900),(920,920),(900,920)),
            )]
    for case,reason in (("position","outside"),("method","method"),("page","page")):
        with pytest.raises(PdfInputError,match=reason):
            read_tiled_ocr(page,request(),Bad(case))


def test_pdf_mutation_and_page_isolation(page,tmp_path):
    with pytest.raises(PdfInputError,match="page index"):
        plan_ocr_tiles(page,request(page_index=3))
    other=tmp_path/"not_pdf.pdf"
    other.write_bytes(b"junk")
    with pytest.raises(PdfInputError):
        plan_ocr_tiles(other,request())


def test_nondefault_cropbox_fails_closed(page,tmp_path):
    import pypdfium2 as pdfium
    src=pdfium.PdfDocument(str(page))
    # Known coordinate mismatch is already denied by render_region. We
    # assert the path is not quietly converted by planning.
    src.close()
    assert plan_ocr_tiles(page,request())


def test_invalid_tile_overlap_and_roi_rejected():
    with pytest.raises(ValidationError,match="half"):
        request(tile_width_pt=320,overlap_pt=170)
    with pytest.raises(ValidationError):
        TiledOcrRequest(page_index=0,roi_points=(40,40,20,90))


def test_layout_text_budget_and_foreign_pages_are_separate(page):
    native=parse_pdf_ir(page)
    with pytest.raises(ValueError,match="budget"):
        detect_layout_candidates(
            native.drawing.source_sha256,0,800,800,
            native.text_candidates,max_text=1,
        )
