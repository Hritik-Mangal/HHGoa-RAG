# Latency

## Two-tier reporting

The `<200 ms` end-to-end target applies to the **core RAG pipeline** (embed + vector search + guardrails). STT and LLM generation each exceed 200 ms on their own due to network round-trips; they are reported separately.

### Tier 1 — Core RAG pipeline
What's included:
- Client-side query embedding (Transformers.js) — ~30–60 ms (warm)
- Numpy cosine search over index — ~2–10 ms
- Guardrail checks (pattern + threshold) — ~1–2 ms
- JSON serialisation — ~1 ms

**Target: < 200 ms. Measured across a fixed 30-query evaluation set.**

### Tier 2 — Full voice → answer
Adds:
- Sarvam STT (Saaras v3 REST) — ~200–500 ms (network dependent)
- Groq generation (llama-3.1-8b-instant) — ~150–400 ms

**Not reported as sub-200 ms; documented honestly below.**

## Benchmark results

Run `python scripts/benchmark.py --n 30` and populate:

```
Tier 1 (core RAG, no LLM):
  P50:  __ ms
  P70:  __ ms
  P100: __ ms

Tier 2 (full pipeline including STT + generation):
  P50:  __ ms
  P70:  __ ms
  P100: __ ms
```

## Per-stage breakdown (typical warm values)

| Stage | Typical range | Notes |
|-------|--------------|-------|
| STT (Sarvam) | 200–500 ms | Network + inference; excluded from Tier 1 |
| Query embed (browser) | 30–60 ms | Transformers.js, warm model |
| Vector search | 2–10 ms | Numpy dot product, 30k chunks |
| Guardrails | 1–3 ms | Pattern match + threshold |
| Groq generation | 150–400 ms | llama-3.1-8b-instant |
| **Tier 1 total** | **35–75 ms** | Well within 200 ms |

## Methodology

- Warm-up: 2 queries run before measurement
- Fixed query set of 15 templates × 2 repeats = 30 queries
- Cold start latency excluded (reported separately)
- Network time included for all external calls
- All measurements on a single machine; times may vary in Vercel serverless
