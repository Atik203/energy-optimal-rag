#!/usr/bin/env python
"""40 - Router training (P1) + threshold-select (qc_fresh), CPU only.

Train logistic-per-depth models on P1 correctness with pre-generation BM25
features only (no probe, no gold), tune the confidence threshold on qc_fresh
against static k=4 with FIXED per-depth block costs, freeze the threshold.

Phases:
  --phase select-only : train + select, write analysis/qc_router/{train,select}.json
  --phase eval-once   : apply frozen threshold to qc_router eval run (fails if
                        runs/squad_qwen4b_qc_router/blocks_design.json missing)

Fixed-cost rule (R5 correction): energy_by_depth is the same J-bar for every
question (J1_bar/J4_bar from the relevant run's blocks). Per-query windows are
never used as costs.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.policy import (  # noqa: E402
    PolicyExample,
    evaluate_policy,
    matched_oracle_evaluation,
    oracle_gain_pct,
    static_evaluation,
    train_policy,
)

SEED = 20261115
K_PAIR = (1, 4)
STATIC_DEPTH = 4


def _load_correct(path: Path) -> dict[tuple[str, int], int]:
    rows: dict[tuple[str, int], int] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[(str(row["question_id"]), int(row["k"]))] = int(row["correct_em"])
    return rows


def _fixed_costs(blocks_path: Path) -> dict[int, float]:
    payload = json.loads(blocks_path.read_text(encoding="utf-8"))
    out: dict[int, float] = {}
    for k_str, v in payload["depths"].items():
        k = int(k_str)
        if k in K_PAIR:
            out[k] = float(v["energy_j"]) / float(v["n"])
    assert set(out) == set(K_PAIR), f"fixed costs missing depths: {out.keys()}"
    return out


def _examples(
    qids: list[str],
    questions: dict[str, str],
    wh_types: dict[str, str],
    correct: dict[tuple[str, int], int],
    fixed: dict[int, float],
    index: RetrievalIndex,
) -> list[PolicyExample]:
    examples: list[PolicyExample] = []
    for qid in qids:
        hits = index.search(qid, questions[qid], max(K_PAIR))
        scores = [hit.score for hit in hits]
        correct_by = {k: int(correct[(qid, k)]) for k in K_PAIR}
        energy_by = {k: float(fixed[k]) for k in K_PAIR}
        examples.append(
            PolicyExample(
                question_id=qid,
                question=questions[qid],
                bm25_scores=scores,
                best_depth=0,
                correct_by_depth=correct_by,
                energy_by_depth=energy_by,
                wh_type=wh_types.get(qid, ""),
            )
        )
    return examples


def _auc(examples: list[PolicyExample], policy, depth: int) -> float:
    from rag_energy.stats.policy import _predict_correct

    scores = [_predict_correct(policy, e, depth) for e in examples]
    labels = [int(e.correct_by_depth[depth]) for e in examples]
    pairs = sorted(zip(scores, labels, strict=True))
    n1 = sum(labels)
    n0 = len(labels) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    rank_sum = sum(i + 1 for i, (_, y) in enumerate(pairs) if y == 1)
    return (rank_sum - n1 * (n1 + 1) / 2) / (n1 * n0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Router train/select/eval (CPU).")
    parser.add_argument("--phase", choices=["select-only", "eval-once"], default="select-only")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root)

    # Train on P1 correctness.
    p1_split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    p1_q = {str(r.qid): str(r.question) for r in p1_split.questions.itertuples(index=False)}
    p1_wh = {str(r.qid): str(r.wh_type) for r in p1_split.questions.itertuples(index=False)}
    p1_correct = _load_correct(root / "runs" / "squad_qwen4b_p1" / "raw.csv")
    index = RetrievalIndex.from_corpus(p1_split.corpus)
    # Fixed costs for training are irrelevant (only correctness trains); use P1-calibrated means.
    p1_fixed = {1: 36.25, 4: 36.25}  # placeholder equal costs so training never sees energy signal
    train = _examples(list(p1_split.ids), p1_q, p1_wh, p1_correct, p1_fixed, index)
    policy = train_policy(train, train)

    # Select threshold on qc_fresh with its fixed block costs.
    fresh_split = load_prepared_split(root / "data" / "processed", "squad", "qc_fresh")
    fresh_q = {str(r.qid): str(r.question) for r in fresh_split.questions.itertuples(index=False)}
    fresh_wh = {str(r.qid): str(r.wh_type) for r in fresh_split.questions.itertuples(index=False)}
    fresh_correct = _load_correct(root / "runs" / "squad_qwen4b_qc_fresh" / "raw.csv")
    fresh_fixed = _fixed_costs(root / "runs" / "squad_qwen4b_qc_fresh" / "blocks_design.json")
    select = _examples(list(fresh_split.ids), fresh_q, fresh_wh, fresh_correct, fresh_fixed, index)

    static_acc = sum(int(e.correct_by_depth[STATIC_DEPTH]) for e in select) / len(select)
    best: tuple[float, float, dict] = (float("inf"), 0.0, {})
    for i in range(21):
        thr = i / 20
        res = evaluate_policy(policy, select, STATIC_DEPTH, thr)
        gap = abs(res["accuracy"] - static_acc)
        if (gap, thr) < (best[0], best[1]):
            best = (gap, thr, res)
    _, threshold, sel_policy = best

    out_dir = root / "analysis" / "qc_router"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "train.json").write_text(
        json.dumps(
            {
                "n_train": len(train),
                "depths": list(K_PAIR),
                "seed": SEED,
                "static_depth": STATIC_DEPTH,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (out_dir / "select.json").write_text(
        json.dumps(
            {
                "n_select": len(select),
                "static_k4_accuracy": static_acc,
                "threshold": threshold,
                "policy": sel_policy,
                "fixed_j_per_query": fresh_fixed,
                "auc_k1": _auc(select, policy, 1),
                "auc_k4": _auc(select, policy, 4),
                "note": "exploratory; threshold frozen here before eval exists",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"select: threshold={threshold:.2f} acc={sel_policy['accuracy']:.4f} vs static {static_acc:.4f}"
    )

    if args.phase == "eval-once":
        eval_blocks = root / "runs" / "squad_qwen4b_qc_router" / "blocks_design.json"
        eval_raw = root / "runs" / "squad_qwen4b_qc_router" / "raw.csv"
        if not eval_blocks.is_file() or not eval_raw.is_file():
            raise SystemExit("eval run missing: run the qc_router GPU run first")
        frozen_thr = float(
            json.loads((out_dir / "select.json").read_text(encoding="utf-8"))["threshold"]
        )
        eval_split = load_prepared_split(root / "data" / "processed", "squad", "qc_router_eval")
        eval_q = {str(r.qid): str(r.question) for r in eval_split.questions.itertuples(index=False)}
        eval_wh = {str(r.qid): str(r.wh_type) for r in eval_split.questions.itertuples(index=False)}
        eval_correct = _load_correct(eval_raw)
        eval_fixed = _fixed_costs(eval_blocks)
        eval_ex = _examples(list(eval_split.ids), eval_q, eval_wh, eval_correct, eval_fixed, index)
        pol = evaluate_policy(policy, eval_ex, STATIC_DEPTH, frozen_thr)
        sta = static_evaluation(eval_ex, STATIC_DEPTH)
        matched = matched_oracle_evaluation(eval_ex, STATIC_DEPTH, allow_abstention=False)
        gap_energy = oracle_gain_pct(
            float(sta["energy_per_correct"]), float(matched["energy_per_correct"])
        )
        saving = 100.0 * (1.0 - float(pol["energy_per_correct"]) / float(sta["energy_per_correct"]))
        capture = 100.0 * saving / gap_energy if gap_energy > 0 else float("nan")
        (out_dir / "eval.json").write_text(
            json.dumps(
                {
                    "threshold": frozen_thr,
                    "static": sta,
                    "policy": pol,
                    "matched_oracle_no_abstention": matched,
                    "capture_pct": capture,
                    "acc_diff_pp": 100.0 * (float(pol["accuracy"]) - float(sta["accuracy"])),
                    "fixed_j_per_query": eval_fixed,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            f"eval-once: capture={capture:.2f}% acc_diff={100.0 * (pol['accuracy'] - sta['accuracy']):+.2f}pp"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
