"""Four chunking strategies over MSMARCO-XI passages.

MS MARCO passages are already short (~50-150 tokens each), so the comparison
is: whole-passage vs semantic sub-splits vs adaptive.

Strategy A — Fixed-size       : token windows + overlap
Strategy B — Semantic          : sentence-boundary splits, similarity-grouped
Strategy C — Metadata-aware    : never cross passage boundaries; full passage if short
Strategy D — Adaptive/hybrid   : choose strategy per passage based on length
"""
from __future__ import annotations
import re
import uuid
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    passage_id: str
    text: str
    lang: str
    strategy: str
    position: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> List[str]:
    """Split on sentence-ending punctuation (handles Devanagari ।)."""
    parts = re.split(r"(?<=[.!?।])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


# ---------------------------------------------------------------------------
# Strategy A — Fixed-size
# ---------------------------------------------------------------------------
_A_MAX_WORDS = 80
_A_OVERLAP_WORDS = 15


def strategy_a_fixed(passage: dict) -> List[Chunk]:
    words = passage["text"].split()
    chunks: List[Chunk] = []
    step = max(1, _A_MAX_WORDS - _A_OVERLAP_WORDS)
    for i, start in enumerate(range(0, max(1, len(words)), step)):
        window = words[start : start + _A_MAX_WORDS]
        text = " ".join(window).strip()
        if not text:
            continue
        chunks.append(Chunk(
            chunk_id=f"{passage['passage_id']}_A{i}",
            doc_id=passage["doc_id"],
            passage_id=passage["passage_id"],
            text=text,
            lang=passage["lang"],
            strategy="A",
            position=i,
        ))
    return chunks or [_whole_passage_chunk(passage, "A")]


# ---------------------------------------------------------------------------
# Strategy B — Semantic (sentence-boundary)
# ---------------------------------------------------------------------------
_B_MAX_WORDS = 100
_B_MIN_WORDS = 15


def strategy_b_semantic(passage: dict) -> List[Chunk]:
    sentences = _split_sentences(passage["text"])
    if len(sentences) <= 1:
        return [_whole_passage_chunk(passage, "B")]

    chunks: List[Chunk] = []
    buffer: List[str] = []
    buf_words = 0
    pos = 0

    for sent in sentences:
        w = _word_count(sent)
        if buf_words + w > _B_MAX_WORDS and buf_words >= _B_MIN_WORDS:
            chunks.append(Chunk(
                chunk_id=f"{passage['passage_id']}_B{pos}",
                doc_id=passage["doc_id"],
                passage_id=passage["passage_id"],
                text=" ".join(buffer),
                lang=passage["lang"],
                strategy="B",
                position=pos,
            ))
            pos += 1
            buffer, buf_words = [], 0
        buffer.append(sent)
        buf_words += w

    if buffer:
        chunks.append(Chunk(
            chunk_id=f"{passage['passage_id']}_B{pos}",
            doc_id=passage["doc_id"],
            passage_id=passage["passage_id"],
            text=" ".join(buffer),
            lang=passage["lang"],
            strategy="B",
            position=pos,
        ))

    return chunks or [_whole_passage_chunk(passage, "B")]


# ---------------------------------------------------------------------------
# Strategy C — Metadata-aware (passage = atomic unit)
# ---------------------------------------------------------------------------

def strategy_c_metadata(passage: dict) -> List[Chunk]:
    """Keep each passage as one chunk; no cross-passage merging."""
    return [_whole_passage_chunk(passage, "C")]


# ---------------------------------------------------------------------------
# Strategy D — Adaptive / hybrid
# ---------------------------------------------------------------------------
_D_SHORT_THRESHOLD = 60   # words; keep whole if short
_D_LONG_THRESHOLD = 200   # words; apply fixed-size if very long


def strategy_d_adaptive(passage: dict) -> List[Chunk]:
    wc = _word_count(passage["text"])
    if wc <= _D_SHORT_THRESHOLD:
        # Short passage → keep whole (Strategy C behaviour)
        return [_whole_passage_chunk(passage, "D")]
    elif wc <= _D_LONG_THRESHOLD:
        # Medium → semantic split
        return [
            Chunk(
                chunk_id=c.chunk_id.replace("_B", "_D"),
                doc_id=c.doc_id,
                passage_id=c.passage_id,
                text=c.text,
                lang=c.lang,
                strategy="D",
                position=c.position,
            )
            for c in strategy_b_semantic(passage)
        ]
    else:
        # Long → fixed-size with overlap
        return [
            Chunk(
                chunk_id=c.chunk_id.replace("_A", "_D"),
                doc_id=c.doc_id,
                passage_id=c.passage_id,
                text=c.text,
                lang=c.lang,
                strategy="D",
                position=c.position,
            )
            for c in strategy_a_fixed(passage)
        ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _whole_passage_chunk(passage: dict, strategy: str) -> Chunk:
    return Chunk(
        chunk_id=f"{passage['passage_id']}_{strategy}0",
        doc_id=passage["doc_id"],
        passage_id=passage["passage_id"],
        text=passage["text"],
        lang=passage["lang"],
        strategy=strategy,
        position=0,
    )


_STRATEGIES = {
    "A": strategy_a_fixed,
    "B": strategy_b_semantic,
    "C": strategy_c_metadata,
    "D": strategy_d_adaptive,
}


def chunk_passages(passages: List[dict], strategy: str = "D") -> List[Chunk]:
    fn = _STRATEGIES.get(strategy.upper())
    if fn is None:
        raise ValueError(f"Unknown strategy '{strategy}'. Choose from A, B, C, D.")
    result: List[Chunk] = []
    for p in passages:
        result.extend(fn(p))
    return result
