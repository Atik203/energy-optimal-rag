"""Tests for the exploratory inference layer."""

from __future__ import annotations

import math

import numpy as np
import pytest

from rag_energy.stats.inference import (
    bca_interval,
    bca_mean_difference,
    bca_savings,
    build_inference_payload,
    cluster_bootstrap,
    joint_question_bootstrap,
    mde,
    ni_exact_sensitivity,
    ni_score_test,
    paired_difference_sd,
    realized_power,
    required_n,
    tost,
)
from rag_energy.stats.p1 import noninferiority


def _paired(b: int, c: int, n: int) -> tuple[list[int], list[int]]:
    """Build paired correctness vectors with ``b`` candidate-only wins."""
    candidate = [1] * b + [0] * c + [1] * (n - b - c)
    reference = [0] * b + [1] * c + [1] * (n - b - c)
    return candidate, reference


def _row(
    qid: str,
    k: int,
    *,
    correct: int,
    j_total: float,
    valid: int = 1,
    context_id: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "run_id": "test",
        "question_id": qid,
        "question_order": 0,
        "k": k,
        "order_in_question": k,
        "nonce": "a" * 10,
        "correct_em": correct,
        "correct_lenient": correct,
        "f1": float(correct),
        "prediction": "x",
        "gold": "x",
        "j_gpu_raw": j_total,
        "j_gpu_calibrated": j_total,
        "j_retrieval_proxy": 1.0,
        "j_total": j_total,
        "latency_s": 1.0,
        "prompt_tokens": 10,
        "output_tokens": 1,
        "load_s": 0.0,
        "prefill_s": 0.1,
        "eval_s": 0.1,
        "gpu_temp_c": 60.0,
        "sm_clock_mhz": 1800,
        "power_mean_w": 50.0,
        "valid": valid,
        "invalid_reason": "",
    }
    if context_id is not None:
        row["context_id"] = context_id
    return row


def _dataset(
    n: int = 40,
    depths: tuple[int, ...] = (0, 1, 2, 4, 8, 16, 32),
    *,
    clustered: bool = False,
) -> list[dict]:
    rows: list[dict] = []
    for index in range(n):
        for k in depths:
            correct = int((index * 7 + k * 3) % 5 != 0)
            rows.append(
                _row(
                    f"q{index:03d}",
                    k,
                    correct=correct,
                    j_total=10.0 + 2.0 * k + 0.1 * index,
                    context_id=f"c{index % 4}" if clustered else None,
                )
            )
    return rows


# ---------------------------------------------------------------------------
# Score test
# ---------------------------------------------------------------------------


def test_score_test_reduces_to_mcnemar_z_at_zero_margin() -> None:
    candidate, reference = _paired(44, 87, 1000)

    result = ni_score_test(candidate, reference, margin=0.0)

    assert result["z"] == pytest.approx((44 - 87) / math.sqrt(131.0), rel=1e-12)
    assert result["p_value"] == pytest.approx(
        float(1.0 - 0.5 * (1.0 + math.erf((44 - 87) / math.sqrt(131.0) / math.sqrt(2.0)))),
        abs=1e-12,
    )


def test_score_test_tracks_the_paired_wald_test() -> None:
    candidate, reference = _paired(44, 87, 1000)

    score = ni_score_test(candidate, reference, margin=0.05)
    wald = noninferiority(candidate, reference, margin=0.05)

    # The score test uses the null-restricted variance, so it should be close
    # to but not identical to the Wald test at this sample size.
    assert score["z"] == pytest.approx(wald.z, abs=0.05)
    assert score["p_value"] == pytest.approx(wald.p_value, abs=0.02)
    assert score["non_inferior"] is False


def test_score_test_is_monotone_in_the_margin() -> None:
    candidate, reference = _paired(44, 87, 1000)

    p_values = [
        ni_score_test(candidate, reference, margin=margin)["p_value"]
        for margin in (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10)
    ]

    assert p_values == sorted(p_values, reverse=True)
    assert p_values[0] > 0.9
    assert p_values[-1] < 0.05


def test_score_test_restricted_mle_solves_the_profile_score_equation() -> None:
    candidate, reference = _paired(44, 87, 1000)

    result = ni_score_test(candidate, reference, margin=0.05)
    pi = result["restricted_discordance"]
    p_b = result["restricted_p_candidate_only"]
    p_c = result["restricted_p_reference_only"]
    b, c, n = 44, 87, 1000
    a = n - b - c

    # d/d pi of the profile log-likelihood must vanish at the restricted MLE.
    gradient = 0.5 * (b / p_b + c / p_c) - a / (1.0 - pi)
    assert gradient == pytest.approx(0.0, abs=1e-8)


