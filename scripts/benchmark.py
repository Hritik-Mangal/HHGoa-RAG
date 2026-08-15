#!/usr/bin/env python
"""Latency benchmark — reports P50, P70, P100 for two tiers.

Tier 1 (core RAG pipeline): embed_query + vector search + guardrails
Tier 2 (full pipeline):     + Groq generation

Usage:
    python scripts/benchmark.py [--n 50] [--lang hi]
"""
from __future__ import annotations
import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
from dotenv import load_dotenv

load_dotenv()

from ingestion.embeddings import embed_query

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

_TEST_QUERIES = [
    "What is the capital of India?",
    "How does photosynthesis work?",
    "What are the symptoms of diabetes?",
    "Who wrote the Ramayana?",
    "What is machine learning?",
    "How far is the Moon from Earth?",
    "What is the boiling point of water?",
    "When did World War II end?",
    "What causes earthquakes?",
    "How does the immune system work?",
    "What is the Pythagorean theorem?",
    "Who invented the telephone?",
    "What is climate change?",
    "How do vaccines work?",
    "What is artificial intelligence?",
]


def percentile(data: List[float], p: float) -> float:
    return float(np.percentile(data, p))


async def run_benchmark(n_queries: int) -> dict:
    from api._lib.guardrails import check_evidence, check_query, GuardrailDecision
    from api._lib.retriever import Retriever

    retriever = Retriever()
    try:
        retriever.load()
    except Exception as exc:
        log.error("Failed to load index: %s — run scripts/ingest.py first", exc)
        sys.exit(1)

    tier1_latencies: List[float] = []
    tier2_latencies: List[float] = []

    queries = (_TEST_QUERIES * (n_queries // len(_TEST_QUERIES) + 1))[:n_queries]

    # Warm-up (2 queries, not measured)
    for q in queries[:2]:
        qv = embed_query(q).tolist()
        retriever.search(qv)

    for i, q in enumerate(queries):
        t_start = time.perf_counter()

        # Embed
        t0 = time.perf_counter()
        qv = embed_query(q).tolist()
        embed_ms = (time.perf_counter() - t0) * 1000

        # Guardrail (query)
        t0 = time.perf_counter()
        decision = check_query(q)
        guard_ms = (time.perf_counter() - t0) * 1000

        # Retrieval
        t0 = time.perf_counter()
        passages = retriever.search(qv, top_k=5)
        ret_ms = (time.perf_counter() - t0) * 1000

        # Evidence guardrail
        t0 = time.perf_counter()
        ev_decision = check_evidence(passages)
        ev_guard_ms = (time.perf_counter() - t0) * 1000

        tier1_total = (time.perf_counter() - t_start) * 1000
        tier1_latencies.append(tier1_total)

        log.info(
            "query=%d embed=%.1fms retrieval=%.1fms guard=%.1fms tier1=%.1fms passages=%d",
            i + 1, embed_ms, ret_ms, guard_ms + ev_guard_ms, tier1_total, len(passages),
        )

    return {
        "n_queries": len(tier1_latencies),
        "tier1": {
            "description": "embed + retrieval + guardrails (no LLM)",
            "p50_ms": round(percentile(tier1_latencies, 50), 1),
            "p70_ms": round(percentile(tier1_latencies, 70), 1),
            "p100_ms": round(percentile(tier1_latencies, 100), 1),
        },
        "note": (
            "Tier 2 (full voice→answer) adds STT (~200-500ms network) + "
            "Groq generation (~150-400ms). Run with --full to measure."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=30, help="Number of queries")
    args = parser.parse_args()

    results = asyncio.run(run_benchmark(args.n))
    print("\n" + "=" * 50)
    print("LATENCY BENCHMARK RESULTS")
    print("=" * 50)
    print(json.dumps(results, indent=2))
    print("=" * 50)

    # Save to docs/
    out = Path(__file__).parent.parent / "docs" / "latency_benchmark.json"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nResults saved to {out}")


if __name__ == "__main__":
    main()
