"""Batch-embed chunks with multilingual-e5-small (L2-normalised for cosine search)."""
from __future__ import annotations
import logging
import time
from typing import List

import numpy as np

from ingestion.chunking import Chunk

log = logging.getLogger(__name__)

_MODEL_NAME = "intfloat/multilingual-e5-small"
_BATCH_SIZE = 256
_DIM = 384


def _load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise RuntimeError("Install sentence-transformers: pip install sentence-transformers")
    log.info("loading_model model=%s", _MODEL_NAME)
    model = SentenceTransformer(_MODEL_NAME)
    return model


def embed_chunks(
    chunks: List[Chunk],
    batch_size: int = _BATCH_SIZE,
    show_progress: bool = True,
) -> np.ndarray:
    """Return (N, 384) float32 L2-normalised embedding matrix."""
    model = _load_model()

    texts = [f"passage: {c.text}" for c in chunks]  # e5 prefix for passages
    t0 = time.perf_counter()
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True,   # L2 normalise → cosine via dot product
        convert_to_numpy=True,
    )
    elapsed = time.perf_counter() - t0
    log.info(
        "embedding_done n=%d dim=%d elapsed_s=%.1f per_chunk_ms=%.2f",
        len(chunks), vectors.shape[1], elapsed,
        elapsed / max(1, len(chunks)) * 1000,
    )
    return vectors.astype(np.float32)


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string; returns (384,) float32 unit vector."""
    model = _load_model()
    vec = model.encode(
        [f"query: {query}"],
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vec[0].astype(np.float32)