def test_score_test_preserves_the_confirmation_verdict() -> None:
    candidate, reference = _paired(44, 87, 1000)

    result = ni_score_test(candidate, reference, margin=0.05)

    assert result["non_inferior"] is False
    assert result["p_value"] > 0.05


def test_score_test_handles_an_empty_discordant_cell() -> None:
    candidate, reference = _paired(0, 87, 1000)

    result = ni_score_test(candidate, reference, margin=0.05)

    assert result["p_value"] == 1.0
    assert result["non_inferior"] is False
    assert result["boundary_mle"] is True


def test_score_test_has_near_nominal_type_one_error() -> None:
    rng = np.random.default_rng(7)
    n = 200
    margin = 0.05
    discordance = 0.20
    p_b = (discordance - margin) / 2.0
    p_c = (discordance + margin) / 2.0
    rejections = 0
    replications = 400
    for _ in range(replications):
        draw = rng.multinomial(n, [p_b, p_c, 1.0 - discordance])
        candidate, reference = _paired(int(draw[0]), int(draw[1]), n)
        result = ni_score_test(candidate, reference, margin=margin)
        if result["p_value"] is not None and result["p_value"] <= 0.05:
            rejections += 1
    rate = rejections / replications
    assert 0.015 <= rate <= 0.10


def test_score_test_rejects_invalid_input() -> None:
    with pytest.raises(ValueError):
        ni_score_test([1, 0], [1], margin=0.05)
    with pytest.raises(ValueError):
        ni_score_test([2, 0], [1, 0], margin=0.05)


# ---------------------------------------------------------------------------
# Exact sensitivity
# ---------------------------------------------------------------------------


def test_exact_p_values_are_probabilities_and_do_not_change_the_verdict() -> None:
    candidate, reference = _paired(44, 87, 1000)

    result = ni_exact_sensitivity(candidate, reference, margin=0.05)

    assert 0.0 <= result["exact_unconditional_p"] <= 1.0
    assert 0.0 <= result["exact_conditional_p"] <= 1.0
    assert result["exact_unconditional_p"] > 0.05
    assert result["sensitive_to_verdict"] is False


def test_exact_test_is_conservative_relative_to_the_score_test() -> None:
    candidate, reference = _paired(44, 87, 1000)

    exact = ni_exact_sensitivity(candidate, reference, margin=0.05)
    score = ni_score_test(candidate, reference, margin=0.05)

    assert exact["exact_unconditional_p"] >= score["p_value"]
    assert exact["exact_conditional_p"] >= score["p_value"] - 1e-12


def test_exact_test_favours_clear_non_inferiority() -> None:
    candidate, reference = _paired(90, 10, 500)

    result = ni_exact_sensitivity(candidate, reference, margin=0.05)

    assert result["exact_unconditional_p"] < 0.01


def test_exact_test_rejects_a_clear_loss() -> None:
    candidate, reference = _paired(10, 90, 500)

    result = ni_exact_sensitivity(candidate, reference, margin=0.05)

    assert result["exact_unconditional_p"] > 0.5


def test_exact_test_with_no_discordant_pairs_is_undefined() -> None:
    candidate, reference = _paired(0, 0, 100)

    result = ni_exact_sensitivity(candidate, reference, margin=0.05)

    assert result["exact_unconditional_p"] is None
    assert result["sensitive_to_verdict"] is None


def test_exact_unconditional_p_matches_brute_force_enumeration() -> None:
    # Direct multinomial enumeration of the same rejection region, used to
    # validate the binomial-factorised kernel in _exact_unconditional_p.
    from rag_energy.stats.inference import _exact_unconditional_p

    b, c, n, margin = 5, 1, 8, 0.1

    def brute_force(prediscordance: float) -> float:
        p_b = (prediscordance - margin) / 2.0
        p_c = (prediscordance + margin) / 2.0
        p_a = 1.0 - prediscordance
        total = 0.0
        for bb in range(n + 1):
            for cc in range(n + 1 - bb):
                if bb - cc >= b - c:
                    counts = (bb, cc, n - bb - cc)
                    probs = (p_b, p_c, p_a)
                    if any(
                        count > 0 and prob <= 0 for count, prob in zip(counts, probs, strict=False)
                    ):
                        continue
                    log_mass = math.lgamma(n + 1) - sum(math.lgamma(count + 1) for count in counts)
                    log_mass += sum(
                        count * math.log(prob)
                        for count, prob in zip(counts, probs, strict=False)
                        if count > 0
                    )
                    total += math.exp(log_mass)
        return total

    values = [brute_force(point) for point in np.linspace(margin, 1.0, 401)]
    kernel_p, kernel_pi = _exact_unconditional_p(b, c, n, margin, grid=401, refine=True)

    assert kernel_p >= max(values) - 1e-12
    assert kernel_p == pytest.approx(max(values), abs=1e-6)
    assert margin <= kernel_pi <= 1.0


