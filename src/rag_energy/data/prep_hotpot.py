"""HotpotQA distractor preparation.

The distractor setting supplies 10 paragraphs per question, 2 gold and 8
distractors, so the depth grid is capped at 10. The powered run uses 500 dev
questions.

This module is a scaffold. ``prepare_hotpot`` documents the intended contract and
raises until the data pipeline is implemented in P2.
"""

from __future__ import annotations

from pathlib import Path


def prepare_hotpot(
    raw_path: Path,
    out_dir: Path,
    n_questions: int = 500,
    seed: int = 20261115,
    chunking: str = "whole_paragraph",
    passage_words: int = 70,
) -> Path:
    """Prepare HotpotQA distractor dev into questions and a per-question corpus.

    The primary condition keeps the 10 provided paragraphs whole so that
    multi-hop evidence is not split: ``chunking="whole_paragraph"`` (the
    default) does not chunk. ``chunking="word"`` is opt-in; only then does
    ``passage_words`` apply, as the no-overlap word-chunk size.

    Intended outputs (git-ignored under ``data/processed/``):
      - ``hotpot_questions.parquet``: qid, question, gold answer, type, level
      - ``hotpot_corpus.parquet``: passage_id, qid, title, text, is_gold
      - ``hotpot_manifest.json``: counts, checksums, and the sampling seed

    The corpus is per-question because the distractor setting is not a shared
    open-domain index. Do not pool paragraphs across questions.
    """
    raise NotImplementedError(
        "prepare_hotpot is implemented in P2; see docs/IMPLEMENTATION_PLAN.md section 6."
    )
