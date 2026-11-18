#!/usr/bin/env python
"""07 - Train and evaluate the query-conditional depth policy.

Builds pre-generation BM25 features from the P1 sweep, splits the 1,000
questions into 600/200/200, trains a small decision tree on the training split,
chooses a confidence threshold on validation to match the best static depth's
accuracy, and evaluates once on the held-out test split.
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
from rag_energy.data.splits import assign_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.policy import (  # noqa: E402
    PolicyExample,
    evaluate_policy,
    matched_oracle_evaluation,
    oracle_evaluation,
    oracle_gain_pct,
    static_evaluation,
    train_policy,
)


def _load_rows(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    rows: dict[tuple[str, int], dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows[(str(row["question_id"]), int(row["k"]))] = row
    return rows


def _examples(
    qids: list[str],
    questions: dict[str, str],
    wh_types: dict[str, str],
    rows: dict[tuple[str, int], dict[str, str]],
    index: RetrievalIndex,
    k_grid: list[int],
) -> list[PolicyExample]:
    examples: list[PolicyExample] = []
    for qid in qids:
        question = questions[qid]
        hits = index.search(qid, question, max(k_grid))
        scores = [hit.score for hit in hits]
        correct = {k: int(rows[(qid, k)]["correct_em"]) for k in k_grid if (qid, k) in rows}
        energy = {k: float(rows[(qid, k)]["j_gpu_calibrated"]) for k in k_grid if (qid, k) in rows}
        if len(correct) != len(k_grid):
            raise ValueError(f"{qid}: incomplete depth grid")
        examples.append(
            PolicyExample(
                question_id=qid,
                question=question,
                bm25_scores=scores,
                best_depth=0,
                correct_by_depth=correct,
                energy_by_depth=energy,
                wh_type=wh_types.get(qid, ""),
            )
        )
    return examples


def _accuracy_energy(examples: list[PolicyExample], depth: int) -> tuple[float, float]:
    total_j = sum(float(e.energy_by_depth[depth]) for e in examples)
    total_c = sum(int(e.correct_by_depth[depth]) for e in examples)
    return total_c / len(examples), total_j / total_c if total_c else float("inf")


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and evaluate the depth policy.")
    parser.add_argument("--run-id", default="squad_qwen4b_p1")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    root = Path(args.root)
    run_dir = root / "runs" / args.run_id
    raw_path = run_dir / "raw.csv"
    if not raw_path.is_file():
        raise SystemExit(f"missing raw CSV: {raw_path}")

    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    questions = {str(row.qid): str(row.question) for row in split.questions.itertuples(index=False)}
    wh_types = {str(row.qid): str(row.wh_type) for row in split.questions.itertuples(index=False)}
    rows = _load_rows(raw_path)
    k_grid = sorted({int(row["k"]) for row in rows.values()})
    index = RetrievalIndex.from_corpus(split.corpus)

    qids = list(split.ids)
    if len(qids) != 1000:
        raise SystemExit(f"expected 1,000 P1 questions, found {len(qids)}")
    train_ids = [qid for qid in qids if assign_split(qid, 20261115) == "train"]
    val_ids = [qid for qid in qids if assign_split(qid, 20261115) == "validation"]
    test_ids = [qid for qid in qids if assign_split(qid, 20261115) == "test"]

    train = _examples(train_ids, questions, wh_types, rows, index, k_grid)
    validation = _examples(val_ids, questions, wh_types, rows, index, k_grid)
    test = _examples(test_ids, questions, wh_types, rows, index, k_grid)

    # Best static depth on validation by ratio of sums.
    static_rows = []
    for depth in k_grid:
        acc, e = _accuracy_energy(validation, depth)
        static_rows.append({"k": depth, "accuracy": acc, "energy_per_correct": e})
    static_depth = min(static_rows, key=lambda row: row["energy_per_correct"])["k"]
    static_val_acc = next(row["accuracy"] for row in static_rows if row["k"] == static_depth)

    policy = train_policy(train, validation)

    # Tune only the confidence threshold on validation, never the test split.
    thresholds = [i / 20 for i in range(21)]
    tuned = []
    for threshold in thresholds:
        result = evaluate_policy(policy, validation, static_depth, threshold)
        tuned.append((abs(result["accuracy"] - static_val_acc), threshold, result))
    _gap, threshold, _val_result = min(tuned, key=lambda item: (item[0], item[1]))

    val_policy = evaluate_policy(policy, validation, static_depth, threshold)
    test_policy = evaluate_policy(policy, test, static_depth, threshold)
    test_static = static_evaluation(test, static_depth)
    test_oracle = oracle_evaluation(test)
    test_matched_oracle = matched_oracle_evaluation(test, static_depth)
    test_matched_oracle_no_abstain = matched_oracle_evaluation(
        test, static_depth, allow_abstention=False
    )
    oracle_gain = oracle_gain_pct(
        float(test_static["energy_per_correct"]),
        float(test_oracle["energy_per_correct"]),
    )
    matched_oracle_gain = oracle_gain_pct(
        float(test_static["energy_per_correct"]),
        float(test_matched_oracle["energy_per_correct"]),
    )
    matched_oracle_gain_no_abstain = oracle_gain_pct(
        float(test_static["energy_per_correct"]),
        float(test_matched_oracle_no_abstain["energy_per_correct"]),
    )
    policy_saving = 100.0 * (
        1.0 - float(test_policy["energy_per_correct"]) / float(test_static["energy_per_correct"])
    )
    captured = 100.0 * policy_saving / oracle_gain if oracle_gain > 0 else float("nan")
    captured_matched = (
        100.0 * policy_saving / matched_oracle_gain if matched_oracle_gain > 0 else float("nan")
    )

    payload = {
        "run_id": args.run_id,
        "n_train": len(train),
        "n_validation": len(validation),
        "n_test": len(test),
        "k_grid": k_grid,
        "static_depth": static_depth,
        "static_validation_accuracy": static_val_acc,
        "threshold": threshold,
        "validation": {
            "static": {row["k"]: row for row in static_rows},
            "policy": val_policy,
        },
        "test": {
            "static": test_static,
            "policy": test_policy,
            "oracle": test_oracle,
            "matched_oracle": test_matched_oracle,
            "matched_oracle_no_abstention": test_matched_oracle_no_abstain,
            "oracle_gain_pct": oracle_gain,
            "matched_oracle_gain_pct": matched_oracle_gain,
            "matched_oracle_gain_no_abstention_pct": matched_oracle_gain_no_abstain,
            "policy_saving_pct": policy_saving,
            "oracle_gap_captured_pct": captured,
            "matched_oracle_gap_captured_pct": captured_matched,
        },
    }

    out_dir = Path(args.out) if args.out else root / "analysis" / "policy"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "policy.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Query-conditional depth policy",
        "",
        f"Split: {len(train)} train / {len(validation)} validation / {len(test)} test.",
        f"Best static depth on validation: k={static_depth} (accuracy {static_val_acc:.4f}).",
        f"Policy confidence threshold: {threshold:.2f}.",
        "",
        "| Split | Method | Accuracy | J/correct | Saving vs static |",
        "|---|---|---:|---:|---:|",
        f"| test | static k={static_depth} | {test_static['accuracy']:.4f} | "
        f"{test_static['energy_per_correct']:.2f} | — |",
        f"| test | policy | {test_policy['accuracy']:.4f} | "
        f"{test_policy['energy_per_correct']:.2f} | {policy_saving:.2f}% |",
        f"| test | oracle (unconstrained) | {test_oracle['accuracy']:.4f} | "
        f"{test_oracle['energy_per_correct']:.2f} | {oracle_gain:.2f}% |",
        f"| test | oracle (matched accuracy) | {test_matched_oracle['accuracy']:.4f} | "
        f"{test_matched_oracle['energy_per_correct']:.2f} | {matched_oracle_gain:.2f}% |",
        "",
        f"Oracle gap captured by the policy (unconstrained oracle): {captured:.2f}%.",
        f"Oracle gap captured by the policy (matched oracle): {captured_matched:.2f}%.",
        "",
        "G4 requires an oracle gain of at least 20% and a policy capture of at least "
        "50% at matched accuracy. The test split is used once.",
    ]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Analysis: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
