"""Build FAISS (offline) and export compact numpy artifacts for Vercel."""
from __future__ import annotations
import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import List

import numpy as np

from ingestion.chunking import Chunk

log = logging.getLogger(__name__)

_OUT_DIR = Path(__file__).parent / "artifacts"
# Target locations also readable by api/_lib/retriever.py
_API_ARTIFACT_DIR = Path(__file__).parent.parent / "api" / "artifacts"


def build_faiss_index(vectors: np.ndarray, index_type: str = "hnsw"):
    """Build an in-memory FAISS index (offline use only)."""
    try:
        import faiss
    except ImportError:
        raise RuntimeError("Install faiss-cpu: pip install faiss-cpu")

    d = vectors.shape[1]
    if index_type == "hnsw":
        index = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
    elif index_type == "flat":
        index = faiss.IndexFlatIP(d)
    else:
        raise ValueError(f"Unknown index type: {index_type}")

    t0 = time.perf_counter()
    index.add(vectors)
    elapsed = time.perf_counter() - t0
    log.info("faiss_built n=%d type=%s elapsed_s=%.2f", index.ntotal, index_type, elapsed)
    return index


def export_artifacts(
    chunks: List[Chunk],
    vectors: np.ndarray,
    out_dir: Path | None = None,
) -> dict:
    """Save vectors.npy and metadata.json for the Vercel serverless function."""
    for target in [out_dir or _OUT_DIR, _API_ARTIFACT_DIR]:
        target.mkdir(parents=True, exist_ok=True)

        npy_path = target / "vectors.npy"
        meta_path = target / "metadata.json"

        np.save(str(npy_path), vectors)
        metadata = [
            {
                "chunk_id": c.chunk_id,
                "doc_id": c.doc_id,
                "passage_id": c.passage_id,
                "text": c.text,
                "lang": c.lang,
                "strategy": c.strategy,
                "position": c.position,
            }
            for c in chunks
        ]
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump(metadata, fh, ensure_ascii=False)

        log.info("artifacts_saved n=%d dir=%s", len(chunks), target)

    return {
        "n_chunks": len(chunks),
        "vector_shape": list(vectors.shape),
        "size_mb": round(vectors.nbytes / 1e6, 2),
    }


def faiss_search(index, query_vec: np.ndarray, k: int = 5):
    """Run a FAISS search; returns (scores, indices)."""
    q = query_vec.reshape(1, -1).astype(np.float32)
    scores, indices = index.search(q, k)
    return scores[0], indices[0]
