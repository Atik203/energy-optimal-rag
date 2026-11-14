#!/usr/bin/env python
"""00 — Prepare SQuAD v1.1 questions, corpus, passages, and ID splits.

Downloads are not automated: confirm the upstream license, place the official
JSON under ``data/raw/``, and record the source SHA-256 through this script.
Use ``--corpus data/raw/train-v1.1.json`` with the dev file to reproduce the
pilot's full unique-context corpus.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag_energy.data.prep_squad import prepare_squad  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare SQuAD v1.1 for the run harness.")
    parser.add_argument("--raw", default="data/raw/dev-v1.1.json", help="SQuAD dev JSON.")
    parser.add_argument(
        "--corpus",
        nargs="*",
        default=None,
        help="Additional corpus JSON files, e.g. data/raw/train-v1.1.json.",
    )
    parser.add_argument("--out", default="data/processed", help="Processed output directory.")
    parser.add_argument("--n-questions", type=int, default=1000, help="P1 sample size.")
    parser.add_argument("--seed", type=int, default=20261115, help="Sampling seed.")
    parser.add_argument("--passage-words", type=int, default=70, help="Words per passage.")
    parser.add_argument(
        "--context-word-limit", type=int, default=256, help="Context truncation limit."
    )
    parser.add_argument(
        "--splits-out",
        default="data/splits/squad_splits.json",
        help="Tracked ID split JSON.",
    )
    parser.add_argument(
        "--manifest",
        default="data/manifest.json",
        help="Tracked manifest to update.",
    )
    parser.add_argument(
        "--split-sizes",
        default=None,
        help="JSON object overriding the default split sizes.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    raw = Path(args.raw)
    if not raw.is_file():
        print(
            f"00_prepare_data: missing {raw}.\n"
            "Download SQuAD v1.1 from the official source, record its license, and place "
            "dev-v1.1.json under data/raw/. Do not commit raw data.",
            file=sys.stderr,
        )
        return 2
    corpus = [Path(path) for path in args.corpus] if args.corpus else None
    split_sizes = json.loads(args.split_sizes) if args.split_sizes else None
    manifest_out = prepare_squad(
        raw,
        Path(args.out),
        n_questions=args.n_questions,
        seed=args.seed,
        passage_words=args.passage_words,
        context_word_limit=args.context_word_limit,
        corpus_paths=corpus,
        split_sizes=split_sizes,
        splits_out=Path(args.splits_out),
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
    print(f"Splits: {args.splits_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
