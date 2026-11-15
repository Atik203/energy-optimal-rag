"""Retrieval recall diagnostics for grouped (per-question) corpora.

HotpotQA supplies 10 paragraphs per question, of which two are supporting
paragraphs. Retrieval recall at depth ``k`` is the fraction of those supporting
paragraphs that appear in the top-``k`` BM25 list. This is a descriptive
diagnostic for the HotpotQA arm; it is not a gate and does not use model output.
"""

from __future__ import annotations

from typing import Any

from rag_energy.retrieval.index import RetrievalIndex


def _gold_ids(corpus: Any) -> dict[str, set[str]]:
    gold: dict[str, set[str]] = {}
    for row in corpus.itertuples(index=False):
        if bool(row.is_gold):
            gold.setdefault(str(row.qid), set()).add(
                str(row.passage_id)
            )
    return gold


def hotpot_recall(
    index: RetrievalIndex,
    questions: Any,
    corpus: Any,
    k_values: Any,
) -> tuple[Any, Any]:
    """Compute per-question and aggregate supporting-paragraph recall.

    Returns ``(per_question, aggregate)`` data frames. ``per_question`` has
    columns ``qid, k, n_gold, n_retrieved_gold, recall, all_gold``.
    ``aggregate`` has columns ``k, n_questions, mean_recall, all_gold_rate,
    min_recall, max_recall``.
    """
    import pandas as pd

    if not isinstance(k_values, (list, tuple)) or not k_values:
        raise ValueError("k_values must be a non-empty list")
    ks = [int(value) for value in k_values]
    if any(value < 0 for value in ks):
        raise ValueError("k_values must be non-negative")
    if len(set(ks)) != len(ks):
        raise ValueError("k_values must be unique")

    gold_by_qid = _gold_ids(corpus)
    question_text = {
        str(row.qid): str(row.question)
        for row in questions.itertuples(index=False)
    }
    if not question_text:
        raise ValueError("questions must not be empty")
    missing_gold = [qid for qid in question_text if not gold_by_qid.get(qid)]
    if missing_gold:
        raise ValueError(f"questions without gold paragraphs: {missing_gold[:5]}")

    max_k = max(ks)
    per_rows: list[dict[str, Any]] = []
    for qid, question in question_text.items():
        gold_ids = gold_by_qid[qid]
        retrieved_ids: list[str] = []
        if max_k > 0:
            retrieved = index.search(qid, question, max_k)
            retrieved_ids = [str(passage.passage_id) for passage in retrieved]
        for k in ks:
            top_ids = retrieved_ids[:k]
            hit = sum(1 for passage_id in top_ids if passage_id in gold_ids)
            per_rows.append(
                {
                    "qid": qid,
                    "k": k,
                    "n_gold": len(gold_ids),
                    "n_retrieved_gold": hit,
                    "recall": hit / len(gold_ids),
                    "all_gold": hit == len(gold_ids),
                }
            )

    per_question = pd.DataFrame(
        per_rows,
        columns=["qid", "k", "n_gold", "n_retrieved_gold", "recall", "all_gold"],
    )
    aggregate_rows: list[dict[str, Any]] = []
    for k in ks:
        subset = per_question[per_question["k"] == k]
        aggregate_rows.append(
            {
                "k": k,
                "n_questions": int(len(subset)),
                "mean_recall": float(subset["recall"].mean()),
                "all_gold_rate": float(subset["all_gold"].mean()),
                "min_recall": float(subset["recall"].min()),
                "max_recall": float(subset["recall"].max()),
            }
        )
    aggregate = pd.DataFrame(
        aggregate_rows,
        columns=[
            "k",
            "n_questions",
            "mean_recall",
            "all_gold_rate",
            "min_recall",
            "max_recall",
        ],
    )
    return per_question, aggregate
