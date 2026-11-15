"""HotpotQA distractor preparation.

The distractor setting supplies 10 paragraphs per question, 2 gold and 8
distractors, so the depth grid is capped at 10. The powered run uses 500 dev
questions.

Sixty dev questions provide fewer than 10 paragraphs. They are excluded from
the sampling frame before sampling, so every prepared question has exactly 10
candidate paragraphs and ``k = 10`` means the same thing for every question.
The exclusion is a property of the upstream data, not of any outcome.
"""

from __future__ import annotations

import hashlib
import json
import random
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_energy.data.manifest import load_manifest, sha256_file

SPLIT_NAMES = ("hotpot",)
STRATA = ("bridge", "comparison")


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _seed_for(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
    return int(digest[:16], 16)


def _hash_ids(ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    temp.replace(path)


def _context_parts(context: Any) -> tuple[list[str], list[list[str]]]:
    """Normalize a parquet struct or an official JSON pair."""
    if isinstance(context, Mapping):
        titles = [str(value) for value in context.get("title", [])]
        sentences = [
            [str(sentence) for sentence in paragraph] for paragraph in context.get("sentences", [])
        ]
        return titles, sentences
    pairs = list(context or [])
    titles = [str(pair[0]) for pair in pairs]
    sentences = [[str(sentence) for sentence in pair[1]] for pair in pairs]
    return titles, sentences


def _supporting_titles(facts: Any) -> list[str]:
    if isinstance(facts, Mapping):
        return [str(value) for value in facts.get("title", [])]
    return [str(pair[0]) for pair in facts or []]


def _load_records(raw_path: Path) -> list[dict[str, Any]]:
    """Load the official distractor JSON or its Hugging Face parquet mirror."""
    suffix = raw_path.suffix.lower()
    if suffix == ".parquet":
        import pandas as pd

        frame = pd.read_parquet(raw_path)
        rows: Iterable[Mapping[str, Any]] = (row for row in frame.to_dict(orient="records"))
    elif suffix == ".json":
        document = json.loads(raw_path.read_text(encoding="utf-8"))
        if not isinstance(document, list):
            raise ValueError(f"{raw_path}: expected a JSON list of questions")
        rows = document
    else:
        raise ValueError(f"{raw_path}: expected a .json or .parquet file")

    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        qid = str(row.get("id", "")).strip()
        question = str(row.get("question", "")).strip()
        gold = str(row.get("answer", "")).strip()
        if not qid or not question or not gold:
            raise ValueError(f"invalid HotpotQA row: {row!r}")
        if qid in seen:
            raise ValueError(f"duplicate HotpotQA question id: {qid}")
        seen.add(qid)
        titles, sentences = _context_parts(row.get("context"))
        if len(titles) != len(sentences):
            raise ValueError(f"{qid}: title and paragraph counts differ")
        records.append(
            {
                "qid": qid,
                "question": question,
                "gold": gold,
                "type": str(row.get("type", "unknown")),
                "level": str(row.get("level", "unknown")),
                "titles": titles,
                "sentences": sentences,
                "gold_titles": sorted(set(_supporting_titles(row.get("supporting_facts")))),
            }
        )
    if not records:
        raise ValueError(f"{raw_path}: no questions found")
    return records


def _paragraph_count(record: Mapping[str, Any]) -> int:
    return len(record["titles"])


def _sampling_frame(records: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep questions with exactly 10 paragraphs and validated gold titles."""
    frame: list[dict[str, Any]] = []
    for record in records:
        if _paragraph_count(record) != 10:
            continue
        available = set(record["titles"])
        if not record["gold_titles"] or not set(record["gold_titles"]) <= available:
            continue
        frame.append(record)
    if not frame:
        raise ValueError("no HotpotQA questions with exactly 10 paragraphs")
    return frame


def _allocate(sizes: Mapping[str, int], n: int) -> dict[str, int]:
    """Largest-remainder allocation proportional to the stratum sizes."""
    total = sum(sizes.values())
    if n > total:
        raise ValueError(f"requested {n} questions but only {total} available")
    exact = {name: n * size / total for name, size in sizes.items()}
    allocated = {name: int(value) for name, value in exact.items()}
    remaining = n - sum(allocated.values())
    order = sorted(
        sizes,
        key=lambda name: (-(exact[name] - allocated[name]), name),
    )
    for name in order[:remaining]:
        allocated[name] += 1
    for name, size in sizes.items():
        if allocated[name] > size:
            raise ValueError(f"{name}: allocated more questions than available")
    return allocated


def _stratified_sample(frame: Sequence[dict[str, Any]], n: int, seed: int) -> list[dict[str, Any]]:
    if n <= 0:
        raise ValueError("n_questions must be positive")
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in frame:
        groups[str(record["type"])].append(record)
    for name, items in groups.items():
        items.sort(key=lambda item: item["qid"])
        random.Random(_seed_for(seed, name)).shuffle(items)
    allocated = _allocate({name: len(items) for name, items in groups.items()}, n)
    selected: list[dict[str, Any]] = []
    for name in sorted(groups):
        selected.extend(groups[name][: allocated[name]])
    selected.sort(key=lambda item: item["qid"])
    return selected


def prepare_hotpot(
    raw_path: Path,
    out_dir: Path,
    n_questions: int = 500,
    seed: int = 20261115,
    chunking: str = "whole_paragraph",
    passage_words: int = 0,
    splits_out: Path | None = None,
    manifest_path: Path | None = None,
) -> Path:
    """Prepare HotpotQA distractor dev into questions and a per-question corpus.

    The primary condition keeps the 10 provided paragraphs whole so that
    multi-hop evidence is not split: ``chunking="whole_paragraph"`` (the
    default) does not chunk. ``chunking="word"`` is opt-in; only then does
    ``passage_words`` apply, as the no-overlap word-chunk size.

    Outputs (git-ignored under ``data/processed/``):
      - ``hotpot_questions.parquet``: qid, question, gold, type, level,
        n_paragraphs, n_gold_paragraphs
      - ``hotpot_corpus.parquet``: passage_id, qid, title, text, is_gold,
        paragraph_index, n_words
      - ``hotpot_manifest.json``: counts, checksums, sampling frame, seed

    Returns:
        Path to the git-ignored ``hotpot_manifest.json``.
    """
    raw_path = Path(raw_path)
    out_dir = Path(out_dir)
    if chunking not in {"whole_paragraph", "word"}:
        raise ValueError("chunking must be 'whole_paragraph' or 'word'")
    if chunking == "word" and passage_words <= 0:
        raise ValueError("passage_words must be positive when chunking='word'")

    records = _load_records(raw_path)
    frame = _sampling_frame(records)
    selected = _stratified_sample(frame, n_questions, seed)

    from rag_energy.data.chunking import chunk_words

    questions: list[dict[str, Any]] = []
    passages: list[dict[str, Any]] = []
    for record in selected:
        qid = str(record["qid"])
        gold_titles = set(record["gold_titles"])
        for index, (title, sentences) in enumerate(
            zip(record["titles"], record["sentences"], strict=True)
        ):
            text = " ".join(sentence.strip() for sentence in sentences if sentence.strip())
            if not text:
                raise ValueError(f"{qid}: empty paragraph {title!r}")
            chunks = (
                [text] if chunking == "whole_paragraph" else chunk_words(text, size=passage_words)
            )
            for chunk_index, chunk in enumerate(chunks):
                passage_id = f"hotpot:{qid}:{index}:{chunk_index}"
                passages.append(
                    {
                        "passage_id": passage_id,
                        "qid": qid,
                        "title": title,
                        "text": chunk,
                        "is_gold": title in gold_titles,
                        "paragraph_index": index,
                        "chunk_index": chunk_index,
                        "n_words": len(chunk.split()),
                    }
                )
        questions.append(
            {
                "qid": qid,
                "question": str(record["question"]),
                "gold": str(record["gold"]),
                "type": str(record["type"]),
                "level": str(record["level"]),
                "n_paragraphs": len(record["titles"]),
                "n_gold_paragraphs": len(gold_titles),
            }
        )
    if not questions:
        raise ValueError("no questions selected")
    if not passages:
        raise ValueError("no passages produced")

    out_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    questions_path = out_dir / "hotpot_questions.parquet"
    corpus_path = out_dir / "hotpot_corpus.parquet"
    pd.DataFrame(
        questions,
        columns=[
            "qid",
            "question",
            "gold",
            "type",
            "level",
            "n_paragraphs",
            "n_gold_paragraphs",
        ],
    ).to_parquet(questions_path, index=False)
    pd.DataFrame(
        passages,
        columns=[
            "passage_id",
            "qid",
            "title",
            "text",
            "is_gold",
            "paragraph_index",
            "chunk_index",
            "n_words",
        ],
    ).to_parquet(corpus_path, index=False)

    ids = sorted(str(question["qid"]) for question in questions)
    split_payload = {
        "schema_version": 1,
        "dataset": "hotpot",
        "seed": seed,
        "n_questions_total": len(records),
        "n_questions_frame": len(frame),
        "strata": list(STRATA),
        "splits": {"hotpot": ids},
        "sha256": {"hotpot": _hash_ids(ids)},
    }
    split_path = out_dir / "hotpot_splits.json"
    _write_json(split_path, split_payload)
    if splits_out is not None:
        _write_json(Path(splits_out), split_payload)

    now = _utc_now()
    checksums = {
        "source_sha256": sha256_file(raw_path),
        "questions_sha256": sha256_file(questions_path),
        "corpus_sha256": sha256_file(corpus_path),
        "splits_sha256": sha256_file(split_path),
    }
    corpus_meta = {
        "construction": (
            "10 provided paragraphs per question (2 gold, 8 distractors), kept whole; "
            "no cross-question pooling"
            if chunking == "whole_paragraph"
            else f"10 provided paragraphs per question split into {passage_words}-word chunks"
        ),
        "n_contexts": len(questions),
        "n_passages": len(passages),
        "passage_words": passage_words if chunking == "word" else None,
        "retrieval_top_k": 10,
        "sampling_frame": (
            f"{len(frame)} of {len(records)} dev questions with exactly 10 paragraphs"
        ),
    }
    dataset_update = {
        "n_questions_total": len(records),
        "n_questions_used": len(questions),
        "corpus": corpus_meta,
        "checksums": checksums,
        "prepared_utc": now,
        "preparation_seed": seed,
        "status": "prepared",
        "notes": (
            "500 dev questions with exactly 10 provided paragraphs, stratified by "
            "question type (bridge/comparison). The split ID list is tracked in "
            "data/splits/hotpot_splits.json. BM25 indexes each question's 10 paragraphs "
            "separately; no cross-question pooling."
        ),
    }
    run_manifest = {
        "schema_version": 1,
        "generated_utc": now,
        "dataset": "hotpot",
        "counts": {
            "n_questions_total": len(records),
            "n_questions_frame": len(frame),
            "n_questions": len(questions),
            "n_passages": len(passages),
        },
        "corpus": corpus_meta,
        "split_sizes": {"hotpot": len(ids)},
        "checksums": checksums,
        "seed": seed,
    }
    manifest_out = out_dir / "hotpot_manifest.json"
    _write_json(manifest_out, run_manifest)

    if manifest_path is not None:
        tracked = load_manifest(Path(manifest_path))
        for dataset in tracked.get("datasets", []):
            if dataset.get("id") == "hotpot":
                dataset.update(dataset_update)
                break
        else:
            raise ValueError(f"{manifest_path}: no hotpot dataset entry")
        tracked["generated_utc"] = now
        _write_json(Path(manifest_path), tracked)

    return manifest_out
