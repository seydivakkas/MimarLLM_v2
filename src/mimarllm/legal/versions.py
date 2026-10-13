"""Source-linked amendment *claims*, not an authoritative consolidated statute."""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.legal.models import LegalDocument, LegalNodeKind, LegalSourceSpan, SHA_PATTERN


class AmendmentRelation(str, Enum):
    REPLACES = "REPLACES"
    REPEALS = "REPEALS"
    ADDS_EXCEPTION = "ADDS_EXCEPTION"
    TRANSITION = "TRANSITION"


class AmendmentClaim(BaseModel):
    """Unverified, manually asserted relationship between TWO original PDFs."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    claim_id: str = Field(min_length=1)
    target_document_sha256: str = Field(pattern=SHA_PATTERN)
    target_node_id: str = Field(min_length=1)
    amending_document_sha256: str = Field(pattern=SHA_PATTERN)
    amending_node_id: str = Field(min_length=1)
    relation: AmendmentRelation
    claimed_effective_from: date
    claimed_effective_until: date | None = None
    reviewer_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    source_span: LegalSourceSpan
    provenance: Literal["HUMAN_ASSERTED_UNVERIFIED"] = "HUMAN_ASSERTED_UNVERIFIED"

    @model_validator(mode="after")
    def review_constraints(self):
        if (self.claimed_effective_until is not None and
                self.claimed_effective_until < self.claimed_effective_from):
            raise ValueError("Inverted amendment effectivity interval")
        if (not self.reviewer_id.strip() or not self.reason.strip()
                or self.target_document_sha256 == self.amending_document_sha256):
            raise ValueError("Claim needs reviewer/reason and a distinct amendment PDF")
        if self.source_span.document_sha256 != self.amending_document_sha256:
            raise ValueError("Amendment source polygon must belong to amending PDF")
        return self


class VersionIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    claim_id: str | None = None
    detail: str


class VersionReview(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_document_sha256: str = Field(pattern=SHA_PATTERN)
    target_node_id: str
    queried_as_of: date | None
    claim_ids: tuple[str, ...] = ()
    issues: tuple[VersionIssue, ...] = ()
    status: Literal["INSUFFICIENT_EVIDENCE", "REVIEW_REQUIRED"] = "INSUFFICIENT_EVIDENCE"
    consolidated_text: None = None
    legal_effect_certified: Literal[False] = False


def assess_version_chain(
    documents: list[LegalDocument],
    claims: list[AmendmentClaim],
    *,
    target_document_sha256: str,
    target_node_id: str,
    as_of: date | None,
    max_documents: int = 100,
    max_claims: int = 2000,
) -> VersionReview:
    """Check references and dates without inferring statutory effectiveness."""
    if (not 1 <= len(documents) <= max_documents
            or len(claims) > max_claims):
        raise ValueError("Version verification safety budget exceeded")
    docs = [LegalDocument.model_validate(d.model_dump()) for d in documents]
    claims = [AmendmentClaim.model_validate(c.model_dump()) for c in claims]
    doc_map = {d.document_sha256: d for d in docs}
    if len(doc_map) != len(docs):
        raise ValueError("Duplicate original PDF SHA in version documents")
    if target_document_sha256 not in doc_map:
        raise ValueError("Target LegalAST PDF not supplied")
    target_nodes = {n.node_id: n for n in doc_map[target_document_sha256].nodes}
    if target_node_id not in target_nodes:
        raise ValueError("Target legal node not in supplied original PDF")
    if len({claim.claim_id for claim in claims}) != len(claims):
        raise ValueError("Duplicate amendment claim ID")
    issues: list[VersionIssue] = []
    relevant = [c for c in claims if (
        c.target_document_sha256 == target_document_sha256 and
        c.target_node_id == target_node_id
    )]
    if not relevant:
        issues.append(VersionIssue(
            code="NO_INDEPENDENTLY_VERIFIED_VERSION_HISTORY",
            detail="No explicit amendment links. Absence is not proof of unchanged law",
        ))
    if as_of is None:
        issues.append(VersionIssue(
            code="PROJECT_EFFECTIVITY_DATE_UNKNOWN",
            detail="Cannot select a claimed amendment interval without a project date",
        ))
    else:
        active_claims = [
            c for c in relevant
            if c.claimed_effective_from <= as_of
            and (c.claimed_effective_until is None or
                 as_of <= c.claimed_effective_until)
        ]
        if len(active_claims) > 1:
            issues.append(VersionIssue(
                code="MULTIPLE_UNCONSOLIDATED_AMENDMENTS",
                detail="Several amendments claim effects on the same node/date",
            ))
        if any(c.claimed_effective_from > as_of for c in relevant):
            issues.append(VersionIssue(
                code="LATER_AMENDMENT_REQUIRES_HISTORICAL_REVIEW",
                detail="A later claimed legal version must not be retroactively applied",
            ))
    for claim in claims:
        target = doc_map.get(claim.target_document_sha256)
        amendment = doc_map.get(claim.amending_document_sha256)
        if not target or not amendment:
            issues.append(VersionIssue(
                code="AMENDMENT_DOCUMENT_NOT_IN_CORPUS", claim_id=claim.claim_id,
                detail="Target or amending original PDF was not supplied",
            ))
            continue
        tnode = next((x for x in target.nodes if x.node_id == claim.target_node_id), None)
        anode = next((x for x in amendment.nodes if x.node_id == claim.amending_node_id), None)
        if tnode is None or anode is None:
            issues.append(VersionIssue(
                code="AMENDMENT_NODE_NOT_IN_CORPUS", claim_id=claim.claim_id,
                detail="Link must cite exact source and target LegalAST node IDs",
            ))
            continue
        if amendment.metadata.document_kind != "AMENDMENT":
            issues.append(VersionIssue(
                code="AMENDMENT_PDF_KIND_UNREVIEWED", claim_id=claim.claim_id,
                detail="Referenced document was not classified as an amendment",
            ))
        if claim.source_span not in anode.spans:
            issues.append(VersionIssue(
                code="AMENDMENT_SOURCE_SPAN_NOT_ON_NODE", claim_id=claim.claim_id,
                detail="Claim polygon must be an actual span of cited amendment node",
            ))
        if tnode.kind not in {
            LegalNodeKind.ARTICLE, LegalNodeKind.TEMPORARY_ARTICLE,
            LegalNodeKind.PARAGRAPH, LegalNodeKind.ITEM,
        }:
            issues.append(VersionIssue(
                code="TARGET_NOT_A_LEGAL_PROVISION", claim_id=claim.claim_id,
                detail="Target cannot be an unscoped heading or body fragment",
            ))
        # An amendment's article number is its OWN number; no matching on
        # article-number strings or inferred target law identity.
        if target.metadata.regulation_id == amendment.metadata.regulation_id:
            issues.append(VersionIssue(
                code="AMENDMENT_TARGET_REGULATION_ID_REVIEW",
                claim_id=claim.claim_id,
                detail="Identical user-supplied regulation IDs do not establish consolidation",
            ))
    issues.append(VersionIssue(
        code="OFFICIAL_AMENDMENT_HISTORY_NOT_AUTHENTICATED",
        detail="Explicit claim records and asserted effectivity do not certify law",
    ))
    status = ("REVIEW_REQUIRED" if any(x.code in {
        "MULTIPLE_UNCONSOLIDATED_AMENDMENTS", "AMENDMENT_DOCUMENT_NOT_IN_CORPUS",
        "AMENDMENT_NODE_NOT_IN_CORPUS", "AMENDMENT_SOURCE_SPAN_NOT_ON_NODE",
        "AMENDMENT_PDF_KIND_UNREVIEWED", "TARGET_NOT_A_LEGAL_PROVISION",
    } for x in issues) else "INSUFFICIENT_EVIDENCE")
    return VersionReview(
        target_document_sha256=target_document_sha256,
        target_node_id=target_node_id, queried_as_of=as_of,
        claim_ids=tuple(sorted(c.claim_id for c in relevant)),
        issues=tuple(issues), status=status,
    )
