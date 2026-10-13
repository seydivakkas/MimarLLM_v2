"""Separate original/amendment visual inspection on explicit date-scoped claims.

VersionReview is always legal HOLD; two source PDFs are NEVER consolidated.
"""
from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict

from mimarllm.legal.models import LegalDocument, SHA_PATTERN
from mimarllm.legal.review import (
    AmendmentSide, ReviewQueue, ReviewSelection, TargetKind, build_review_queue,
)
from mimarllm.legal.versions import (
    AmendmentClaim, VersionReview, assess_version_chain,
)


class VersionReviewPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    target_document_sha256: str
    target_node_id: str
    evaluated_as_of: date | None
    review_queue: ReviewQueue
    chain_assessment: VersionReview
    version_status: Literal["UNVERIFIED_HISTORICAL_VERSION"] = (
        "UNVERIFIED_HISTORICAL_VERSION"
    )
    approved_for_check: Literal[False] = False


def create_version_review_packet(
    documents: list[LegalDocument],
    amendment_claims: list[AmendmentClaim],
    *, target_document_sha256: str,
    target_node_id: str, as_of: date | None,
    max_relevant_amendments: int = 10,
) -> VersionReviewPacket:
    """Pair the *actual* original node with every selected amendment node.

    A later amendment is included even for earlier project dates, so the
    reviewer sees the historical distinction. No automatic effective text.
    """
    chain = assess_version_chain(
        documents, amendment_claims,
        target_document_sha256=target_document_sha256,
        target_node_id=target_node_id, as_of=as_of,
    )
    related = [c for c in amendment_claims
               if c.target_document_sha256 == target_document_sha256
               and c.target_node_id == target_node_id]
    if len(related) > max_relevant_amendments:
        raise ValueError("Too many amendment PDF comparison candidates")
    selections = [
        ReviewSelection(
            document_sha256=target_document_sha256,
            kind=TargetKind.NODE, reference_id=target_node_id,
        ),
    ]
    for c in sorted(related, key=lambda c: (c.claimed_effective_from, c.claim_id)):
        selections.append(ReviewSelection(
            document_sha256=c.amending_document_sha256,
            kind=TargetKind.AMENDMENT_SIDE, reference_id=c.claim_id,
            amendment_side=AmendmentSide.AMENDING,
        ))
    queue = build_review_queue(
        documents, selections, amendment_claims=amendment_claims,
        max_tasks=24,
    )
    return VersionReviewPacket(
        target_document_sha256=target_document_sha256,
        target_node_id=target_node_id, evaluated_as_of=as_of,
        review_queue=queue, chain_assessment=chain,
    )
