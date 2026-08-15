#!/usr/bin/env python
"""Retrieval quality evaluation — Recall@K, Hit@K, MRR per chunking strategy.

Usage:
    python scripts/evaluate.py [--strategy A] [--k 5] [--n 500]
"""
from __future__ import annotations
import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def recall_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    top_k = set(retrieved[:k])
    hits = sum(1 for r in relevant if r in top_k)
    return hits / len(relevant) if relevant else 0.0


def hit_at_k(relevant: List[str], retrieved: List[str], k: int) -> float:
    top_k = set(retrieved[:k])
    return float(any(r in top_k for r in relevant))


def reciprocal_rank(relevant: List[str], retrieved: List[str]) -> float:
    rel_set = set(relevant)
    for rank, rid in enumerate(retrieved, start=1):
        if rid in rel_set:
            return 1.0 / rank
    return 0.0


def evaluate_strategy(
    strategy: str,
    k: int,
    n_eval: int,
) -> dict:
    from ingestion.chunking import chunk_passages
    from ingestion.embeddings import embed_chunks, embed_query
    from ingestion.indexing import build_faiss_index, faiss_search

    corpus_path = Path("ingestion/artifacts/corpus_raw.json")
    qrels_path = Path("ingestion/artifacts/qrels.json")
    if not corpus_path.exists():
        log.error("Run scripts/ingest.py first")
        sys.exit(1)

    with open(corpus_path, encoding="utf-8") as fh:
        passages = json.load(fh)
    with open(qrels_path, encoding="utf-8") as fh:
        qrels: dict = json.load(fh)

    log.info("chunking strategy=%s", strategy)
    chunks = chunk_passages(passages, strategy=strategy)
    log.info("embedding %d chunks", len(chunks))
    vectors = embed_chunks(chunks, show_progress=True)

    log.info("building FAISS index")
    t0 = time.perf_counter()
    index = build_faiss_index(vectors, index_type="flat")
    build_ms = (time.perf_counter() - t0) * 1000

    chunk_ids = [c.chunk_id for c in chunks]
    # Map passage_id → list of chunk indices in the index
    pid_to_chunk_ids: dict[str, List[str]] = {}
    for c in chunks:
        pid_to_chunk_ids.setdefault(c.passage_id, []).append(c.chunk_id)

    recall_scores, hit_scores, mrr_scores, latencies = [], [], [], []

    eval_qids = list(qrels.keys())[:n_eval]
    # Need queries; load them from corpus (doc_id maps to query_id)
    qid_to_query: dict[str, str] = {}
    with open(corpus_path, encoding="utf-8") as fh:
        for p in json.load(fh):
            if p["doc_id"] not in qid_to_query:
                qid_to_query[p["doc_id"]] = p.get("query", "")  # best effort

    for qid in eval_qids:
        query_text = qid_to_query.get(qid, "")
        if not query_text:
            continue
        relevant_pids = qrels[qid]
        # Map relevant passage_ids to chunk_ids
        relevant_chunk_ids = []
        for pid in relevant_pids:
            relevant_chunk_ids.extend(pid_to_chunk_ids.get(pid, []))

        t0 = time.perf_counter()
        qv = embed_query(query_text)
        scores, indices = faiss_search(index, qv, k=k)
        ret_ms = (time.perf_counter() - t0) * 1000
        latencies.append(ret_ms)

        retrieved = [chunk_ids[int(i)] for i in indices if i >= 0]
        recall_scores.append(recall_at_k(relevant_chunk_ids, retrieved, k))
        hit_scores.append(hit_at_k(relevant_chunk_ids, retrieved, k))
        mrr_scores.append(reciprocal_rank(relevant_chunk_ids, retrieved))

    return {
        "strategy": strategy,
        "k": k,
        "n_eval": len(recall_scores),
        "n_chunks": len(chunks),
        "recall_at_k": round(float(np.mean(recall_scores)), 4),
        "hit_at_k": round(float(np.mean(hit_scores)), 4),
        "mrr": round(float(np.mean(mrr_scores)), 4),
        "retrieval_p50_ms": round(float(np.percentile(latencies, 50)), 2),
        "retrieval_p100_ms": round(float(np.percentile(latencies, 100)), 2),
        "index_build_ms": round(build_ms, 1),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="D", choices=list("ABCD"))
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--n", type=int, default=200)
    args = parser.parse_args()

    results = evaluate_strategy(args.strategy, k=args.k, n_eval=args.n)
    print(json.dumps(results, indent=2))

    out = Path("docs") / f"eval_strategy_{args.strategy}.json"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
