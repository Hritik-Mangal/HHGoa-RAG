# Architecture

## Overview

HH Goa 2026 is a voice-enabled RAG system operating over `ai4bharat/MSMARCO-XI`. The system follows a strict offline/online split so the latency-critical online path is torch-free and fits within Vercel's serverless limits.

## Offline / Online Split

```
OFFLINE (local, one-time)                 ONLINE (Vercel, per request)
─────────────────────────                 ────────────────────────────
stream MSMARCO-XI subset                  Browser → /api/stt (audio → transcript)
  → extract + dedup passages              Browser  → client-side embed (Transformers.js)
  → 4 chunking strategies                 Browser → /api/query {transcript, query_vector}
  → embed with multilingual-e5-small         ↓
  → build FAISS + benchmark               numpy cosine search over vectors.npy
  → export vectors.npy + metadata.json    guardrails (pattern + threshold)
     (committed to api/artifacts/)        Groq generation (JSON mode)
                                          PipelineResponse → browser
```

## Component Map

```
api/
  index.py              FastAPI app (Vercel handler)
  artifacts/
    vectors.npy         (N, 384) float32, L2-normalised — never re-computed online
    metadata.json       chunk metadata array
  _lib/
    schemas.py          Pydantic I/O models (single source of truth)
    errors.py           Typed exception hierarchy
    latency.py          LatencyTracker context manager
    retry.py            tenacity wrapper + timeout helper
    sarvam_client.py    Sarvam STT (Saaras v3)
    groq_client.py      Groq generation (OpenAI-compatible)
    retriever.py        Load artifacts → numpy cosine search
    guardrails.py       Query safety, evidence check, grounding verify
    pipeline.py         RAGPipeline orchestrator (typed stages, retries, fallbacks)

ingestion/              OFFLINE ONLY — never imported by api/
  load_dataset.py       Stream MSMARCO-XI; extract corpus + qrels
  chunking.py           Strategies A, B, C, D
  embeddings.py         multilingual-e5-small batch encode
  indexing.py           FAISS build + export artifacts

web/                    React 18 + Vite + Tailwind + Framer Motion
  src/
    types/index.ts      Shared TypeScript types
    lib/api.ts          fetch wrapper for /api/stt and /api/query
    lib/embedder.ts     Transformers.js (Xenova/multilingual-e5-small) client-side embed
    hooks/useMic.ts     MediaRecorder + Web Audio API
    hooks/useVoiceQuery.ts  Full pipeline state machine
    components/         VoiceOrb, WaveformVisualizer, AnswerCard, SourceCard, etc.
    pages/              HomePage, AnalyticsView
```

## Request Flow

```
1. User presses VoiceOrb → MediaRecorder starts (useMic)
2. User releases → audio blob captured
3. POST /api/stt {audio_b64, format, language}
     → SarvamSTT.transcribe() → transcript
4. embedQuery(transcript) via Transformers.js [client-side, ~30-50ms]
5. POST /api/query {transcript, query_vector, top_k}
     → check_query() guardrail (pattern match)
     → Retriever.search(query_vector) [numpy dot product, ~2-10ms]
     → check_evidence() guardrail (similarity threshold)
     → GroqClient.generate(transcript, passages) [~150-400ms]
     → verify_grounding() [source cross-check]
6. PipelineResponse → AnswerCard + SourceCard rendered
```

## Vercel Deployment

- **Frontend**: `web/dist/` (Vite build) served as static files
- **API**: `api/index.py` as a Python 3.11 serverless function
- **Index**: `api/artifacts/vectors.npy` + `metadata.json` bundled with function (~50-80MB)
- **Routing**: `/api/*` → `api/index.py`; everything else → `index.html` (SPA)
- **Cold start**: index loaded once on startup via `@app.on_event("startup")`
