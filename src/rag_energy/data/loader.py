"""Load a prepared SQuAD question/corpus split.

The parquet files stay git-ignored. The tracked split file fixes the question
order, so a rerun sees the same sequence regardless of parquet row order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUESTION_COLUMNS = ("qid", "question", "gold", "wh_type", "context_id", "title")
CORPUS_COLUMNS = ("passage_id", "context_id", "text")


@dataclass(frozen=True)
class SquadSplit:
    """One named question split plus the retrieval corpus."""

    name: str
    ids: tuple[str, ...]
    questions: Any
    corpus: Any


def load_squad_split(
    processed_dir: Path,
    split_name: str,
    limit: int | None = None,
) -> SquadSplit:
    """Load a named ID split and the full corpus in deterministic order."""
    processed_dir = Path(processed_dir)
    questions_path = processed_dir / "squad_questions.parquet"
    corpus_path = processed_dir / "squad_corpus.parquet"
    splits_path = processed_dir / "squad_splits.json"
    for path in (questions_path, corpus_path, splits_path):
        if not path.is_file():
            raise ValueError(f"prepared SQuAD file not found: {path}")

    split_document = json.loads(splits_path.read_text(encoding="utf-8"))
    splits = split_document.get("splits") if isinstance(split_document, dict) else None
    if not isinstance(splits, dict) or split_name not in splits:
        raise ValueError(f"split {split_name!r} not found in {splits_path}")
    raw_ids = splits[split_name]
    if not isinstance(raw_ids, list) or not raw_ids:
        raise ValueError(f"split {split_name!r} must be a non-empty list of IDs")
    ids = [str(value) for value in raw_ids]
    if any(not value for value in ids):
        raise ValueError(f"split {split_name!r} contains an empty ID")
    if len(set(ids)) != len(ids):
        raise ValueError(f"split {split_name!r} contains duplicate IDs")
    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError("limit must be a positive integer")
        ids = ids[:limit]

    import pandas as pd

    questions = pd.read_parquet(questions_path)
    corpus = pd.read_parquet(corpus_path)
    missing_columns = [column for column in QUESTION_COLUMNS if column not in questions]
    if missing_columns:
        raise ValueError(f"{questions_path}: missing columns {missing_columns}")
    missing_columns = [column for column in CORPUS_COLUMNS if column not in corpus]
    if missing_columns:
        raise ValueError(f"{corpus_path}: missing columns {missing_columns}")
    if not questions["qid"].is_unique:
        raise ValueError(f"{questions_path}: duplicate qids")
    missing = [qid for qid in ids if qid not in set(questions["qid"])]
    if missing:
        raise ValueError(f"split {split_name!r} references missing questions: {missing[:5]}")
    ordered = questions.set_index("qid").loc[list(ids)].reset_index()
    corpus = corpus.sort_values("passage_id").reset_index(drop=True)
    return SquadSplit(
        name=split_name,
        ids=tuple(ids),
        questions=ordered,
        corpus=corpus,
    )
