"""Evidence-linked retrieval output; relevance is NOT legal verification."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from mimarllm.legal.models import LegalSourceSpan, SHA_PATTERN


class RagKind(str, Enum):
    NODE = "NODE"
    TABLE_CELL = "TABLE_CELL"


class SearchMode(str, Enum):
    LEXICAL_ONLY = "LEXICAL_ONLY"
    HYBRID = "HYBRID"
    DENSE_ONLY = "DENSE_ONLY"


class IndexedPassage(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    passage_id: str = Field(min_length=1)
    document_sha256: str = Field(pattern=SHA_PATTERN)
    regulation_id: str = Field(min_length=1)
    document_kind: str
    entry_kind: RagKind
    node_kind: str
    node_id: str | None = None
    parent_node_id: str | None = None
    article_number: str | None = None
    paragraph_number: str | None = None
    item_key: str | None = None
    text: str
    spans: tuple[LegalSourceSpan, ...] = Field(min_length=1)
    review_required: bool = True
    review_status: Literal["UNREVIEWED"] = "UNREVIEWED"


class RagHit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    passage: IndexedPassage
    rrf_score: float = Field(gt=0, allow_inf_nan=False)
    fts_rank: int | None = Field(default=None, ge=1)
    dense_rank: int | None = Field(default=None, ge=1)
    source_pdf_available: bool = False
    legal_compliance_certified: Literal[False] = False
    claim_scope: Literal["RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE"] = (
        "RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE"
    )


class RagResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    query: str
    mode: SearchMode
    dense_model_id: str | None = None
    dense_state: Literal["DISABLED", "INDEXED", "NO_MODEL_VECTORS"] = "DISABLED"
    results: tuple[RagHit, ...]
    note: Literal["UNREVIEWED_SOURCES_RELEVANCE_NOT_LEGAL_VALIDITY"] = (
        "UNREVIEWED_SOURCES_RELEVANCE_NOT_LEGAL_VALIDITY"
    )
