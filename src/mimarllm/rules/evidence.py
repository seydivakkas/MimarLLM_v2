"""LegalAST + local original PDF + version + project context rule evidence.

This module links exact nodes, NOT legal compliance. The only regulatory
verdict permitted by RuleEngine v0.1 is INSUFFICIENT_EVIDENCE.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from mimarllm.legal.applicability import (
    ApplicabilityEvidence, ProjectLegalContext, assess_project_context,
)
from mimarllm.legal.models import LegalDocument, LegalNodeKind, LegalSourceSpan, SHA_PATTERN
from mimarllm.legal.verification import (
    SourceAudit, SourceAuditStatus, verify_local_pdf,
)
from mimarllm.legal.versions import (
    AmendmentClaim, VersionReview, assess_version_chain,
)
from mimarllm.rag.models import RagHit, RagKind
from mimarllm.rules.base import (
    RuleDefinition, RuleDomain, RuleRequest, RuleResult, RuleStatus,
)
from mimarllm.rules.engine import RuleEngine


class BindingInputError(ValueError):
    """Malformed evidence input; never a regulatory pass."""


class BindingStatus(str, Enum):
    HOLD_LEGAL_NODE = "HOLD_LEGAL_NODE"
    HOLD_RAG_CANDIDATE = "HOLD_RAG_CANDIDATE"
    HOLD_ORIGINAL_SOURCE = "HOLD_ORIGINAL_SOURCE"
    HOLD_AMENDMENT_CHAIN = "HOLD_AMENDMENT_CHAIN"
    HOLD_PROJECT_CONTEXT = "HOLD_PROJECT_CONTEXT"
    HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW = (
        "HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW"
    )


class RuleEvidenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    rule_id: str
    rule_version: str
    status: BindingStatus
    reason_codes: tuple[str, ...]
    source_document_sha256: str = Field(pattern=SHA_PATTERN)
    source_node_id: str
    original_spans: tuple[LegalSourceSpan, ...]
    local_source_audit: SourceAudit | None = None
    amendment_source_audits: tuple[SourceAudit, ...] = ()
    version_review: VersionReview | None = None
    project_review: ApplicabilityEvidence | None = None
    rag_passage_id: str | None = None
    rag_rrf_score: float | None = None
    legal_compliance_certified: Literal[False] = False
    approval_status: Literal["HUKUKI_HOLD"] = "HUKUKI_HOLD"


class RegulatoryEvidenceEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    binding: RuleEvidenceBinding
    rule_result: RuleResult
    regulatory_gate: Literal["LOCKED_IN_RULEENGINE_V0_1"] = (
        "LOCKED_IN_RULEENGINE_V0_1"
    )


def _ancestry(document: LegalDocument, node_id: str):
    nodes = {n.node_id: n for n in document.nodes}
    sequence = []
    seen = set()
    current = node_id
    while current is not None:
        if current in seen or current not in nodes:
            raise BindingInputError("LegalAST ancestry cycle or broken node")
        seen.add(current)
        node = nodes[current]
        sequence.append(node)
        current = node.parent_node_id
    return sequence


def bind_regulatory_evidence(
    rule: RuleDefinition,
    documents: list[LegalDocument],
    *,
    source_node_id: str,
    local_pdf_path: str | Path | None,
    project: ProjectLegalContext | None = None,
    amendment_claims: list[AmendmentClaim] | None = None,
    amendment_pdf_paths: dict[str, str | Path] | None = None,
    rag_hit: RagHit | None = None,
    max_documents: int = 100,
) -> RuleEvidenceBinding:
    """Attach original-citation evidence and enumerate missing legal gates.

    PDF/locality validation is real. Every conclusion about official origin,
    amendment effectiveness, applicability and authority remains on HOLD.
    """
    rule = RuleDefinition.model_validate(rule.model_dump())
    if rule.domain != RuleDomain.REGULATORY or rule.legal_source is None:
        raise BindingInputError("Only regulatory rules have a legal source binding")
    if not source_node_id or not source_node_id.strip():
        raise BindingInputError("Exact LegalAST node ID required")
    if not 1 <= len(documents) <= max_documents:
        raise BindingInputError("Regulatory source document budget exceeded")
    docs = [LegalDocument.model_validate(d.model_dump()) for d in documents]
    if len({d.document_sha256 for d in docs}) != len(docs):
        raise BindingInputError("Duplicate original PDF document SHA")
    if amendment_claims is None:
        amendment_claims = []
    # Always validate claims even if they are not for selected target.
    claims = [AmendmentClaim.model_validate(c.model_dump()) for c in amendment_claims]
    if project is not None:
        project = ProjectLegalContext.model_validate(project.model_dump())
    if rag_hit is not None:
        rag_hit = RagHit.model_validate(rag_hit.model_dump())

    locator = rule.legal_source
    target = next((d for d in docs
                   if d.document_sha256 == locator.document_sha256), None)
    if target is None:
        raise BindingInputError("Rule referenced PDF is absent from supplied LegalAST set")

    ids = [n.node_id for n in target.nodes]
    if source_node_id not in ids:
        raise BindingInputError("Source LegalAST node ID does not exist in original PDF")
    node = next(n for n in target.nodes if n.node_id == source_node_id)
    lineage = _ancestry(target, source_node_id)
    reasons: list[str] = []
    citation_ok = True
    if target.metadata.regulation_id != locator.regulation_id:
        reasons.append("RULE_REGULATION_ID_MISMATCH")
        citation_ok = False
    if node.kind not in {
        LegalNodeKind.ARTICLE, LegalNodeKind.TEMPORARY_ARTICLE,
        LegalNodeKind.PARAGRAPH, LegalNodeKind.ITEM,
    }:
        reasons.append("RULE_TARGET_NOT_A_PROVISION")
        citation_ok = False
    article_numbers = [
        n.article_number for n in lineage
        if n.kind in {LegalNodeKind.ARTICLE, LegalNodeKind.TEMPORARY_ARTICLE}
    ]
    if locator.article_id not in article_numbers:
        reasons.append("RULE_ARTICLE_NUMBER_NOT_IN_ANCESTRY")
        citation_ok = False
    if locator.clause_id is not None:
        clause = locator.clause_id.strip().strip("()").strip().lower()
        clause_numbers = [
            n.paragraph_number for n in lineage if n.kind == LegalNodeKind.PARAGRAPH
        ] + [n.item_key for n in lineage if n.kind == LegalNodeKind.ITEM]
        if clause not in clause_numbers:
            reasons.append("RULE_CLAUSE_NOT_IN_ANCESTRY")
            citation_ok = False
    if not any(span.page_index == locator.page_index for span in node.spans):
        reasons.append("RULE_PAGE_NOT_ON_TARGET_LEGAL_NODE")
        citation_ok = False
    if target.metadata.document_kind == "AMENDMENT":
        reasons.append("AMENDING_PDF_NODE_NOT_CONSOLIDATED_TARGET_RULE")
        citation_ok = False

    # RAG is optional discovery metadata. Rank is stored for diagnostics
    # ONLY. It can never satisfy an officiality/date/approval condition.
    rag_ok = True
    if rag_hit is not None:
        entry = rag_hit.passage
        if (entry.entry_kind != RagKind.NODE
                or entry.node_id != node.node_id
                or entry.document_sha256 != target.document_sha256
                or entry.regulation_id != target.metadata.regulation_id
                or entry.text != node.text
                or entry.spans != node.spans
                or entry.node_kind != node.kind.value
                or entry.review_status != "UNREVIEWED"):
            rag_ok = False
            reasons.append("RAG_HIT_DOES_NOT_EQUAL_ORIGINAL_LEGALAST_NODE")
        # DO NOT compare rrf_score to a confidence threshold.
        if rag_hit.legal_compliance_certified:
            rag_ok = False
            reasons.append("RAG_FALSE_LEGAL_CERTIFICATION")

    source = verify_local_pdf(target, local_pdf_path)
    if source.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED:
        reasons.append("LOCAL_ORIGINAL_PDF_NOT_VERIFIED")
    else:
        reasons.append("LOCAL_PDF_INTEGRITY_NOT_PROOF_OF_OFFICIAL_PUBLICATION")

    # A user-asserted amendment link has two independent PDF identities.
    # Verify source files of every relevant amending document, not only the
    # target statute. Absence of a local amendment PDF remains an explicit HOLD.
    amendment_pdf_paths = amendment_pdf_paths or {}
    related_amendment_hashes = sorted({
        claim.amending_document_sha256 for claim in claims
        if claim.target_document_sha256 == target.document_sha256
        and claim.target_node_id == node.node_id
    })
    document_map = {d.document_sha256: d for d in docs}
    amendment_audits = tuple(
        verify_local_pdf(
            document_map[hash_value],
            amendment_pdf_paths.get(hash_value),
        )
        for hash_value in related_amendment_hashes
        if hash_value in document_map
    )
    if len(amendment_audits) != len(related_amendment_hashes):
        reasons.append("AMENDING_PDF_AST_NOT_SUPPLIED")
    if any(audit.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED
           for audit in amendment_audits):
        reasons.append("AMENDING_ORIGINAL_PDF_NOT_VERIFIED")

    version = assess_version_chain(
        docs, claims, target_document_sha256=target.document_sha256,
        target_node_id=node.node_id,
        as_of=project.permit_or_application_date if project else None,
    )
    reasons.extend(issue.code for issue in version.issues)
    app = assess_project_context(project) if project else None
    if app is None:
        reasons.append("PROJECT_CONTEXT_NOT_SUPPLIED")
    else:
        reasons.append(app.reason_code)
    if project is not None and project.permit_or_application_date is not None:
        if project.permit_or_application_date < locator.effective_from:
            reasons.append("PROJECT_DATE_BEFORE_ASSERTED_RULE_START")
        if (locator.effective_until is not None and
                project.permit_or_application_date > locator.effective_until):
            reasons.append("PROJECT_DATE_AFTER_ASSERTED_RULE_END")
        # Dates are UNVERIFIED even if they are internally compatible.
        reasons.append("CLAIMED_RULE_DATE_NOT_OFFICIALLY_VERIFIED")

    if not citation_ok:
        status = BindingStatus.HOLD_LEGAL_NODE
    elif not rag_ok:
        status = BindingStatus.HOLD_RAG_CANDIDATE
    elif source.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED:
        status = BindingStatus.HOLD_ORIGINAL_SOURCE
    elif (version.status == "REVIEW_REQUIRED"
          or len(amendment_audits) != len(related_amendment_hashes)
          or any(a.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED
                 for a in amendment_audits)):
        status = BindingStatus.HOLD_AMENDMENT_CHAIN
    elif app is None or app.unknown_fields or app.status == "REVIEW_REQUIRED":
        status = BindingStatus.HOLD_PROJECT_CONTEXT
    else:
        # A complete user form, local PDF hash, exact source node and complete
        # amendment *claim* graph still CANNOT establish official publication.
        status = BindingStatus.HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW

    return RuleEvidenceBinding(
        rule_id=rule.rule_id, rule_version=rule.version, status=status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        source_document_sha256=target.document_sha256,
        source_node_id=node.node_id, original_spans=node.spans,
        local_source_audit=source, amendment_source_audits=amendment_audits,
        version_review=version,
        project_review=app,
        rag_passage_id=rag_hit.passage.passage_id if rag_hit else None,
        rag_rrf_score=rag_hit.rrf_score if rag_hit else None,
    )


def evaluate_regulatory_with_evidence(
    engine: RuleEngine,
    rule: RuleDefinition,
    request: RuleRequest,
    documents: list[LegalDocument],
    *,
    source_node_id: str,
    local_pdf_path: str | Path | None,
    project: ProjectLegalContext | None = None,
    amendment_claims: list[AmendmentClaim] | None = None,
    amendment_pdf_paths: dict[str, str | Path] | None = None,
    rag_hit: RagHit | None = None,
) -> RegulatoryEvidenceEvaluation:
    """Report bound source and existing RuleEngine HOLD side-by-side."""
    rule = RuleDefinition.model_validate(rule.model_dump())
    # A project context cannot be borrowed from another DXF/PDF drawing.
    request = RuleRequest.model_validate(request.model_dump())
    if project is not None and project.drawing_sha256 != request.drawing.source_sha256:
        raise BindingInputError("Project legal context belongs to another drawing SHA")
    binding = bind_regulatory_evidence(
        rule, documents, source_node_id=source_node_id,
        local_pdf_path=local_pdf_path, project=project,
        amendment_claims=amendment_claims,
        amendment_pdf_paths=amendment_pdf_paths, rag_hit=rag_hit,
    )
    result = engine.evaluate(rule.rule_id, request)
    if (result.domain != RuleDomain.REGULATORY
            or result.rule_version != rule.version
            or result.legal_source != rule.legal_source
            or result.status != RuleStatus.INSUFFICIENT_EVIDENCE
            or result.legal_compliance_certified):
        raise BindingInputError("RuleEngine regulatory safety gate does not match binding")
    return RegulatoryEvidenceEvaluation(binding=binding, rule_result=result)
