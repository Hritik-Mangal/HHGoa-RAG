"""Stream a subset of ai4bharat/MSMARCO-XI and extract passages + qrels.

Loading strategy:
  Uses fsspec + PyArrow to open the language-specific Parquet file via HTTP range requests.
  This avoids PyArrow's "Nested data conversions not implemented for chunked array outputs"
  bug that occurs when opening local Parquet files via a direct path.

  Opening via a fsspec file-object triggers a different (working) read code path.
  Only the requested columns' data is downloaded — not the full file.

Repo file naming:
  train/{lang_code}train.parquet
  validation/{lang_code}val.parquet

Schema (confirmed by probing hinval.parquet):
  query_id (int64), query (str), target_lang (str),
  passages: struct{English_passages: list[str], Translated_passages: list[str], is_selected: list[int64]}

Default split = validation (97k rows, 462 MB file; only needed columns fetched).
Train split = 778k rows, 3.7 GB file (avoid unless you have a fast connection).

Run probe:
    python -c "from ingestion.load_dataset import probe_schema; probe_schema()"
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Iterator

log = logging.getLogger(__name__)

DATASET_REPO = "ai4bharat/MSMARCO-XI"
DEFAULT_SPLIT = "validation"   # 97k rows; small enough to stream quickly
DEFAULT_N_QUERIES = 5_000
READ_COLUMNS = ["query_id", "query", "target_lang", "passages"]

LANG_FILE_MAP: dict[str, str] = {
    "hi": "hin",
    "ta": "tam",
    "bn": "ben",
    "te": "tel",
    "kn": "kan",
    "ml": "mal",
    "mr": "mar",
    "gu": "guj",
    "pa": "pan",
    "or": "ori",
    "as": "asm",
    "ur": "urd",
    "ne": "nep",
    "sa": "san",
}

_OUT_DIR = Path(__file__).parent / "artifacts"


def _hf_path(lang: str, split: str) -> str:
    prefix = LANG_FILE_MAP.get(lang, lang)
    suffix = "train" if split == "train" else "val"
    return f"datasets/{DATASET_REPO}/{split}/{prefix}{suffix}.parquet"


def iter_records(
    lang: str = "hi",
    split: str = DEFAULT_SPLIT,
    max_queries: int = DEFAULT_N_QUERIES,
) -> Iterator[dict]:
    """Yield row dicts via fsspec HTTP range requests (no full file download)."""
    try:
        import fsspec
        import pyarrow.parquet as pq
    except ImportError:
        raise RuntimeError("Install fsspec pyarrow: pip install fsspec pyarrow")

    hf_path = _hf_path(lang, split)
    log.info("opening lang=%s split=%s path=%s max=%d", lang, split, hf_path, max_queries)

    fs = fsspec.filesystem("hf", repo_type="dataset")
    with fs.open(hf_path, "rb") as fobj:
        pf = pq.ParquetFile(fobj)
        log.info("parquet rows=%d row_groups=%d", pf.metadata.num_rows, pf.num_row_groups)

        count = 0
        for rg_idx in range(pf.num_row_groups):
            if count >= max_queries:
                break
            table = pf.read_row_group(rg_idx, columns=READ_COLUMNS)
            df = table.to_pandas()
            for _, row in df.iterrows():
                if count >= max_queries:
                    break
                yield _row_to_dict(row)
                count += 1

    log.info("yielded %d records", count)


def _row_to_dict(row) -> dict:
    """Normalise a pandas row, unwrapping the passages struct."""
    # pandas Series behaves like a dict via row["col"]
    p = row["passages"]

    def _to_list(v):
        """Convert numpy array / list / None to plain Python list."""
        if v is None:
            return []
        try:
            return list(v)
        except TypeError:
            return []

    if isinstance(p, dict):
        passages = {
            "English_passages": _to_list(p.get("English_passages")),
            "Translated_passages": _to_list(p.get("Translated_passages")),
            "is_selected": [int(x) for x in _to_list(p.get("is_selected"))],
        }
    else:
        passages = {"English_passages": [], "Translated_passages": [], "is_selected": []}

    return {
        "query_id": str(int(row["query_id"])),
        "query": str(row["query"]),
        "target_lang": str(row["target_lang"]),
        "passages": passages,
    }


def extract_corpus_and_qrels(
    records: Iterator[dict],
    use_translated: bool = True,
) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Return (passages_by_id, qrels)."""
    passages_out: dict[str, dict] = {}
    qrels: dict[str, list[str]] = {}

    for rec in records:
        qid = rec.get("query_id", "").strip()
        if not qid:
            continue

        p_block = rec.get("passages") or {}
        is_selected = p_block.get("is_selected") or []
        eng_passages = p_block.get("English_passages") or []
        trans_passages = p_block.get("Translated_passages") or []

        if not eng_passages:
            continue

        relevant_ids: list[str] = []
        for idx, eng in enumerate(eng_passages):
            pid = f"{qid}_p{idx}"
            if pid not in passages_out:
                if use_translated and idx < len(trans_passages) and trans_passages[idx]:
                    text = str(trans_passages[idx]).strip()
                else:
                    text = str(eng or "").strip()
                if not text:
                    continue
                passages_out[pid] = {
                    "passage_id": pid,
                    "doc_id": qid,
                    "text": text,
                    "lang": rec.get("target_lang", "hin_Deva"),
                    "query_id": qid,
                    "query": rec.get("query", ""),
                }
            sel = int(is_selected[idx]) if idx < len(is_selected) else 0
            if sel:
                relevant_ids.append(pid)

        if relevant_ids:
            qrels[qid] = relevant_ids

    return passages_out, qrels


def probe_schema(lang: str = "hi", n: int = 2) -> None:
    """Print first *n* records to verify field names and types."""
    for i, rec in enumerate(iter_records(lang, max_queries=n)):
        print(f"\n--- Record {i} ---")
        p = rec.get("passages", {})
        for k, v in rec.items():
            if k != "passages":
                print(f"  {k}: {str(v)[:80]}")
        print(f"  passages.English_passages[:1]: {str(p.get('English_passages', [])[:1])[:100]}")
        print(f"  passages.is_selected[:5]: {p.get('is_selected', [])[:5]}")
        if i >= n - 1:
            break


def save_corpus(passages: dict[str, dict], path: Path | None = None) -> Path:
    out = path or (_OUT_DIR / "corpus_raw.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(list(passages.values()), fh, ensure_ascii=False)
    log.info("corpus_saved n=%d path=%s", len(passages), out)
    return out


def save_qrels(qrels: dict[str, list[str]], path: Path | None = None) -> Path:
    out = path or (_OUT_DIR / "qrels.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(qrels, fh, ensure_ascii=False)
    log.info("qrels_saved n=%d path=%s", len(qrels), out)
    return out
