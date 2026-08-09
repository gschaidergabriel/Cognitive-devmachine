#!/usr/bin/env python3
"""Live-refresh addendum: conditioning-depth stability counterexample.

Compares a true lag-1 path with an apparent lag-1 path caused by an omitted
lag-3 mechanism in a persistent binary process.  The diagnostic is deliberately
bounded: instability can flag state inadequacy but cannot identify its cause,
and stability does not prove causal sufficiency.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path

from v03_parameter_sweep import conditional_mutual_information
from v03_adversarial_probe import mutual_information


def binary_markov(rng: random.Random, n: int, persistence: float) -> list[int]:
    value = rng.getrandbits(1)
    values = []
    for _ in range(n):
        if rng.random() > persistence:
            value ^= 1
        values.append(value)
    return values


def noisy_lag_target(
    xs: list[int], *, lag: int, noise: float, rng: random.Random
) -> list[int]:
    ys = [0] * len(xs)
    for index in range(lag, len(xs)):
        ys[index] = xs[index - lag] ^ int(rng.random() < noise)
    return ys


def link_information_by_depth(
    xs: list[int], ys: list[int], *, max_depth: int, max_mechanism_lag: int
) -> list[float]:
    start = max_depth + max_mechanism_lag + 1
    source = [xs[index - 1] for index in range(start, len(xs))]
    target = [ys[index] for index in range(start, len(xs))]
    curve = [mutual_information(source, target)]
    for depth in range(1, max_depth + 1):
        context = [
            tuple(
                [xs[index - lag] for lag in range(2, depth + 2)]
                + [ys[index - lag] for lag in range(1, depth + 1)]
            )
            for index in range(start, len(xs))
        ]
        curve.append(conditional_mutual_information(source, target, context))
    return curve


def run(
    *,
    seeds: int = 20,
    samples: int = 20_000,
    persistence: float = 0.92,
    noise: float = 0.1,
    max_depth: int = 4,
) -> dict:
    direct_curves: list[list[float]] = []
    omitted_curves: list[list[float]] = []
    for seed in range(seeds):
        xs = binary_markov(random.Random(1_100_000 + seed), samples, persistence)
        direct = noisy_lag_target(
            xs, lag=1, noise=noise, rng=random.Random(1_200_000 + seed)
        )
        omitted = noisy_lag_target(
            xs, lag=3, noise=noise, rng=random.Random(1_300_000 + seed)
        )
        direct_curves.append(
            link_information_by_depth(
                xs, direct, max_depth=max_depth, max_mechanism_lag=3
            )
        )
        omitted_curves.append(
            link_information_by_depth(
                xs, omitted, max_depth=max_depth, max_mechanism_lag=3
            )
        )

    direct_median = [
        statistics.median(curve[depth] for curve in direct_curves)
        for depth in range(max_depth + 1)
    ]
    omitted_median = [
        statistics.median(curve[depth] for curve in omitted_curves)
        for depth in range(max_depth + 1)
    ]
    return {
        "schema_version": "1.0",
        "evidence_class": "SYNTHETIC_CONDITIONING_DEPTH_COUNTEREXAMPLE",
        "live_frank_validated": False,
        "seeds": seeds,
        "samples_per_seed": samples,
        "source_persistence": persistence,
        "target_flip_noise": noise,
        "conditioning_depth_definition": "depth d adds X lags 2..d+1 and Y lags 1..d while testing candidate X[t-1]->Y[t]",
        "depths": list(range(max_depth + 1)),
        "true_lag1_path_median_information_bits": direct_median,
        "omitted_lag3_apparent_lag1_median_information_bits": omitted_median,
        "depth1_retention_fraction_true_path": direct_median[1] / direct_median[0],
        "depth1_retention_fraction_omitted_path": omitted_median[1]
        / omitted_median[0],
        "adjudication": "ADD_CONDITIONING_DEPTH_STABILITY_DIAGNOSTIC_BUT_NEVER_TREAT_STABILITY_AS_CAUSAL_PROOF",
        "limitations": [
            "The diagnostic flags observed-state inadequacy but does not identify hidden memory, latent confounding, nonstationarity or measurement dynamics as the cause.",
            "Finite-sample CMI bias increases with conditioning dimension.",
            "A weak or highly predictable true path may also lose conditional information.",
            "Adaptive parent-selection methods do not expose one directly comparable nominal depth parameter.",
            "Thresholds require regime-specific null calibration and power analysis."
        ]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out", type=Path, default=Path("V031_CONDITIONING_DEPTH_RESULTS.json")
    )
    args = parser.parse_args()
    result = run()
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

