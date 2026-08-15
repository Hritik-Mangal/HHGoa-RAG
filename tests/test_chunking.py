import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from ingestion.chunking import (
    Chunk,
    chunk_passages,
    strategy_a_fixed,
    strategy_b_semantic,
    strategy_c_metadata,
    strategy_d_adaptive,
)

_SHORT_PASSAGE = {
    "passage_id": "p1",
    "doc_id": "d1",
    "text": "The capital of India is New Delhi.",
    "lang": "en",
}

_LONG_PASSAGE = {
    "passage_id": "p2",
    "doc_id": "d2",
    "text": " ".join(["word"] * 250),
    "lang": "en",
}

_MULTI_SENTENCE = {
    "passage_id": "p3",
    "doc_id": "d3",
    "text": "Photosynthesis is the process by which plants make food. It uses sunlight. It produces oxygen.",
    "lang": "en",
}


class TestStrategyA:
    def test_short_passage_single_chunk(self):
        chunks = strategy_a_fixed(_SHORT_PASSAGE)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.strategy == "A"
            assert c.doc_id == "d1"

    def test_long_passage_multiple_chunks(self):
        chunks = strategy_a_fixed(_LONG_PASSAGE)
        assert len(chunks) > 1
        # No chunk should exceed max words
        for c in chunks:
            assert len(c.text.split()) <= 85  # slight tolerance for split edge

    def test_chunk_ids_unique(self):
        chunks = strategy_a_fixed(_LONG_PASSAGE)
        ids = [c.chunk_id for c in chunks]
        assert len(ids) == len(set(ids))


class TestStrategyB:
    def test_single_sentence_returns_one_chunk(self):
        p = {"passage_id": "p10", "doc_id": "d10", "text": "One sentence only.", "lang": "en"}
        chunks = strategy_b_semantic(p)
        assert len(chunks) == 1

    def test_multi_sentence_split(self):
        chunks = strategy_b_semantic(_MULTI_SENTENCE)
        # 3 short sentences should stay as one chunk (under min)
        assert len(chunks) >= 1
        for c in chunks:
            assert c.strategy == "B"


class TestStrategyC:
    def test_always_one_chunk(self):
        for p in [_SHORT_PASSAGE, _LONG_PASSAGE, _MULTI_SENTENCE]:
            chunks = strategy_c_metadata(p)
            assert len(chunks) == 1
            assert chunks[0].text == p["text"]
            assert chunks[0].strategy == "C"


class TestStrategyD:
    def test_short_stays_whole(self):
        chunks = strategy_d_adaptive(_SHORT_PASSAGE)
        assert len(chunks) == 1
        assert chunks[0].text == _SHORT_PASSAGE["text"]

    def test_long_gets_split(self):
        chunks = strategy_d_adaptive(_LONG_PASSAGE)
        assert len(chunks) > 1

    def test_strategy_label(self):
        for p in [_SHORT_PASSAGE, _LONG_PASSAGE]:
            chunks = strategy_d_adaptive(p)
            for c in chunks:
                assert c.strategy == "D"


class TestChunkPassages:
    def test_all_strategies_run(self):
        passages = [_SHORT_PASSAGE, _MULTI_SENTENCE]
        for s in ["A", "B", "C", "D"]:
            chunks = chunk_passages(passages, strategy=s)
            assert len(chunks) > 0

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError):
            chunk_passages([_SHORT_PASSAGE], strategy="X")

    def test_empty_input(self):
        assert chunk_passages([]) == []
