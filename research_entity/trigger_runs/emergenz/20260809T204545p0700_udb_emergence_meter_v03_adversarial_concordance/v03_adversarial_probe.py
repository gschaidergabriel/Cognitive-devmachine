#!/usr/bin/env python3
"""Adversarial validation for the UnifiedDB Emergence Meter v0.2.

The probe attacks four assumptions that were not exercised by the v0.2 seed/OOD
sweep: independent ticks, a single time-series null, in-sample macro selection,
and additive counting of overlapping synergy estimates.  It also constructs an
endpoint-valid but path-invalid causal abstraction.

Only Python's standard library is used so the experiment can be replayed in a
minimal sandbox.  Results are synthetic method evidence, never live FRANK proof.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter
from pathlib import Path


def entropy(values: list[object]) -> float:
    counts = Counter(values)
    n = len(values)
    if not n:
        return 0.0
    return -sum((count / n) * math.log2(count / n) for count in counts.values())


def mutual_information(xs: list[object], ys: list[object]) -> float:
    return max(0.0, entropy(xs) + entropy(ys) - entropy(list(zip(xs, ys))))


def mmi_synergy(xs: list[int], ys: list[int], target: list[int]) -> float:
    joint = list(zip(xs, ys))
    return max(
        0.0,
        mutual_information(joint, target)
        - max(mutual_information(xs, target), mutual_information(ys, target)),
    )


def permutation_signflip_p(values: list[float], rng: random.Random, draws: int) -> float:
    observed = abs(statistics.fmean(values))
    extreme = 0
    for _ in range(draws):
        permuted_mean = abs(
            sum(value if rng.getrandbits(1) else -value for value in values) / len(values)
        )
        extreme += permuted_mean >= observed
    return (extreme + 1) / (draws + 1)


def exact_cluster_signflip_p(cluster_means: list[float]) -> float:
    observed = abs(statistics.fmean(cluster_means))
    extreme = 0
    total = 1 << len(cluster_means)
    for mask in range(total):
        value = abs(
            sum(
                item if (mask >> index) & 1 else -item
                for index, item in enumerate(cluster_means)
            )
            / len(cluster_means)
        )
        extreme += value >= observed - 1e-15
    return extreme / total


def clustered_pseudoreplication(
    seeds: int = 100,
    episodes: int = 12,
    ticks_per_episode: int = 80,
    draws: int = 199,
) -> dict:
    naive_rejects = 0
    cluster_rejects = 0
    paired = []
    for seed in range(seeds):
        rng = random.Random(10_000 + seed)
        clusters: list[list[float]] = []
        for _ in range(episodes):
            episode_offset = rng.gauss(0.0, 0.35)
            clusters.append(
                [episode_offset + rng.gauss(0.0, 0.02) for _ in range(ticks_per_episode)]
            )
        flat = [value for cluster in clusters for value in cluster]
        means = [statistics.fmean(cluster) for cluster in clusters]
        naive_p = permutation_signflip_p(flat, random.Random(20_000 + seed), draws)
        cluster_p = exact_cluster_signflip_p(means)
        naive_rejects += naive_p <= 0.05
        cluster_rejects += cluster_p <= 0.05
        if seed < 8:
            paired.append({"seed": seed, "naive_tick_p": naive_p, "episode_cluster_p": cluster_p})
    return {
        "null": "zero population effect with episode-level random effects",
        "seeds": seeds,
        "episodes_per_seed": episodes,
        "ticks_per_episode": ticks_per_episode,
        "naive_tick_false_positive_rate": naive_rejects / seeds,
        "episode_cluster_false_positive_rate": cluster_rejects / seeds,
        "examples": paired,
        "decision": "FAIL_V02_INDEPENDENT_TICK_ASSUMPTION"
        if naive_rejects > cluster_rejects * 2 + 5
        else "UNRESOLVED",
    }


def ar1(rng: random.Random, n: int, phi: float = 0.985, burn: int = 250) -> list[float]:
    value = rng.gauss(0.0, 1.0)
    out = []
    innovation_scale = math.sqrt(1.0 - phi * phi)
    for index in range(n + burn):
        value = phi * value + innovation_scale * rng.gauss(0.0, 1.0)
        if index >= burn:
            out.append(value)
    return out


def median_bits(values: list[float]) -> list[int]:
    middle = statistics.median(values)
    return [int(value > middle) for value in values]


def lag_mi(xs: list[int], ys: list[int]) -> float:
    return mutual_information(xs[:-1], ys[1:])


def time_null_sensitivity(seeds: int = 60, n: int = 400, draws: int = 199) -> dict:
    full_rejects = 0
    circular_rejects = 0
    disagreements = 0
    examples = []
    for seed in range(seeds):
        rng = random.Random(30_000 + seed)
        xs = median_bits(ar1(rng, n))
        ys = median_bits(ar1(rng, n))
        observed = lag_mi(xs, ys)
        full_null = []
        circular_null = []
        null_rng = random.Random(40_000 + seed)
        for _ in range(draws):
            shuffled = list(xs)
            null_rng.shuffle(shuffled)
            full_null.append(lag_mi(shuffled, ys))
            shift = null_rng.randrange(max(20, n // 10), n - max(20, n // 10))
            shifted = xs[shift:] + xs[:shift]
            circular_null.append(lag_mi(shifted, ys))
        full_p = (1 + sum(value >= observed for value in full_null)) / (draws + 1)
        circular_p = (1 + sum(value >= observed for value in circular_null)) / (draws + 1)
        full_sig = full_p <= 0.05
        circular_sig = circular_p <= 0.05
        full_rejects += full_sig
        circular_rejects += circular_sig
        disagreements += full_sig != circular_sig
        if seed < 8:
            examples.append(
                {
                    "seed": seed,
                    "observed_lag_mi_bits": observed,
                    "full_shuffle_p": full_p,
                    "circular_shift_p": circular_p,
                }
            )
    return {
        "null": "independent strongly autocorrelated AR(1) channels",
        "seeds": seeds,
        "full_shuffle_false_positive_rate": full_rejects / seeds,
        "autocorrelation_preserving_circular_false_positive_rate": circular_rejects / seeds,
        "null_model_disagreement_rate": disagreements / seeds,
        "examples": examples,
        "decision": "REQUIRE_NULL_ENSEMBLE_AND_ABSTAIN_ON_DISAGREEMENT",
    }


def random_nonconstant_map(rng: random.Random, states: int) -> tuple[int, ...]:
    while True:
        mapping = tuple(rng.getrandbits(1) for _ in range(states))
        if 0 in mapping and 1 in mapping:
            return mapping


def apply_map(values: list[int], mapping: tuple[int, ...]) -> list[int]:
    return [mapping[value] for value in values]


def macro_selection_bias(
    seeds: int = 40,
    train_n: int = 140,
    test_n: int = 5000,
    candidate_maps: int = 2500,
    states: int = 16,
) -> dict:
    train_best = []
    heldout = []
    false_discoveries = 0
    for seed in range(seeds):
        rng = random.Random(50_000 + seed)
        train_now = [rng.randrange(states) for _ in range(train_n)]
        train_next = [rng.randrange(states) for _ in range(train_n)]
        test_now = [rng.randrange(states) for _ in range(test_n)]
        test_next = [rng.randrange(states) for _ in range(test_n)]
        best_value = -1.0
        best_mapping: tuple[int, ...] | None = None
        for _ in range(candidate_maps):
            mapping = random_nonconstant_map(rng, states)
            value = mutual_information(
                apply_map(train_now, mapping), apply_map(train_next, mapping)
            )
            if value > best_value:
                best_value = value
                best_mapping = mapping
        assert best_mapping is not None
        heldout_value = mutual_information(
            apply_map(test_now, best_mapping), apply_map(test_next, best_mapping)
        )
        train_best.append(best_value)
        heldout.append(heldout_value)
        false_discoveries += best_value >= 0.05 and heldout_value < 0.01
    return {
        "null": "independent microstate transitions; same macro partition applied at t and t+1",
        "seeds": seeds,
        "candidate_maps_searched_per_seed": candidate_maps,
        "train_samples": train_n,
        "heldout_samples": test_n,
        "median_selected_train_mi_bits": statistics.median(train_best),
        "median_heldout_mi_bits": statistics.median(heldout),
        "max_selected_train_mi_bits": max(train_best),
        "false_discovery_fraction_train_ge_0_05_holdout_lt_0_01": false_discoveries / seeds,
        "decision": "REQUIRE_PREREGISTERED_OR_CROSSFIT_MACRO_SELECTION",
    }


def redundancy_overcount() -> dict:
    xs: list[int] = []
    ys: list[int] = []
    for _ in range(200):
        for x, y in ((0, 0), (0, 1), (1, 0), (1, 1)):
            xs.append(x)
            ys.append(y)
    duplicate_x = list(xs)
    target = [x ^ y for x, y in zip(xs, ys)]
    synergy_xy = mmi_synergy(xs, ys, target)
    synergy_duplicate_y = mmi_synergy(duplicate_x, ys, target)
    target_h = entropy(target)
    naive_sum = synergy_xy + synergy_duplicate_y
    return {
        "mechanism": "XOR with a perfectly duplicated source X' = X",
        "target_entropy_bits": target_h,
        "synergy_X_Y_bits": synergy_xy,
        "synergy_Xduplicate_Y_bits": synergy_duplicate_y,
        "naive_pairwise_sum_bits": naive_sum,
        "overcount_factor_vs_target_entropy": naive_sum / target_h,
        "decision": "FAIL_IF_OVERLAPPING_SYNERGY_IS_ADDITIVE",
    }


def hidden_path_counterexample() -> dict:
    xs: list[int] = []
    ys: list[int] = []
    for _ in range(250):
        for x, y in ((0, 0), (0, 1), (1, 0), (1, 1)):
            xs.append(x)
            ys.append(y)
    intended = [x ^ y for x, y in zip(xs, ys)]
    hidden_a = [1] * len(xs)
    hidden_b = [0] * len(xs)
    hidden_perturbed = [main | (a ^ b) for main, a, b in zip(intended, hidden_a, hidden_b)]
    hidden_effect = statistics.fmean(
        abs(after - before) for before, after in zip(intended, hidden_perturbed)
    )
    return {
        "visible_mechanism": "Y = X1 XOR X2",
        "unmapped_backup": "Y = visible OR (H1 XOR H2)",
        "baseline_when_H1_eq_H2_eq_0": "endpoint-equivalent to visible macro model",
        "visible_synergy_bits": mmi_synergy(xs, ys, intended),
        "standard_visible_lesion_rescue_can_pass": True,
        "excluded_variable_intervention_mean_absolute_effect": hidden_effect,
        "decision": "ENDPOINT_CONCORDANCE_INSUFFICIENT_REQUIRE_PATH_AND_EXCLUDED_VARIABLE_TESTS",
    }


def run() -> dict:
    results = {
        "clustered_pseudoreplication": clustered_pseudoreplication(),
        "time_null_sensitivity": time_null_sensitivity(),
        "macro_selection_bias": macro_selection_bias(),
        "redundancy_overcount": redundancy_overcount(),
        "hidden_path_counterexample": hidden_path_counterexample(),
    }
    return {
        "schema_version": "1.0",
        "instrument_target": "UDB_EMERGENCE_METER_V03_ADVERSARIAL_CONCORDANCE_GATE",
        "evidence_class": "SYNTHETIC_METHOD_FALSIFICATION",
        "live_frank_validated": False,
        "results": results,
        "v02_adjudication": "SYNTHETIC_REGIME_CLASSIFIER_RETAINED_BUT_RELIABLE_EMERGENCE_INSTRUMENT_CLAIM_REJECTED",
        "required_gates": [
            "episode_or_seed_cluster_aware_inference",
            "null_ensemble_preserving_relevant_autocorrelation_and_regimes",
            "abstention_on_null_model_disagreement",
            "preregistered_or_crossfit_macrostate_selection_with_heldout_interventions",
            "estimator_multiverse_and_redundancy_bounds_for_PID_PEID",
            "pathwise_causal_abstraction_and_excluded_variable_interventions",
            "receiver_specific_lesion_rescue_truthful_reentry_and_OOD_transfer",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("V03_ADVERSARIAL_RESULTS.json"))
    args = parser.parse_args()
    result = run()
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
