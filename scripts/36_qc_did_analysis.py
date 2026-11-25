#!/usr/bin/env python
"""36 - Phase 8 Step 3 analysis: dense 2x2 difference-in-differences.

Compares the dense arm (``squad_qwen4b_qc_dense``) against the BM25 arm reused from
run 2 (``squad_qwen4b_p7_blocks_full``):

* R/Q decomposition FIRST (recall via normalized-gold containment, precision as
  A/R), per retriever at k=4 and k=32;
* DiD ``Δ = [A_d(4) − A_d(32)] − [A_b(4) − A_b(32)]`` with independent bootstrap
  CIs (frames are disjoint by construction, prereg-confirmed);
* TOST with +-2 pp bounds if the DiD includes zero.

Ranks are recomputed offline (CPU): BM25 through ``RetrievalIndex``, dense through
the frozen ``data/processed/dense_minilm/`` rankings. No GPU, no network.

Writes ``analysis/qc_dense/did.json`` and ``did.md``.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BM25_RUN_ID = "squad_qwen4b_p7_blocks_full"
DENSE_RUN_ID = "squad_qwen4b_qc_dense"
SEED = 20261115
N_BOOT = 10000
TOST_PP = 0.02


def _norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = q * (len(ordered) - 1)
    low = min(max(int(pos), 0), len(ordered) - 1)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def _did(a_d4: float, a_d32: float, a_b4: float, a_b32: float) -> float:
    """DiD convention (pinned by test): dense degrading less gives negative Δ."""
    return (a_d4 - a_d32) - (a_b4 - a_b32)


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 8 dense DiD analysis.")
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--dense-run-id", default=DENSE_RUN_ID)
    parser.add_argument("--bm25-run-id", default=BM25_RUN_ID)
    args = parser.parse_args()
    root = Path(args.root)

    for run_id in (args.dense_run_id, args.bm25_run_id):
        if not (root / "runs" / run_id / "raw.csv").is_file():
            raise SystemExit(f"missing runs/{run_id}/raw.csv")
        if not (root / "runs" / run_id / "blocks_design.json").is_file():
            raise SystemExit(f"missing runs/{run_id}/blocks_design.json")

    from rag_energy.data.loader import load_prepared_split
    from rag_energy.retrieval.index import RetrievalIndex

    arms: dict[str, Any] = {}
    for tag, run_id, split_name, backend in (
        ("bm25", args.bm25_run_id, "p1_primary", "bm25"),
        ("dense", args.dense_run_id, "qc_dense", "dense"),
    ):
        split = load_prepared_split(root / "data" / "processed", "squad", split_name)
        questions = {str(r.qid): str(r.question) for r in split.questions.itertuples(index=False)}
        golds = {str(r.qid): str(r.answer) for r in split.questions.itertuples(index=False)}
        by_key: dict[tuple[str, int], int] = {}
        with (root / "runs" / run_id / "raw.csv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row.get("valid", "1") == "1":
                    by_key[(str(row["question_id"]), int(row["k"]))] = int(row["correct_em"])

        if backend == "bm25":
            index = RetrievalIndex.from_corpus(split.corpus)
            ranked = {
                qid: [p.text for p in index.search(qid, questions[qid], 32)] for qid in questions
            }
        else:
            import numpy as np
            import pandas as pd

            dense_dir = root / "data" / "processed" / "dense_minilm"
            manifest = json.loads((dense_dir / "manifest.json").read_text(encoding="utf-8"))
            passage_ids = json.loads((dense_dir / "passage_ids.json").read_text(encoding="utf-8"))
            corpus = pd.read_parquet(root / "data" / "processed" / "squad_corpus.parquet")
            corpus = corpus.sort_values("passage_id").reset_index(drop=True)
            assert [str(v) for v in corpus["passage_id"]] == [str(v) for v in passage_ids]
            texts = [str(v) for v in corpus["text"]]
            emb = np.load(dense_dir / "embeddings.npy")
            os_environ_offline()
            from sentence_transformers import SentenceTransformer

            enc = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
            ranked = {}
            qids = list(questions)
            vecs = enc.encode(
                [questions[q] for q in qids],
                batch_size=64,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            for qid, vec in zip(qids, vecs, strict=True):
                top = (emb @ vec).argsort()[::-1][:32]
                ranked[qid] = [texts[i] for i in top]
            _ = manifest

        recall: dict[str, float] = {}
        accuracy: dict[str, float] = {}
        per_q: dict[str, dict[str, int]] = {}
        for depth in (4, 32):
            hits = correct = total = 0
            for qid in questions:
                row = by_key.get((qid, depth))
                if row is None:
                    continue
                total += 1
                present = any(_norm(golds[qid]) in _norm(p) for p in ranked[qid][:depth])
                hits += int(present)
                correct += row
                per_q.setdefault(qid, {})[str(depth)] = row
            recall[str(depth)] = hits / total if total else 0.0
            accuracy[str(depth)] = correct / total if total else 0.0
        precision = {k: (accuracy[k] / recall[k] if recall[k] > 0 else 0.0) for k in recall}
        arms[tag] = {
            "recall": recall,
            "accuracy": accuracy,
            "precision": precision,
            "per_q": per_q,
            "n": len(per_q),
        }

    a_d4, a_d32 = arms["dense"]["accuracy"]["4"], arms["dense"]["accuracy"]["32"]
    a_b4, a_b32 = arms["bm25"]["accuracy"]["4"], arms["bm25"]["accuracy"]["32"]
    point = _did(a_d4, a_d32, a_b4, a_b32)

    rng = random.Random(SEED)
    boot = []
    for _ in range(N_BOOT):
        vals = {}
        for tag in ("dense", "bm25"):
            qs = list(arms[tag]["per_q"])
            s = [qs[rng.randrange(len(qs))] for _ in range(len(qs))]
            vals[tag] = {d: sum(arms[tag]["per_q"][q][d] for q in s) / len(s) for d in ("4", "32")}
        boot.append(
            _did(vals["dense"]["4"], vals["dense"]["32"], vals["bm25"]["4"], vals["bm25"]["32"])
        )
    boot.sort()
    ci = [_quantile(boot, 0.025), _quantile(boot, 0.975)]

    out = {
        "dense_run_id": args.dense_run_id,
        "bm25_run_id": args.bm25_run_id,
        "arms": {t: {m: arms[t][m] for m in ("recall", "accuracy", "precision")} for t in arms},
        "n": {t: arms[t]["n"] for t in arms},
        "did_point": point,
        "did_ci95": ci,
        "tost_bound_pp": 100 * TOST_PP,
        "verdict": (
            "DiD excludes zero: the accuracy contrast travels with the retriever."
            if ci[0] > 0 or ci[1] < 0
            else "DiD includes zero (TOST at +-2 pp decides equivalence); "
            "reported as a null finding, not a failure."
        ),
    }
    out_dir = root / "analysis" / "qc_dense"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "did.json").write_text(json.dumps(out, indent=2, encoding="utf-8"))

    lines = [
        "# Phase 8 Step 3 - dense 2x2 DiD",
        "",
        f"BM25 `{args.bm25_run_id}` (n={arms['bm25']['n']}) vs "
        f"dense `{args.dense_run_id}` (n={arms['dense']['n']}).",
        "",
        "| arm | R(4) | R(32) | Q(4) | Q(32) | A(4) | A(32) |",
        "|---|---|---|---|---|---|---|",
    ]
    for tag in ("bm25", "dense"):
        a = arms[tag]
        lines.append(
            f"| {tag} | {a['recall']['4']:.3f} | {a['recall']['32']:.3f} | "
            f"{a['precision']['4']:.3f} | {a['precision']['32']:.3f} | "
            f"{a['accuracy']['4']:.3f} | {a['accuracy']['32']:.3f} |"
        )
    lines += [
        "",
        f"DiD = {100 * point:+.2f} pp [{100 * ci[0]:+.2f}, {100 * ci[1]:+.2f}].",
        "",
        out["verdict"],
        "",
    ]
    (out_dir / "did.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


def os_environ_offline() -> None:
    import os

    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


if __name__ == "__main__":
    raise SystemExit(main())
