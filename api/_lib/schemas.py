from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class GuardrailDecision(str, Enum):
    PASS = "pass"
    UNSAFE = "unsafe"
    OFF_TOPIC = "off_topic"
    NO_EVIDENCE = "no_evidence"


class PassageChunk(BaseModel):
    chunk_id: str
    doc_id: str
    passage_id: str
    text: str
    lang: str
    strategy: str
    score: Optional[float] = None


class PipelineLatencies(BaseModel):
    stt_ms: Optional[float] = None
    embed_ms: Optional[float] = None
    retrieval_ms: Optional[float] = None
    guardrail_ms: Optional[float] = None
    generation_ms: Optional[float] = None
    total_ms: Optional[float] = None


class STTRequest(BaseModel):
    audio_b64: str  # base64-encoded audio
    format: str = "webm"
    mime_type: Optional[str] = None  # full MIME e.g. "audio/mp4" or "audio/webm;codecs=opus"
    language: str = "hi-IN"


class STTResponse(BaseModel):
    transcript: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    latency_ms: float


class QueryRequest(BaseModel):
    transcript: str
    query_vector: Optional[List[float]] = None  # from Transformers.js; server embeds if absent
    language: str = "hi-IN"
    top_k: int = Field(default=5, ge=1, le=20)


class GenerationOutput(BaseModel):
    answer: str
    grounded: bool
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str]  # chunk_ids


class PipelineResponse(BaseModel):
    answer: str
    grounded: bool
    confidence: float
    sources: List[str]
    guardrail: GuardrailDecision
    latencies: PipelineLatencies
    # debug block — excluded from default user view
    retrieved_passages: Optional[List[PassageChunk]] = None
    transcript: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    index_loaded: bool
    index_size: int
    model: str
