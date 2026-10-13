"""Synthetic original PDF visual evidence and amendment inspection tests."""
from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import re

import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import LegalDocumentMetadata, LegalNodeKind
from mimarllm.legal.review import (
    AmendmentSide, ReviewChoice, ReviewDecision, ReviewInputError,
    ReviewSelection, TargetKind, build_review_queue, task_digest,
    validate_decisions,
)
from mimarllm.legal.review_ledger import (
    ReviewLedgerError, append_review_decisions, import_exported_review_json,
    read_review_ledger,
)
from mimarllm.legal.review_viewer import VisualReviewError, create_visual_review_html
from mimarllm.legal.version_workflow import create_version_review_packet
from mimarllm.legal.versions import AmendmentClaim, AmendmentRelation


@pytest.fixture
def documents(tmp_path):
    original = tmp_path / "fake_original.pdf"
    c = Canvas(str(original), pagesize=(420, 340))
    c.setFont("Helvetica", 11)
    c.drawString(33, 306, "MADDE 7 - Synthetic provision for review.")
    c.drawString(33, 283, "(1) First paragraph of fake legislation.")
    c.drawString(33, 262, "a) Review this source fragment.")
    c.rect(34, 90, 350, 120)
    c.line(34, 150, 384, 150)
    c.line(209, 90, 209, 210)
    c.drawString(42, 180, "Name")
    c.drawString(219, 180, "Area")
    c.drawString(42, 120, "Example")
    c.drawString(219, 120, "58.5")
    c.showPage()
    c.setFont("Helvetica", 11)
    c.drawString(33, 300, "MADDE 8 - Other page stays separate.")
    c.drawString(33, 274, "(1) More synthetic review content.")
    c.save()

    amendment = tmp_path / "fake_amendment.pdf"
    a = Canvas(str(amendment), pagesize=(430, 340))
    a.setFont("Helvetica", 11)
    a.drawString(33, 300, "MADDE 1 - Fake modification of an older law.")
    a.drawString(33, 275, "(1) This claim becomes effective only if independently verified.")
    a.save()
    base = parse_legal_pdf(original, LegalDocumentMetadata(
        regulation_id="SYNTHETIC-ORIGINAL",
        document_kind="ORIGINAL",
        claimed_publication_date=date(2023, 2, 1),
    ))
    changed = parse_legal_pdf(amendment, LegalDocumentMetadata(
        regulation_id="SYNTHETIC-AMENDMENT",
        document_kind="AMENDMENT",
        claimed_publication_date=date(2025, 8, 1),
    ))
    paragraph = next(n for n in base.nodes if n.kind == LegalNodeKind.PARAGRAPH)
    amend_node = next(n for n in changed.nodes if n.kind == LegalNodeKind.ARTICLE)
    claim = AmendmentClaim(
        claim_id="synthetic-c1", target_document_sha256=base.document_sha256,
        target_node_id=paragraph.node_id,
        amending_document_sha256=changed.document_sha256,
        amending_node_id=amend_node.node_id,
        source_span=amend_node.spans[0],
        claimed_effective_from=date(2025, 9, 1),
        relation=AmendmentRelation.REPLACES,
        reviewer_id="demo-user", reason="Human asserted fictional mapping",
    )
    return (original, amendment, base, changed, paragraph, amend_node, claim)


def node_queue(documents):
    _, _, base, _, paragraph, _, _ = documents
    return build_review_queue([base], [ReviewSelection(
        document_sha256=base.document_sha256,
        kind=TargetKind.NODE, reference_id=paragraph.node_id,
    )])


def test_node_task_uses_true_pdf_source_polygon_and_sha(documents):
    _, _, base, _, paragraph, _, _ = documents
    queue = node_queue(documents)
    task = queue.tasks[0]
    assert task.source == paragraph.spans[0]
    assert task.source.document_sha256 == base.document_sha256
    assert task.source.page_index == 0
    assert task.legal_review_status == "UNREVIEWED"
    assert queue.approved_for_check is False
    assert len(task_digest(task)) == 64
    assert build_review_queue([base], [ReviewSelection(
        document_sha256=base.document_sha256,
        kind=TargetKind.NODE, reference_id=paragraph.node_id,
    )]).model_dump_json() == queue.model_dump_json()


