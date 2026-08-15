"""Main RAG orchestrator — typed stages, bounded retries, deterministic fallbacks."""
from __future__ import annotations
import asyncio
import logging
import os
import uuid
from typing import List, Optional

import structlog

from api._lib.errors import (
    EmbeddingError,
    GenerationError,
    GenerationTimeoutError,
    IndexNotLoadedError,
    RetrievalError,
    STTError,
)
from api._lib.schemas import GuardrailDecision
from api._lib.guardrails import (
    REFUSAL_MESSAGES,
    check_evidence,
    check_query,
    verify_grounding,
)
from api._lib.latency import LatencyTracker
from api._lib.retriever import Retriever
from api._lib.retry import run_with_timeout, with_retry
from api._lib.sarvam_client import SarvamSTT
from api._lib.schemas import (
    PassageChunk,
    PipelineLatencies,
    PipelineResponse,
    QueryRequest,
    STTRequest,
    STTResponse,
)

log = structlog.get_logger(__name__)

_MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
_GEN_TIMEOUT = float(os.getenv("GENERATION_TIMEOUT_MS", "500"))
_RET_TIMEOUT = float(os.getenv("RETRIEVAL_TIMEOUT_MS", "100"))


def _extractive_fallback(transcript: str, passages: List[PassageChunk]) -> str:
    """Return the highest-scoring passage as a fallback answer when generation fails."""
    if not passages:
        return REFUSAL_MESSAGES[GuardrailDecision.NO_EVIDENCE]
    best = max(passages, key=lambda p: p.score or 0.0)
    return best.text[:500]


class RAGPipeline:
    def __init__(
        self,
        retriever: Retriever,
        stt: Optional[SarvamSTT] = None,
        generator=None,
    ) -> None:
        self._retriever = retriever
        self._stt = stt
        self._generator = generator

    # ------------------------------------------------------------------
    # Public entry: STT
    # ------------------------------------------------------------------
    async def transcribe(self, req: STTRequest) -> STTResponse:
        if self._stt is None:
            raise STTError("STT provider not initialised")
        tracker = LatencyTracker()
        with tracker.track("stt"):
            resp = await with_retry(
                self._stt.transcribe,
                req.audio_b64,
                req.format,
                req.language,
                req.mime_type,
                max_attempts=_MAX_RETRIES,
            )
        return resp

    # ------------------------------------------------------------------
    # Public entry: Query (retrieve + generate)
    # ------------------------------------------------------------------
    async def query(self, req: QueryRequest, correlation_id: str = "") -> PipelineResponse:
        cid = correlation_id or str(uuid.uuid4())[:8]
        tracker = LatencyTracker()
        tracker.start_pipeline()
        safe_transcript = req.transcript[:60].encode('ascii', 'replace').decode('ascii')
        bound_log = log.bind(cid=cid, transcript=safe_transcript)

        # Stage 0: check we have a usable query vector
        if not req.query_vector:
            bound_log.warning("no_query_vector")
            return PipelineResponse(
                answer="Query embedding not available yet — please try again.",
                grounded=False, confidence=0.0, sources=[],
                guardrail=GuardrailDecision.NO_EVIDENCE,
                latencies=tracker.to_schema(),
            )

        # Stage 1: query guardrail
        with tracker.track("guardrail_query"):
            decision = check_query(req.transcript)
        if decision != GuardrailDecision.PASS:
            bound_log.info("query_rejected", reason=decision)
            return _refusal(decision, tracker)

        # Stage 2: vector search
        # Note: asyncio.wait_for cancels the coroutine wrapper on timeout but the underlying
        # thread continues until completion — known Python limitation with asyncio.to_thread.
        passages: List[PassageChunk] = []
        try:
            with tracker.track("retrieval"):
                passages = await asyncio.wait_for(
                    asyncio.to_thread(
                        self._retriever.search,
                        req.query_vector or [],
                        req.top_k,
                    ),
                    timeout=_RET_TIMEOUT / 1000,
                )
        except asyncio.TimeoutError:
            bound_log.warning("retrieval_timeout")
        except (IndexNotLoadedError, RetrievalError) as exc:
            bound_log.error("retrieval_error", err=str(exc))

        # Stage 3: evidence guardrail
        with tracker.track("guardrail_evidence"):
            evidence_decision = check_evidence(passages)
        if evidence_decision != GuardrailDecision.PASS:
            bound_log.info("insufficient_evidence", n=len(passages))
            return _refusal(evidence_decision, tracker, passages=passages)

        # Stage 4: generation (with retry + timeout + extractive fallback)
        answer = ""
        grounded = False
        confidence = 0.0
        sources: List[str] = []

        if self._generator and req.query_vector:
            for attempt in range(_MAX_RETRIES + 1):
                try:
                    with tracker.track("generation"):
                        gen = await run_with_timeout(
                            self._generator.generate(req.transcript, passages),
                            _GEN_TIMEOUT,
                        )
                    # Verify grounding externally — don't trust model's own flag
                    actual_grounded = verify_grounding(gen, passages)
                    answer = gen.answer
                    grounded = actual_grounded
                    confidence = gen.confidence if actual_grounded else 0.0
                    sources = gen.sources if actual_grounded else []
                    break
                except (GenerationTimeoutError, GenerationError, asyncio.TimeoutError) as exc:
                    bound_log.warning("generation_error", attempt=attempt, err=str(exc))
                    if attempt == _MAX_RETRIES:
                        answer = _extractive_fallback(req.transcript, passages)
                        grounded = True  # extractive = directly from corpus
                        confidence = max(p.score or 0.0 for p in passages) if passages else 0.0
                        sources = [passages[0].chunk_id] if passages else []
        else:
            # No Groq client or no query vector → extractive fallback
            answer = _extractive_fallback(req.transcript, passages)
            grounded = True
            confidence = max(p.score or 0.0 for p in passages) if passages else 0.0
            sources = [passages[0].chunk_id] if passages else []

        bound_log.info("pipeline_ok", grounded=grounded, n_passages=len(passages))
        return PipelineResponse(
            answer=answer,
            grounded=grounded,
            confidence=confidence,
            sources=sources,
            guardrail=GuardrailDecision.PASS,
            latencies=tracker.to_schema(),
            retrieved_passages=passages,
            transcript=req.transcript,
        )


def _refusal(
    decision: GuardrailDecision,
    tracker: LatencyTracker,
    passages: Optional[List[PassageChunk]] = None,
) -> PipelineResponse:
    return PipelineResponse(
        answer=REFUSAL_MESSAGES[decision],
        grounded=False,
        confidence=0.0,
        sources=[],
        guardrail=decision,
        latencies=tracker.to_schema(),
        retrieved_passages=passages or [],
    )