# ---------------------------------------------------------------------------
# TOST
# ---------------------------------------------------------------------------


def test_tost_equals_the_maximum_of_the_two_one_sided_tests() -> None:
    candidate, reference = _paired(44, 87, 1000)

    result = tost(candidate, reference, margin=0.05)

    assert result["p_tost"] == pytest.approx(max(result["p_lower"], result["p_upper"]))
    assert result["p_tost"] == pytest.approx(
        noninferiority(candidate, reference, margin=0.05).p_value
    )
    assert result["equivalent"] is False


def test_tost_declares_equivalence_inside_the_margin() -> None:
    candidate, reference = _paired(50, 50, 1000)

    result = tost(candidate, reference, margin=0.05)

    assert result["mean_diff"] == pytest.approx(0.0)
    assert result["equivalent"] is True
    assert result["p_tost"] == pytest.approx(0.0, abs=1e-6)
    assert result["lower_bound"] > -0.05
    assert result["upper_bound"] < 0.05


def test_tost_interval_agrees_with_the_equivalence_decision() -> None:
    candidate, reference = _paired(44, 87, 1000)

    for margin in (0.02, 0.05, 0.10):
        result = tost(candidate, reference, margin=margin)
        assert result["equivalent"] == result["equivalent_from_interval"]


def test_tost_rejects_non_positive_margin() -> None:
    candidate, reference = _paired(1, 1, 10)
    with pytest.raises(ValueError):
        tost(candidate, reference, margin=0.0)


# ---------------------------------------------------------------------------
# Power, required n, MDE
# ---------------------------------------------------------------------------


def test_paired_difference_sd_matches_the_observed_sample() -> None:
    candidate, reference = _paired(44, 87, 1000)
    differences = np.asarray(candidate, dtype=float) - np.asarray(reference, dtype=float)

    assert paired_difference_sd(0.131, -0.043) == pytest.approx(differences.std(ddof=0), rel=1e-9)


def test_realized_power_matches_the_normal_approximation() -> None:
    power = realized_power(n=1000, margin=0.05, true_diff=-0.043, alpha=0.05, discordance=0.131)

    se = math.sqrt(0.131 - 0.043**2) / math.sqrt(1000)
    expected = 0.5 * (1.0 + math.erf(((0.05 - 0.043) / se - 1.6448536269514722) / math.sqrt(2)))
    assert power == pytest.approx(expected, rel=1e-9)
    assert 0.10 < power < 0.20


def test_realized_power_increases_with_the_true_difference() -> None:
    powers = [
        realized_power(n=1000, margin=0.05, true_diff=value, discordance=0.131)
        for value in (0.0, -0.01, -0.02, -0.03, -0.043)
    ]
    assert powers == sorted(powers, reverse=True)


def test_required_n_inverts_realized_power() -> None:
    for power in (0.5, 0.8):
        needed = required_n(margin=0.05, true_diff=-0.03, power=power, discordance=0.131)
        assert needed is not None
        achieved = realized_power(
            n=needed, margin=0.05, true_diff=-0.03, alpha=0.05, discordance=0.131
        )
        assert achieved >= power - 0.01


def test_required_n_matches_the_registered_margin_frontier() -> None:
    # analysis/squad_qwen4b_p1/margin_frontier.json reports 7,138 pairs at the
    # 5 pp margin from the observed sample SD; the discordance formula must
    # agree to well under 1%.
    needed = required_n(margin=0.05, true_diff=-0.043, power=0.5, discordance=0.131)
    assert needed == pytest.approx(7138, rel=0.01)


