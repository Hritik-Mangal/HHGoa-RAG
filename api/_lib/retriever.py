"""Load pre-built FAISS/numpy index and answer top-k queries."""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import List, Optional

import logging
import numpy as np

from api._lib.errors import IndexNotLoadedError, RetrievalError
from api._lib.schemas import PassageChunk

# Artifacts committed alongside the serverless function
_ARTIFACT_DIR = Path(__file__).parent.parent / "artifacts"
_VECTORS_PATH = _ARTIFACT_DIR / "vectors.npy"
_METADATA_PATH = _ARTIFACT_DIR / "metadata.json"

_DEFAULT_TOP_K = int(os.getenv("TOP_K", "5"))
_SIM_THRESHOLD = float(os.getenv("SIM_THRESHOLD", "0.30"))


class Retriever:
    def __init__(self) -> None:
        self._vectors: Optional[np.ndarray] = None  # (N, D) float32, L2-normalised
        self._metadata: Optional[List[dict]] = None
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        if not _VECTORS_PATH.exists() or not _METADATA_PATH.exists():
            raise IndexNotLoadedError(
                f"Artifacts not found at {_ARTIFACT_DIR}. "
                "Run `python scripts/ingest.py` first."
            )
        self._vectors = np.load(str(_VECTORS_PATH), allow_pickle=False).astype(np.float32)
        with open(_METADATA_PATH, encoding="utf-8") as fh:
            self._metadata = json.load(fh)
        self._loaded = True

    def search(
        self,
        query_vector: List[float],
        top_k: int = _DEFAULT_TOP_K,
    ) -> List[PassageChunk]:
        if not self._loaded:
            raise IndexNotLoadedError("Call Retriever.load() before search().")
        if not query_vector or len(query_vector) != 384:
            logging.getLogger(__name__).warning(
                "invalid_query_vector dim=%s expected=384", len(query_vector) if query_vector else 0
            )
            return []

        q = np.array(query_vector, dtype=np.float32)
        # Normalise to unit sphere for cosine similarity via dot product
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm

        t0 = time.perf_counter()
        scores: np.ndarray = self._vectors @ q  # (N,)
        top_idx = np.argsort(scores)[::-1][:top_k]
        elapsed_ms = (time.perf_counter() - t0) * 1000

        results = []
        for idx in top_idx:
            score = float(scores[idx])
            if score < _SIM_THRESHOLD:
                continue
            meta = self._metadata[int(idx)]
            results.append(
                PassageChunk(
                    chunk_id=meta["chunk_id"],
                    doc_id=meta["doc_id"],
                    passage_id=meta["passage_id"],
                    text=meta["text"],
                    lang=meta["lang"],
                    strategy=meta["strategy"],
                    score=score,
                )
            )

        return results

    @property
    def size(self) -> int:
        return len(self._metadata) if self._metadata else 0

    @property
    def loaded(self) -> bool:
        return self._loaded


# Module-level singleton — loaded once at cold start
_retriever = Retriever()


def get_retriever() -> Retriever:
    return _retriever
