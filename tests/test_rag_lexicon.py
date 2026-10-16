"""Operation 024: offline Turkish search hints & bounded SQLite lexical cache.

This is retrieval contract testing, never an official regulation or model
benchmark. Original source text, PDF page polygons and legal HOLD remain.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from reportlab.pdfgen.canvas import Canvas

from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import LegalDocumentMetadata
from mimarllm.rag import LegalRagStore, search_legal
from mimarllm.rag.lexicon import (
    LEXICON_VERSION, expand_architectural_terms,
)
from mimarllm.rag.store import RagStoreError, match_expression


@pytest.fixture
def samples(tmp_path):
    first=tmp_path/"original.pdf"
    c=Canvas(str(first),pagesize=(440,340))
    c.setFont("Helvetica",11)
    c.drawString(25,300,"MADDE 7 - Isiklik hakkinda sentetik inceleme.")
    c.drawString(25,275,"(1) Isiklik ile dogal isik adayi incelenir.")
    c.showPage()
    c.drawString(25,300,"MADDE 8 - Kapinin sentetik olculeri.")
    c.drawString(25,275,"(1) Kapi temiz genisligi teknik adaydir.")
    c.save()
    second=tmp_path/"amendment.pdf"
    d=Canvas(str(second),pagesize=(440,340))
    d.setFont("Helvetica",11)
    d.drawString(25,300,"MADDE 1 - Isik kuyusu hakkinda sentetik degisiklik.")
    d.drawString(25,275,"(1) Isik kuyusu terimi farkli PDF metnidir.")
    d.save()
    meta=lambda reg,kind: LegalDocumentMetadata(
        regulation_id=reg,
        document_kind=kind,
        claimed_publication_date=date(2026,10,16),
    )
    original=parse_legal_pdf(first,meta("REG-BASE-TEST","ORIGINAL"))
    amend=parse_legal_pdf(second,meta("REG-CHANGE-TEST","AMENDMENT"))
    return (first,original),(second,amend)


def test_default_no_expansion_preserves_old_ranking_and_source(samples):
    (base_path,original),(change_path,change)=samples
    with LegalRagStore() as db:
        db.index_document(original,original_pdf_path=base_path)
        db.index_document(change,original_pdf_path=change_path)
        response=search_legal(db,"isiklik",top_k=10)
        expanded=search_legal(db,"isiklik",lexical_expansion=True,top_k=10)
        assert response.search_hint_terms==()
        assert response.expansion_version is None
        assert expanded.expansion_version==LEXICON_VERSION
        assert "isik kuyusu" in expanded.search_hint_terms
        assert response.results and expanded.results
        assert all(hit.passage.document_sha256==original.document_sha256
                   for hit in response.results)
        assert {h.passage.document_sha256 for h in expanded.results}=={
            original.document_sha256,change.document_sha256,
        }
        assert expanded.results[0].passage.document_sha256==original.document_sha256
        assert all(h.legal_compliance_certified is False for h in expanded.results)
        for hit in expanded.results:
            assert hit.passage.spans
            assert all(span.document_sha256==hit.passage.document_sha256
                       for span in hit.passage.spans)
            assert hit.passage.review_status=="UNREVIEWED"


def test_multiword_phrase_only_and_no_partial_word_expansion():
    full=expand_architectural_terms("Kapı temiz genişliği hakkında")
    assert "kapi net genisligi" in full.hints
    assert "kapi gecis acikligi" in full.hints
    partial=expand_architectural_terms("kapıcı net değildir")
    assert partial.hints==()
    no_trigger=expand_architectural_terms("özel işlevli olmayan terim")
    assert no_trigger.hints==()
    for item in [full,*[expand_architectural_terms("yangın merdiveni")]]:
        assert item.advisory=="SEARCH_CANDIDATES_ONLY_NOT_LEGAL_EQUIVALENCE"


def test_diacritics_case_and_bounded_variants():
    assert expand_architectural_terms("IŞIKLIK").hints==expand_architectural_terms("isiklik").hints
    assert "isik kuyusu" in expand_architectural_terms("ışıklık").hints
    with pytest.raises(RagStoreError,match="budget"):
        expand_architectural_terms("ışıklık",max_hints=0)
    with pytest.raises(RagStoreError,match="Query requires"):
        expand_architectural_terms(" " * 513)
    with pytest.raises(RagStoreError,match="token budget"):
        expand_architectural_terms("isiklik " * 40)


def test_fts_injection_is_still_only_quoted_literal_and_no_table_drop(samples):
    (path,source),_=samples
    with LegalRagStore() as db:
        db.index_document(source)
        for user_input in [
            "ışıklık\" OR <script>",
            "ışıklık' ; DROP TABLE passages; --",
            "isiklik (NEAR) or /**/ 1=1",
        ]:
            result=search_legal(db,user_input,lexical_expansion=True)
            assert all(h.legal_compliance_certified is False for h in result.results)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM passages"
        ).fetchone()[0] > 0
        expression=match_expression("isiklik OR anormal")
        assert expression == '"isiklik" OR "or" OR "anormal"'


def test_sqlite_cache_ranked_ids_idempotent_no_duplicate_entries(samples,tmp_path):
    (_,base),_=samples
    dbpath=tmp_path/"workspace.sqlite"
    with LegalRagStore(dbpath) as db:
        db.index_document(base)
        a=search_legal(db,"isiklik",lexical_expansion=True)
        before=db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]
        b=search_legal(db,"isiklik",lexical_expansion=True)
        after=db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]
        assert before>0 and before==after
        assert a.model_dump_json()==b.model_dump_json()
        rows=db.conn.execute(
            "SELECT passage_ids_json FROM rag_lexical_cache"
        ).fetchall()
        assert rows and all("polygon" not in row[0] and "pdf_path" not in row[0]
                            for row in rows)
    with LegalRagStore(dbpath) as reopened:
        assert search_legal(reopened,"isiklik",lexical_expansion=True).results


def test_source_pdf_current_hash_rechecked_after_cache_hit(samples):
    (source_file,base),_=samples
    with LegalRagStore() as db:
        db.index_document(base,original_pdf_path=source_file)
        first=search_legal(db,"isiklik",lexical_expansion=True)
        assert first.results and all(h.source_pdf_available for h in first.results)
        with source_file.open("ab") as f:
            f.write(b"\n%source-altered\n")
        repeated=search_legal(db,"isiklik",lexical_expansion=True)
        assert repeated.results and all(not h.source_pdf_available for h in repeated.results)


def test_cache_invalidation_on_reindex_and_foreign_sha_filter(samples):
    (original_path,original),(amend_path,amend)=samples
    with LegalRagStore() as db:
        db.index_document(original)
        db.index_document(amend)
        cache_hit=search_legal(db,"isiklik",lexical_expansion=True,top_k=12)
        assert len(cache_hit.results)>0
        assert db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]>0
        db.index_document(original)
        assert db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]==0
        filtered=search_legal(db,"isiklik",lexical_expansion=True,
                              document_sha256=amend.document_sha256)
        assert filtered.results
        assert all(h.passage.document_sha256==amend.document_sha256
                   for h in filtered.results)
        # Regulation filter must stay bound; hints cannot bypass it.
        filtered_reg=search_legal(db,"isiklik",lexical_expansion=True,
                                  regulation_id=original.metadata.regulation_id)
        assert filtered_reg.results
        assert all(h.passage.regulation_id==original.metadata.regulation_id
                   for h in filtered_reg.results)


def test_lexical_cache_key_scopes_limit_and_filters(samples):
    (_,base),(_,amend)=samples
    with LegalRagStore() as db:
        db.index_document(base)
        db.index_document(amend)
        for limit in [1,3,10]:
            for sha in [None,base.document_sha256,amend.document_sha256]:
                response=search_legal(db,"isiklik",lexical_expansion=True,
                                      document_sha256=sha,
                                      candidate_limit=limit,top_k=1)
                assert len(response.results)<=1
                if sha:
                    assert all(h.passage.document_sha256==sha for h in response.results)
        assert db.conn.execute(
            "SELECT COUNT(*) FROM rag_lexical_cache"
        ).fetchone()[0]>=3


def test_cache_bound_128_entries_and_no_raw_source_pdf_data(samples):
    (_,base),_=samples
    with LegalRagStore() as db:
        db.index_document(base)
        for idx in range(160):
            db.lexical_rank(f"isiklik cacheword{idx}",limit=5)
        count=db.conn.execute(
            "SELECT COUNT(*) FROM rag_lexical_cache"
        ).fetchone()[0]
        assert count<=128
        assert count>0
        for (raw,) in db.conn.execute(
            "SELECT passage_ids_json FROM rag_lexical_cache"
        ):
            assert len(raw)<10000


def test_reindex_fail_closed_cache_preserved_after_failed_pdf_or_embed(samples,tmp_path):
    (first,base),_=samples
    with LegalRagStore() as db:
        db.index_document(base)
        response=search_legal(db,"isiklik",lexical_expansion=True)
        rows=db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]
        bad=tmp_path/"not-a-pdf.pdf"
        bad.write_bytes(b"garbage")
        with pytest.raises(RagStoreError):
            db.index_document(base,original_pdf_path=bad)
        assert db.conn.execute("SELECT COUNT(*) FROM rag_lexical_cache").fetchone()[0]==rows
        assert search_legal(db,"isiklik",lexical_expansion=True).model_dump_json()==response.model_dump_json()


def test_no_model_claim_and_expansion_query_metadata(samples):
    (_,original),_=samples
    with LegalRagStore() as db:
        db.index_document(original)
        out=search_legal(db,"isiklik",lexical_expansion=True)
        assert out.mode.value=="LEXICAL_ONLY"
        assert out.dense_state=="DISABLED"
        assert out.note=="UNREVIEWED_SOURCES_RELEVANCE_NOT_LEGAL_VALIDITY"
        assert out.expansion_version==LEXICON_VERSION
        assert all(h.claim_scope=="RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE"
                   for h in out.results)


def test_local_sql_passage_mutation_triggers_cache_invalidation(samples):
    (_,base),_=samples
    with LegalRagStore() as db:
        db.index_document(base)
        assert search_legal(db,"isiklik").results
        assert db.conn.execute(
            "SELECT COUNT(*) FROM rag_lexical_cache"
        ).fetchone()[0]>0
        # A separate local SQL utility bypasses the normal index API; the
        # SQLite trigger must still invalidate stale ranked passage IDs.
        target=db.conn.execute("SELECT passage_id FROM passages LIMIT 1").fetchone()[0]
        with db.conn:
            db.conn.execute(
                "UPDATE passages SET payload_json=payload_json WHERE passage_id=?",
                (target,),
            )
        assert db.conn.execute(
            "SELECT COUNT(*) FROM rag_lexical_cache"
        ).fetchone()[0]==0
        assert search_legal(db,"isiklik").results


def test_cache_isolated_across_two_local_connections_and_reindex(samples,tmp_path):
    (first,base),(second,amend)=samples
    file=tmp_path/"two-connections.sqlite"
    with LegalRagStore(file) as a:
        a.index_document(base)
        with LegalRagStore(file) as b:
            first_results=search_legal(b,"isik kuyusu",lexical_expansion=True)
            assert all(h.passage.document_sha256==base.document_sha256
                       for h in first_results.results)
            assert b.conn.execute(
                "SELECT COUNT(*) FROM rag_lexical_cache"
            ).fetchone()[0]>0
            a.index_document(amend)
            second_results=search_legal(b,"isik kuyusu",lexical_expansion=True)
            assert amend.document_sha256 in {
                h.passage.document_sha256 for h in second_results.results
            }
            assert all(h.legal_compliance_certified is False
                       for h in second_results.results)
