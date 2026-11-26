#!/usr/bin/env python
"""41 - Router once-only eval CIs + stop-rule adjudication (CPU only).

Uses the frozen threshold from analysis/qc_router/select.json and the
qc_router eval run. No re-tuning: the threshold is read, never searched.

Design note (why this is fast): every per-question decision is computed
**once** and cached as an integer depth. The bootstrap then resamples index
arrays over precomputed correctness/energy vectors. The earlier version called
sklearn ``predict_proba`` inside the resample loop (10k x 2k calls) and ran for
hours; this version is O(n) per resample and finishes in seconds.

Energy convention (fixed costs, R5 correction): each depth carries one block
mean J per query, so energy is a count-weighted sum -- never a per-query window.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("qc_router_policy", ROOT / "scripts" / "40_qc_router_policy.py")
assert _spec is not None and _spec.loader is not None
_pol = _ilu.module_from_spec(_spec)
sys.modules["qc_router_policy"] = _pol
_spec.loader.exec_module(_pol)

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.policy import _predict_correct, train_policy  # noqa: E402

SEED = 20261115
N_BOOT = 10000
TOST_PP = 2.0
STOP_GAP = 0.10
STATIC_DEPTH = 4
K1 = 1


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = q * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def _auc(scores: list[float], labels: list[int]) -> float:
    pairs = sorted(zip(scores, labels, strict=True))
    n1 = sum(labels)
    n0 = len(labels) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    rank_sum = sum(i + 1 for i, (_, y) in enumerate(pairs) if y == 1)
    return (rank_sum - n1 * (n1 + 1) / 2) / (n1 * n0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Router eval CIs (CPU).")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root)

    out_dir = root / "analysis" / "qc_router"
    if not out_dir.is_dir():
        raise SystemExit(f"missing {out_dir}; run --phase select-only first")
    frozen_thr = float(json.loads((out_dir / "select.json").read_text(encoding="utf-8"))["threshold"])

    eval_blocks = root / "runs" / "squad_qwen4b_qc_router" / "blocks_design.json"
    eval_raw = root / "runs" / "squad_qwen4b_qc_router" / "raw.csv"
    for p in (eval_blocks, eval_raw):
        if not p.is_file():
            raise SystemExit(f"missing {p}")

    fixed = _pol._fixed_costs(eval_blocks)
    eval_split = load_prepared_split(root / "data" / "processed", "squad", "qc_router_eval")
    eval_q = {str(r.qid): str(r.question) for r in eval_split.questions.itertuples(index=False)}
    eval_wh = {str(r.qid): str(r.wh_type) for r in eval_split.questions.itertuples(index=False)}
    eval_correct = _pol._load_correct(eval_raw)

    p1_split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    index = RetrievalIndex.from_corpus(p1_split.corpus)

    # Retrain exactly as in select (deterministic seed, P1 labels only).
    p1_q = {str(r.qid): str(r.question) for r in p1_split.questions.itertuples(index=False)}
    p1_wh = {str(r.qid): str(r.wh_type) for r in p1_split.questions.itertuples(index=False)}
    p1_correct = _pol._load_correct(root / "runs" / "squad_qwen4b_p1" / "raw.csv")
    train = _pol._examples(list(p1_split.ids), p1_q, p1_wh, p1_correct, {1: 1.0, 4: 1.0}, index)
    policy = train_policy(train, train)

    examples = _pol._examples(list(eval_split.ids), eval_q, eval_wh, eval_correct, fixed, index)
    n = len(examples)

    # ---- precompute every decision once ----
    pol_depth: list[int] = []
    pol_score_k1: list[float] = []
    pol_score_k4: list[float] = []
    c_pol: list[int] = []
    c_static: list[int] = []
    c_k1: list[int] = []
    oracle_hit: list[int] = []
    for e in examples:
        k1 = float(_predict_correct(policy, e, K1))
        k4 = float(_predict_correct(policy, e, STATIC_DEPTH))
        depth = K1 if k1 >= frozen_thr else STATIC_DEPTH
        pol_depth.append(depth)
        pol_score_k1.append(k1)
        pol_score_k4.append(k4)
        c_pol.append(int(e.correct_by_depth[depth]))
        c_static.append(int(e.correct_by_depth[STATIC_DEPTH]))
        c_k1.append(int(e.correct_by_depth[K1]))
        oracle_hit.append(1 if (e.correct_by_depth[K1] or e.correct_by_depth[STATIC_DEPTH]) else 0)

    j_by_depth = {K1: float(fixed[K1]), STATIC_DEPTH: float(fixed[STATIC_DEPTH])}

    def stats(idx: list[int]) -> tuple[float, float, float, float, float, float]:
        """Gap, capture, acc-diff for one resample. Pure integer/float math."""
        nj = n
        a4 = sum(c_static[i] for i in idx) / nj
        ao = sum(oracle_hit[i] for i in idx) / nj
        gap = ao - a4
        # policy energy per correct at fixed costs
        jp = sum(j_by_depth[pol_depth[i]] for i in idx)
        cp = sum(c_pol[i] for i in idx)
        js = sum(j_by_depth[STATIC_DEPTH] for i in idx)
        cs = sum(c_static[i] for i in idx)
        if cp == 0 or cs == 0:
            return gap, float("nan"), float("nan"), float("nan"), a4, 0.0
        ep = jp / cp
        es = js / cs
        saving = 100.0 * (1.0 - ep / es)
        # matched-accuracy oracle at fixed costs: cheapest upgrades only
        base = sum(min(j_by_depth[K1], j_by_depth[STATIC_DEPTH]) for _ in idx)
        upgrade = j_by_depth[STATIC_DEPTH] - j_by_depth[K1]
        gainers = [i for i in idx if (c_k1[i] == 0 and c_static[i] == 1)]
        need = cs
        correct_k1 = sum(c_k1[i] for i in idx)
        extra_needed = max(0, need - correct_k1)
        mo_j = base + upgrade * min(extra_needed, len(gainers))
        mo_ep = mo_j / cs if cs else float("nan")
        gap_energy = 100.0 * (1.0 - mo_ep / es) if es else float("nan")
        capture = 100.0 * saving / gap_energy if gap_energy and gap_energy > 0 else float("nan")
        acc_diff = 100.0 * (cp / nj - cs / nj)
        return gap, capture, acc_diff, saving, a4, gap_energy

    point = stats(list(range(n)))

    rng = random.Random(SEED)
    gaps: list[float] = []
    caps: list[float] = []
    accs: list[float] = []
    for _ in range(N_BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        g, cap, ad, _sv, _a4, _ge = stats(idx)
        gaps.append(g * 100.0)
        if cap == cap:
            caps.append(cap)
        accs.append(ad)

    gap_pt = point[0] * 100.0
    cap_pt = point[1]
    acc_pt = point[2]
    stop_fired = bool(point[0] < STOP_GAP)

    payload = {
        "threshold": frozen_thr,
        "n_eval": n,
        "gap_pp": {"point": gap_pt, "ci95": [_quantile(gaps, 0.025), _quantile(gaps, 0.975)]},
        "capture_pct": {"point": cap_pt, "ci95": [_quantile(caps, 0.025), _quantile(caps, 0.975)] if caps else None},
        "acc_diff_pp": {"point": acc_pt, "ci95": [_quantile(accs, 0.025), _quantile(accs, 0.975)]},
        "policy_saving_pct": point[3],
        "gap_energy_pct": point[5],
        "depth_histogram": {str(k): v for k, v in sorted(Counter(pol_depth).items())},
        "mean_depth": sum(pol_depth) / n,
        "auc_k1": _auc(pol_score_k1, c_k1),
        "auc_k4": _auc(pol_score_k4, c_static),
        "fixed_j_per_query": {str(k): v for k, v in fixed.items()},
        "stop_rule_fired": stop_fired,
        "g8_router_verdict": "pass" if (not stop_fired and cap_pt >= 30.0) else "null-finding",
        "seed": SEED,
        "n_boot": N_BOOT,
    }
    (out_dir / "eval_ci.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"gap      {gap_pt:6.2f} pp  [{payload['gap_pp']['ci95'][0]:.2f}, {payload['gap_pp']['ci95'][1]:.2f}]")
    print(f"capture  {cap_pt:6.2f} %")
    print(f"acc diff {acc_pt:+6.2f} pp")
    print(f"mean depth {payload['mean_depth']:.3f}  hist {payload['depth_histogram']}")
    print(f"stop rule fired: {stop_fired}  ->  {payload['g8_router_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
