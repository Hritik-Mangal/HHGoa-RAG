import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from api._lib.pipeline import RAGPipeline
from api._lib.retriever import Retriever
from api._lib.schemas import (
    GenerationOutput,
    GuardrailDecision,
    PassageChunk,
    QueryRequest,
    STTRequest,
    STTResponse,
)


def _fake_retriever(passages=None, loaded=True) -> Retriever:
    r = MagicMock(spec=Retriever)
    r.loaded = loaded
    r.size = len(passages or [])
    r.search.return_value = passages or []
    return r


def _make_passage(score=0.6) -> PassageChunk:
    return PassageChunk(
        chunk_id="c1", doc_id="d1", passage_id="p1",
        text="New Delhi is the capital of India.", lang="en", strategy="D", score=score,
    )


@pytest.mark.asyncio
async def test_unsafe_query_refused():
    pipeline = RAGPipeline(retriever=_fake_retriever())
    req = QueryRequest(transcript="How to make a bomb?", query_vector=[0.0] * 384)
    resp = await pipeline.query(req)
    assert resp.guardrail == GuardrailDecision.UNSAFE
    assert not resp.grounded


@pytest.mark.asyncio
async def test_off_topic_refused():
    pipeline = RAGPipeline(retriever=_fake_retriever())
    req = QueryRequest(transcript="Today's weather forecast please", query_vector=[0.0] * 384)
    resp = await pipeline.query(req)
    assert resp.guardrail == GuardrailDecision.OFF_TOPIC


@pytest.mark.asyncio
async def test_no_evidence_refused():
    # retriever returns low-similarity results
    low_passages = [_make_passage(score=0.05)]
    pipeline = RAGPipeline(retriever=_fake_retriever(low_passages))
    req = QueryRequest(transcript="What is photosynthesis?", query_vector=[0.1] * 384)
    resp = await pipeline.query(req)
    assert resp.guardrail == GuardrailDecision.NO_EVIDENCE


@pytest.mark.asyncio
async def test_extractive_fallback_when_no_groq():
    passages = [_make_passage(score=0.7)]
    pipeline = RAGPipeline(retriever=_fake_retriever(passages), groq=None)
    req = QueryRequest(transcript="What is the capital of India?", query_vector=[0.1] * 384)
    resp = await pipeline.query(req)
    assert resp.guardrail == GuardrailDecision.PASS
    assert resp.grounded
    assert "New Delhi" in resp.answer


@pytest.mark.asyncio
async def test_generation_success():
    passages = [_make_passage(score=0.75)]
    groq_mock = AsyncMock()
    groq_mock.generate.return_value = GenerationOutput(
        answer="New Delhi is the capital of India.",
        grounded=True,
        confidence=0.9,
        sources=["c1"],
    )
    pipeline = RAGPipeline(retriever=_fake_retriever(passages), groq=groq_mock)
    req = QueryRequest(transcript="What is capital of India?", query_vector=[0.1] * 384)
    resp = await pipeline.query(req)
    assert resp.grounded
    assert resp.guardrail == GuardrailDecision.PASS
    assert len(resp.sources) > 0


@pytest.mark.asyncio
async def test_latencies_populated():
    passages = [_make_passage(score=0.65)]
    pipeline = RAGPipeline(retriever=_fake_retriever(passages))
    req = QueryRequest(transcript="What is gravity?", query_vector=[0.1] * 384)
    resp = await pipeline.query(req)
    assert resp.latencies.total_ms is not None
    assert resp.latencies.total_ms >= 0
