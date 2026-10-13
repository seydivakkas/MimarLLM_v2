"""Simple explicit PDF→LegalAST→SQLite index pipeline, entirely offline."""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from mimarllm.legal.etl import parse_legal_pdf
from mimarllm.legal.models import LegalDocumentMetadata
from mimarllm.rag.embeddings import LocalEmbedder
from mimarllm.rag.store import LegalRagStore


class IndexSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str
    indexed_passages: int = Field(ge=0)
    node_count: int = Field(ge=0)
    table_count: int = Field(ge=0)
    legal_review_required: bool = True
    embedded_model_id: str | None = None


def index_local_legal_pdf(
    pdf_path: str | Path,
    metadata: LegalDocumentMetadata,
    store: LegalRagStore,
    *,
    embedder: LocalEmbedder | None = None,
    ocr_pages: tuple[int, ...] = (),
    ocr_engine=None,
) -> IndexSummary:
    document = parse_legal_pdf(
        pdf_path, metadata, ocr_pages=ocr_pages, ocr_engine=ocr_engine,
    )
    count = store.index_document(
        document, embedder=embedder, original_pdf_path=pdf_path,
    )
    return IndexSummary(
        document_sha256=document.document_sha256,
        indexed_passages=count, node_count=len(document.nodes),
        table_count=len(document.tables),
        embedded_model_id=embedder.model_id if embedder else None,
    )
