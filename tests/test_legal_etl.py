"""Synthetic Gazette-style PDF→LegalAST contract tests; no copyrighted laws."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import os

import pytest
from pydantic import ValidationError
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from mimarllm.core.models import TextCandidate
from mimarllm.legal.etl import export_legal_json, parse_legal_pdf
from mimarllm.legal.extractor import LegalInputError, extract_legal_observations
from mimarllm.legal.models import (
    ChangeKind, LegalDocument, LegalDocumentMetadata, LegalNodeKind,
    LegalSourceSpan, TextOrigin,
)


def _font():
    candidate = (Path("C:/Windows/Fonts/arial.ttf") if os.name == "nt"
                 else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    if candidate.exists():
        pdfmetrics.registerFont(TTFont("LegalSyntheticUnicode", str(candidate)))
        return "LegalSyntheticUnicode"
    return "Helvetica"


@pytest.fixture
def gazette_pdf(tmp_path):
    path = tmp_path / "sentetik_resmi_gazete.pdf"
    c = Canvas(str(path), pagesize=(500, 700))
    c.setFont(_font(), 11)
    c.drawString(45, 665, "BİRİNCİ BÖLÜM")
    c.drawString(45, 640, "MADDE 1 - Örnek hüküm")
    c.drawString(45, 620, "(1) Bu metin tamamen sentetiktir.")
    c.drawString(45, 600, "(2) İstisna hariç tutulur.")
    c.drawString(65, 580, "a) Birinci sentetik bent.")
    c.drawString(65, 560, "b) İkinci sentetik bent.")
    c.drawString(45, 540, "Ek açıklama devam satırıdır.")
    # Native vector grid, two rows x two columns.
    x0, y0, width, height = 45, 355, 400, 140
    c.rect(x0, y0, width, height)
    c.line(x0, y0 + 70, x0 + width, y0 + 70)
    c.line(x0 + 200, y0, x0 + 200, y0 + height)
    c.drawString(55, y0 + 103, "Kod")
    c.drawString(255, y0 + 103, "Değer")
    c.drawString(55, y0 + 33, "A")
    c.drawString(255, y0 + 33, "12.50")
    c.showPage()
    c.setFont(_font(), 11)
    c.drawString(45, 660, "GEÇİCİ MADDE 1 - Geçiş düzeni.")
    c.drawString(45, 640, "(1) Önceki koşullar geçerlidir.")
    c.drawString(45, 615, "MADDE 2 - Değişiklik metni.")
    c.drawString(45, 595, "(1) Aşağıdaki şekilde değiştirilmiştir.")
    c.drawString(45, 570, "Bu metin yayımı tarihinde yürürlüğe girer.")
    c.save()
    return path


@pytest.fixture
def meta():
    return LegalDocumentMetadata(
        regulation_id="SYNTHETIC-TR",
        document_kind="AMENDMENT",
        claimed_title="Sentetik mevzuat testi - resmî değildir",
        claimed_publication_date=date(2026, 10, 13),
        claimed_gazette_number="TEST-NONOFFICIAL",
        claimed_source_url="https://example.invalid/fake.pdf",
    )


def test_original_sha_page_coords_and_turkish_ast(gazette_pdf, meta):
    ast = parse_legal_pdf(gazette_pdf, meta)
    assert ast.page_count == 2
    assert ast.review_status == "UNREVIEWED"
    assert not ast.legal_compliance_certified
    assert ast.metadata.provenance_status == "USER_ASSERTED_UNVERIFIED"
    assert len(ast.document_sha256) == 64
    assert {n.kind for n in ast.nodes} >= {
        LegalNodeKind.SECTION, LegalNodeKind.ARTICLE,
        LegalNodeKind.TEMPORARY_ARTICLE, LegalNodeKind.PARAGRAPH,
        LegalNodeKind.ITEM,
    }
    assert sum(n.kind == LegalNodeKind.ARTICLE for n in ast.nodes) == 2
    assert sum(n.kind == LegalNodeKind.TEMPORARY_ARTICLE for n in ast.nodes) == 1
    paragraphs = [n for n in ast.nodes if n.kind == LegalNodeKind.PARAGRAPH]
    assert len(paragraphs) == 4
    items = [n for n in ast.nodes if n.kind == LegalNodeKind.ITEM]
    assert [n.item_key for n in items] == ["a", "b"]
    by_id = {n.node_id: n for n in ast.nodes}
    assert all(by_id[item.parent_node_id].kind == LegalNodeKind.PARAGRAPH
               for item in items)
    assert any("devam satırıdır" in n.text for n in ast.nodes)
    assert any("değiştirilmiştir" in n.text for n in ast.nodes)
    assert {line.source.page_index for line in ast.lines} == {0, 1}
    assert all(s.document_sha256 == ast.document_sha256 for n in ast.nodes for s in n.spans)
    assert all(s.printed_page_number is None for n in ast.nodes for s in n.spans)
    assert all(s.extraction == TextOrigin.NATIVE_PDF for line in ast.lines
               for s in (line.source,))
    assert all(s.polygon[0][0] < s.polygon[2][0] for line in ast.lines
               for s in (line.source,))


def test_native_table_cell_coordinates_preserve_grid(gazette_pdf, meta):
    ast = parse_legal_pdf(gazette_pdf, meta)
    assert ast.tables
    target = next((t for t in ast.tables if len(t.cells) >= 4), None)
    assert target is not None
    assert target.review_required
    assert target.suggested_parent_node_id is not None
    assert {c.row_index for c in target.cells} >= {0, 1}
    assert {c.column_index for c in target.cells} >= {0, 1}
    texts = " ".join(c.text for c in target.cells)
    assert "12.50" in texts and "Kod" in texts
    assert all(c.source.reference_type == "TABLE_CELL_BBOX" for c in target.cells)
    assert all(c.source.page_index == target.page_index for c in target.cells)
    assert any(i.code == "TABLE_PARENT_AND_GRID_REVIEW_REQUIRED" for i in ast.issues)
    # Grid text must not be treated as free-standing article paragraphs.
    assert not any(n.kind == LegalNodeKind.PARAGRAPH and "12.50" in n.text
                   for n in ast.nodes)


def test_change_mentions_preserve_original_line_not_effectivity(gazette_pdf, meta):
    ast = parse_legal_pdf(gazette_pdf, meta)
    assert {candidate.kind for candidate in ast.changes} >= {
        ChangeKind.AMENDMENT_MENTION, ChangeKind.EFFECTIVITY_MENTION,
    }
    assert any(issue.code == "AMENDMENT_ARTICLE_NOT_CONSOLIDATED"
               for issue in ast.issues)
    assert all(change.review_required for change in ast.changes)
    assert ast.metadata.claimed_effective_from is None
    assert not hasattr(ast, "approved_for_check")


def test_json_roundtrip_and_no_overwriting_original(gazette_pdf, meta, tmp_path):
    ast = parse_legal_pdf(gazette_pdf, meta)
    saved = export_legal_json(ast, tmp_path / "legalast.json")
    assert saved.exists()
    assert LegalDocument.model_validate_json(saved.read_text("utf-8")) == ast
    with pytest.raises(LegalInputError, match="overwrite"):
        export_legal_json(ast, saved)
    with pytest.raises(LegalInputError, match=".json"):
        export_legal_json(ast, gazette_pdf)
    assert gazette_pdf.read_bytes().startswith(b"%PDF-")


def test_metadata_date_is_only_claim_and_not_reviewed(gazette_pdf):
    meta = LegalDocumentMetadata(
        regulation_id="SYNTHETIC", document_kind="CONSOLIDATION",
        claimed_effective_from=date(2026, 12, 1),
    )
    ast = parse_legal_pdf(gazette_pdf, meta)
    assert ast.review_status == "UNREVIEWED"
    assert any(i.code == "CONSOLIDATION_NOT_INDEPENDENTLY_VERIFIED"
               for i in ast.issues)
    assert any(i.code == "SOURCE_OFFICIALITY_EFFECTIVITY_AND_APPLICABILITY_UNVERIFIED"
               for i in ast.issues)
    with pytest.raises(ValidationError):
        LegalDocumentMetadata(
            regulation_id="X", claimed_effective_from=date(2026, 5, 1),
            claimed_effective_until=date(2025, 5, 1),
        )


def test_fake_span_or_approval_rejected(gazette_pdf, meta):
    ast = parse_legal_pdf(gazette_pdf, meta)
    n = ast.nodes[0]
    foreign = n.spans[0].model_copy(update={"document_sha256": "0" * 64})
    broken = ast.model_copy(update={
        "nodes": [n.model_copy(update={"spans": (foreign,)}), *ast.nodes[1:]],
    })
    with pytest.raises(ValidationError, match="does not match"):
        LegalDocument.model_validate(broken.model_dump())
    with pytest.raises(ValidationError):
        LegalDocument.model_validate(ast.model_dump() | {"review_status": "APPROVED"})
    with pytest.raises(ValidationError):
        LegalDocument.model_validate(ast.model_dump() | {"legal_compliance_certified": True})


def test_limits_invalid_pdf_and_explicit_ocr_gate(gazette_pdf, meta, tmp_path):
    with pytest.raises(LegalInputError, match="page budget"):
        parse_legal_pdf(gazette_pdf, meta, max_pages=1)
    with pytest.raises(LegalInputError, match="source line budget"):
        parse_legal_pdf(gazette_pdf, meta, max_total_lines=1)
    with pytest.raises(LegalInputError, match="node budget"):
        parse_legal_pdf(gazette_pdf, meta, max_nodes=1)
    with pytest.raises(LegalInputError, match="OCR requires"):
        parse_legal_pdf(gazette_pdf, meta, ocr_pages=(0,))
    with pytest.raises(LegalInputError, match="OCR page"):
        parse_legal_pdf(gazette_pdf, meta, ocr_pages=(9,), ocr_engine=FakeReader())
    with pytest.raises(LegalInputError, match="OCR page selection"):
        parse_legal_pdf(gazette_pdf, meta, ocr_pages=(0, 0), ocr_engine=FakeReader())
    empty = tmp_path / "broken.pdf"
    empty.write_bytes(b"Not PDF")
    with pytest.raises((LegalInputError, ValueError)):
        parse_legal_pdf(empty, meta)


class FakeReader:
    def read(self, region):
        quad = tuple(region.pixel_to_source(x, y) for x, y in (
            (20, 20), (250, 20), (250, 52), (20, 52)
        ))
        return [TextCandidate(
            candidate_id="native-fixture", page_index=region.page_index,
            method="rapidocr_cpu", text="MADDE 7 - OCR sentetik madde.",
            polygon=quad, confidence=.83, review_required=True,
        )]


def test_raster_blank_pdf_ocr_explicit_source_quad(tmp_path, meta):
    file = tmp_path / "blank_scanned_fixture.pdf"
    c = Canvas(str(file), pagesize=(320, 280))
    c.rect(10, 10, 30, 30)
    c.save()
    without = parse_legal_pdf(file, meta)
    assert not without.nodes
    assert any(i.code == "NO_NATIVE_CONTENT_OCR_NOT_SELECTED" for i in without.issues)
    with_ocr = parse_legal_pdf(file, meta, ocr_pages=(0,),
                               ocr_engine=FakeReader())
    assert any(n.kind == LegalNodeKind.ARTICLE and n.article_number == "7"
               for n in with_ocr.nodes)
    assert with_ocr.nodes[0].spans[0].reference_type == "OCR_DETECTION_QUAD"
    assert with_ocr.nodes[0].spans[0].confidence == pytest.approx(.83)
    assert all(n.spans[0].document_sha256 == with_ocr.document_sha256
               for n in with_ocr.nodes)


def test_misplaced_ocr_quad_and_method_are_rejected(tmp_path, meta):
    file = tmp_path / "ocr.pdf"
    c = Canvas(str(file), pagesize=(320, 280))
    c.showPage()
    c.save()

    class WrongReader:
        def read(self, region):
            return [TextCandidate(
                candidate_id="bad", page_index=0, text="MADDE 2 - bad",
                method="rapidocr_cpu",
                polygon=((9000, 9000), (9001, 9000), (9001, 9001), (9000, 9001)),
            )]

    with pytest.raises(LegalInputError, match="outside original"):
        parse_legal_pdf(file, meta, ocr_pages=(0,),
                        ocr_engine=WrongReader())


def test_determinism_on_same_pdf_and_metadata(gazette_pdf, meta):
    a = parse_legal_pdf(gazette_pdf, meta)
    b = parse_legal_pdf(gazette_pdf, meta)
    assert a.model_dump_json() == b.model_dump_json()
    assert not any(c.review_required is False for c in a.changes)


def test_inline_article_paragraph_preserves_only_full_line_span(tmp_path, meta):
    path = tmp_path / "inline.pdf"
    c = Canvas(str(path), pagesize=(450, 260))
    c.setFont(_font(), 11)
    c.drawString(30, 220, "MADDE 8 - (1) Tek satırda sentetik hüküm.")
    c.drawString(30, 200, "a) Bu hükme bağlı bent.")
    c.save()
    ast = parse_legal_pdf(path, meta)
    article = next(n for n in ast.nodes if n.kind == LegalNodeKind.ARTICLE)
    paragraph = next(n for n in ast.nodes if n.kind == LegalNodeKind.PARAGRAPH)
    item = next(n for n in ast.nodes if n.kind == LegalNodeKind.ITEM)
    assert article.article_number == "8"
    assert paragraph.paragraph_number == "1"
    assert paragraph.parent_node_id == article.node_id
    assert item.parent_node_id == paragraph.node_id
    assert paragraph.spans[0] == article.spans[0]
    assert any(i.code == "INLINE_PARAGRAPH_FULL_LINE_BBOX" for i in ast.issues)


def test_repeal_text_is_unreviewed_mention_not_a_repealed_rule(tmp_path, meta):
    file = tmp_path / "repeal.pdf"
    c = Canvas(str(file), pagesize=(420, 250))
    c.setFont(_font(), 11)
    c.drawString(30, 220, "MADDE 1 - Önceki hüküm yürürlükten kaldırılmıştır.")
    c.save()
    ast = parse_legal_pdf(file, meta)
    assert any(c.kind == ChangeKind.REPEAL_MENTION for c in ast.changes)
    assert all(c.review_required for c in ast.changes)
    assert not hasattr(ast, "repealed_articles")
    assert ast.review_status == "UNREVIEWED"
