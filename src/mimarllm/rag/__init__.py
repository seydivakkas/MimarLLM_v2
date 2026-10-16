"""Local LegalAST search: SQLite FTS5, optional CPU embeddings, RRF."""
from mimarllm.rag.indexer import IndexSummary, index_local_legal_pdf
from mimarllm.rag.lexicon import expand_architectural_terms, LEXICON_VERSION
from mimarllm.rag.retriever import search_legal
from mimarllm.rag.store import LegalRagStore, RagStoreError

__all__ = [
    "IndexSummary", "LegalRagStore", "RagStoreError",
    "index_local_legal_pdf", "search_legal",
    "expand_architectural_terms", "LEXICON_VERSION",
]