def test_pdf_html_svg_highlight_and_review_export_controls(documents, tmp_path):
    original, _, base, _, _, _, _ = documents
    queue = node_queue(documents)
    output = tmp_path / "review.html"
    written = create_visual_review_html(
        queue, [base], {base.document_sha256: original}, output,
    )
    assert written == output
    html = output.read_text("utf-8")
    assert 'data:image/png;base64,' in html
    assert "<polygon points=" in html
    assert 'viewBox="0 0 420.000000 340.000000"' in html
    assert "VISUALLY_MATCHED" in html and "CORRECTION_REQUIRED" in html
    assert "application/json" in html and "task_digest" in html
    assert queue.tasks[0].task_id in html
    assert "resmî" in html
    assert "<script" in html and "Blob(" in html
    with pytest.raises(VisualReviewError, match="overwrite"):
        create_visual_review_html(queue, [base], {base.document_sha256: original},
                                  output)


def test_review_table_cell_has_exact_row_column_bbox(documents, tmp_path):
    original, _, base, _, paragraph, _, _ = documents
    assert base.tables
    table = next(t for t in base.tables
                 if any(c.text == "58.5" for c in t.cells))
    cell = next(c for c in table.cells if c.text == "58.5")
    queue = build_review_queue([base], [ReviewSelection(
        document_sha256=base.document_sha256,
        kind=TargetKind.TABLE_CELL,
        reference_id=table.table_id,
        row_index=cell.row_index, column_index=cell.column_index,
    )])
    task = queue.tasks[0]
    assert task.text == "58.5"
    assert task.source.reference_type == "TABLE_CELL_BBOX"
    assert task.row_index == cell.row_index
    written = create_visual_review_html(
        queue, [base], {base.document_sha256: original}, tmp_path / "table.html",
    )
    html = written.read_text("utf-8")
    assert "58.5" in html
    assert "TABLE_CELL_BBOX" in html


def test_same_multiline_node_each_original_span_can_be_selected(tmp_path):
    pdf = tmp_path / "multiline_clause.pdf"
    c = Canvas(str(pdf), pagesize=(420, 330))
    c.setFont("Helvetica", 11)
    c.drawString(30, 300, "MADDE 3 - A synthetic source.")
    c.drawString(30, 276, "(1) First line of a paragraph.")
    c.drawString(30, 255, "Continuation of this exact paragraph.")
    c.save()
    doc = parse_legal_pdf(pdf, LegalDocumentMetadata(regulation_id="MULTILINE"))
    paragraph = next(n for n in doc.nodes if n.kind == LegalNodeKind.PARAGRAPH)
    assert len(paragraph.spans) == 2
    queue = build_review_queue([doc], [
        ReviewSelection(document_sha256=doc.document_sha256,
                        kind=TargetKind.NODE, reference_id=paragraph.node_id,
                        span_index=i)
        for i in range(len(paragraph.spans))
    ])
    assert [x.source for x in queue.tasks] == list(paragraph.spans)
    html = create_visual_review_html(
        queue, [doc], {doc.document_sha256: pdf},
        tmp_path / "multiline.html",
    ).read_text("utf-8")
    assert html.count('data:image/png;base64,') == 2
    assert html.count("<polygon points=") == 2


def test_wrong_sha_bad_reference_and_duplicate_selection_fail(documents):
    _, _, base, _, paragraph, _, _ = documents
    good = ReviewSelection(document_sha256=base.document_sha256,
                           kind=TargetKind.NODE, reference_id=paragraph.node_id)
    with pytest.raises(ReviewInputError, match="Duplicate"):
        build_review_queue([base], [good, good])
    with pytest.raises(ReviewInputError, match="not in LegalAST"):
        build_review_queue([base], [good.model_copy(update={
            "document_sha256":"a" * 64,
        })])
    with pytest.raises(ReviewInputError, match="does not exist"):
        build_review_queue([base], [good.model_copy(update={
            "reference_id":"fake-node",
        })])
    with pytest.raises(ValidationError):
        ReviewSelection(document_sha256=base.document_sha256,
                        kind=TargetKind.TABLE_CELL, reference_id="t0")


def test_foreign_changed_pdf_rejected_instead_of_highlight(documents, tmp_path):
    original, amendment, base, _, _, _, _ = documents
    with pytest.raises(VisualReviewError, match="SHA/page"):
        create_visual_review_html(
            node_queue(documents), [base],
            {base.document_sha256: amendment}, tmp_path / "fake.html",
        )
    assert not (tmp_path / "fake.html").exists()
    with original.open("ab") as writer:
        writer.write(b"\n%changed\n")
    with pytest.raises(VisualReviewError, match="SHA/page"):
        create_visual_review_html(
            node_queue(documents), [base],
            {base.document_sha256: original}, tmp_path / "changed.html",
        )