def test_required_n_is_none_when_the_margin_is_consumed() -> None:
    assert required_n(margin=0.05, true_diff=-0.05, power=0.8, discordance=0.2) is None
    assert required_n(margin=0.05, true_diff=-0.08, power=0.8, discordance=0.2) is None


def test_required_n_and_mde_are_consistent() -> None:
    n = 1000
    target = mde(n=n, margin=0.05, power=0.8, discordance=0.131)

    assert target["mde_difference"] < 0.0
    assert target["mde_loss_pp"] == pytest.approx(-100.0 * target["mde_difference"])
    needed = required_n(
        margin=0.05, true_diff=target["mde_difference"], power=0.8, discordance=0.131
    )
    assert needed == pytest.approx(n, abs=2)


def test_mde_solves_the_discordance_power_equation() -> None:
    discordance = 0.131
    n = 1000
    result = mde(n=n, margin=0.05, power=0.5, discordance=discordance)
    difference = result["mde_difference"]
    scale = 1.6448536269514722 / math.sqrt(n)

    assert difference + 0.05 == pytest.approx(
        scale * paired_difference_sd(discordance, difference), rel=1e-9
    )


def test_power_helpers_reject_both_sd_and_discordance() -> None:
    with pytest.raises(ValueError):
        realized_power(n=10, margin=0.05, true_diff=0.0, sd=0.1, discordance=0.1)


# ---------------------------------------------------------------------------
# BCa
# ---------------------------------------------------------------------------


def test_bca_mean_difference_is_close_to_the_percentile_interval() -> None:
    rng = np.random.default_rng(3)
    differences = rng.choice([-1.0, 0.0, 1.0], size=500, p=[0.09, 0.87, 0.04])

    result = bca_mean_difference(differences, resamples=800, seed=11, alpha=0.05)

    assert result["lower"] < result["point"] < result["upper"]
    assert abs(result["lower"] - result["percentile_interval"]["lower"]) < 0.02
    assert abs(result["upper"] - result["percentile_interval"]["upper"]) < 0.02
    assert result["n_infinite"] == 0


def test_bca_acceleration_matches_the_brute_force_jackknife() -> None:
    rng = np.random.default_rng(5)
    values = rng.normal(1.0, 2.0, size=40)
    indices = np.arange(values.size)

    result = bca_interval(
        values.size, lambda index: float(values[index].mean()), resamples=200, seed=1
    )

    jackknife = np.array([values[np.delete(indices, i)].mean() for i in range(values.size)])
    deviations = jackknife - jackknife.mean()
    expected = float(np.sum(deviations**3)) / (6.0 * float(np.sum(deviations**2)) ** 1.5)

    assert result["acceleration"] == pytest.approx(expected, rel=1e-9)


def test_bca_is_reproducible_under_a_fixed_seed() -> None:
    differences = [0.0] * 60 + [1.0] * 10 + [-1.0] * 5

    first = bca_mean_difference(differences, resamples=300, seed=42)
    second = bca_mean_difference(differences, resamples=300, seed=42)

    assert first["lower"] == second["lower"]
    assert first["upper"] == second["upper"]


def test_bca_savings_reproduces_the_ratio_of_sums_point_estimate() -> None:
    candidate_j = [10.0, 12.0, 11.0, 13.0, 9.0]
    candidate_c = [1, 1, 0, 1, 1]
    reference_j = [20.0, 22.0, 21.0, 23.0, 19.0]
    reference_c = [1, 1, 1, 1, 1]

    result = bca_savings(candidate_j, candidate_c, reference_j, reference_c, resamples=200, seed=7)

    e_candidate = sum(candidate_j) / sum(candidate_c)
    e_reference = sum(reference_j) / sum(reference_c)
    assert result["point"] == pytest.approx(1.0 - e_candidate / e_reference)
    assert result["lower"] <= result["point"] <= result["upper"]
    assert result["estimand"].startswith("savings")


def test_bca_keeps_infinite_tails_explicit() -> None:
    # The candidate has one correct answer out of three, so resamples with no
    # correct candidate answer give E = inf and a savings of -inf.
    result = bca_savings(
        [1.0, 1.0, 1.0],
        [1, 0, 0],
        [1.0, 1.0, 1.0],
        [1, 1, 0],
        resamples=300,
        seed=3,
    )

    assert result["n_infinite"] > 0
    assert math.isinf(result["lower"])
    assert not math.isnan(result["upper"])


# ---------------------------------------------------------------------------
# Joint bootstrap
# ---------------------------------------------------------------------------


