#!/usr/bin/env python
"""17 - Recall x precision decomposition.

Computes retrieval recall R(k), conditional reader precision Q(k)=A(k)/R(k),
and fits a two-stage model A(k)=R(k)(q0-gamma k) against the one-stage coverage
fit. Descriptive mechanism analysis; no gate is changed.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.models import coverage_fit  # noqa: E402

ARMS = {
    "squad_qwen4b_p1": ("squad", "p1_primary"),
    "squad_qwen15b_p2": ("squad", "replication"),
    "squad_llama3b_p2": ("squad", "replication"),
    "hotpot_qwen4b_p2": ("hotpot", "hotpot"),
}
K_GRID = (0, 1, 2, 4, 8, 10, 16, 32)


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Recall x precision decomposition.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    payload = {}
    for run_id, (dataset, split_name) in ARMS.items():
        raw = root / "runs" / run_id / "raw.csv"
        if not raw.is_file():
            continue
        split = load_prepared_split(root / "data" / "processed", dataset, split_name)
        rows = list(csv.DictReader(raw.open("r", encoding="utf-8", newline="")))
        by_key = {(r["question_id"], int(r["k"])): r for r in rows if r.get("valid", "1") == "1"}
        index = RetrievalIndex.from_corpus(split.corpus)
        gold_ids = {}
        if dataset == "hotpot":
            for row in split.corpus.itertuples(index=False):
                if bool(row.is_gold):
                    gold_ids.setdefault(str(row.qid), set()).add(str(row.passage_id))
        questions = {
            str(r.qid): (str(r.question), str(r.gold))
            for r in split.questions.itertuples(index=False)
        }
        depths = sorted({int(r["k"]) for r in rows})
        max_depth = max(depths)
        retrieved_by_qid = {
            qid: index.search(qid, questions[qid][0], max_depth) for qid in split.ids
        }
        recall = {}
        accuracy = {}
        for depth in depths:
            hits = 0
            correct = 0
            total = 0
            for qid in split.ids:
                retrieved = retrieved_by_qid[qid][:depth]
                gold = questions[qid][1]
                if dataset == "hotpot":
                    present = any(p.passage_id in gold_ids.get(qid, set()) for p in retrieved)
                else:
                    present = any(_norm(gold) in _norm(p.text) for p in retrieved)
                row = by_key.get((qid, depth))
                if row is None:
                    continue
                total += 1
                hits += int(present)
                correct += int(row["correct_em"])
            recall[depth] = hits / total if total else 0.0
            accuracy[depth] = correct / total if total else 0.0
        q = {k: (accuracy[k] / recall[k] if recall[k] > 0 else 0.0) for k in depths}
        # Linear Q(k) = q0 - gamma k.
        xs = [k for k in depths if recall[k] > 0]
        ys = [q[k] for k in xs]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        sxx = sum((x - mean_x) ** 2 for x in xs)
        sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
        gamma = -sxy / sxx if sxx else 0.0
        q0 = mean_y + gamma * mean_x
        two_stage = {k: recall[k] * (q0 - gamma * k) for k in depths}
        rmse_two = (sum((accuracy[k] - two_stage[k]) ** 2 for k in depths) / len(depths)) ** 0.5
        a0, p, _r2 = coverage_fit([float(k) for k in depths], [accuracy[k] for k in depths])
        one_stage = {k: 1 - (1 - a0) * (1 - p) ** k for k in depths}
        rmse_one = (sum((accuracy[k] - one_stage[k]) ** 2 for k in depths) / len(depths)) ** 0.5
        payload[run_id] = {
            "dataset": dataset,
            "split": split_name,
            "depths": depths,
            "recall": recall,
            "accuracy": accuracy,
            "precision": q,
            "q0": q0,
            "gamma": gamma,
            "rmse_two_stage": rmse_two,
            "rmse_one_stage": rmse_one,
            "coverage_a0": a0,
            "coverage_p": p,
        }
    out = Path(args.out) if args.out else root / "analysis" / "recall_precision.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
