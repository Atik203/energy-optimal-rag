"""SQuAD v1.1 preparation.

Pilot protocol: 200 dev questions stratified over the 7 SQuAD wh-types; all
unique contexts (20,958 in the pilot; train+dev) truncated to 256 words and
chunked into 70-word passages (45,651 in the pilot). The powered run uses 1,000
questions.

The corpus and the question sample are separate inputs. ``raw_path`` supplies
the questions and is included in the corpus; ``corpus_paths`` may add the SQuAD
train file so the retrieval corpus matches the pilot's full unique-context set.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rag_energy.data.chunking import chunk_words
from rag_energy.data.manifest import load_manifest, sha256_file

WH_TYPES = ("what", "when", "where", "which", "who", "why", "how")
WH_STRATA = (*WH_TYPES, "other")
_WH_RE = re.compile(r"\b(what|when|where|which|who|why|how)\b", re.IGNORECASE)
_SPLIT_NAMES = (
    "p0_golden",
    "p1_primary",
    "replication",
    "boundary",
    "context",
    "tax",
)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_squad(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"SQuAD file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict) or not isinstance(document.get("data"), list):
        raise ValueError(f"{path}: expected a SQuAD document with a 'data' list")
    return document


def _wh_type(question: str) -> str:
    match = _WH_RE.search(question)
    return match.group(1).lower() if match else "other"


def _context_id(text: str) -> str:
    return "squad:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _seed_for(seed: int, label: str) -> int:
    digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
    return int(digest[:16], 16)


def _collect_questions(document: dict[str, Any]) -> list[dict[str, str]]:
    questions: list[dict[str, str]] = []
    seen: set[str] = set()
    for article in document["data"]:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title", ""))
        for paragraph in article.get("paragraphs", []):
            if not isinstance(paragraph, dict):
                continue
            context = str(paragraph.get("context", ""))
            if not context.strip():
                continue
            context_id = _context_id(context)
            for qa in paragraph.get("qas", []):
                if not isinstance(qa, dict):
                    continue
                qid = str(qa.get("id", "")).strip()
                question = str(qa.get("question", "")).strip()
                if not qid or not question:
                    continue
                if qid in seen:
                    raise ValueError(f"duplicate SQuAD question id: {qid}")
                seen.add(qid)
                answers = qa.get("answers") or []
                if not answers or not isinstance(answers[0], dict):
                    raise ValueError(f"{qid}: no gold answer")
                gold = str(answers[0].get("text", "")).strip()
                if not gold:
                    raise ValueError(f"{qid}: empty gold answer")
                questions.append(
                    {
                        "qid": qid,
                        "question": question,
                        "gold": gold,
                        "wh_type": _wh_type(question),
                        "context_id": context_id,
                        "title": title,
                    }
                )
    if not questions:
        raise ValueError("no questions found in the SQuAD document")
    return questions


def _collect_contexts(document: dict[str, Any]) -> dict[str, dict[str, str]]:
    contexts: dict[str, dict[str, str]] = {}
    for article in document["data"]:
        if not isinstance(article, dict):
            continue
        title = str(article.get("title", ""))
        for paragraph in article.get("paragraphs", []):
            if not isinstance(paragraph, dict):
                continue
            text = str(paragraph.get("context", ""))
            if not text.strip():
                continue
            context_id = _context_id(text)
            contexts.setdefault(
                context_id,
                {"context_id": context_id, "title": title, "text": text},
            )
    return contexts


def _stratified_sample(
    records: Sequence[dict[str, str]],
    n: int,
    seed: int,
    label: str,
) -> list[dict[str, str]]:
    if n < 0:
        raise ValueError(f"{label}: sample size must be non-negative")
    if n > len(records):
        raise ValueError(f"{label}: requested {n} questions but only {len(records)} available")
    if n == 0:
        return []

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        groups[record["wh_type"]].append(record)
    for name, items in groups.items():
        items.sort(key=lambda item: item["qid"])
        random.Random(_seed_for(seed, name)).shuffle(items)

    names = sorted(groups)
    target = {name: n * len(groups[name]) / len(records) for name in names}
    allocated = {name: 0 for name in names}
    for _ in range(n):
        candidates = [name for name in names if allocated[name] < len(groups[name])]
        if not candidates:
            raise ValueError(f"{label}: not enough questions to fill the sample")
        name = max(
            candidates,
            key=lambda candidate: (
                target[candidate] - allocated[candidate],
                len(groups[candidate]),
                candidate,
            ),
        )
        allocated[name] += 1

    selected: list[dict[str, str]] = []
    for name in names:
        selected.extend(groups[name][: allocated[name]])
    selected.sort(key=lambda item: item["qid"])
    return selected


def _split_sizes(n_questions: int, overrides: Mapping[str, int] | None) -> dict[str, int]:
    if n_questions <= 0:
        raise ValueError("n_questions must be positive")
    sizes: dict[str, int] = {
        "p0_golden": 200,
        "p1_primary": n_questions,
        "replication": 500,
        "boundary": 200,
        "context": 200,
        "tax": 150,
    }
    if overrides:
        unknown = set(overrides) - set(_SPLIT_NAMES)
        if unknown:
            raise ValueError(f"unknown split names: {sorted(unknown)}")
        for name, value in overrides.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"{name}: split size must be a non-negative integer")
            sizes[name] = value
    if sizes["context"] != sizes["boundary"]:
        raise ValueError("context and boundary split sizes must match")
    return sizes


def _sample_splits(
    questions: Sequence[dict[str, str]],
    sizes: Mapping[str, int],
    seed: int,
) -> dict[str, list[str]]:
    p0 = _stratified_sample(questions, sizes["p0_golden"], seed, "p0_golden")
    p0_ids = {record["qid"] for record in p0}
    remaining = [record for record in questions if record["qid"] not in p0_ids]

    p1 = _stratified_sample(remaining, sizes["p1_primary"], seed + 1, "p1_primary")
    p1_ids = {record["qid"] for record in p1}
    p1_records = [record for record in remaining if record["qid"] in p1_ids]

    replication = _stratified_sample(p1_records, sizes["replication"], seed + 2, "replication")
    replication_ids = {record["qid"] for record in replication}
    after_replication = [record for record in p1_records if record["qid"] not in replication_ids]

    boundary = _stratified_sample(after_replication, sizes["boundary"], seed + 3, "boundary")
    boundary_ids = {record["qid"] for record in boundary}
    after_boundary = [record for record in after_replication if record["qid"] not in boundary_ids]

    tax = _stratified_sample(after_boundary, sizes["tax"], seed + 4, "tax")

    return {
        "p0_golden": sorted(p0_ids),
        "p1_primary": sorted(p1_ids),
        "replication": sorted(replication_ids),
        "boundary": sorted(boundary_ids),
        "context": sorted(boundary_ids),
        "tax": sorted(record["qid"] for record in tax),
    }


def _hash_ids(ids: Sequence[str]) -> str:
    return hashlib.sha256("\n".join(ids).encode("utf-8")).hexdigest()


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    temp.replace(path)


def _corpus_records(
    contexts: Mapping[str, Mapping[str, str]],
    passage_words: int,
    context_word_limit: int,
) -> list[dict[str, Any]]:
    passages: list[dict[str, Any]] = []
    for context_id in sorted(contexts):
        context = contexts[context_id]
        words = context["text"].split()
        truncated = " ".join(words[:context_word_limit])
        chunks = chunk_words(truncated, size=passage_words)
        for index, chunk in enumerate(chunks):
            passages.append(
                {
                    "passage_id": f"{context_id}:{index}",
                    "context_id": context_id,
                    "title": context["title"],
                    "chunk_index": index,
                    "text": chunk,
                    "n_words": len(chunk.split()),
                }
            )
    return passages


def prepare_squad(
    raw_path: Path,
    out_dir: Path,
    n_questions: int = 1000,
    seed: int = 20261115,
    passage_words: int = 70,
    context_word_limit: int = 256,
    corpus_paths: Sequence[Path] | None = None,
    split_sizes: Mapping[str, int] | None = None,
    splits_out: Path | None = None,
    manifest_path: Path | None = None,
) -> Path:
    """Prepare SQuAD v1.1 into questions, corpus, passages, and ID splits.

    Args:
        raw_path: SQuAD dev JSON; supplies the question population.
        out_dir: Git-ignored processed directory.
        n_questions: Primary (P1) sample size; default 1,000.
        seed: Sampling seed.
        passage_words: Words per passage.
        context_word_limit: Context truncation limit in words.
        corpus_paths: Files supplying retrieval contexts. Defaults to ``[raw_path]``;
            pass train and dev to reproduce the pilot's full unique-context corpus.
        split_sizes: Optional overrides for the six named split sizes.
        splits_out: Optional tracked JSON path for the ID lists.
        manifest_path: Optional tracked ``data/manifest.json`` to update.

    Returns:
        Path to the git-ignored ``squad_manifest.json``.
    """
    raw_path = Path(raw_path)
    out_dir = Path(out_dir)
    if passage_words <= 0:
        raise ValueError("passage_words must be positive")
    if context_word_limit <= 0:
        raise ValueError("context_word_limit must be positive")
    sizes = _split_sizes(n_questions, split_sizes)

    dev_document = _load_squad(raw_path)
    questions = _collect_questions(dev_document)

    corpus_files = [raw_path] if corpus_paths is None else [Path(path) for path in corpus_paths]
    contexts: dict[str, dict[str, str]] = {}
    for corpus_path in corpus_files:
        for context_id, context in _collect_contexts(_load_squad(corpus_path)).items():
            contexts.setdefault(context_id, context)
    if not contexts:
        raise ValueError("no contexts found in the corpus files")
    missing = sorted(
        {record["qid"] for record in questions if record["context_id"] not in contexts}
    )
    if missing:
        raise ValueError(f"{len(missing)} questions have contexts outside the corpus")

    splits = _sample_splits(questions, sizes, seed)
    passages = _corpus_records(contexts, passage_words, context_word_limit)
    if not passages:
        raise ValueError("no passages produced")

    out_dir.mkdir(parents=True, exist_ok=True)
    import pandas as pd

    questions_path = out_dir / "squad_questions.parquet"
    corpus_path = out_dir / "squad_corpus.parquet"
    pd.DataFrame(
        questions,
        columns=["qid", "question", "gold", "wh_type", "context_id", "title"],
    ).to_parquet(questions_path, index=False)
    pd.DataFrame(
        passages,
        columns=["passage_id", "context_id", "title", "chunk_index", "text", "n_words"],
    ).to_parquet(corpus_path, index=False)

    now = _utc_now()
    split_payload = {
        "schema_version": 1,
        "dataset": "squad",
        "seed": seed,
        "n_questions_total": len(questions),
        "strata": list(WH_STRATA),
        "splits": splits,
        "sha256": {name: _hash_ids(ids) for name, ids in splits.items()},
    }
    split_path = out_dir / "squad_splits.json"
    _write_json(split_path, split_payload)
    if splits_out is not None:
        _write_json(Path(splits_out), split_payload)

    checksums = {
        "source_sha256": sha256_file(raw_path),
        "questions_sha256": sha256_file(questions_path),
        "corpus_sha256": sha256_file(corpus_path),
        "splits_sha256": sha256_file(split_path),
        "corpus_sources": {path.name: sha256_file(path) for path in corpus_files},
    }
    corpus_meta = {
        "construction": (
            f"unique contexts truncated to {context_word_limit} words, chunked into "
            f"{passage_words}-word passages, no overlap"
        ),
        "n_contexts": len(contexts),
        "n_passages": len(passages),
        "passage_words": passage_words,
        "context_word_limit": context_word_limit,
        "retrieval_top_k": 32,
    }
    dataset_update = {
        "n_questions_total": len(questions),
        "n_questions_used": sizes["p1_primary"],
        "corpus": corpus_meta,
        "checksums": checksums,
        "prepared_utc": now,
        "preparation_seed": seed,
        "status": "prepared",
        "notes": (
            "P0 golden, P1 primary, replication, boundary/context, and tax IDs are "
            "tracked in data/splits/squad_splits.json. P0 is disjoint from P1."
        ),
    }
    run_manifest = {
        "schema_version": 1,
        "generated_utc": now,
        "dataset": "squad",
        "counts": {
            "n_questions": len(questions),
            "n_contexts": len(contexts),
            "n_passages": len(passages),
            "n_questions_used": sizes["p1_primary"],
        },
        "split_sizes": {name: len(ids) for name, ids in splits.items()},
        "checksums": checksums,
        "seed": seed,
    }
    manifest_out = out_dir / "squad_manifest.json"
    _write_json(manifest_out, run_manifest)

    if manifest_path is not None:
        tracked = load_manifest(Path(manifest_path))
        for dataset in tracked.get("datasets", []):
            if dataset.get("id") == "squad":
                dataset.update(dataset_update)
                break
        else:
            raise ValueError(f"{manifest_path}: no squad dataset entry")
        tracked["generated_utc"] = now
        _write_json(Path(manifest_path), tracked)

    return manifest_out
