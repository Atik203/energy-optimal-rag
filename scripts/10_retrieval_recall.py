#!/usr/bin/env python
"""10 - Supporting-paragraph retrieval recall for HotpotQA.

Descriptive diagnostic: for each question, how many of its gold paragraphs does
BM25 retrieve at each depth? No model is invoked and no energy is measured.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.config import load_toml  # noqa: E402
from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.retrieval.recall import hotpot_recall  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HotpotQA supporting-paragraph recall.")
    parser.add_argument("--config", required=True, help="Run config TOML.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root.")
    parser.add_argument("--out", default=None, help="Output JSON path.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root = Path(args.root)
    config = load_toml(
        root / args.config if not Path(args.config).is_absolute() else Path(args.config)
    )
    dataset = str(config.get("dataset"))
    if dataset != "hotpot":
        raise SystemExit("retrieval recall is only defined for the hotpot dataset")
    id_split = str(config.get("id_split", "hotpot"))
    processed_dir = root / "data" / "processed"
    split = load_prepared_split(processed_dir, dataset, id_split)
    index = RetrievalIndex.from_corpus(split.corpus)
    k_grid = [int(value) for value in config.get("k_grid", [])]
    per_question, aggregate = hotpot_recall(index, split.questions, split.corpus, k_grid)

    run_id = str(config.get("run_id", "hotpot"))
    out_path = Path(args.out) if args.out else root / "analysis" / f"{run_id}_retrieval_recall.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "run_id": run_id,
        "dataset": dataset,
        "split": id_split,
        "n_questions": int(len(split.ids)),
        "k_grid": k_grid,
        "per_k": {
            int(row["k"]): {
                "n_questions": int(row["n_questions"]),
                "mean_recall": float(row["mean_recall"]),
                "all_gold_rate": float(row["all_gold_rate"]),
                "min_recall": float(row["min_recall"]),
                "max_recall": float(row["max_recall"]),
            }
            for _, row in aggregate.iterrows()
        },
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    per_question_path = out_path.with_name(out_path.stem + "_per_question.csv")
    per_question.to_csv(per_question_path, index=False)

    print(json.dumps(payload, indent=2))
    print(f"wrote {out_path}")
    print(f"wrote {per_question_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
