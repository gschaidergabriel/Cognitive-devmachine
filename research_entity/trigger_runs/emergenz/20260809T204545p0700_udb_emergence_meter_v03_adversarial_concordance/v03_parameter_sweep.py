#!/usr/bin/env python3
"""Parameter-surface attacks for the v0.3 adversarial concordance gate.

The experiment deliberately varies dependence strength, sample size, cluster
count, within-cluster replication, causal signal, and macro search budget.  It
also adds a persistent-regime common-driver counterexample.  The goal is to
locate failure boundaries, not to certify an emergence detector.

All evidence is synthetic method evidence.  It is not a live FRANK result and
does not support a consciousness claim.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from v03_adversarial_probe import (
    apply_map,
    ar1,
    entropy,
    exact_cluster_signflip_p,
    lag_mi,
    median_bits,
    mutual_information,
    permutation_signflip_p,
    random_nonconstant_map,
)


def empirical_p(observed: float, null: list[float]) -> float:
    return (1 + sum(value >= observed for value in null)) / (len(null) + 1)


def conditional_mutual_information(
    xs: list[object], ys: list[object], zs: list[object]
) -> float:
    return max(
        0.0,
        entropy(list(zip(xs, zs)))
        + entropy(list(zip(ys, zs)))
        - entropy(zs)
        - entropy(list(zip(xs, ys, zs))),
    )


def paired_series(
    *, seed: int, n: int, phi: float, beta: float = 0.0
) -> tuple[list[int], list[int]]:
    """Independent AR channels at beta=0; lagged X contribution otherwise."""

    rng_x = random.Random(100_000 + seed)
    rng_y = random.Random(200_000 + seed)
    x_values = ar1(rng_x, n, phi=phi)
    y_noise = ar1(rng_y, n, phi=phi)
    y_values = [
        noise + (beta * x_values[index - 1] if index else 0.0)
        for index, noise in enumerate(y_noise)
    ]
    return median_bits(x_values), median_bits(y_values)


def null_pvalues(
    xs: list[int], ys: list[int], *, seed: int, draws: int
) -> tuple[float, float]:
    observed = lag_mi(xs, ys)
    rng = random.Random(300_000 + seed)
    n = len(xs)
    edge = max(20, n // 10)
    full_null: list[float] = []
    circular_null: list[float] = []
    for _ in range(draws):
        shuffled = list(xs)
        rng.shuffle(shuffled)
        full_null.append(lag_mi(shuffled, ys))
        shift = rng.randrange(edge, n - edge)
        shifted = xs[shift:] + xs[:shift]
        circular_null.append(lag_mi(shifted, ys))
    return empirical_p(observed, full_null), empirical_p(observed, circular_null)


def time_null_surface(
    *,
    phis: tuple[float, ...] = (0.0, 0.8, 0.95, 0.985),
    sample_sizes: tuple[int, ...] = (200, 400, 800),
    seeds: int = 30,
    draws: int = 99,
) -> list[dict]:
    cells: list[dict] = []
    for phi in phis:
        for n in sample_sizes:
            full_rejects = 0
            circular_rejects = 0
            disagreements = 0
            for seed in range(seeds):
                xs, ys = paired_series(seed=seed, n=n, phi=phi)
                full_p, circular_p = null_pvalues(
                    xs, ys, seed=seed + int(phi * 10_000) + n, draws=draws
                )
                full_sig = full_p <= 0.05
                circular_sig = circular_p <= 0.05
                full_rejects += full_sig
                circular_rejects += circular_sig
                disagreements += full_sig != circular_sig
            cells.append(
                {
                    "phi": phi,
                    "samples": n,
                    "seeds": seeds,
                    "full_shuffle_false_positive_rate": full_rejects / seeds,
                    "circular_shift_false_positive_rate": circular_rejects / seeds,
                    "null_model_disagreement_rate": disagreements / seeds,
                }
            )
    return cells


def time_power_surface(
    *,
    betas: tuple[float, ...] = (0.0, 0.15, 0.3, 0.6),
    phi: float = 0.95,
    n: int = 400,
    seeds: int = 30,
    draws: int = 99,
) -> list[dict]:
    cells: list[dict] = []
    for beta in betas:
        full_rejects = 0
        circular_rejects = 0
        disagreements = 0
        for seed in range(seeds):
            xs, ys = paired_series(seed=10_000 + seed, n=n, phi=phi, beta=beta)
            full_p, circular_p = null_pvalues(
                xs, ys, seed=20_000 + seed + int(beta * 10_000), draws=draws
            )
            full_sig = full_p <= 0.05
            circular_sig = circular_p <= 0.05
            full_rejects += full_sig
            circular_rejects += circular_sig
            disagreements += full_sig != circular_sig
        cells.append(
            {
                "beta": beta,
                "phi": phi,
                "samples": n,
                "seeds": seeds,
                "full_shuffle_rejection_rate": full_rejects / seeds,
                "circular_shift_rejection_rate": circular_rejects / seeds,
                "null_model_disagreement_rate": disagreements / seeds,
            }
        )
    return cells


def cluster_signflip_p(
    cluster_means: list[float], *, seed: int, draws: int
) -> float:
    if len(cluster_means) <= 12:
        return exact_cluster_signflip_p(cluster_means)
    return permutation_signflip_p(cluster_means, random.Random(seed), draws)


def cluster_surface(
    *,
    episode_counts: tuple[int, ...] = (6, 12, 24, 48),
    tick_counts: tuple[int, ...] = (5, 20, 80),
    effects: tuple[float, ...] = (0.0, 0.2),
    seeds: int = 40,
    draws: int = 199,
) -> list[dict]:
    cells: list[dict] = []
    for effect in effects:
        for episodes in episode_counts:
            for ticks in tick_counts:
                tick_rejects = 0
                cluster_rejects = 0
                for seed in range(seeds):
                    rng = random.Random(
                        400_000
                        + seed
                        + episodes * 100
                        + ticks
                        + int(effect * 10_000)
                    )
                    clusters = []
                    for _ in range(episodes):
                        episode_value = effect + rng.gauss(0.0, 0.35)
                        clusters.append(
                            [episode_value + rng.gauss(0.0, 0.02) for _ in range(ticks)]
                        )
                    flat = [value for cluster in clusters for value in cluster]
                    means = [statistics.fmean(cluster) for cluster in clusters]
                    tick_p = permutation_signflip_p(
                        flat, random.Random(500_000 + seed + episodes + ticks), draws
                    )
                    cluster_p = cluster_signflip_p(
                        means,
                        seed=600_000 + seed + episodes + ticks,
                        draws=draws,
                    )
                    tick_rejects += tick_p <= 0.05
                    cluster_rejects += cluster_p <= 0.05
                cells.append(
                    {
                        "population_effect": effect,
                        "episodes": episodes,
                        "ticks_per_episode": ticks,
                        "seeds": seeds,
                        "tick_level_rejection_rate": tick_rejects / seeds,
                        "episode_cluster_rejection_rate": cluster_rejects / seeds,
                    }
                )
    return cells


def macro_search_curve(
    *,
    checkpoints: tuple[int, ...] = (1, 10, 100, 500, 2500),
    seeds: int = 40,
    train_n: int = 140,
    test_n: int = 5000,
    states: int = 16,
) -> list[dict]:
    per_checkpoint: dict[int, dict[str, list[float] | int]] = {
        checkpoint: {"train": [], "heldout": [], "false_discoveries": 0}
        for checkpoint in checkpoints
    }
    for seed in range(seeds):
        rng = random.Random(700_000 + seed)
        train_now = [rng.randrange(states) for _ in range(train_n)]
        train_next = [rng.randrange(states) for _ in range(train_n)]
        test_now = [rng.randrange(states) for _ in range(test_n)]
        test_next = [rng.randrange(states) for _ in range(test_n)]
        best_value = -1.0
        best_mapping: tuple[int, ...] | None = None
        for candidate in range(1, max(checkpoints) + 1):
            mapping = random_nonconstant_map(rng, states)
            value = mutual_information(
                apply_map(train_now, mapping), apply_map(train_next, mapping)
            )
            if value > best_value:
                best_value = value
                best_mapping = mapping
            if candidate in per_checkpoint:
                assert best_mapping is not None
                heldout_value = mutual_information(
                    apply_map(test_now, best_mapping), apply_map(test_next, best_mapping)
                )
                bucket = per_checkpoint[candidate]
                bucket["train"].append(best_value)  # type: ignore[union-attr]
                bucket["heldout"].append(heldout_value)  # type: ignore[union-attr]
                if best_value >= 0.05 and heldout_value < 0.01:
                    bucket["false_discoveries"] += 1  # type: ignore[operator]
    curve = []
    for checkpoint in checkpoints:
        bucket = per_checkpoint[checkpoint]
        train_values = bucket["train"]
        heldout_values = bucket["heldout"]
        assert isinstance(train_values, list) and isinstance(heldout_values, list)
        false_discoveries = bucket["false_discoveries"]
        assert isinstance(false_discoveries, int)
        curve.append(
            {
                "candidate_maps": checkpoint,
                "seeds": seeds,
                "median_selected_train_mi_bits": statistics.median(train_values),
                "median_heldout_mi_bits": statistics.median(heldout_values),
                "train_ge_0_05_heldout_lt_0_01_fraction": false_discoveries / seeds,
            }
        )
    return curve


def regime_common_driver(
    *, seeds: int = 40, n: int = 400, phi: float = 0.8, shift: float = 2.0, draws: int = 99
) -> dict:
    full_rejects = 0
    circular_rejects = 0
    unconditional: list[float] = []
    conditioned: list[float] = []
    for seed in range(seeds):
        base_x = ar1(random.Random(800_000 + seed), n, phi=phi)
        base_y = ar1(random.Random(900_000 + seed), n, phi=phi)
        regime = [0 if index < n // 2 else 1 for index in range(n)]
        x_values = [value + (-shift if not state else shift) for value, state in zip(base_x, regime)]
        y_values = [value + (-shift if not state else shift) for value, state in zip(base_y, regime)]
        xs = median_bits(x_values)
        ys = median_bits(y_values)
        unconditional.append(lag_mi(xs, ys))
        conditioned.append(conditional_mutual_information(xs[:-1], ys[1:], regime[1:]))
        full_p, circular_p = null_pvalues(
            xs, ys, seed=1_000_000 + seed, draws=draws
        )
        full_rejects += full_p <= 0.05
        circular_rejects += circular_p <= 0.05
    return {
        "null_of_interest": "no direct X->Y path; shared persistent regime only",
        "seeds": seeds,
        "samples": n,
        "phi": phi,
        "shared_regime_shift": shift,
        "full_shuffle_unconditional_dependence_rejection_rate_without_direct_path": full_rejects
        / seeds,
        "circular_shift_unconditional_dependence_rejection_rate_without_direct_path": circular_rejects
        / seeds,
        "median_unconditional_lag_mi_bits": statistics.median(unconditional),
        "median_regime_conditioned_lag_cmi_bits": statistics.median(conditioned),
        "decision": "NULL_ENSEMBLE_IS_NOT_A_SUBSTITUTE_FOR_CONTEXT_CONDITIONING",
    }


def run() -> dict:
    return {
        "schema_version": "1.0",
        "evidence_class": "SYNTHETIC_PARAMETER_SURFACE_AND_COUNTEREXAMPLE",
        "live_frank_validated": False,
        "time_null_surface": time_null_surface(),
        "time_power_surface": time_power_surface(),
        "cluster_surface": cluster_surface(),
        "macro_search_curve": macro_search_curve(),
        "regime_common_driver": regime_common_driver(),
        "adjudication": {
            "full_shuffle": "REJECT_AS_DEFAULT_FOR_DEPENDENT_TICKS",
            "circular_shift": "RETAIN_AS_ONE_DIAGNOSTIC_ONLY_NOT_A_UNIVERSAL_NULL",
            "cluster_inference": "REQUIRE_CORRECT_INDEPENDENCE_UNIT_AND_REPORT_POWER",
            "crossfit": "REQUIRE_TIME_OR_EPISODE_AWARE_SPLITS_AND_LEAKAGE_RECEIPTS",
            "null_ensemble": "ABSTAIN_ON_DISAGREEMENT_AND_ON_SHARED_CONTEXT_RISK",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("V03_PARAMETER_SWEEP_RESULTS.json"))
    args = parser.parse_args()
    result = run()
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