def test_spoofed_queue_text_polygon_and_refused_offpage(documents, tmp_path):
    original, _, base, _, _, _, _ = documents
    queue = node_queue(documents)
    task = queue.tasks[0]
    forged = task.model_copy(update={"text":"invented original paragraph"})
    other = queue.model_copy(update={"tasks":(forged,)})
    with pytest.raises(VisualReviewError, match="differs from LegalAST"):
        create_visual_review_html(
            other, [base], {base.document_sha256: original},
            tmp_path / "forged.html",
        )
    bad_source = task.source.model_copy(update={
        "polygon":((900, 3), (910, 3), (910, 16), (900, 16)),
    })
    altered_task = task.model_copy(update={"source":bad_source})
    fake = queue.model_copy(update={"tasks":(altered_task,)})
    with pytest.raises(VisualReviewError):
        create_visual_review_html(
            fake, [base], {base.document_sha256: original},
            tmp_path / "offpage.html",
        )


def test_html_pdf_text_with_script_like_text_is_escaped(tmp_path):
    pdf = tmp_path / "untrusted.pdf"
    c = Canvas(str(pdf), pagesize=(420, 310))
    c.setFont("Helvetica", 10)
    c.drawString(30, 280, "MADDE 4 - <script>alert('unsafe')</script>")
    c.save()
    doc = parse_legal_pdf(pdf, LegalDocumentMetadata(regulation_id="FAKE"))
    node = next(n for n in doc.nodes if n.kind == LegalNodeKind.ARTICLE)
    queue = build_review_queue([doc], [ReviewSelection(
        document_sha256=doc.document_sha256,
        kind=TargetKind.NODE, reference_id=node.node_id,
    )])
    html = create_visual_review_html(
        queue, [doc], {doc.document_sha256: pdf},
        tmp_path / "escaped.html",
    ).read_text("utf-8")
    assert "&lt;script&gt;" in html
    assert "<script>alert('unsafe')</script>" not in html


def test_source_selection_export_decision_and_hash_chained_ledger(documents, tmp_path):
    q = node_queue(documents)
    task = q.tasks[0]
    decision = ReviewDecision(
        task_id=task.task_id, task_digest=task_digest(task),
        choice=ReviewChoice.VISUALLY_MATCHED,
        reviewer_label="Local human test",
        observation="The synthetic phrase appears at the displayed polygon.",
        reviewed_at=datetime(2026, 10, 14, 0, 10, tzinfo=timezone.utc),
    )
    assert validate_decisions(q, [decision]) == (decision,)
    dest = tmp_path / "review.jsonl"
    first = append_review_decisions(dest, q, [decision])
    assert first[0].sequence == 1
    assert first[0].approval_status == "HUKUKI_HOLD"
    assert not first[0].decision.legal_approval
    assert read_review_ledger(dest) == first
    second = decision.model_copy(update={
        "choice":ReviewChoice.CORRECTION_REQUIRED,
        "observation":"Needs a manual glyph correction.",
    })
    later = append_review_decisions(dest, q, [second])
    assert later[0].previous_sha256 == first[0].record_sha256
    assert len(read_review_ledger(dest)) == 2


def test_changed_review_history_detected_but_not_signed(documents, tmp_path):
    q = node_queue(documents)
    t = q.tasks[0]
    d = ReviewDecision(
        task_id=t.task_id,task_digest=task_digest(t),
        choice=ReviewChoice.CORRECTION_REQUIRED,
        reviewer_label="Test",observation="Example mismatch",
        reviewed_at=datetime.now(timezone.utc),
    )
    dest=tmp_path/"history.jsonl"
    append_review_decisions(dest,q,[d])
    content=dest.read_text("utf-8").replace("Example mismatch", "Altered claim")
    dest.write_text(content, encoding="utf-8")
    with pytest.raises(ReviewLedgerError, match="verification failed"):
        read_review_ledger(dest)
    with pytest.raises(ReviewLedgerError, match="verification failed"):
        append_review_decisions(dest,q,[d])


def test_wrong_task_digest_duplicate_and_unsigned_approval_rejected(documents):
    q=node_queue(documents)
    t=q.tasks[0]
    d=ReviewDecision(
        task_id=t.task_id,task_digest=task_digest(t),choice=ReviewChoice.UNREVIEWED,
        reviewer_label="Test",observation="Not checked",
        reviewed_at=datetime.now(timezone.utc),
    )
    with pytest.raises(ReviewInputError, match="digest"):
        validate_decisions(q,[d.model_copy(update={"task_digest":"e"*64})])
    with pytest.raises(ReviewInputError, match="Duplicate"):
        validate_decisions(q,[d,d])
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate(d.model_dump() | {"legal_approval":True})
    with pytest.raises(ValidationError):
        ReviewDecision.model_validate(d.model_dump() | {"authentic_identity_verified":True})


