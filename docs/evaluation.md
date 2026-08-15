# Evaluation

## Retrieval metrics

Ground truth comes from `passages.is_selected` in `MSMARCO-XI` — binary qrels included in the dataset. No external annotation required.

### Recall@K
Fraction of relevant passages recovered in top-K results.

`Recall@K = |relevant ∩ top-K| / |relevant|`

### Hit@K
Binary: 1 if any relevant passage is in top-K, else 0. Averaged over all queries.

### MRR (Mean Reciprocal Rank)
`MRR = mean(1 / rank_of_first_relevant)`

## Answer quality metrics

Since MSMARCO-XI includes `Answer` and `Eng_Answer` fields, answer quality can be measured against the reference answer:

- **Groundedness**: does the generated answer cite passages from the retrieved set? (verified by `verify_grounding()`)
- **Refusal correctness**: does the system correctly refuse off-topic/unsafe/no-evidence queries?
- **Hallucination rate**: claims in the answer not supported by any retrieved passage (estimated via source cross-check)

## Running evaluation

```bash
# Evaluate all strategies
for strategy in A B C D; do
    python scripts/evaluate.py --strategy $strategy --k 5 --n 200
done

# Results saved to docs/eval_strategy_{A,B,C,D}.json
```

## Dataset split

- Train split used for ingestion (corpus building)
- Validation split used for evaluation queries (held-out)
- No test split exists in MSMARCO-XI; validation is the evaluation set

## Limitations

1. Passages in MSMARCO-XI are machine-translated (NLLB-1.3B-Distilled); translation quality varies by language.
2. Binary relevance only — no graded judgements for NDCG.
3. The 55 GB dataset is streamed and subsampled; full-corpus results may differ.
4. Groq generation quality is measured qualitatively; automatic QA metrics (ROUGE, BERTScore) not yet implemented.
