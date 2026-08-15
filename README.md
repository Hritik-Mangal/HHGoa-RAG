# HH Goa 2026 — Voice-Enabled RAG

A production-oriented **voice → speech-to-text → retrieval → grounded answer** pipeline over `ai4bharat/MSMARCO-XI`, built for HH Goa 2026.

**Stack:** Sarvam AI (STT) · Groq (generation) · multilingual-e5-small (embeddings) · FAISS + numpy (retrieval) · React + Framer Motion (UI) · Vercel (deployment)

---

## Architecture

```
Voice → Sarvam STT → [client-side embed] → numpy vector search → guardrails → Groq → answer
```

See [docs/architecture.md](docs/architecture.md) for the full system map.

---

## Setup

### 1. Clone and configure

```bash
git clone <repo-url>
cd HHGoa-RAG
cp .env.example .env
# Edit .env — add SARVAM_API_KEY and GROQ_API_KEY
```

### 2. Python environment (offline ingestion)

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements-offline.txt
```

### 3. Frontend dependencies

```bash
cd web
npm install
cd ..
```

---

## Offline Ingestion

Run once to build the vector index. Creates `api/artifacts/vectors.npy` and `api/artifacts/metadata.json`.

```bash
# Stream 5000 Hindi queries, chunk with strategy D (adaptive), embed, export
python scripts/ingest.py --lang hi --n 5000 --strategy D
```

Benchmark chunking strategies:
```bash
for strategy in A B C D; do
    python scripts/evaluate.py --strategy $strategy --k 5 --n 200
done
```

---

## Running Locally

```bash
# Install Vercel CLI
npm i -g vercel

# Start dev server (proxies /api to Python)
vercel dev
```

Open [http://localhost:3000](http://localhost:3000) — hold the orb to speak.

For Python-only API dev:
```bash
pip install uvicorn
uvicorn api.index:app --reload --port 8000
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/stt` | `{audio_b64, format, language}` → `{transcript, latency_ms}` |
| `POST` | `/api/query` | `{transcript, query_vector, top_k}` → `PipelineResponse` |
| `GET` | `/api/health` | Index status + model info |
| `GET` | `/api/docs` | FastAPI OpenAPI docs |

---

## Latency Benchmark

```bash
python scripts/benchmark.py --n 30
```

Reports P50/P70/P100 for Tier 1 (embed + retrieval + guardrails, target `<200 ms`). See [docs/latency.md](docs/latency.md) for methodology.

---

## Tests

```bash
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## Design

The UI uses a **royal emerald + restrained gold** design system: deep green backgrounds, glass panels, emerald/gold animations. The VoiceOrb is the primary interaction with 8 animated states (idle, listening, transcribing, retrieving, generating, complete, error). See `Claude.md §20` for the full design spec.

---

## Limitations

- `<200 ms` applies to Tier 1 (embed + retrieval + guardrails). STT (~200–500 ms) and generation (~150–400 ms) are reported separately.
- Index is built offline from a 5k-query subset of MSMARCO-XI Hindi; full 55 GB corpus not indexed.
- Client-side embedding (Transformers.js) requires a one-time model download (~30 MB, cached).

---

## Submission checklist

- [ ] GitHub repo clean (no secrets, no large binaries except index artifacts)
- [ ] Live Vercel link
- [ ] 90-second process video
- [ ] End-to-end demo video
- [ ] Videos posted by every member (Instagram + X + LinkedIn)
- [ ] `#RAGInGoa` on every post
- [ ] At least one public Instagram account
- [ ] Submission form
- [ ] Submitted before **2026-08-22 23:59**
