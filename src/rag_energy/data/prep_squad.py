"""SQuAD v1.1 preparation.

Pilot protocol: 200 dev questions stratified over the 7 SQuAD wh-types; all
unique dev contexts (20,958) truncated to 256 words and chunked into 70-word
passages (45,651 in the pilot). The powered run uses 1,000 questions.

This module is a scaffold. ``prepare_squad`` documents the intended contract and
raises until the data pipeline is implemented in P0.
"""

from __future__ import annotations

from pathlib import Path


def prepare_squad(
    raw_path: Path,
    out_dir: Path,
    n_questions: int = 1000,
    seed: int = 20261115,
    passage_words: int = 70,
    context_word_limit: int = 256,
) -> Path:
    """Prepare SQuAD v1.1 dev into questions, corpus, and passages.

    Intended outputs (git-ignored under ``data/processed/``):
      - ``squad_questions.parquet``: qid, question, gold answer, wh-type
      - ``squad_corpus.parquet``: passage_id, context_id, text
      - ``squad_manifest.json``: counts, checksums, and the sampling seed

    The function must not write raw text outside ``out_dir`` and must never
    modify files under ``data/raw/``.
    """
    raise NotImplementedError(
        "prepare_squad is implemented in P0; see docs/IMPLEMENTATION_PLAN.md section 4."
    )
