#!/usr/bin/env python
"""31 - Phase 8 dense ranking precompute (CPU only).

Encodes the 45,651 corpus passages with ``sentence-transformers/all-MiniLM-L6-v2``
taken from the local Hugging Face cache and writes frozen dense rankings for the
Phase 8 dense-vs-BM25 comparison (Step 3 of ``docs/PHASE8_PLAN.md``).

Rules:

* Offline mode: ``HF_HUB_OFFLINE=1`` / ``TRANSFORMERS_OFFLINE=1`` are set before
  any model import, and the encoder is loaded with no network access.
* No download: the script refuses to run when the model directory is absent
  from the local cache instead of fetching weights.
* Frozen output: embeddings, passage ids, and a manifest carrying the model
  revision hash are written once; reruns refuse to overwrite unless ``--force``
  is given, and the revision hash is recorded in the prereg.

Importing this module is dependency-light (stdlib only). All heavy imports
(sentence-transformers, numpy, corpus loader) happen inside ``main()`` or the
encode helper so unit tests exercise the pure path without a model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
REPO_DIR_NAME = "models--sentence-transformers--all-MiniLM-L6-v2"
DEFAULT_CACHE_DIRS = (
    Path(r"G:\SmartScan-Cache\hf\hub"),
    Path.home() / ".cache" / "huggingface" / "hub",
)
EXPECTED_PASSAGES = 45_651


def candidate_cache_dirs(explicit: str | None = None, extra: list[str] | None = None) -> list[Path]:
    """Ordered candidate locations for the Hugging Face hub cache."""
    dirs: list[Path] = []
    if explicit:
        dirs.append(Path(explicit))
    if extra:
        dirs.extend(Path(d) for d in extra)
    env = os.environ.get("HF_HUB_CACHE") or os.environ.get("HUGGINGFACE_HUB_CACHE")
    if env:
        dirs.append(Path(env))
    dirs.extend(DEFAULT_CACHE_DIRS)
    seen: list[Path] = []
    for candidate in dirs:
        if candidate not in seen:
            seen.append(candidate)
    return seen


def resolve_model_dir(explicit: str | None = None, extra: list[str] | None = None) -> Path:
    """Return the cached snapshot directory for the dense encoder.

    Raises ``FileNotFoundError`` when no candidate cache holds the model, so
    the caller fails closed instead of downloading weights.
    """
    tried: list[str] = []
    for cache in candidate_cache_dirs(explicit, extra):
        repo = cache / REPO_DIR_NAME
        tried.append(str(repo))
        if not repo.is_dir():
            continue
        snapshots = repo / "snapshots"
        if not snapshots.is_dir():
            continue
        hashes = sorted(p for p in snapshots.iterdir() if p.is_dir())
        if not hashes:
            continue
        # The hub cache keeps one directory per revision; prefer the refs/main
        # pointer when it resolves, otherwise take the lexicographically last
        # snapshot deterministically and record it in the manifest.
        ref = repo / "refs" / "main"
        if ref.is_file():
            pointed = ref.read_text(encoding="utf-8").strip()
            candidate = snapshots / pointed
            if candidate.is_dir():
                return candidate
        return hashes[-1]
    raise FileNotFoundError(
        f"dense encoder {MODEL_ID!r} not found in the local HF cache; "
        f"refusing to download. Tried: {'; '.join(tried)}"
    )


def read_revision_hash(snapshot_dir: Path) -> str:
    """Return the model revision hash recorded beside a hub snapshot."""
    # Layout: <cache>/<repo>/snapshots/<hash>/... with refs/main holding <hash>.
    repo = snapshot_dir.parents[1] if len(snapshot_dir.parents) >= 2 else snapshot_dir
    ref = repo / "refs" / "main"
    if ref.is_file() and ref.read_text(encoding="utf-8").strip():
        return ref.read_text(encoding="utf-8").strip()
    # Fall back to the snapshot directory name, which is the commit hash.
    return snapshot_dir.name


def offline_env() -> dict[str, str]:
    """Environment overrides forcing offline model loading."""
    return {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}


def build_manifest(
    *,
    model_id: str,
    revision_hash: str,
    snapshot_dir: str,
    n_passages: int,
    embedding_dim: int,
    normalize: bool,
    batch_size: int,
    created_utc: str,
) -> dict[str, Any]:
    """Frozen-output manifest: everything needed to reproduce the rankings."""
    return {
        "schema_version": 1,
        "model_id": model_id,
        "revision_hash": revision_hash,
        "snapshot_dir": snapshot_dir,
        "n_passages": n_passages,
        "embedding_dim": embedding_dim,
        "normalize_embeddings": normalize,
        "batch_size": batch_size,
        "offline": offline_env(),
        "created_utc": created_utc,
        "frozen": True,
    }


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 8 dense ranking precompute.")
    parser.add_argument(
        "--model-dir", default=None, help="Explicit snapshot dir; otherwise the HF cache is used."
    )
    parser.add_argument(
        "--cache-dir",
        action="append",
        default=None,
        help="Extra hub-cache location to search (repeatable).",
    )
    parser.add_argument(
        "--output",
        default="data/processed/dense_minilm",
        help="Directory for embeddings.npy, passage_ids.json, manifest.json.",
    )
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Store raw encoder outputs instead of L2-normalized rows.",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Encode only the first N passages (diagnostic)."
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing frozen output.")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)

    root = Path(args.root)
    for key, value in offline_env().items():
        os.environ.setdefault(key, value)

    # Fail closed before importing anything heavy: no cache, no run, no download.
    snapshot = Path(args.model_dir) if args.model_dir else resolve_model_dir(extra=args.cache_dir)
    if not snapshot.is_dir():
        raise SystemExit(
            f"model directory absent: {snapshot}; refusing to download "
            f"{MODEL_ID!r}. Point --model-dir at a cached snapshot."
        )
    revision = read_revision_hash(snapshot)
    print(f"model         {MODEL_ID}")
    print(f"snapshot      {snapshot}")
    print(f"revision      {revision}")

    import numpy as np
    import pandas as pd

    corpus_path = root / "data" / "processed" / "squad_corpus.parquet"
    if not corpus_path.is_file():
        raise SystemExit(f"prepared corpus not found: {corpus_path}")
    corpus = pd.read_parquet(corpus_path)
    for column in ("passage_id", "text"):
        if column not in corpus.columns:
            raise SystemExit(f"{corpus_path}: missing column {column!r}")
    # Frozen order: sorted by passage_id, so the precompute is deterministic
    # and reruns produce identical rankings.
    corpus = corpus.sort_values("passage_id").reset_index(drop=True)
    passage_ids = [str(v) for v in corpus["passage_id"]]
    texts = [str(t) for t in corpus["text"]]
    if args.limit is not None:
        passage_ids = passage_ids[: args.limit]
        texts = texts[: args.limit]
    elif len(passage_ids) != EXPECTED_PASSAGES:
        raise SystemExit(
            f"expected {EXPECTED_PASSAGES} passages, found {len(passage_ids)}; "
            "refusing to freeze a partial corpus"
        )
    print(f"passages      {len(passage_ids)}")

    out_dir = root / args.output if not Path(args.output).is_absolute() else Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    embeddings_path = out_dir / "embeddings.npy"
    if embeddings_path.exists() and not args.force:
        raise SystemExit(f"frozen output exists: {embeddings_path}; pass --force to overwrite")

    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(snapshot), device="cpu", trust_remote_code=False)
    normalize = not args.no_normalize
    embeddings = model.encode(
        texts,
        batch_size=args.batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=normalize,
    )
    embeddings = np.asarray(embeddings, dtype=np.float32)
    np.save(embeddings_path, embeddings)

    (out_dir / "passage_ids.json").write_text(json.dumps(passage_ids), encoding="utf-8")
    manifest = build_manifest(
        model_id=MODEL_ID,
        revision_hash=revision,
        snapshot_dir=str(snapshot),
        n_passages=len(passage_ids),
        embedding_dim=int(embeddings.shape[1]),
        normalize=normalize,
        batch_size=args.batch_size,
        created_utc=_utc_now(),
    )
    manifest["embeddings_sha256"] = _sha256_file(embeddings_path)
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(
        f"wrote {out_dir} ({embeddings.shape[0]}x{embeddings.shape[1]}, revision {revision[:12]})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
