#!/usr/bin/env python
"""00 — Prepare a dataset for the run harness.

Downloads are not automated: confirm the upstream license, place the official
file under ``data/raw/``, and record the source SHA-256 through this script.
SQuAD uses ``--dataset squad`` (default). HotpotQA distractor uses
``--dataset hotpot``; pass the official JSON or its Hugging Face parquet mirror.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.prep_hotpot import prepare_hotpot  # noqa: E402
from rag_energy.data.prep_squad import prepare_squad  # noqa: E402

DEFAULTS = {
    "squad": {
        "raw": "data/raw/dev-v1.1.json",
        "out": "data/processed",
        "n_questions": 1000,
        "splits_out": "data/splits/squad_splits.json",
    },
    "hotpot": {
        "raw": "data/raw/hotpot_dev_distractor_v1.parquet",
        "out": "data/processed",
        "n_questions": 500,
        "splits_out": "data/splits/hotpot_splits.json",
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare a QA dataset for the run harness.")
    parser.add_argument("--dataset", choices=sorted(DEFAULTS), default="squad")
    parser.add_argument("--raw", default=None, help="Raw input file (default depends on dataset).")
    parser.add_argument(
        "--corpus",
        nargs="*",
        default=None,
        help="SQuAD only: additional corpus JSON files, e.g. data/raw/train-v1.1.json.",
    )
    parser.add_argument("--out", default="data/processed", help="Processed output directory.")
    parser.add_argument("--n-questions", type=int, default=None, help="Question sample size.")
    parser.add_argument("--seed", type=int, default=20261115, help="Sampling seed.")
    parser.add_argument("--passage-words", type=int, default=None, help="Words per passage.")
    parser.add_argument(
        "--context-word-limit", type=int, default=256, help="SQuAD context truncation limit."
    )
    parser.add_argument(
        "--splits-out",
        default=None,
        help="Tracked ID split JSON (default depends on dataset).",
    )
    parser.add_argument(
        "--manifest",
        default="data/manifest.json",
        help="Tracked manifest to update.",
    )
    parser.add_argument(
        "--split-sizes",
        default=None,
        help="SQuAD only: JSON object overriding the default split sizes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    defaults = DEFAULTS[args.dataset]
    raw = Path(args.raw or defaults["raw"])
    if not raw.is_file():
        print(
            f"00_prepare_data: missing {raw}.\n"
            "Download the dataset from the official source (or its Hugging Face mirror), "
            "record its license, and place it under data/raw/. Do not commit raw data.",
            file=sys.stderr,
        )
        return 2
    splits_out = Path(args.splits_out or defaults["splits_out"])
    n_questions = args.n_questions if args.n_questions is not None else defaults["n_questions"]

    if args.dataset == "hotpot":
        passage_words = 0 if args.passage_words is None else args.passage_words
        manifest_out = prepare_hotpot(
            raw,
            Path(args.out),
            n_questions=n_questions,
            seed=args.seed,
            chunking="whole_paragraph" if passage_words == 0 else "word",
            passage_words=passage_words,
            splits_out=splits_out,
            manifest_path=Path(args.manifest),
        )
        summary = json.loads(manifest_out.read_text(encoding="utf-8"))
        counts = summary["counts"]
        print(
            "Prepared HotpotQA: "
            f"{counts['n_questions']} questions, {counts['n_passages']} passages "
            f"(frame {counts['n_questions_frame']} of {counts['n_questions_total']})."
        )
    else:
        passage_words = 70 if args.passage_words is None else args.passage_words
        corpus = [Path(path) for path in args.corpus] if args.corpus else None
        split_sizes = json.loads(args.split_sizes) if args.split_sizes else None
        manifest_out = prepare_squad(
            raw,
            Path(args.out),
            n_questions=n_questions,
            seed=args.seed,
            passage_words=passage_words,
            context_word_limit=args.context_word_limit,
            corpus_paths=corpus,
            split_sizes=split_sizes,
            splits_out=splits_out,
            manifest_path=Path(args.manifest),
        )
        summary = json.loads(manifest_out.read_text(encoding="utf-8"))
        counts = summary["counts"]
        print(
            "Prepared SQuAD: "
            f"{counts['n_questions']} questions, {counts['n_contexts']} contexts, "
            f"{counts['n_passages']} passages."
        )
    print(f"Manifest: {manifest_out}")
    print(f"Splits: {splits_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
