"""Vercel Python serverless entry-point.
Routes: POST /api/stt, POST /api/query, GET /api/health
All heavy state (vector index) is loaded once at cold start.
"""
from __future__ import annotations
import logging
import os
import sys
import time
import uuid
from pathlib import Path

# Make sure the project root is on sys.path for relative imports
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

# Configure structured logging
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, os.getenv("LOG_LEVEL", "INFO"))
    )
)
log = structlog.get_logger(__name__)

from api._lib.errors import (
    EmptyTranscriptError,
    IndexNotLoadedError,
    ProviderRateLimitError,
    RagError,
    STTError,
)
from api._lib.gemini_client import GeminiClient
from api._lib.pipeline import RAGPipeline
from api._lib.retriever import get_retriever
from api._lib.sarvam_client import SarvamSTT
from api._lib.schemas import (
    HealthResponse,
    PipelineResponse,
    QueryRequest,
    STTRequest,
    STTResponse,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="HH Goa RAG", version="0.1.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - t0) * 1000
    log.info("http_request", method=request.method, path=request.url.path,
             status=response.status_code, ms=round(elapsed, 1))
    return response

# ---------------------------------------------------------------------------
# Cold-start initialisation
# ---------------------------------------------------------------------------
_retriever = get_retriever()
_stt: SarvamSTT | None = None
_gemini: GeminiClient | None = None
_pipeline: RAGPipeline | None = None


@app.on_event("startup")
async def _startup() -> None:
    global _stt, _gemini, _pipeline

    # Load vector index (required)
    try:
        _retriever.load()
        log.info("index_loaded", size=_retriever.size)
    except IndexNotLoadedError as exc:
        log.warning("index_not_loaded", reason=str(exc))

    # Initialise providers (fail gracefully if keys absent in dev)
    try:
        _stt = SarvamSTT()
    except RuntimeError as exc:
        log.warning("stt_unavailable", reason=str(exc))

    try:
        _gemini = GeminiClient()
    except RuntimeError as exc:
        log.warning("gemini_unavailable", reason=str(exc))

    _pipeline = RAGPipeline(retriever=_retriever, stt=_stt, generator=_gemini)
    log.info("pipeline_ready")


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
@app.exception_handler(RagError)
async def rag_error_handler(request: Request, exc: RagError) -> JSONResponse:
    if isinstance(exc, ProviderRateLimitError):
        status = 429
    elif isinstance(exc, EmptyTranscriptError):
        status = 400
    else:
        status = 502
    return JSONResponse({"error": str(exc)}, status_code=status)


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
    import traceback
    tb = traceback.format_exc()
    log.error("unhandled_error err=%s tb=%s", str(exc)[:200], tb[-400:])
    return JSONResponse({"error": f"Server error: {type(exc).__name__}: {str(exc)[:200]}"}, status_code=500)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        index_loaded=_retriever.loaded,
        index_size=_retriever.size,
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )


@app.post("/api/stt", response_model=STTResponse)
async def stt(req: STTRequest) -> STTResponse:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not ready")
    return await _pipeline.transcribe(req)


@app.post("/api/query", response_model=PipelineResponse)
async def query(req: QueryRequest, request: Request) -> PipelineResponse:
    if _pipeline is None:
        raise HTTPException(503, "Pipeline not ready")
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())[:8]
    return await _pipeline.query(req, correlation_id=cid)


# Vercel requires the ASGI app to be named `handler`
handler = app
