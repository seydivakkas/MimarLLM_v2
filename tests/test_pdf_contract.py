"""Synthetic local tests. Real customer files and internet access are not required."""
from pathlib import Path

import pytest

from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import PdfInputError, inspect_pdf, render_region


@pytest.fixture()
def sample_pdf(tmp_path: Path) -> Path:
    from reportlab.pdfgen import canvas
    dest = tmp_path / "fixture.pdf"
    page = canvas.Canvas(str(dest), pagesize=(432, 288))
    page.drawString(52, 230, "ROOM A 12.5 m2")
    page.line(40, 40, 380, 40)
    page.rect(40, 60, 280, 140)
    page.save()
    return dest


def test_pdf_vector_and_text_preserved(sample_pdf: Path):
    result = inspect_pdf(sample_pdf)
    assert result.page_count == 1
    assert len(result.document_sha256) == 64
    page = result.pages[0]
    assert page.width_pt == pytest.approx(432)
    assert any(ch.text == "R" and ch.method == "native_pdf" for ch in page.text)
    assert any(shape.kind == "line" for shape in page.vectors)
    assert any(shape.kind == "rect" for shape in page.vectors)


def test_render_region_roundtrip(sample_pdf: Path):
    crop = render_region(sample_pdf, 0, (25.0, 20.0, 125.0, 120.0), dpi=144)
    assert crop.image.width > 0 and crop.image.height > 0
    assert crop.pixel_to_source(0, 0) == pytest.approx((25, 20))
    assert crop.pixel_to_source(100, 100) == pytest.approx((75, 70))
    assert crop.document_sha256 == inspect_pdf(sample_pdf).document_sha256


def test_outside_crop_is_rejected(sample_pdf: Path):
    with pytest.raises(PdfInputError):
        render_region(sample_pdf, 0, (-1.0, 0.0, 30.0, 30.0))


def test_pixel_budget_is_enforced(sample_pdf: Path):
    with pytest.raises(PdfInputError):
        render_region(sample_pdf, 0, (0.0, 0.0, 432.0, 288.0), dpi=300, max_pixels=100_000)


def test_contract_preserves_rotated_quad():
    quad = ((0., 0.), (2., 2.), (1., 3.), (-1., 1.))
    obj = TextCandidate(candidate_id="r0", page_index=0, text="45", method="native_pdf", polygon=quad)
    assert obj.polygon == quad


def test_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        inspect_pdf(tmp_path / "missing.pdf")
