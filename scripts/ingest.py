#!/usr/bin/env python
"""Offline ingestion pipeline.

Usage:
    python scripts/ingest.py [--lang hi] [--n 5000] [--strategy D]
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.chunking import chunk_passages
from ingestion.embeddings import embed_chunks
from ingestion.indexing import export_artifacts
from ingestion.load_dataset import extract_corpus_and_qrels, iter_records, save_corpus, save_qrels

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="hi", help="Language code (hi, ta, bn, ...)")
    parser.add_argument("--split", default="validation", choices=["train", "validation"], help="Dataset split (validation recommended)")
    parser.add_argument("--n", type=int, default=5_000, help="Number of queries to stream")
    parser.add_argument("--strategy", default="D", choices=list("ABCD"), help="Chunking strategy")
    parser.add_argument("--no-translated", dest="translated", action="store_false", default=True, help="Use English passages only")
    args = parser.parse_args()

    log.info("step=1/4 streaming dataset lang=%s split=%s n=%d", args.lang, args.split, args.n)
    records = iter_records(lang=args.lang, split=args.split, max_queries=args.n)
    passages_by_id, qrels = extract_corpus_and_qrels(records, use_translated=args.translated)
    log.info("extracted passages=%d queries_with_qrels=%d", len(passages_by_id), len(qrels))

    # Persist raw corpus + qrels (for evaluation)
    save_corpus(passages_by_id)
    save_qrels(qrels)

    log.info("step=2/4 chunking strategy=%s", args.strategy)
    passage_list = list(passages_by_id.values())
    chunks = chunk_passages(passage_list, strategy=args.strategy)
    log.info("chunks=%d", len(chunks))

    log.info("step=3/4 embedding with multilingual-e5-small")
    vectors = embed_chunks(chunks)

    log.info("step=4/4 exporting artifacts")
    summary = export_artifacts(chunks, vectors)
    log.info("done %s", summary)


if __name__ == "__main__":
    main()
