"""Explicit CPU-only embedding interface; no model downloads or cloud APIs.

A deterministic fake embedder is appropriate for RRF *contract* tests, but
MUST NOT be marketed as genuine semantic model quality validation.
"""
from __future__ import annotations

from math import isfinite, sqrt
from pathlib import Path
from typing import Protocol, Sequence, runtime_checkable


class EmbeddingError(ValueError):
    pass


@runtime_checkable
class LocalEmbedder(Protocol):
    model_id: str
    dimensions: int

    def encode(self, texts: Sequence[str]) -> Sequence[Sequence[float]]:
        """Encode an ordered list locally, into one vector per input."""


def normalize_vectors(
    vectors: Sequence[Sequence[float]], expected_count: int,
    dimensions: int,
) -> list[tuple[float, ...]]:
    if not isinstance(dimensions, int) or not 2 <= dimensions <= 4096:
        raise EmbeddingError("Dense embedding dimensions outside safety limits")
    if len(vectors) != expected_count:
        raise EmbeddingError("Dense embedder returned incorrect vector count")
    normalized: list[tuple[float, ...]] = []
    for vector in vectors:
        if len(vector) != dimensions:
            raise EmbeddingError("Dense embedding dimension mismatch")
        try:
            values = tuple(float(v) for v in vector)
        except (TypeError, ValueError, OverflowError) as exc:
            raise EmbeddingError("Embedding contains nonnumeric components") from exc
        if not all(isfinite(x) for x in values):
            raise EmbeddingError("Embedding contains NaN or Infinity")
        length = sqrt(sum(x * x for x in values))
        if not isfinite(length) or length <= 1e-12:
            raise EmbeddingError("Cannot normalize a zero/overflow embedding")
        normalized.append(tuple(x / length for x in values))
    return normalized


def require_embedder(embedder: LocalEmbedder) -> None:
    if (not isinstance(embedder.model_id, str) or
            not embedder.model_id.strip() or len(embedder.model_id) > 200 or
            not isinstance(embedder.dimensions, int) or
            not 2 <= embedder.dimensions <= 4096):
        raise EmbeddingError("Embedding model ID/dimension contract invalid")


class LocalSentenceTransformer:
    """Optional real dense model from an existing *local* directory only.

    sentence-transformers is deliberately NOT a core dependency. A user must
    install it and provide a complete compatible model folder. No repo IDs,
    remote code, GPU, or implicit model downloads are allowed.
    """

    def __init__(self, model_directory: str | Path, *, model_id: str):
        folder = Path(model_directory).expanduser().resolve(strict=True)
        if not folder.is_dir() or not (folder / "modules.json").is_file():
            raise EmbeddingError(
                "Require a preinstalled local SentenceTransformer model directory"
            )
        if not model_id or not model_id.strip():
            raise EmbeddingError("Explicit local model ID is required")
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "Install optional sentence-transformers locally before use"
            ) from exc
        try:
            self._model = SentenceTransformer(
                str(folder), device="cpu", local_files_only=True,
                trust_remote_code=False,
            )
        except Exception as exc:
            raise EmbeddingError(
                f"Local sentence transformer could not load: {type(exc).__name__}"
            ) from exc
        self.model_id = model_id
        dim = self._model.get_sentence_embedding_dimension()
        if dim is None:
            raise EmbeddingError("Installed local model has unknown dimensions")
        self.dimensions = int(dim)
        require_embedder(self)

    def encode(self, texts: Sequence[str]) -> list[tuple[float, ...]]:
        out = self._model.encode(
            list(texts), convert_to_numpy=True,
            normalize_embeddings=False, show_progress_bar=False,
        )
        return normalize_vectors(out, len(texts), self.dimensions)