def test_import_browser_json_against_exact_source_queue(documents,tmp_path):
    q=node_queue(documents)
    t=q.tasks[0]
    d=ReviewDecision(
        task_id=t.task_id,task_digest=task_digest(t),
        choice=ReviewChoice.VISUALLY_MATCHED,
        reviewer_label="Synthetic reviewer",observation="Same position",
        reviewed_at=datetime(2026,10,14,1,tzinfo=timezone.utc),
    )
    path=tmp_path/"download.json"
    path.write_text(json.dumps([d.model_dump(mode="json")]),encoding="utf-8")
    recovered=import_exported_review_json(path)
    assert recovered==[d]
    assert validate_decisions(q,recovered)==(d,)
    path.write_text(json.dumps([{"untrusted":True}]),encoding="utf-8")
    with pytest.raises(ReviewLedgerError, match="invalid"):
        import_exported_review_json(path)


def test_amendment_version_packet_shows_both_original_pdfs(documents,tmp_path):
    original, amendment, base, changed, node, amend_node, claim=documents
    packet=create_version_review_packet(
        [base,changed],[claim],
        target_document_sha256=base.document_sha256,
        target_node_id=node.node_id,as_of=date(2024,1,1),
    )
    assert packet.version_status=="UNVERIFIED_HISTORICAL_VERSION"
    assert packet.approved_for_check is False
    assert len(packet.review_queue.tasks)==2
    assert set(packet.review_queue.source_documents)=={
        base.document_sha256,changed.document_sha256,
    }
    amending=next(t for t in packet.review_queue.tasks
                  if t.kind==TargetKind.AMENDMENT_SIDE)
    assert amending.source==claim.source_span
    assert amending.claimed_effective_from==date(2025,9,1)
    assert any(issue.code=="LATER_AMENDMENT_REQUIRES_HISTORICAL_REVIEW"
               for issue in packet.chain_assessment.issues)
    html=create_visual_review_html(
        packet.review_queue,[base,changed],
        {base.document_sha256:original,changed.document_sha256:amendment},
        tmp_path/"compare.html",amendment_claims=[claim],
    ).read_text("utf-8")
    assert html.count('data:image/png;base64,')==2
    assert "AMENDING" in html and "TARGET" not in html.split("<main>")[0]
    assert claim.claim_id in html


def test_amendment_review_requires_true_original_source(documents,tmp_path):
    original,amendment,base,changed,node,amend_node,claim=documents
    packet=create_version_review_packet(
        [base,changed],[claim],target_document_sha256=base.document_sha256,
        target_node_id=node.node_id,as_of=date(2026,1,1),
    )
    with pytest.raises(VisualReviewError,match="Supply exactly"):
        create_visual_review_html(
            packet.review_queue,[base,changed],
            {base.document_sha256:original},
            tmp_path/"missing.html",amendment_claims=[claim],
        )
    with pytest.raises(VisualReviewError,match="differs from LegalAST"):
        create_visual_review_html(
            packet.review_queue,[base,changed],
            {base.document_sha256:original,changed.document_sha256:amendment},
            tmp_path/"missing_claim.html",
        )


def test_version_packet_not_a_consolidated_law(documents):
    _,_,base,changed,node,_,claim=documents
    packet=create_version_review_packet(
        [base,changed],[claim],target_document_sha256=base.document_sha256,
        target_node_id=node.node_id,as_of=date(2026,1,1),
    )
    assert packet.chain_assessment.consolidated_text is None
    assert packet.chain_assessment.legal_effect_certified is False
    assert packet.chain_assessment.status=="INSUFFICIENT_EVIDENCE"
    assert len(packet.review_queue.tasks)==2


def test_multi_source_html_budget_and_wrong_output_suffix(documents,tmp_path):
    original,_,base,_,_,_,_=documents
    q=node_queue(documents)
    with pytest.raises(VisualReviewError):
        create_visual_review_html(
            q,[base],{base.document_sha256:original},
            tmp_path/"tiny.html",max_html_bytes=100,
        )
    with pytest.raises(VisualReviewError,match="new .html"):
        create_visual_review_html(
            q,[base],{base.document_sha256:original},
            tmp_path/"invalid.json",
        )
