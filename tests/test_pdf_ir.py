"""PDF to DrawingIR integration: genuine synthetic PDFs and injected CPU OCR."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from PIL import ImageChops
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.ir import CoordinateKind, EvidenceOrigin, PrimitiveKind
from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import PdfInputError, render_region
from mimarllm.importers.pdf_ir import parse_pdf_ir
from mimarllm.ocr.rapid_engine import RapidCpuOcr, OcrUnavailable


@pytest.fixture()
def diagram_pdf(tmp_path):
    target = tmp_path / "test-drawing.pdf"
    canvas = Canvas(str(target), pagesize=(432, 288))
    canvas.drawString(40, 220, "ROOM 12.50")
    canvas.line(25, 55, 205, 170)      # diagonal: bbox endpoints are wrong!
    canvas.rect(50, 75, 70, 80)
    canvas.bezier(210, 30, 245, 200, 320, 170, 345, 80)
    canvas.showPage()
    canvas.drawString(30, 230, "SECOND PAGE")
    canvas.line(35, 65, 85, 65)
    canvas.save()
    return target


class FakeCpuOcr:
    """In-memory stand-in. Never loads a model or makes a network request."""

    def read(self, region):
        polygon = ((4.0, 8.0), (72.0, 8.0),
                   (72.0, 32.0), (4.0, 32.0))
        source_quad = tuple(region.pixel_to_source(x, y) for x, y in polygon)
        return [TextCandidate(
            candidate_id="synthetic", page_index=region.page_index,
            text="KAPI 90", method="rapidocr_cpu",
            polygon=source_quad, confidence=.88, review_required=True,
        )]


def test_multi_page_pdf_native_ir_provenance_and_true_diagonal(diagram_pdf):
    result = parse_pdf_ir(diagram_pdf)
    ir = result.drawing
    assert ir.source_kind.value == "PDF"
    assert ir.calibration.metres_per_unit is None
    assert len(ir.frames) == 2
    assert all(f.kind is CoordinateKind.PDF_POINT and f.y_direction.value == "DOWN"
               for f in ir.frames)
    assert {e.source.page_index for e in ir.entities} == {0, 1}
    assert all(e.source.document_sha256 == ir.source_sha256 for e in ir.entities)
    assert all(e.frame_id == f"pdf:page{e.source.page_index}" for e in ir.entities)
    assert all(e.origin is EvidenceOrigin.PDF_NATIVE for e in ir.entities)
    assert not ir.findings and not ir.measurements
    line = next(e for e in ir.entities
                if e.type_candidate == "PDF_LINE" and e.source.page_index == 0)
    assert line.geometry.kind is PrimitiveKind.SEGMENT
    assert line.geometry.points[0] == pytest.approx((25, 233))
    assert line.geometry.points[1] == pytest.approx((205, 118))
    assert line.geometry.points != (line.source.source_polygon[0], line.source.source_polygon[2])
    rect = next(e for e in ir.entities if e.type_candidate == "PDF_RECT")
    assert rect.geometry.kind is PrimitiveKind.POLYGON
    assert len(rect.geometry.points) == 4
    curve = next(e for e in ir.entities if e.type_candidate == "PDF_CURVE")
    assert len(curve.geometry.points) > 4
    assert any(s.code == "APPROXIMATED_PDF_CURVE" for s in result.issues)
    assert any(t.text == "R" and t.method == "native_pdf" for t in result.text_candidates)
    assert all(t.confidence is None for t in result.text_candidates)


def test_explicit_ocr_region_preserves_rotated_quadrilateral_and_unique_ids(diagram_pdf):
    roi = (15.0, 15.0, 115.0, 115.0)
    result = parse_pdf_ir(
        diagram_pdf, ocr_regions={0: [roi, roi]}, ocr_engine=FakeCpuOcr(),
    )
    ocr = [t for t in result.text_candidates if t.method == "rapidocr_cpu"]
    assert len(ocr) == 2
    assert len({t.candidate_id for t in ocr}) == 2
    entities = [e for e in result.drawing.entities
                if e.origin is EvidenceOrigin.OCR_CANDIDATE]
    assert len(entities) == 2
    assert all(e.geometry.kind is PrimitiveKind.POLYGON for e in entities)
    assert all(e.is_verified_semantics is False for e in entities)
    assert all(e.source.source_polygon == e.geometry.points for e in entities)
    assert all(e.source.document_sha256 == result.drawing.source_sha256 for e in entities)


def test_ocr_without_explicit_reader_never_auto_downloads(diagram_pdf):
    with pytest.raises(OcrUnavailable, match="explicitly installed"):
        parse_pdf_ir(diagram_pdf, ocr_regions={0: [(10, 10, 100, 100)]})


def test_ocr_bad_page_index_and_excessive_rois_rejected(diagram_pdf):
    with pytest.raises(PdfInputError, match="unavailable page"):
        parse_pdf_ir(diagram_pdf, ocr_regions={9: [(0, 0, 10, 10)]},
                     ocr_engine=FakeCpuOcr())
    with pytest.raises(PdfInputError, match="budget"):
        parse_pdf_ir(diagram_pdf, ocr_regions={0: [(0, 0, 10, 10)] * 3},
                     max_ocr_regions=2, ocr_engine=FakeCpuOcr())


def test_ocr_misplaced_polygon_rejected(diagram_pdf):
    class OffPage:
        def read(self, region):
            return [TextCandidate(
                candidate_id="invalid", page_index=0, text="FAKE",
                method="rapidocr_cpu",
                polygon=((9999, 9999), (10000, 9999), (10000, 10000), (9999, 10000)),
            )]
    with pytest.raises(PdfInputError, match="outside"):
        parse_pdf_ir(diagram_pdf, ocr_regions={0: [(10, 10, 100, 100)]},
                     ocr_engine=OffPage())


def test_mocked_rapid_engine_quad_pixel_to_page_is_correct(diagram_pdf):
    crop = render_region(diagram_pdf, 0, (25, 20, 125, 120), dpi=144)
    engine = RapidCpuOcr.__new__(RapidCpuOcr)
    engine._engine = lambda _image: SimpleNamespace(
        boxes=[[(2, 4), (40, 4), (40, 24), (2, 24)]],
        txts=["+0.00"], scores=[.9],
    )
    candidates = engine.read(crop)
    assert len(candidates) == 1
    assert candidates[0].polygon[0] == pytest.approx((26, 22))
    assert candidates[0].polygon[2] == pytest.approx((45, 32))
    assert candidates[0].confidence == pytest.approx(.9)


@pytest.mark.parametrize("degrees", [0, 90, 180, 270])
def test_rotated_pdf_page_render_crop_matches_full_page(tmp_path, degrees):
    file = tmp_path / f"rotate-{degrees}.pdf"
    pdf = Canvas(str(file), pagesize=(432, 288))
    pdf.setPageRotation(degrees)
    pdf.drawString(42, 223, "ROTATION SOURCE")
    pdf.line(35, 35, 215, 175)
    pdf.save()

    # Both pdfplumber and pypdfium2 report displayed-page top-left coords.
    # Compare actual pixels: rotated render ROI must match same full page crop.
    imported = parse_pdf_ir(file)
    assert len(imported.drawing.frames) == 1
    assert any(t.text for t in imported.text_candidates)
    roi = (20.0, 20.0, 120.0, 120.0)
    full = render_region(file, 0, (0, 0, 432, 288), dpi=144)
    cut = render_region(file, 0, roi, dpi=144)
    assert cut.page_rotation_degrees == degrees
    assert full.page_rotation_degrees == degrees
    assert cut.image.size == (200, 200)
    expected = full.image.crop((40, 40, 240, 240))
    assert ImageChops.difference(cut.image, expected).getbbox() is None
    for xy in ((0, 0), (13.5, 5.25), (200, 200)):
        assert cut.source_to_pixel(*cut.pixel_to_source(*xy)) == pytest.approx(xy)


def test_pdf_ocr_rejects_reader_lying_about_source_or_page(diagram_pdf):
    class WrongMethod:
        def read(self, region):
            return [TextCandidate(candidate_id="fake", page_index=1,
                                  text="OUT", method="native_pdf",
                                  polygon=((10, 10), (20, 10), (20, 20), (10, 20)))]
    with pytest.raises(PdfInputError, match="inconsistent"):
        parse_pdf_ir(diagram_pdf, ocr_regions={0: [(10, 10, 100, 100)]},
                     ocr_engine=WrongMethod())


def test_pdf_import_json_roundtrip_and_page_origin(diagram_pdf):
    result = parse_pdf_ir(diagram_pdf)
    loaded = type(result).model_validate_json(result.model_dump_json())
    assert loaded.drawing.source_sha256 == result.drawing.source_sha256
    assert loaded.text_candidates[0].text_matrix is not None
    assert all(ent.source.page_index is not None for ent in loaded.drawing.entities)


def test_nondefault_cropbox_is_fail_closed_not_false_source_highlight(tmp_path):
    output = tmp_path / "cropped.pdf"
    pdf = Canvas(str(output), pagesize=(432, 288))
    pdf.setCropBox((300, 200))
    pdf.drawString(50, 180, "CROP TEST")
    pdf.save()
    # Native media-page observations remain possible.
    parsed = parse_pdf_ir(output)
    assert parsed.text_candidates
    with pytest.raises(PdfInputError, match="CropBox"):
        render_region(output, 0, (10, 10, 50, 50), dpi=144)


def test_rotated_large_page_fails_instead_of_full_render_oom(tmp_path):
    output = tmp_path / "large-rotated.pdf"
    pdf = Canvas(str(output), pagesize=(1000, 800))
    pdf.setPageRotation(90)
    pdf.drawString(40, 40, "BIG DRAWING")
    pdf.save()
    # A tiny ROI is cheap; but this rotated path needs full bitmap.
    with pytest.raises(PdfInputError, match="full-page render"):
        render_region(output, 0, (10, 10, 30, 30), dpi=150,
                      max_pixels=150_000)


def test_subpixel_crop_records_actual_rendered_origin(diagram_pdf):
    crop = render_region(diagram_pdf, 0,
                         (25.25, 20.75, 125.25, 120.75), dpi=144)
    assert crop.pixel_origin_pdf_points == pytest.approx((25.5, 21.0))
    assert crop.pixel_to_source(0, 0) == pytest.approx((25.5, 21.0))
    assert crop.source_to_pixel(*crop.pixel_to_source(19, 15)) == pytest.approx((19, 15))
