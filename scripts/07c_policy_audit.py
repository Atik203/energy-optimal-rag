#!/usr/bin/env python
"""07c - P3 predictability and oracle audit.

CPU-only. Reports (a) how well pre-generation features predict correct@1,
(b) a learning curve, and (c) an answer-presence oracle upper bound. All
results are exploratory; the confirmatory G4 result remains the hashed-split
policy evaluation in analysis/policy/.
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
    featurize,
    matched_oracle_evaluation,
    static_evaluation,
)

K_GRID = (0, 1, 2, 4, 8, 16, 32)


def _rows(path: Path) -> dict[tuple[str, int], dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {(str(row["question_id"]), int(row["k"])): row for row in csv.DictReader(handle)}


def _norm(text: str) -> str:
    return " ".join(text.lower().split())


def main() -> int:
    parser = argparse.ArgumentParser(description="P3 predictability and oracle audit.")
    parser.add_argument("--run-id", default="squad_qwen4b_p1")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    root = Path(args.root)
    split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    rows = _rows(root / "runs" / args.run_id / "raw.csv")
    index = RetrievalIndex.from_corpus(split.corpus)
    questions = {str(r.qid): str(r.question) for r in split.questions.itertuples(index=False)}
    golds = {str(r.qid): str(r.gold) for r in split.questions.itertuples(index=False)}
    wh_types = {str(r.qid): str(r.wh_type) for r in split.questions.itertuples(index=False)}

    examples: dict[str, PolicyExample] = {}
    top1_text: dict[str, str] = {}
    for qid in split.ids:
        hits = index.search(qid, questions[qid], 1)
        top1_text[qid] = hits[0].text if hits else ""
        examples[qid] = PolicyExample(
            question_id=qid,
            question=questions[qid],
            bm25_scores=[hit.score for hit in index.search(qid, questions[qid], 32)],
            best_depth=0,
            correct_by_depth={k: int(rows[(qid, k)]["correct_em"]) for k in K_GRID},
            energy_by_depth={k: float(rows[(qid, k)]["j_gpu_calibrated"]) for k in K_GRID},
            wh_type=wh_types[qid],
        )

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    feature_names = [
        "top",
        "second",
        "gap",
        "mean",
        "std",
        "entropy",
        "n_positive",
        "question_words",
        "wh_what",
        "wh_who",
        "wh_when",
        "wh_where",
        "wh_which",
        "wh_why",
        "wh_how",
        "wh_other",
    ]
    x = np.array([[featurize(e)[name] for name in feature_names] for e in examples.values()])
    y = np.array([e.correct_by_depth[1] for e in examples.values()])
    model = make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=2000, random_state=20261115)
    )
    oof = cross_val_predict(
        model,
        x,
        y,
        cv=StratifiedKFold(5, shuffle=True, random_state=20261115),
        method="predict_proba",
    )[:, 1]
    auc = float(roc_auc_score(y, oof))

    train_ids = [qid for qid in split.ids if assign_split(qid, 20261115) == "train"]
    val_ids = [qid for qid in split.ids if assign_split(qid, 20261115) == "validation"]
    test_ids = [qid for qid in split.ids if assign_split(qid, 20261115) == "test"]
    x_train = {qid: [featurize(examples[qid])[name] for name in feature_names] for qid in train_ids}
    x_val = {qid: [featurize(examples[qid])[name] for name in feature_names] for qid in val_ids}

    learning = []
    for size in (50, 100, 200, 400, len(train_ids)):
        if size > len(train_ids):
            continue
        ids = train_ids[:size]
        m = make_pipeline(
            StandardScaler(), LogisticRegression(max_iter=2000, random_state=20261115)
        )
        m.fit([x_train[qid] for qid in ids], [examples[qid].correct_by_depth[1] for qid in ids])
        prob = m.predict_proba([x_val[qid] for qid in val_ids])[:, 1]
        learning.append(
            {
                "n_train": size,
                "val_auc": float(
                    roc_auc_score([examples[qid].correct_by_depth[1] for qid in val_ids], prob)
                ),
            }
        )

    # Answer-presence oracle: k=1 if the normalized gold is in the top-1 passage, else k=0.
    presence = {qid: _norm(golds[qid]) in _norm(top1_text[qid]) for qid in split.ids}
    test_examples = [examples[qid] for qid in test_ids]
    chosen = [1 if presence[qid] else 0 for qid in test_ids]
    total_j = sum(e.energy_by_depth[d] for e, d in zip(test_examples, chosen, strict=True))
    total_c = sum(e.correct_by_depth[d] for e, d in zip(test_examples, chosen, strict=True))
    oracle_gate = {
        "accuracy": total_c / len(test_examples),
        "energy_per_correct": total_j / total_c if total_c else float("inf"),
        "coverage_k1": sum(chosen) / len(chosen),
    }
    static = static_evaluation(test_examples, 1)
    matched = matched_oracle_evaluation(test_examples, 1)
    payload = {
        "run_id": args.run_id,
        "n": len(examples),
        "correct_at_1_rate": float(y.mean()),
        "oof_auc_correct_at_1": auc,
        "learning_curve": learning,
        "splits": {"train": len(train_ids), "validation": len(val_ids), "test": len(test_ids)},
        "answer_presence_oracle": oracle_gate,
        "static_k1": static,
        "matched_oracle": matched,
        "capture_pct": 100.0
        * (1.0 - oracle_gate["energy_per_correct"] / static["energy_per_correct"])
        / (1.0 - matched["energy_per_correct"] / static["energy_per_correct"])
        if matched["energy_per_correct"] < static["energy_per_correct"]
        else None,
        "note": "Exploratory; confirmatory G4 remains analysis/policy.",
    }
    out = Path(args.out) if args.out else root / "analysis" / "policy_audit"
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# P3 predictability audit",
        "",
        f"- OOF AUC for correct@1: **{auc:.3f}** (n={len(examples)}).",
        "- Learning curve: "
        + ", ".join(f"{row['n_train']}->{row['val_auc']:.3f}" for row in learning),
        f"- Answer-presence oracle: accuracy {oracle_gate['accuracy']:.4f}, "
        f"E/c {oracle_gate['energy_per_correct']:.2f}, k=1 coverage {100 * oracle_gate['coverage_k1']:.1f}%.",
        f"- Static k=1: accuracy {static['accuracy']:.4f}, E/c {static['energy_per_correct']:.2f}.",
        f"- Matched oracle: E/c {matched['energy_per_correct']:.2f}.",
        f"- Answer-presence capture: {payload['capture_pct']:.1f}%."
        if payload["capture_pct"] is not None
        else "- Answer-presence capture: n/a",
        "",
        "Exploratory only; the confirmatory G4 result is in analysis/policy.",
    ]
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Audit: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
