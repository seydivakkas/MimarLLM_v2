"""Bounded local SQLite FTS5/BM25 and JSON-cosine evidence index.

No HTTP, no hosted vectors, no background model acquisition.  FTS indexes a
normalized SEARCH copy; returned excerpts remain exactly from LegalAST.
"""
from __future__ import annotations

from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import re
import sqlite3
import unicodedata
from typing import Sequence

from mimarllm.legal.models import LegalDocument, LegalNodeKind
from mimarllm.rag.embeddings import (
    EmbeddingError, LocalEmbedder, normalize_vectors, require_embedder,
)
from mimarllm.rag.models import IndexedPassage, RagKind


class RagStoreError(ValueError):
    """Unsafe index/search request or unavailable FTS capability."""


def normalize_search_text(text: str) -> str:
    """Unicode-compatible Turkish lexical search, not semantic inference."""
    simplified = unicodedata.normalize("NFKD", text.casefold().replace("ı", "i"))
    return "".join(x for x in simplified if unicodedata.category(x) != "Mn")


def match_expression(query: str) -> str:
    """Escape MATCH syntax by emitting only quoted word tokens."""
    if not isinstance(query, str) or not query.strip() or len(query) > 512:
        raise RagStoreError("Query requires 1..512 characters")
    tokens = re.findall(r"\w+", normalize_search_text(query), flags=re.UNICODE)
    if not tokens:
        return ""
    if len(tokens) > 24 or any(len(word) > 72 for word in tokens):
        raise RagStoreError("FTS query token budget exceeded")
    return " OR ".join('"' + word + '"' for word in tokens)


def _passages(document: LegalDocument, *, max_passages: int) -> list[IndexedPassage]:
    nodes = {n.node_id: n for n in document.nodes}
    records: list[IndexedPassage] = []

    def ancestry(node_id: str | None):
        seen: set[str] = set()
        article = paragraph = item = None
        while node_id is not None:
            if node_id in seen or node_id not in nodes:
                raise RagStoreError("Illegal LegalAST parent cycle/missing ancestor")
            seen.add(node_id)
            n = nodes[node_id]
            if article is None and n.kind in {
                LegalNodeKind.ARTICLE, LegalNodeKind.TEMPORARY_ARTICLE
            }:
                article = n.article_number
            if paragraph is None and n.kind == LegalNodeKind.PARAGRAPH:
                paragraph = n.paragraph_number
            if item is None and n.kind == LegalNodeKind.ITEM:
                item = n.item_key
            node_id = n.parent_node_id
        return article, paragraph, item

    for node in document.nodes:
        if not node.text.strip():
            continue
        article, paragraph, item = ancestry(node.node_id)
        records.append(IndexedPassage(
            passage_id=f"{document.document_sha256}:node:{node.node_id}",
            document_sha256=document.document_sha256,
            regulation_id=document.metadata.regulation_id,
            document_kind=document.metadata.document_kind,
            entry_kind=RagKind.NODE, node_kind=node.kind.value,
            node_id=node.node_id, parent_node_id=node.parent_node_id,
            article_number=article, paragraph_number=paragraph, item_key=item,
            text=node.text, spans=node.spans,
        ))
    for table in document.tables:
        article, paragraph, item = ancestry(table.suggested_parent_node_id)
        seen_coords: set[tuple[int, int]] = set()
        for cell in table.cells:
            coords = (cell.row_index, cell.column_index)
            if coords in seen_coords:
                raise RagStoreError("Duplicate table row/column source coordinates")
            seen_coords.add(coords)
            if not cell.text.strip():
                continue
            records.append(IndexedPassage(
                passage_id=(
                    f"{document.document_sha256}:table:{table.table_id}:"
                    f"r{cell.row_index}:c{cell.column_index}"
                ),
                document_sha256=document.document_sha256,
                regulation_id=document.metadata.regulation_id,
                document_kind=document.metadata.document_kind,
                entry_kind=RagKind.TABLE_CELL, node_kind="TABLE_CELL",
                table_id=table.table_id, row_index=cell.row_index,
                column_index=cell.column_index,
                node_id=table.suggested_parent_node_id,
                parent_node_id=None,
                article_number=article, paragraph_number=paragraph, item_key=item,
                text=cell.text, spans=(cell.source,), review_required=True,
            ))
    if len(records) > max_passages:
        raise RagStoreError("Legal passage count exceeds index budget")
    if len({p.passage_id for p in records}) != len(records):
        raise RagStoreError("Duplicate index passage identity")
    if any(len(p.text) > 50_000 or len(p.spans) > 300 for p in records):
        raise RagStoreError("Text/span per-passage safety budget exceeded")
    return records


