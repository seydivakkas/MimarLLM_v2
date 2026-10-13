"""Process 015 — evidence binding across synthetic PDF, LegalAST, RAG, Rules.

No official Gazette content is downloaded; no law compliance is asserted.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import ezdxf
import pytest
from pydantic import ValidationError
from reportlab.pdfgen.canvas import Canvas

from mimarllm.importers.dxf import parse_dxf
from mimarllm.legal.applicability import (
    ExceptionReview, ProjectLegalContext, assess_project_context,
)
from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import LegalDocumentMetadata, LegalNodeKind
from mimarllm.legal.verification import SourceAuditStatus, verify_local_pdf
from mimarllm.legal.versions import (
    AmendmentClaim, AmendmentRelation, assess_version_chain,
)
from mimarllm.rag import LegalRagStore, search_legal
from mimarllm.rules.base import (
    Comparison, LegalSourceLocator, MetricKind, RuleDefinition,
    RuleDomain, RuleRequest, RuleStatus,
)
from mimarllm.rules.engine import RuleEngine
from mimarllm.rules.evidence import (
    BindingInputError, BindingStatus, bind_regulatory_evidence,
    evaluate_regulatory_with_evidence,
)


@pytest.fixture
def sources(tmp_path):
    original_pdf = tmp_path / "fake_original.pdf"
    c = Canvas(str(original_pdf), pagesize=(460, 320))
    c.setFont("Helvetica", 11)
    c.drawString(40, 275, "MADDE 7 - Synthetic door provisions.")
    c.drawString(40, 250, "(1) Example door width not a real legal threshold.")
    c.drawString(40, 225, "a) The source paragraph references a sample door.")
    c.save()
    amendment_pdf = tmp_path / "fake_amendment.pdf"
    a = Canvas(str(amendment_pdf), pagesize=(460, 320))
    a.setFont("Helvetica", 11)
    a.drawString(40, 280, "MADDE 1 - Example amendment; not legally binding.")
    a.drawString(40, 250, "(1) The previous wording is changed for synthetic testing.")
    a.save()
    original = parse_legal_pdf(original_pdf, LegalDocumentMetadata(
        regulation_id="SYNTHETIC-REGULATION-BASE",
        document_kind="ORIGINAL",
        claimed_source_url="https://example.invalid/pretend-official-source.pdf",
        claimed_publication_date=date(2020, 1, 1),
    ))
    amendment = parse_legal_pdf(amendment_pdf, LegalDocumentMetadata(
        regulation_id="SYNTHETIC-CHANGE-2025",
        document_kind="AMENDMENT",
        claimed_publication_date=date(2025, 3, 1),
    ))
    target = next(n for n in original.nodes
                  if n.kind == LegalNodeKind.PARAGRAPH)
    amending_node = next(n for n in amendment.nodes
                         if n.kind == LegalNodeKind.ARTICLE)
    return original_pdf, amendment_pdf, original, amendment, target, amending_node


@pytest.fixture
def project():
    return ProjectLegalContext(
        drawing_sha256="a" * 64, province="Trabzon",
        district="Ortahisar", municipality="Ortahisar",
        use_classification="synthetic housing", building_class="test class",
        permit_or_application_date=date(2026, 5, 6),
        evaluation_date=date(2026, 10, 13),
        exception_review=ExceptionReview.USER_ASSERTED_NONE,
        reviewer_id="fixture-reviewer",
    )


def rule_for(source, node):
    return RuleDefinition(
        rule_id="unapproved.synthetic.test", version="2026-draft",
        domain=RuleDomain.REGULATORY,
        metric=MetricKind.SEGMENT_LENGTH_M,
        description="Only a synthetic candidate with no lawful force",
        operator=Comparison.GE, threshold=1.2,
        legal_source=LegalSourceLocator(
            document_sha256=source.document_sha256,
            page_index=node.spans[0].page_index,
            regulation_id=source.metadata.regulation_id,
            article_id="7", clause_id="1",
            effective_from=date(2020, 1, 1),
        ),
    )


def claimed_change(source, amendment, target, amending_node,
                   *, identifier="c1", effective_from=date(2025, 4, 1)):
    return AmendmentClaim(
        claim_id=identifier,
        target_document_sha256=source.document_sha256,
        target_node_id=target.node_id,
        amending_document_sha256=amendment.document_sha256,
        amending_node_id=amending_node.node_id,
        relation=AmendmentRelation.REPLACES,
        claimed_effective_from=effective_from,
        reviewer_id="fixture-reviewer",
        reason="Test-only reviewed link, not an authentic law",
        source_span=amending_node.spans[0],
    )


def test_matching_local_pdf_is_not_official_gazette(sources):
    pdf, _, source, _, target, _ = sources
    audit = verify_local_pdf(source, pdf)
    assert audit.status == SourceAuditStatus.LOCAL_SOURCE_MATCHED
    assert audit.inspected_spans >= len(source.lines)
    assert audit.document_sha256 == source.document_sha256
    assert audit.officiality == "OFFICIAL_PUBLICATION_NOT_VERIFIED"
    assert not audit.legal_compliance_certified
    missing = verify_local_pdf(source, None)
    assert missing.status == SourceAuditStatus.ORIGINAL_PDF_MISSING


def test_modified_pdf_byte_sequence_fails_even_when_metadata_claims_official(sources):
    pdf, _, original, _, _, _ = sources
    with pdf.open("ab") as f:
        f.write(b"\n% altered without changing AST\n")
    audit = verify_local_pdf(original, pdf)
    assert audit.status == SourceAuditStatus.ORIGINAL_PDF_MISMATCH
    assert not audit.legal_compliance_certified


def test_offpage_forged_span_rejected_by_visual_bounds(sources):
    pdf, _, original, _, target, _ = sources
    bad = target.spans[0].model_copy(update={
        "polygon": ((700, 12), (715, 12), (715, 28), (700, 28)),
    })
    altered = [n.model_copy(update={"spans": (bad,)}) if n.node_id == target.node_id
               else n for n in original.nodes]
    forged = original.model_copy(update={"nodes": altered})
    audit = verify_local_pdf(forged, pdf)
    assert audit.status == SourceAuditStatus.PAGE_GEOMETRY_MISMATCH


def test_source_node_rule_and_original_pdf_binding_never_auto_approved(sources, project):
    pdf, _, original, _, target, _ = sources
    rule = rule_for(original, target)
    result = bind_regulatory_evidence(
        rule, [original], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    assert result.status == BindingStatus.HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW
    assert result.local_source_audit.status == SourceAuditStatus.LOCAL_SOURCE_MATCHED
    assert result.source_document_sha256 == original.document_sha256
    assert result.original_spans == target.spans
    assert result.project_review.unknown_fields == ()
    assert "NO_INDEPENDENTLY_VERIFIED_VERSION_HISTORY" in result.reason_codes
    assert result.approval_status == "HUKUKI_HOLD"
    assert result.legal_compliance_certified is False


def test_missing_project_date_and_exception_cannot_claim_applicability(sources):
    pdf, _, original, _, target, _ = sources
    rule = rule_for(original, target)
    empty = ProjectLegalContext(drawing_sha256="a" * 64)
    status = assess_project_context(empty)
    assert "permit_or_application_date" in status.unknown_fields
    assert "exception_review" in status.unknown_fields
    bound = bind_regulatory_evidence(
        rule, [original], source_node_id=target.node_id,
        local_pdf_path=pdf, project=empty,
    )
    assert bound.status == BindingStatus.HOLD_PROJECT_CONTEXT
    assert bound.project_review.status == "INSUFFICIENT_EVIDENCE"
    assert bound.legal_compliance_certified is False


def test_exception_claim_needs_reference_and_remains_review_required(project):
    with pytest.raises(ValidationError, match="source IDs"):
        ProjectLegalContext(
            **(project.model_dump() | {
                "exception_review": ExceptionReview.USER_ASSERTED_PRESENT,
                "exception_source_ids": (),
            })
        )
    context = project.model_copy(update={
        "exception_review": ExceptionReview.USER_ASSERTED_PRESENT,
        "exception_source_ids": ("user-evidence-1",),
    })
    status = assess_project_context(context)
    assert status.status == "REVIEW_REQUIRED"
    assert status.reason_code == "CLAIMED_EXCEPTION_MUST_BE_REVIEWED_AGAINST_LEGAL_TEXT"


def test_rag_hit_exact_node_only_never_score_based_approval(sources, project):
    pdf, _, original, _, target, _ = sources
    with LegalRagStore() as db:
        db.index_document(original, original_pdf_path=pdf)
        hits = search_legal(db, "door", top_k=20)
        hit = next(h for h in hits.results if h.passage.node_id == target.node_id)
        assert hit.rrf_score > 0
        bound = bind_regulatory_evidence(
            rule_for(original, target), [original],
            source_node_id=target.node_id, local_pdf_path=pdf,
            project=project, rag_hit=hit,
        )
        assert bound.status == BindingStatus.HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW
        assert bound.rag_passage_id == hit.passage.passage_id
        assert bound.rag_rrf_score == hit.rrf_score
        assert not bound.legal_compliance_certified


def test_forged_rag_hit_with_right_node_id_but_wrong_text_is_rejected(sources, project):
    pdf, _, original, _, target, _ = sources
    with LegalRagStore() as db:
        db.index_document(original, original_pdf_path=pdf)
        hit = next(h for h in search_legal(db, "door", top_k=20).results
                   if h.passage.node_id == target.node_id)
    fake_entry = hit.passage.model_copy(update={"text": "invented legal conclusion"})
    forged = hit.model_copy(update={"passage": fake_entry, "rrf_score": 9999.0})
    binding = bind_regulatory_evidence(
        rule_for(original, target), [original],
        source_node_id=target.node_id, local_pdf_path=pdf,
        project=project, rag_hit=forged,
    )
    assert binding.status == BindingStatus.HOLD_RAG_CANDIDATE
    assert "RAG_HIT_DOES_NOT_EQUAL_ORIGINAL_LEGALAST_NODE" in binding.reason_codes


def test_rule_locator_wrong_article_or_page_is_rejected(sources, project):
    pdf, _, source, _, target, _ = sources
    r = rule_for(source, target)
    altered = r.model_copy(update={
        "legal_source": r.legal_source.model_copy(update={
            "article_id": "99",
        }),
    })
    result = bind_regulatory_evidence(
        altered, [source], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    assert result.status == BindingStatus.HOLD_LEGAL_NODE
    assert "RULE_ARTICLE_NUMBER_NOT_IN_ANCESTRY" in result.reason_codes
    wrong_page_rule = r.model_copy(update={
        "legal_source": r.legal_source.model_copy(update={"page_index": 3}),
    })
    result = bind_regulatory_evidence(
        wrong_page_rule, [source], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    assert result.status == BindingStatus.HOLD_LEGAL_NODE
    assert "RULE_PAGE_NOT_ON_TARGET_LEGAL_NODE" in result.reason_codes


def test_amendment_source_and_target_ids_preserved_not_consolidated(sources, project):
    pdf, amendment_pdf, base, change, target, amending_node = sources
    claim = claimed_change(base, change, target, amending_node)
    chain = assess_version_chain(
        [base, change], [claim],
        target_document_sha256=base.document_sha256,
        target_node_id=target.node_id, as_of=project.permit_or_application_date,
    )
    assert chain.claim_ids == ("c1",)
    assert chain.consolidated_text is None
    assert not chain.legal_effect_certified
    assert chain.status == "INSUFFICIENT_EVIDENCE"
    assert "OFFICIAL_AMENDMENT_HISTORY_NOT_AUTHENTICATED" in {
        x.code for x in chain.issues
    }
    binding = bind_regulatory_evidence(
        rule_for(base, target), [base, change],
        source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
        amendment_claims=[claim],
        amendment_pdf_paths={change.document_sha256: amendment_pdf},
    )
    assert binding.status == BindingStatus.HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW
    assert binding.amendment_source_audits[0].status == SourceAuditStatus.LOCAL_SOURCE_MATCHED
    assert not binding.legal_compliance_certified


def test_amendment_wrong_source_polygon_and_missing_original_corpus(sources, project):
    _, _, base, change, target, amending_node = sources
    c = claimed_change(base, change, target, amending_node)
    wrong_span = target.spans[0].model_copy(update={
        "document_sha256": change.document_sha256
    })
    wrong_claim = c.model_copy(update={"source_span": wrong_span})
    review = assess_version_chain(
        [base, change], [wrong_claim],
        target_document_sha256=base.document_sha256,
        target_node_id=target.node_id, as_of=project.permit_or_application_date,
    )
    assert review.status == "REVIEW_REQUIRED"
    assert "AMENDMENT_SOURCE_SPAN_NOT_ON_NODE" in {x.code for x in review.issues}
    missing = assess_version_chain(
        [base], [c], target_document_sha256=base.document_sha256,
        target_node_id=target.node_id, as_of=project.permit_or_application_date,
    )
    assert "AMENDMENT_DOCUMENT_NOT_IN_CORPUS" in {x.code for x in missing.issues}


def test_multiple_active_amendments_at_same_date_review_required(sources, project):
    _, _, base, change, target, amend = sources
    a = claimed_change(base, change, target, amend, identifier="A")
    b = claimed_change(base, change, target, amend, identifier="B")
    outcome = assess_version_chain(
        [base, change], [b, a],
        target_document_sha256=base.document_sha256,
        target_node_id=target.node_id, as_of=project.permit_or_application_date,
    )
    assert outcome.status == "REVIEW_REQUIRED"
    assert outcome.claim_ids == ("A", "B")
    assert "MULTIPLE_UNCONSOLIDATED_AMENDMENTS" in {i.code for i in outcome.issues}


def test_project_earlier_than_asserted_effective_date_cannot_retroactively_apply(sources, project):
    pdf, _, base, _, target, _ = sources
    r = rule_for(base, target)
    changed_rule = r.model_copy(update={
        "legal_source": r.legal_source.model_copy(
            update={"effective_from": date(2027, 1, 1)}
        ),
    })
    bound = bind_regulatory_evidence(
        changed_rule, [base], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    assert "PROJECT_DATE_BEFORE_ASSERTED_RULE_START" in bound.reason_codes
    assert bound.status != "APPROVED_FOR_CHECK"


def test_ruleengine_remains_locked_even_with_all_claims_and_high_rrf(sources, project, tmp_path):
    pdf, _, base, _, target, _ = sources
    doc = ezdxf.new("R2013")
    doc.modelspace().add_line((0, 0), (2, 0))
    dxf = tmp_path / "drawing.dxf"
    doc.saveas(dxf)
    drawing = parse_dxf(dxf).drawing
    rule = rule_for(base, target)
    engine = RuleEngine([rule])
    request = RuleRequest(drawing=drawing)
    with LegalRagStore() as db:
        db.index_document(base, original_pdf_path=pdf)
        hit = next(h for h in search_legal(db, "door", top_k=20).results
                   if h.passage.node_id == target.node_id)
    with pytest.raises(BindingInputError, match="another drawing SHA"):
        evaluate_regulatory_with_evidence(
            engine, rule, request, [base],
            source_node_id=target.node_id, local_pdf_path=pdf,
            project=project, rag_hit=hit,
        )
    correct_project = project.model_copy(update={
        "drawing_sha256": drawing.source_sha256,
    })
    wrapped = evaluate_regulatory_with_evidence(
        engine, rule, request, [base],
        source_node_id=target.node_id, local_pdf_path=pdf,
        project=correct_project, rag_hit=hit,
    )
    assert wrapped.regulatory_gate == "LOCKED_IN_RULEENGINE_V0_1"
    assert wrapped.rule_result.status == RuleStatus.INSUFFICIENT_EVIDENCE
    assert wrapped.rule_result.reason_code == (
        "REGULATORY_SOURCE_AND_APPLICABILITY_UNVERIFIED"
    )
    assert wrapped.rule_result.legal_compliance_certified is False
    assert wrapped.binding.approval_status == "HUKUKI_HOLD"


def test_source_not_found_never_approves_and_wrong_node_rejected(sources, project):
    _, _, base, _, target, _ = sources
    no_pdf = bind_regulatory_evidence(
        rule_for(base, target), [base],
        source_node_id=target.node_id, local_pdf_path=None,
        project=project,
    )
    assert no_pdf.status == BindingStatus.HOLD_ORIGINAL_SOURCE
    with pytest.raises(BindingInputError, match="does not exist"):
        bind_regulatory_evidence(
            rule_for(base, target), [base],
            source_node_id="does-not-exist", local_pdf_path=None,
            project=project,
        )


def test_json_roundtrip_deterministic_binding_and_budget(sources, project):
    pdf, _, base, _, target, _ = sources
    rule = rule_for(base, target)
    a = bind_regulatory_evidence(
        rule, [base], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    b = bind_regulatory_evidence(
        rule, [base], source_node_id=target.node_id,
        local_pdf_path=pdf, project=project,
    )
    assert a.model_dump_json() == b.model_dump_json()
    assert type(a).model_validate_json(a.model_dump_json()) == a
    with pytest.raises(BindingInputError, match="budget"):
        bind_regulatory_evidence(
            rule, [base], source_node_id=target.node_id,
            local_pdf_path=pdf, max_documents=0,
        )


def test_amendment_claim_without_original_pdf_is_held(sources, project):
    pdf, amendment_pdf, original, amend, node, amended_node = sources
    claim = claimed_change(original, amend, node, amended_node)
    bound = bind_regulatory_evidence(
        rule_for(original, node), [original, amend],
        source_node_id=node.node_id, local_pdf_path=pdf,
        project=project, amendment_claims=[claim],
    )
    assert bound.status == BindingStatus.HOLD_AMENDMENT_CHAIN
    assert "AMENDING_ORIGINAL_PDF_NOT_VERIFIED" in bound.reason_codes
    assert bound.amendment_source_audits[0].status == SourceAuditStatus.ORIGINAL_PDF_MISSING


def test_amendment_modified_after_ast_creation_is_not_trusted(sources, project):
    pdf, amendment_pdf, original, amend, node, amended_node = sources
    claim = claimed_change(original, amend, node, amended_node)
    with amendment_pdf.open("ab") as f:
        f.write(b"\n%after-legalast\n")
    bound = bind_regulatory_evidence(
        rule_for(original, node), [original, amend],
        source_node_id=node.node_id, local_pdf_path=pdf,
        project=project, amendment_claims=[claim],
        amendment_pdf_paths={amend.document_sha256: amendment_pdf},
    )
    assert bound.status == BindingStatus.HOLD_AMENDMENT_CHAIN
    assert bound.amendment_source_audits[0].status == SourceAuditStatus.ORIGINAL_PDF_MISMATCH