def test_joint_bootstrap_is_a_probability_partition() -> None:
    result = joint_question_bootstrap(_dataset(), resamples=300, seed=20261115)

    assert 0.0 <= result["p_joint"] <= 1.0
    assert result["p_joint"] <= result["p_non_inferior"] + 1e-12
    assert result["p_joint"] <= result["p_savings_floor"] + 1e-12
    assert result["p_joint"] >= result["p_joint_interior"] - 1e-12
    assert sum(result["p_k_optimal"].values()) == pytest.approx(1.0)
    assert result["resamples"] == 300
    assert result["seed"] == 20261115


def test_joint_bootstrap_point_estimates_match_the_descriptive_metrics() -> None:
    rows = _dataset()
    result = joint_question_bootstrap(rows, resamples=50, seed=1)

    accuracy_32 = sum(int(row["correct_em"]) for row in rows if int(row["k"]) == 32) / 40
    assert result["point"]["accuracy"]["32"] == pytest.approx(accuracy_32)
    assert result["n_pairs_point"] == 40
    assert result["paired_n"]["median"] == 40
    assert 0.0 <= result["point"]["savings"] <= 1.0


def test_joint_bootstrap_is_reproducible() -> None:
    first = joint_question_bootstrap(_dataset(), resamples=100, seed=99)
    second = joint_question_bootstrap(_dataset(), resamples=100, seed=99)

    assert first["p_joint"] == second["p_joint"]
    assert first["savings_interval"] == second["savings_interval"]


# ---------------------------------------------------------------------------
# Cluster bootstrap
# ---------------------------------------------------------------------------


def test_cluster_bootstrap_skips_when_the_column_is_absent() -> None:
    result = cluster_bootstrap(_dataset())

    assert result["supported"] is False
    assert result["status"] == "skipped"
    assert "context_id" in result["reason"]
    assert "context_id" not in result["columns_observed"]


def test_cluster_bootstrap_runs_when_the_column_is_present() -> None:
    rows = _dataset()
    for row in rows:
        row["context_id"] = f"c{int(row['question_id'][1:]) % 5}"

    result = cluster_bootstrap(rows, resamples=100, seed=5)

    assert result["supported"] is True
    assert result["status"] == "computed"
    assert result["n_clusters"] == 5
    assert result["unit"] == "cluster"
    assert 0.0 <= result["p_joint"] <= 1.0


# ---------------------------------------------------------------------------
# Payload
# ---------------------------------------------------------------------------


def test_payload_preserves_the_confirmatory_verdict_and_labels_the_layer() -> None:
    rows = _dataset()
    baseline = build_inference_payload(rows, run_id="test", resamples=20)
    design = baseline["design"]
    registered = {
        "primary": {
            "n_pairs": design["n_pairs"],
            "mean_diff": design["mean_diff"],
            "lower_bound": 0.0,
            "non_inferior": False,
        }
    }

    payload = build_inference_payload(rows, run_id="test", resamples=20, registered=registered)

    assert payload["layer"] == "exploratory/sensitivity"
    assert payload["preregistered_primary"]["role"] == "confirmatory, unchanged"
    assert payload["preregistered_primary"]["non_inferior"] is False
    assert payload["consistency_with_registered_analysis"]["consistent"] is False
    assert payload["cluster_bootstrap"]["status"] == "skipped"
    assert 4 <= len(payload["realized_power"]) <= 5
    assert any(
        abs(row["true_diff"] - payload["design"]["mean_diff"]) < 1e-9
        for row in payload["realized_power"]
    )


def test_payload_detects_a_consistent_registered_analysis() -> None:
    rows = _dataset()
    baseline = build_inference_payload(rows, run_id="test", resamples=20)
    design = baseline["design"]
    registered = {
        "primary": {
            "n_pairs": design["n_pairs"],
            "mean_diff": design["mean_diff"],
            "lower_bound": baseline["preregistered_primary"]["lower_bound"],
            "non_inferior": baseline["preregistered_primary"]["non_inferior"],
        }
    }

    payload = build_inference_payload(rows, run_id="test", resamples=20, registered=registered)

    assert payload["consistency_with_registered_analysis"]["consistent"] is True


def test_payload_requires_paired_questions() -> None:
    rows = [_row("q1", 4, correct=1, j_total=10.0)]

    with pytest.raises(ValueError):
        build_inference_payload(rows, run_id="test", resamples=10)
