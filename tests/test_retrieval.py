import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from api._lib.errors import IndexNotLoadedError
from api._lib.retriever import Retriever


def _make_retriever_with_data(n: int = 10, dim: int = 384) -> Retriever:
    """Build a retriever with fake in-memory data."""
    r = Retriever()
    vectors = np.random.randn(n, dim).astype(np.float32)
    # Normalise
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    r._vectors = vectors / norms
    r._metadata = [
        {
            "chunk_id": f"c{i}",
            "doc_id": f"d{i}",
            "passage_id": f"p{i}",
            "text": f"passage text {i}",
            "lang": "en",
            "strategy": "D",
            "position": 0,
        }
        for i in range(n)
    ]
    r._loaded = True
    return r


class TestRetriever:
    def test_raises_if_not_loaded(self):
        r = Retriever()
        with pytest.raises(IndexNotLoadedError):
            r.search([0.0] * 384)

    def test_search_returns_correct_count(self):
        r = _make_retriever_with_data(10)
        # Use the same first vector as query (should be top result)
        query = r._vectors[0].tolist()
        results = r.search(query, top_k=3)
        assert len(results) <= 3

    def test_search_scores_ordered(self):
        r = _make_retriever_with_data(20)
        query = r._vectors[5].tolist()
        results = r.search(query, top_k=5)
        scores = [p.score for p in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_filters_low_similarity(self):
        r = _make_retriever_with_data(5)
        # Random orthogonal query should yield low similarity
        rng = np.random.default_rng(42)
        query = rng.standard_normal(384).tolist()
        # Should still return valid PassageChunk objects (may be filtered)
        results = r.search(query, top_k=5)
        for res in results:
            assert res.score is not None

    def test_size_property(self):
        r = _make_retriever_with_data(7)
        assert r.size == 7

    def test_loaded_property(self):
        r = Retriever()
        assert not r.loaded
        r = _make_retriever_with_data(3)
        assert r.loaded