def _sha_file(path: Path, *, max_bytes: int = 100 * 1024 * 1024):
    if not path.is_file() or not 0 < path.stat().st_size <= max_bytes:
        raise RagStoreError("Original PDF source missing or outside file budget")
    digest = sha256()
    with path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise RagStoreError("Original source is not a PDF")
        stream.seek(0)
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()



def validate_pdf_page_bounds(
    pdf_path: Path, document: LegalDocument,
    entries: Sequence[IndexedPassage],
) -> None:
    """Check highlight polygons are inside the ORIGINAL PDF page rectangles.

    This is a coordinate-bound check, NOT OCR/glyph matching or a guarantee
    the text is really on that page. Visual source confirmation stays HOLD.
    """
    try:
        import pypdfium2 as pdfium
        with pdfium.PdfDocument(str(pdf_path)) as original:
            if len(original) != document.page_count:
                raise RagStoreError("Original PDF page count differs from LegalAST")
            page_sizes = [tuple(float(v) for v in page.get_size())
                          for page in original]
    except RagStoreError:
        raise
    except Exception as exc:
        raise RagStoreError(
            f"Original PDF geometry not inspectable: {type(exc).__name__}"
        ) from exc
    for entry in entries:
        for span in entry.spans:
            if span.page_index >= len(page_sizes):
                raise RagStoreError("Source span points to missing original PDF page")
            width, height = page_sizes[span.page_index]
            if any(not (-1e-5 <= x <= width + 1e-5 and
                        -1e-5 <= y <= height + 1e-5)
                   for x, y in span.polygon):
                raise RagStoreError(
                    "Source polygon exceeds original PDF page dimensions"
                )


