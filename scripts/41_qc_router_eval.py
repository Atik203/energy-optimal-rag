#!/usr/bin/env python
"""41 - Router once-only eval CIs + stop-rule adjudication (CPU only).

Uses the frozen threshold from analysis/qc_router/select.json and the
qc_router eval run. No re-tuning. Shared-resample paired bootstrap (10k,
seed 20261115) for the accuracy gap, policy capture, and accuracy
difference; TOST with +-2pp bounds for the null accuracy claim.

Stop rule (prereg s7): eval Gap = A_oracle{1,4} - A(4) < 10% -> report the
null with static baselines only.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "qc_router_policy", ROOT / "scripts" / "40_qc_router_policy.py"
)
assert _spec is not None and _spec.loader is not None
_mod = _ilu.module_from_spec(_spec)
sys.modules["qc_router_policy"] = _mod
_spec.loader.exec_module(_mod)

from rag_energy.data.loader import load_prepared_split  # noqa: E402
from rag_energy.retrieval.index import RetrievalIndex  # noqa: E402
from rag_energy.stats.policy import (  # noqa: E402
    _predict_correct,
    evaluate_policy,
    matched_oracle_evaluation,
    oracle_gain_pct,
    static_evaluation,
)

SEED = 20261115
N_BOOT = 10000
TOST_PP = 2.0
STOP_GAP = 0.10


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    pos = q * (len(ordered) - 1)
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Router eval CIs (CPU).")
    parser.add_argument("--root", default=str(ROOT))
    args = parser.parse_args(argv)
    root = Path(args.root)

    frozen_thr = float(
        json.loads((root / "analysis" / "qc_router" / "select.json").read_text())["threshold"]
    )
    eval_split = load_prepared_split(root / "data" / "processed", "squad", "qc_router_eval")
    eval_q = {str(r.qid): str(r.question) for r in eval_split.questions.itertuples(index=False)}
    eval_wh = {str(r.qid): str(r.wh_type) for r in eval_split.questions.itertuples(index=False)}
    eval_correct = _mod._load_correct(root / "runs" / "squad_qwen4b_qc_router" / "raw.csv")
    eval_fixed = _mod._fixed_costs(root / "runs" / "squad_qwen4b_qc_router" / "blocks_design.json")
    p1_split = load_prepared_split(root / "data" / "processed", "squad", "p1_primary")
    index = RetrievalIndex.from_corpus(p1_split.corpus)
    examples = _mod._examples(
        list(eval_split.ids), eval_q, eval_wh, eval_correct, eval_fixed, index
    )

    # Retrain on P1 exactly as in select (deterministic, same seed) — no eval labels used.
    p1_q = {str(r.qid): str(r.question) for r in p1_split.questions.itertuples(index=False)}
    p1_wh = {str(r.qid): str(r.wh_type) for r in p1_split.questions.itertuples(index=False)}
    p1_correct = _mod._load_correct(root / "runs" / "squad_qwen4b_p1" / "raw.csv")
    train = _mod._examples(list(p1_split.ids), p1_q, p1_wh, p1_correct, {1: 1.0, 4: 1.0}, index)
    from rag_energy.stats.policy import train_policy

    policy = train_policy(train, train)

    n = len(examples)
    oracle_hit = [1 if (e.correct_by_depth[1] or e.correct_by_depth[4]) else 0 for e in examples]
    gap_point = sum(oracle_hit) / n - sum(e.correct_by_depth[4] for e in examples) / n

    rng = random.Random(SEED)
    gap_bs: list[float] = []
    cap_bs: list[float] = []
    acc_bs: list[float] = []
    for _ in range(N_BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        samp = [examples[i] for i in idx]
        oh = sum(1 for e in samp if e.correct_by_depth[1] or e.correct_by_depth[4]) / n
        a4 = sum(e.correct_by_depth[4] for e in samp) / n
        gap_bs.append(oh - a4)
        pol = evaluate_policy(policy, samp, 4, frozen_thr)
        sta = static_evaluation(samp, 4)
        mo = matched_oracle_evaluation(samp, 4, allow_abstention=False)
        ge = oracle_gain_pct(float(sta["energy_per_correct"]), float(mo["energy_per_correct"]))
        sv = 100.0 * (1.0 - float(pol["energy_per_correct"]) / float(sta["energy_per_correct"]))
        cap_bs.append(100.0 * sv / ge if ge > 0 else float("nan"))
        acc_bs.append(pol["accuracy"] - sta["accuracy"])

    pol_pt = evaluate_policy(policy, examples, 4, frozen_thr)
    sta_pt = static_evaluation(examples, 4)
    mo_pt = matched_oracle_evaluation(examples, 4, allow_abstention=False)
    gap_energy = oracle_gain_pct(
        float(sta_pt["energy_per_correct"]), float(mo_pt["energy_per_correct"])
    )
    saving = 100.0 * (
        1.0 - float(pol_pt["energy_per_correct"]) / float(sta_pt["energy_per_correct"])
    )
    capture = 100.0 * saving / gap_energy if gap_energy > 0 else float("nan")
    acc_diff_pp = 100.0 * (float(pol_pt["accuracy"]) - float(sta_pt["accuracy"]))

    # Depth histogram + eval AUCs.
    from collections import Counter

    depths = []
    for e in examples:
        d = None
        for k in (1, 4):
            if _predict_correct(policy, e, k) >= frozen_thr:
                d = k
                break
        depths.append(4 if d is None else d)
    hist = {str(k): v for k, v in sorted(Counter(depths).items())}

    def _auc(depth: int) -> float:
        scores = [_predict_correct(policy, e, depth) for e in examples]
        labels = [int(e.correct_by_depth[depth]) for e in examples]
        pairs = sorted(zip(scores, labels, strict=True))
        n1, n0 = sum(labels), len(labels) - sum(labels)
        if n1 == 0 or n0 == 0:
            return float("nan")
        rs = sum(i + 1 for i, (_, y) in enumerate(pairs) if y == 1)
        return (rs - n1 * (n1 + 1) / 2) / (n1 * n0)

    stop_fired = bool(gap_point < STOP_GAP)
    tost_low = _quantile(acc_bs, 0.025) * 100.0
    tost_high = _quantile(acc_bs, 0.975) * 100.0
    payload = {
        "threshold": frozen_thr,
        "n_eval": n,
        "gap_pp": {
            "point": gap_point * 100.0,
            "ci95": [_quantile(gap_bs, 0.025) * 100.0, _quantile(gap_bs, 0.975) * 100.0],
        },
        "capture_pct": {
            "point": capture,
            "ci95": [_quantile(cap_bs, 0.025), _quantile(cap_bs, 0.975)],
        },
        "acc_diff_pp": {"point": acc_diff_pp, "ci95": [tost_low, tost_high]},
        "tost_inside_pm2pp": bool(tost_low > -TOST_PP and tost_high < TOST_PP),
        "gap_energy_pct": gap_energy,
        "policy_saving_pct": saving,
        "depth_histogram": hist,
        "auc_k1": _auc(1),
        "auc_k4": _auc(4),
        "stop_rule_fired": stop_fired,
        "g8_router": "null-finding" if (stop_fired or capture < 30.0) else "pass",
    }
    out = root / "analysis" / "qc_router" / "eval_ci.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"gap={gap_point * 100:.2f}pp capture={capture:.2f}% acc_diff={acc_diff_pp:+.2f}pp stop={stop_fired}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
