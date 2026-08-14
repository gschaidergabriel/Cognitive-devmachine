#!/usr/bin/env python3
"""Out-of-distribution robustness sweep for UDB Emergence Meter v0.1.

This does not tune the detector. It stress-tests the frozen v0.1 decision rule over
sample size and measurement corruption and records abstention-worthy regions.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from emergence_meter import assess, synthetic_case


KINDS = ("null", "additive", "common_driver", "xor_no_reentry", "xor_reentry")
EXPECTED = {
    "null": "NOT_SUPPORTED",
    "additive": "INTERACTION_ONLY",
    "common_driver": "NOT_SUPPORTED",
    "xor_no_reentry": "MECHANISM_SUPPORTED_NOT_EMERGENCE",
    "xor_reentry": "CAUSAL_EMERGENCE_CANDIDATE_OPEN",
}


def corrupt(data: tuple, probability: float, seed: int) -> tuple:
    """Flip observed binary channels and replace continuous outcomes independently."""
    rng = random.Random(seed)
    baseline, lesion, rescue, truthful, shuffled, x, y, target, driver, rows = data

    def flip(values):
        return [1 - int(v) if rng.random() < probability else int(v) for v in values]

    def replace(values):
        return [float(rng.randrange(2)) if rng.random() < probability else float(v) for v in values]

    x2, y2, target2, driver2 = flip(x), flip(y), flip(target), flip(driver)
    baseline2, lesion2, rescue2 = replace(baseline), replace(lesion), replace(rescue)
    truthful2, shuffled2 = replace(truthful), replace(shuffled)
    rows2 = [(a, b, v) for a, b, v in zip(x2, y2, baseline2)]
    return baseline2, lesion2, rescue2, truthful2, shuffled2, x2, y2, target2, driver2, rows2


def run(samples: list[int], noise: list[float], seeds: int) -> dict:
    cells = []
    for n in samples:
        for p in noise:
            counts = {kind: Counter() for kind in KINDS}
            examples = {}
            for seed in range(seeds):
                for i, kind in enumerate(KINDS):
                    data = synthetic_case(kind, n, 100_000 + seed * 101 + i)
                    data = corrupt(data, p, 200_000 + seed * 101 + i)
                    result = assess(
                        kind, *data, seed=300_000 + seed * 101 + i,
                        permutation_draws=99, bootstrap_draws=100, paired_draws=199,
                    )
                    counts[kind][result.status] += 1
                    examples.setdefault((kind, result.status), asdict(result))
            correct = sum(counts[k][EXPECTED[k]] for k in KINDS)
            negative_promotions = sum(
                counts[k]["CAUSAL_EMERGENCE_CANDIDATE_OPEN"]
                for k in ("null", "additive", "common_driver")
            )
            candidate_sensitivity = counts["xor_reentry"]["CAUSAL_EMERGENCE_CANDIDATE_OPEN"] / seeds
            cell = {
                "samples": n,
                "measurement_corruption": p,
                "total_runs": seeds * len(KINDS),
                "exact_expected_rate": correct / (seeds * len(KINDS)),
                "false_causal_promotions_negative_controls": negative_promotions,
                "xor_reentry_candidate_sensitivity": candidate_sensitivity,
                "status_counts": {k: dict(v) for k, v in counts.items()},
            }
            # A preregistered operational abstention rule, not a retuned classifier.
            cell["deployment_disposition"] = (
                "CALIBRATED_REGION"
                if negative_promotions == 0
                and correct / (seeds * len(KINDS)) >= 0.95
                and candidate_sensitivity >= 0.95
                else "INSUFFICIENT_POWER_OR_ROBUSTNESS"
            )
            cells.append(cell)
    return {
        "schema_version": "1.0",
        "detector_contract": "UDB-EM-0.1-FROZEN_FAST_SCREEN",
        "seeds_per_cell": seeds,
        "expected_status": EXPECTED,
        "cells": cells,
        "interpretation_rule": "Fast screen only. Never promote outside CALIBRATED_REGION; confirm boundary cells with full-draw test and preserve UNKNOWN/insufficient-power semantics.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("robustness_sweep.json"))
    parser.add_argument("--seeds", type=int, default=20)
    args = parser.parse_args()
    result = run([100, 200, 400, 800], [0.0, 0.05, 0.10, 0.20], args.seeds)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
