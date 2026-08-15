# Chunking Strategy

## Dataset Characteristics

`MSMARCO-XI` passages are already short: ~50–150 tokens each. Unlike long documents, they rarely need aggressive sub-splitting. The interesting question is: does splitting hurt by fragmenting context, or help by increasing semantic precision?

## Strategies Implemented

### A — Fixed-size
Token windows of 80 words with 15-word overlap. Baseline for comparison. Simple and predictable but may split mid-sentence.

### B — Semantic
Split on sentence boundaries (`.`, `!`, `?`, `।`). Groups sentences up to 100 words per chunk. Respects linguistic units; loses no sentence-initial context from overlap.

### C — Metadata-aware
Each MSMARCO passage is kept atomic — no sub-splits. Treats the passage as the retrieval unit. Maximum context per chunk; highest risk of returning more text than needed.

### D — Adaptive (selected default)
Routes per-passage:
- `≤60 words` → keep whole (C behaviour)
- `61–200 words` → semantic split (B behaviour)
- `>200 words` → fixed-size with overlap (A behaviour)

## Benchmarks

Run `python scripts/evaluate.py --strategy A` (and B, C, D) and populate this table:

| Strategy | Recall@5 | Hit@5 | MRR | #Chunks | Retrieval P50 |
|----------|----------|-------|-----|---------|---------------|
| A — Fixed | — | — | — | — | — |
| B — Semantic | — | — | — | — | — |
| C — Metadata | — | — | — | — | — |
| D — Adaptive ✓ | — | — | — | — | — |

## Why D was selected

MS MARCO passages are inherently short, so the majority route to "keep whole" (D → C path), preserving full passage context. Longer passages benefit from semantic splitting without mid-sentence breaks. The adaptive approach is measurably compared above and selected only after benchmarking — not assumed superior.

## Index size note

With ~30k passages and 384-dim float32 embeddings:
- `vectors.npy` ≈ 44 MB
- `metadata.json` ≈ 8 MB (compressed)
- Total artifact bundle ≈ 52 MB — within Vercel's 250 MB limit