class LegalRagStore:
    """One local SQLite database. Caller is responsible for close()."""

    def __init__(self, database: str | Path = ":memory:"):
        if str(database) == ":memory:":
            db = ":memory:"
        else:
            path = Path(database).expanduser().resolve(strict=False)
            if not path.parent.is_dir():
                raise RagStoreError("SQLite index parent directory must exist")
            db = str(path)
        self.conn = sqlite3.connect(db, timeout=15.0)
        self.conn.execute("PRAGMA foreign_keys=ON")
        try:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents(
                    doc_sha TEXT PRIMARY KEY,
                    regulation_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    pdf_path TEXT
                );
                CREATE TABLE IF NOT EXISTS passages(
                    passage_id TEXT PRIMARY KEY,
                    doc_sha TEXT NOT NULL REFERENCES documents(doc_sha) ON DELETE CASCADE,
                    regulation_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_passages_document
                    ON passages(doc_sha);
                CREATE VIRTUAL TABLE IF NOT EXISTS passage_fts
                    USING fts5(search_text, passage_id UNINDEXED,
                               tokenize='unicode61 remove_diacritics 2');
                CREATE TABLE IF NOT EXISTS passage_vectors(
                    passage_id TEXT PRIMARY KEY
                        REFERENCES passages(passage_id) ON DELETE CASCADE,
                    model_id TEXT NOT NULL,
                    dimensions INTEGER NOT NULL,
                    vector_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_vector_model
                    ON passage_vectors(model_id);
                -- Small, source-ID-only local query memoization. No PDF/image
                -- bytes, legal interpretation, user identity or embeddings.
                CREATE TABLE IF NOT EXISTS rag_lexical_cache(
                    cache_key TEXT PRIMARY KEY,
                    passage_ids_json TEXT NOT NULL,
                    cache_seq INTEGER NOT NULL
                );
            """)
        except sqlite3.OperationalError as exc:
            self.conn.close()
            raise RagStoreError(
                "Local sqlite3 build must support FTS5"
            ) from exc

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self) -> None:
        self.conn.close()

    def index_document(
        self, document: LegalDocument, *,
        embedder: LocalEmbedder | None = None,
        original_pdf_path: str | Path | None = None,
        max_passages: int = 20_000,
        embed_batch_size: int = 64,
    ) -> int:
        if not isinstance(max_passages, int) or not 1 <= max_passages <= 50_000:
            raise RagStoreError("Invalid indexing record budget")
        if not isinstance(embed_batch_size, int) or not 1 <= embed_batch_size <= 256:
            raise RagStoreError("Invalid dense batch budget")
        checked = LegalDocument.model_validate(document.model_dump())
        if checked.review_status != "UNREVIEWED" or checked.legal_compliance_certified:
            raise RagStoreError("LegalAST review status cannot authorize indexing claims")
        entries = _passages(checked, max_passages=max_passages)
        local_pdf: str | None = None
        if original_pdf_path is not None:
            p = Path(original_pdf_path).expanduser().resolve(strict=True)
            if _sha_file(p) != checked.document_sha256:
                raise RagStoreError("Original PDF hash does not match LegalAST")
            validate_pdf_page_bounds(p, checked, entries)
            local_pdf = str(p)
        vectors: list[tuple[float, ...]] = []
        if embedder is not None:
            require_embedder(embedder)
            for i in range(0, len(entries), embed_batch_size):
                chunk = entries[i:i + embed_batch_size]
                vectors.extend(normalize_vectors(
                    embedder.encode([p.text for p in chunk]),
                    len(chunk), embedder.dimensions,
                ))
        # Prevalidate all model inputs BEFORE deleting old SQLite index rows.
        # If embedding fails, the previous document remains searchable.
        with self.conn:
            # Index replacement and cache invalidation share ONE transaction.
            # Failed embedding/source checks above leave both intact.
            self.conn.execute("DELETE FROM rag_lexical_cache")
            self.conn.execute(
                "INSERT INTO documents(doc_sha,regulation_id,kind,metadata_json,pdf_path)"
                " VALUES(?,?,?,?,?) ON CONFLICT(doc_sha) DO UPDATE SET"
                " regulation_id=excluded.regulation_id,kind=excluded.kind,"
                " metadata_json=excluded.metadata_json,pdf_path=excluded.pdf_path",
                (checked.document_sha256, checked.metadata.regulation_id,
                 checked.metadata.document_kind,
                 checked.metadata.model_dump_json(), local_pdf),
            )
            old_rows = self.conn.execute(
                "SELECT passage_id FROM passages WHERE doc_sha=?",
                (checked.document_sha256,),
            ).fetchall()
            if old_rows:
                self.conn.executemany(
                    "DELETE FROM passage_fts WHERE passage_id=?",
                    old_rows,
                )
            self.conn.execute(
                "DELETE FROM passages WHERE doc_sha=?",
                (checked.document_sha256,),
            )
            for i, entry in enumerate(entries):
                self.conn.execute(
                    "INSERT INTO passages(passage_id,doc_sha,regulation_id,payload_json)"
                    " VALUES(?,?,?,?)",
                    (entry.passage_id, entry.document_sha256,
                     entry.regulation_id, entry.model_dump_json()),
                )
                self.conn.execute(
                    "INSERT INTO passage_fts(search_text,passage_id) VALUES(?,?)",
                    (normalize_search_text(entry.text), entry.passage_id),
                )
                if embedder is not None:
                    self.conn.execute(
                        "INSERT INTO passage_vectors(passage_id,model_id,dimensions,vector_json)"
                        " VALUES(?,?,?,?)",
                        (entry.passage_id, embedder.model_id, embedder.dimensions,
                         json.dumps(vectors[i], ensure_ascii=False)),
                    )
        return len(entries)

    def lexical_rank(
        self, query: str, *, limit: int,
        regulation_id: str | None = None,
        document_sha256: str | None = None,
    ) -> list[str]:
        """Parameterised FTS5 BM25 with bounded SQLite-local passage-ID cache.

        The key includes the query, filters and ranking limit. Reindexing
        clears cache transactionally. Source-PDF availability is deliberately
        checked AFTER retrieval by the caller on every request.
        """
        if not isinstance(limit, int) or not 1 <= limit <= 200:
            raise RagStoreError("FTS rank limit exceeded")
        expression = match_expression(query)
        if not expression:
            return []
        key_payload = json.dumps(
            ["lexical-cache-v1", expression, limit, regulation_id,
             document_sha256],
            ensure_ascii=False, separators=(",", ":"),
        )
        key = sha256(key_payload.encode("utf-8")).hexdigest()
        cached = self.conn.execute(
            "SELECT passage_ids_json FROM rag_lexical_cache WHERE cache_key=?",
            (key,),
        ).fetchone()
        if cached is not None:
            try:
                ids = json.loads(cached[0])
                if (isinstance(ids, list) and len(ids) <= limit
                        and all(isinstance(ident, str) for ident in ids)
                        and len(set(ids)) == len(ids)):
                    # The index cache is never a source of source text/quad;
                    # those are loaded from authoritative passages per hit.
                    return ids
            except (ValueError, TypeError):
                pass
        try:
            ids = [row[0] for row in self.conn.execute(
                "SELECT p.passage_id FROM passage_fts"
                " JOIN passages p ON p.passage_id = passage_fts.passage_id"
                " WHERE passage_fts MATCH ?"
                " AND (? IS NULL OR p.regulation_id=?)"
                " AND (? IS NULL OR p.doc_sha=?)"
                " ORDER BY bm25(passage_fts), p.passage_id LIMIT ?",
                (expression, regulation_id, regulation_id,
                 document_sha256, document_sha256, limit),
            ).fetchall()]
        except sqlite3.OperationalError as exc:
            raise RagStoreError(f"FTS query failed: {type(exc).__name__}") from exc
        # Store the ranked passage IDs only. Bound the SQLite workspace cache
        # to 128 query variants; on next query old rows are evicted.
        with self.conn:
            self.conn.execute(
                "INSERT INTO rag_lexical_cache(cache_key,passage_ids_json,cache_seq)"
                " VALUES(?,?,COALESCE((SELECT MAX(cache_seq)+1 FROM rag_lexical_cache),1))"
                " ON CONFLICT(cache_key) DO UPDATE SET passage_ids_json=excluded.passage_ids_json,"
                " cache_seq=excluded.cache_seq",
                (key, json.dumps(ids, separators=(",", ":"))),
            )
            self.conn.execute(
                "DELETE FROM rag_lexical_cache WHERE cache_key NOT IN ("
                "SELECT cache_key FROM rag_lexical_cache "
                "ORDER BY cache_seq DESC LIMIT 128)",
            )
        return ids

    def dense_rank(
        self, query_vector: Sequence[float], *, model_id: str, dimensions: int,
        limit: int, max_scan: int = 50_000,
        regulation_id: str | None = None,
        document_sha256: str | None = None,
    ) -> list[str]:
        if not 1 <= limit <= 200 or not 1 <= max_scan <= 100_000:
            raise RagStoreError("Dense scan budget invalid")
        vector = normalize_vectors([query_vector], 1, dimensions)[0]
        rows = self.conn.execute(
            "SELECT v.passage_id,v.vector_json,v.dimensions"
            " FROM passage_vectors v JOIN passages p ON v.passage_id=p.passage_id"
            " WHERE v.model_id=? AND (? IS NULL OR p.regulation_id=?)"
            " AND (? IS NULL OR p.doc_sha=?)",
            (model_id, regulation_id, regulation_id, document_sha256,
             document_sha256),
        ).fetchmany(max_scan + 1)
        if len(rows) > max_scan:
            raise RagStoreError("Exact cosine scan budget exceeded")
        scores: list[tuple[float, str]] = []
        for passage_id, raw, dim in rows:
            if dim != dimensions:
                raise RagStoreError("Stored embedding dimension mismatch")
            saved = normalize_vectors([json.loads(raw)], 1, dimensions)[0]
            score = sum(a * b for a, b in zip(saved, vector))
            if not isfinite(score):
                raise RagStoreError("Nonfinite dense cosine")
            scores.append((score, passage_id))
        scores.sort(key=lambda row: (-row[0], row[1]))
        return [passage_id for _, passage_id in scores[:limit]]

    def get_passage(self, passage_id: str) -> IndexedPassage:
        row = self.conn.execute(
            "SELECT payload_json FROM passages WHERE passage_id=?", (passage_id,),
        ).fetchone()
        if row is None:
            raise RagStoreError("Missing indexed passage")
        return IndexedPassage.model_validate_json(row[0])

    def source_pdf_available(self, document_sha256: str) -> bool:
        row = self.conn.execute(
            "SELECT pdf_path FROM documents WHERE doc_sha=?",
            (document_sha256,),
        ).fetchone()
        if row is None or not row[0]:
            return False
        try:
            return _sha_file(Path(row[0])) == document_sha256
        except (OSError, RagStoreError):
            return False

    def has_dense_vectors(self, model_id: str) -> bool:
        return self.conn.execute(
            "SELECT EXISTS(SELECT 1 FROM passage_vectors WHERE model_id=?)",
            (model_id,),
        ).fetchone()[0] == 1
