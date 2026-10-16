"""Pure local BM25/dense rank fusion with stable Reciprocal Rank Fusion."""
from __future__ import annotations

import re

from mimarllm.rag.embeddings import LocalEmbedder, normalize_vectors, require_embedder
from mimarllm.rag.models import RagHit, RagResponse, SearchMode
from mimarllm.rag.lexicon import expand_architectural_terms
from mimarllm.rag.store import LegalRagStore, RagStoreError


def search_legal(
    store: LegalRagStore,
    query: str,
    *,
    embedder: LocalEmbedder | None = None,
    top_k: int = 10,
    candidate_limit: int = 100,
    rrf_k: int = 60,
    max_dense_scan: int = 50_000,
    lexical_expansion: bool = False,
    regulation_id: str | None = None,
    document_sha256: str | None = None,
) -> RagResponse:
    """Evidence retrieval only. Never promote matches to regulatory approval."""
    if (not isinstance(top_k, int) or not 1 <= top_k <= 50
            or not isinstance(candidate_limit, int) or
            not top_k <= candidate_limit <= 200
            or not isinstance(rrf_k, int) or not 1 <= rrf_k <= 1000):
        raise RagStoreError("RRF result and candidate limits are invalid")
    if document_sha256 is not None and not re.fullmatch(r"[0-9a-f]{64}", document_sha256):
        raise RagStoreError("Source PDF SHA filter must be 64 lowercase hex digits")
    if regulation_id is not None and (
        not isinstance(regulation_id, str) or
        not regulation_id.strip() or len(regulation_id) > 200
    ):
        raise RagStoreError("Invalid regulation identifier filter")
    # lexical_rank validates query even for no dense model.
    lexical = store.lexical_rank(
        query, limit=candidate_limit,
        regulation_id=regulation_id, document_sha256=document_sha256,
    )
    expansion = None
    if lexical_expansion:
        expansion = expand_architectural_terms(query)
        if expansion.hints:
            # Expansion is deliberately a SECOND, lower-priority lexical
            # channel; exact original query hits are never displaced by
            # related terminology when no dense rank is available.
            alt_ids = store.lexical_rank(
                " ".join(expansion.hints), limit=candidate_limit,
                regulation_id=regulation_id, document_sha256=document_sha256,
            )
            original = set(lexical)
            lexical += [ident for ident in alt_ids if ident not in original]
    dense: list[str] = []
    dense_state = "DISABLED"
    model_id: str | None = None
    if embedder is not None:
        require_embedder(embedder)
        model_id = embedder.model_id
        if store.has_dense_vectors(model_id):
            vector = normalize_vectors(
                embedder.encode([query]), 1, embedder.dimensions,
            )[0]
            dense = store.dense_rank(
                vector, model_id=model_id, dimensions=embedder.dimensions,
                limit=candidate_limit, max_scan=max_dense_scan,
                regulation_id=regulation_id,
                document_sha256=document_sha256,
            )
            dense_state = "INDEXED"
        else:
            dense_state = "NO_MODEL_VECTORS"

    fts_positions = {ident: rank for rank, ident in enumerate(lexical, 1)}
    dense_positions = {ident: rank for rank, ident in enumerate(dense, 1)}
    fused = {
        ident: (1 / (rrf_k + fts_positions[ident]) if ident in fts_positions else 0)
        + (1 / (rrf_k + dense_positions[ident]) if ident in dense_positions else 0)
        for ident in fts_positions.keys() | dense_positions.keys()
    }
    ordered = sorted(fused, key=lambda ident: (-fused[ident], ident))[:top_k]
    local_paths: dict[str, bool] = {}
    hits = []
    for passage_id in ordered:
        passage = store.get_passage(passage_id)
        if passage.document_sha256 not in local_paths:
            local_paths[passage.document_sha256] = store.source_pdf_available(
                passage.document_sha256
            )
        hits.append(RagHit(
            passage=passage, rrf_score=fused[passage_id],
            fts_rank=fts_positions.get(passage_id),
            dense_rank=dense_positions.get(passage_id),
            source_pdf_available=local_paths[passage.document_sha256],
        ))
    mode = (SearchMode.HYBRID if lexical and dense
            else SearchMode.DENSE_ONLY if dense else SearchMode.LEXICAL_ONLY)
    return RagResponse(
        query=query, mode=mode,
        dense_model_id=model_id, dense_state=dense_state,
        results=tuple(hits),
    )
