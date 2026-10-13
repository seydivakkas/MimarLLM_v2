"""Offline LegalAST->SQLite FTS5->RRF: synthetic contracts, not legal verdicts."""
from __future__ import annotations

from dataclasses import replace
from datetime import date
import hashlib
import math
import os
from pathlib import Path

import pytest
from pydantic import ValidationError
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import (
    LegalDocument, LegalDocumentMetadata, LegalNode,
    LegalNodeKind, LegalSourceSpan, TextOrigin,
)
from mimarllm.rag import LegalRagStore, RagStoreError, index_local_legal_pdf, search_legal
from mimarllm.rag.embeddings import (
    EmbeddingError, LocalSentenceTransformer, normalize_vectors,
)
from mimarllm.rag.models import RagKind, SearchMode
from mimarllm.rag.store import match_expression


def fixture_font():
    file = (Path("C:/Windows/Fonts/arial.ttf") if os.name == "nt"
            else Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
    if file.is_file():
        pdfmetrics.registerFont(TTFont("RagSyntheticUnicode", str(file)))
        return "RagSyntheticUnicode"
    return "Helvetica"


@pytest.fixture
def sample_pdf(tmp_path):
    path = tmp_path / "sample_fake_regulation.pdf"
    c = Canvas(str(path), pagesize=(480, 600))
    c.setFont(fixture_font(), 11)
    c.drawString(35, 565, "BİRİNCİ BÖLÜM")
    c.drawString(35, 535, "MADDE 7 - Işıklık ve doğal günışığı hükmü.")
    c.drawString(35, 510, "(1) Işıklık için doğal aydınlatma önemlidir.")
    c.drawString(35, 485, "a) Oda penceresi sentetik örnektir.")
    # Visually real vector grid, coordinates are PDF top-left upon read.
    c.rect(35, 255, 380, 140)
    c.line(35, 325, 415, 325)
    c.line(225, 255, 225, 395)
    c.drawString(45, 355, "Alan kodu")
    c.drawString(235, 355, "Miktar")
    c.drawString(45, 285, "G-2")
    c.drawString(235, 285, "48.75")
    c.showPage()
    c.setFont(fixture_font(), 11)
    c.drawString(35, 565, "MADDE 8 - Kapı temiz genişlik analizi.")
    c.drawString(35, 540, "(1) Geçiş ve yangın güvenliği örneği.")
    c.drawString(35, 515, "Bu hüküm yürürlüğe girer ifadesi sadece testtir.")
    c.save()
    return path


@pytest.fixture
def metadata():
    return LegalDocumentMetadata(
        regulation_id="LOCAL-SYNTHETIC-NOT-LAW",
        document_kind="AMENDMENT",
        claimed_title="Not official: two synthetic articles",
        claimed_publication_date=date(2026, 10, 13),
        claimed_gazette_number="FAKE-NUMBER",
    )


class SyntheticEmbedder:
    """Deterministic numeric *test stub*, not a genuine learned language model."""
    model_id = "synthetic-only:four-dimensional-v1"
    dimensions = 4

    def encode(self, texts):
        def encode_one(s):
            t = s.casefold().replace("ı", "i")
            if "günışığı" in t or "günisigi" in t or "aydınlatma" in t or "ışıklık" in t:
                return [1.0, 0.0, 0.0, 0.0]
            if "kapı" in t or "geçiş" in t or "yangın" in t:
                return [0.0, 1.0, 0.0, 0.0]
            if "48.75" in t or "miktar" in t:
                return [0.0, 0.0, 1.0, 0.0]
            return [0.0, 0.0, 0.0, 1.0]
        return [encode_one(t) for t in texts]


def test_native_pdf_to_fts_article_paragraph_and_source_polygon(sample_pdf, metadata):
    with LegalRagStore() as db:
        indexed = index_local_legal_pdf(sample_pdf, metadata, db)
        assert indexed.legal_review_required
        assert indexed.indexed_passages >= 7
        assert indexed.embedded_model_id is None
        result = search_legal(db, "ışıklık", top_k=6)
        assert result.mode == SearchMode.LEXICAL_ONLY
        assert result.dense_state == "DISABLED"
        assert result.results
        assert any(hit.passage.article_number == "7" for hit in result.results)
        for hit in result.results:
            assert hit.passage.document_sha256 == indexed.document_sha256
            assert hit.passage.review_status == "UNREVIEWED"
            assert hit.claim_scope == "RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE"
            assert hit.legal_compliance_certified is False
            assert hit.source_pdf_available
            assert hit.passage.spans
            for span in hit.passage.spans:
                assert 0 <= span.page_index <= 1
                assert all(0 <= x <= 480 and 0 <= y <= 600
                           for x, y in span.polygon)
                assert span.document_sha256 == indexed.document_sha256
        assert any(hit.passage.node_kind == "PARAGRAPH" for hit in result.results)


def test_turkish_diacritics_fold_without_losing_original_text(sample_pdf, metadata):
    with LegalRagStore() as db:
        db.index_document(parse_legal_pdf(sample_pdf, metadata))
        out = search_legal(db, "isiklik", top_k=10)
        assert out.results
        assert any("Işıklık" in hit.passage.text for hit in out.results)
        assert all(hit.passage.spans[0].printed_page_number is None
                   for hit in out.results)


def test_table_cell_retrieval_preserves_row_column_and_pdf_source(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    assert ast.tables and any(c.text == "48.75" for t in ast.tables for c in t.cells)
    with LegalRagStore() as db:
        db.index_document(ast)
        result = search_legal(db, "48.75")
        cell = next(hit for hit in result.results
                    if hit.passage.entry_kind == RagKind.TABLE_CELL and
                    hit.passage.text == "48.75")
        assert cell.passage.table_id is not None
        assert cell.passage.row_index == 1 and cell.passage.column_index == 1
        assert cell.passage.spans[0].reference_type == "TABLE_CELL_BBOX"
        assert cell.passage.spans[0].page_index == 0
        assert cell.passage.document_sha256 == ast.document_sha256
        assert cell.passage.review_required


def test_multi_page_article_returns_second_source_page(sample_pdf, metadata):
    with LegalRagStore() as db:
        db.index_document(parse_legal_pdf(sample_pdf, metadata))
        found = search_legal(db, "yangın", top_k=10).results
        assert any(h.passage.article_number == "8" and
                   any(span.page_index == 1 for span in h.passage.spans)
                   for h in found)


def test_reindex_idempotent_and_lexical_db_persistent(sample_pdf, metadata, tmp_path):
    file = tmp_path / "fts5.sqlite"
    ast = parse_legal_pdf(sample_pdf, metadata)
    with LegalRagStore(file) as db:
        first = db.index_document(ast, original_pdf_path=sample_pdf)
        second = db.index_document(ast, original_pdf_path=sample_pdf)
        assert first == second
        result = search_legal(db, "yangın")
        assert len({h.passage.passage_id for h in result.results}) == len(result.results)
        old_ids = [h.passage.passage_id for h in result.results]
    with LegalRagStore(file) as reopened:
        out = search_legal(reopened, "yangın")
        assert [h.passage.passage_id for h in out.results] == old_ids
        assert all(hit.source_pdf_available for hit in out.results)


def test_local_pdf_hash_staleness_explicitly_reported(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    with LegalRagStore() as db:
        db.index_document(ast, original_pdf_path=sample_pdf)
        assert search_legal(db, "ışıklık").results[0].source_pdf_available
        # Current file bytes no longer match the immutable source SHA.
        with sample_pdf.open("ab") as fh:
            fh.write(b"\n%changed\n")
        result = search_legal(db, "ışıklık")
        assert result.results and not result.results[0].source_pdf_available


def test_original_pdf_hash_mismatch_never_indexed(sample_pdf, metadata, tmp_path):
    ast = parse_legal_pdf(sample_pdf, metadata)
    foreign = tmp_path / "unrelated.pdf"
    foreign.write_bytes(b"%PDF-1.4\nnot same")
    with LegalRagStore() as db:
        with pytest.raises(RagStoreError, match="hash"):
            db.index_document(ast, original_pdf_path=foreign)
        assert db.lexical_rank("ışıklık", limit=10) == []


def test_fts_match_query_escaping_and_sql_injection(sample_pdf, metadata):
    with LegalRagStore() as db:
        db.index_document(parse_legal_pdf(sample_pdf, metadata))
        assert match_expression('"ışıklık" OR -isiklik')  # Escapes operators as tokens
        for q in ["'; DROP TABLE passages; --", '"" OR 1=1 --', "***((??))"]:
            response = search_legal(db, q)
            assert response.mode == SearchMode.LEXICAL_ONLY
        assert search_legal(db, "kapı").results  # Tables never dropped
        assert not search_legal(db, '***??').results


def test_query_and_result_limits_rejected(sample_pdf, metadata):
    with LegalRagStore() as db:
        db.index_document(parse_legal_pdf(sample_pdf, metadata))
        for query in ["", " " * 30, "x" * 513, "word " * 27]:
            with pytest.raises(RagStoreError):
                search_legal(db, query)
        with pytest.raises(RagStoreError, match="limit"):
            search_legal(db, "kapı", top_k=0)
        with pytest.raises(RagStoreError, match="limit"):
            search_legal(db, "kapı", top_k=51)
        with pytest.raises(RagStoreError, match="limit"):
            search_legal(db, "kapı", top_k=5, candidate_limit=3)
        with pytest.raises(RagStoreError, match="SHA"):
            search_legal(db, "kapı", document_sha256="invalid")


def test_hybrid_rrf_preserves_lexical_and_dense_ranks(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    engine = SyntheticEmbedder()
    with LegalRagStore() as db:
        db.index_document(ast, embedder=engine)
        result = search_legal(db, "aydınlatma", embedder=engine, top_k=10)
        assert result.mode == SearchMode.HYBRID
        assert result.dense_state == "INDEXED"
        assert result.dense_model_id == engine.model_id
        assert any(h.fts_rank is not None and h.dense_rank is not None
                   for h in result.results)
        assert all(h.rrf_score > 0 and not h.legal_compliance_certified
                   for h in result.results)
        for hit in result.results:
            manual_rrf = (
                (1 / (60 + hit.fts_rank) if hit.fts_rank is not None else 0)
                + (1 / (60 + hit.dense_rank) if hit.dense_rank is not None else 0)
            )
            assert hit.rrf_score == pytest.approx(manual_rrf)
        rerun = search_legal(db, "aydınlatma", embedder=engine, top_k=10)
        assert result.model_dump_json() == rerun.model_dump_json()


def test_dense_only_semantic_style_candidate_uses_stub_not_real_model(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    e = SyntheticEmbedder()
    with LegalRagStore() as db:
        db.index_document(ast, embedder=e)
        result = search_legal(db, "günisigi", embedder=e, top_k=6)
        assert result.mode in {SearchMode.DENSE_ONLY, SearchMode.HYBRID}
        assert result.results
        assert any(h.dense_rank is not None for h in result.results)
        assert all(h.legal_compliance_certified is False for h in result.results)


def test_dense_model_id_mismatch_uses_lexical_not_forced_dense(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    e = SyntheticEmbedder()
    with LegalRagStore() as db:
        db.index_document(ast, embedder=e)

        class Different(SyntheticEmbedder):
            model_id = "other-local-model"
        response = search_legal(db, "ışıklık", embedder=Different())
        assert response.dense_state == "NO_MODEL_VECTORS"
        assert response.mode == SearchMode.LEXICAL_ONLY
        assert response.results
        db.index_document(ast, embedder=None)
        assert not db.has_dense_vectors(e.model_id)


def test_bad_embedder_preserves_old_index_atomically(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    with LegalRagStore() as db:
        db.index_document(ast)
        before = search_legal(db, "ışıklık").model_dump_json()

        class Wrong(SyntheticEmbedder):
            def encode(self, texts):
                return [[float("nan")] * 4 for _ in texts]
        with pytest.raises(EmbeddingError, match="NaN"):
            db.index_document(ast, embedder=Wrong())
        assert search_legal(db, "ışıklık").model_dump_json() == before


@pytest.mark.parametrize("vec,pattern", [
    ([0, 0, 0, 0], "zero"),
    ([1, 2], "dimension"),
    ([math.inf, 0, 0, 0], "NaN or Infinity"),
])
def test_embedding_validation_prevents_invalid_cosine(vec, pattern):
    with pytest.raises(EmbeddingError, match=pattern):
        normalize_vectors([vec], 1, 4)


def test_local_model_requires_directory_no_network(tmp_path):
    with pytest.raises((EmbeddingError, FileNotFoundError)):
        LocalSentenceTransformer(tmp_path / "no-model", model_id="model")
    assert not (tmp_path / "no-model").exists()


def test_docsha_filter_and_separate_amendment_not_consolidated(sample_pdf, metadata, tmp_path):
    first_ast = parse_legal_pdf(sample_pdf, metadata)
    other_pdf = tmp_path / "different_fake_gazette.pdf"
    c = Canvas(str(other_pdf), pagesize=(440, 240))
    c.setFont(fixture_font(), 11)
    c.drawString(30, 195, "MADDE 1 - Yürürlüğe girer ve kapı.")
    c.save()
    other_ast = parse_legal_pdf(other_pdf, metadata)
    with LegalRagStore() as db:
        db.index_document(first_ast)
        db.index_document(other_ast)
        all_hits = search_legal(db, "kapı", top_k=20)
        assert {h.passage.document_sha256 for h in all_hits.results} == {
            first_ast.document_sha256, other_ast.document_sha256,
        }
        filtered = search_legal(
            db, "kapı", document_sha256=other_ast.document_sha256,
        )
        assert all(h.passage.document_sha256 == other_ast.document_sha256
                   for h in filtered.results)
        assert all(h.passage.document_kind == "AMENDMENT"
                   for h in all_hits.results)


def test_source_span_forgery_and_approved_ast_refused(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    forged = ast.model_copy(update={"review_status": "APPROVED_FOR_CHECK"})
    with LegalRagStore() as db:
        with pytest.raises(ValidationError):
            db.index_document(forged)
        changed = ast.nodes[0].spans[0].model_copy(
            update={"document_sha256": "f" * 64},
        )
        bad_node = ast.nodes[0].model_copy(update={"spans": (changed,)})
        wrong = ast.model_copy(update={"nodes": [bad_node, *ast.nodes[1:]]})
        with pytest.raises(ValidationError):
            db.index_document(wrong)


def test_tight_dense_candidate_budgets_are_fail_closed(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    engine = SyntheticEmbedder()
    with LegalRagStore() as db:
        db.index_document(ast, embedder=engine)
        with pytest.raises(RagStoreError, match="scan budget"):
            search_legal(db, "ışıklık", embedder=engine, max_dense_scan=1)
        with pytest.raises(RagStoreError, match="index budget"):
            db.index_document(ast, max_passages=1)
        assert search_legal(db, "ışıklık").results


def test_forged_offpage_highlight_rejected_when_original_pdf_present(sample_pdf, metadata):
    ast = parse_legal_pdf(sample_pdf, metadata)
    first = ast.nodes[0]
    bad_source = first.spans[0].model_copy(update={
        "polygon": ((9000, 5), (9010, 5), (9010, 15), (9000, 15)),
    })
    forged_node = first.model_copy(update={"spans": (bad_source,)})
    forged = ast.model_copy(update={
        "nodes": [forged_node, *ast.nodes[1:]],
    })
    # Hash is genuine and page index is valid, but coordinates lie beyond page.
    assert LegalDocument.model_validate(forged.model_dump())
    with LegalRagStore() as db:
        with pytest.raises(RagStoreError, match="polygon exceeds"):
            db.index_document(forged, original_pdf_path=sample_pdf)
        assert not search_legal(db, "ışıklık").results


def test_index_requires_existing_parent_sqlite_directory(tmp_path):
    with pytest.raises(RagStoreError, match="parent directory"):
        LegalRagStore(tmp_path / "missing-dir" / "index.sqlite")
