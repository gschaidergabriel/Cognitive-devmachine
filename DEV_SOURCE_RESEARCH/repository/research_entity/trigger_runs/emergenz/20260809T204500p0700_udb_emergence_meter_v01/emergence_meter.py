#!/usr/bin/env python3
"""UDB Emergence Meter v0.1.

An evidence-preserving measurement kernel for copied FRANK/UnifiedDB data.
It deliberately returns a vector and gate state, never a consciousness or
single "emergence" score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sqlite3
import statistics
import time
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence


CONTRACT_VERSION = "UDB-EM-0.1"


def stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def entropy(xs: Sequence[object]) -> float:
    if not xs:
        return 0.0
    counts = Counter(xs)
    n = len(xs)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def mutual_information(xs: Sequence[object], ys: Sequence[object]) -> float:
    pairs = list(zip(xs, ys))
    return max(0.0, entropy(xs) + entropy(ys) - entropy(pairs))


def conditional_mutual_information(
    xs: Sequence[object], ys: Sequence[object], zs: Sequence[object]
) -> float:
    xyz = list(zip(xs, ys, zs))
    xz = list(zip(xs, zs))
    yz = list(zip(ys, zs))
    return max(0.0, entropy(xz) + entropy(yz) - entropy(zs) - entropy(xyz))


def two_source_synergy_mmi(
    xs: Sequence[object], ys: Sequence[object], target: Sequence[object]
) -> float:
    """Conservative discrete PID proxy: I(X,Y;T)-max(I(X;T),I(Y;T))."""
    joint = list(zip(xs, ys))
    return max(
        0.0,
        mutual_information(joint, target)
        - max(mutual_information(xs, target), mutual_information(ys, target)),
    )


def factorial_omega(rows: Sequence[tuple[int, int, float]]) -> float | None:
    cells: dict[tuple[int, int], list[float]] = defaultdict(list)
    for a, b, y in rows:
        cells[(int(a), int(b))].append(float(y))
    if any(not cells[k] for k in ((0, 0), (0, 1), (1, 0), (1, 1))):
        return None
    means = {k: statistics.fmean(v) for k, v in cells.items()}
    return means[(1, 1)] - means[(1, 0)] - means[(0, 1)] + means[(0, 0)]


def factorial_permutation_p(
    rows: Sequence[tuple[int, int, float]], seed: int, draws: int = 499
) -> float | None:
    observed = factorial_omega(rows)
    if observed is None:
        return None
    rng = random.Random(seed)
    factors = [(a, b) for a, b, _ in rows]
    outcomes = [v for _, _, v in rows]
    extreme = 0
    for _ in range(draws):
        shuffled = outcomes[:]
        rng.shuffle(shuffled)
        value = factorial_omega([(a, b, v) for (a, b), v in zip(factors, shuffled)])
        extreme += value is not None and abs(value) >= abs(observed)
    return (extreme + 1) / (draws + 1)


def bootstrap_ci(values: Sequence[float], seed: int, draws: int = 400) -> list[float]:
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)
    n = len(values)
    means = sorted(statistics.fmean(rng.choices(values, k=n)) for _ in range(draws))
    return [means[int(0.025 * (draws - 1))], means[int(0.975 * (draws - 1))]]


def permutation_paired_p(deltas: Sequence[float], seed: int, draws: int = 999) -> float:
    if not deltas:
        return 1.0
    observed = abs(statistics.fmean(deltas))
    rng = random.Random(seed)
    extreme = 0
    for _ in range(draws):
        value = abs(statistics.fmean(d * rng.choice((-1, 1)) for d in deltas))
        extreme += value >= observed
    return (extreme + 1) / (draws + 1)


@dataclass(frozen=True)
class Assessment:
    candidate_id: str
    factorial_omega: float | None
    factorial_permutation_p: float | None
    synergy_bits: float
    source_target_mi_bits: float
    source_target_cmi_given_driver_bits: float | None
    lesion_loss: float | None
    rescue_recovery: float | None
    truthful_vs_shuffled_delta: float | None
    delta_ci95: list[float] | None
    permutation_p: float | None
    controls_passed: list[str]
    controls_failed: list[str]
    evidence_level: str
    status: str
    falsifiers: list[str]


def assess(
    candidate_id: str,
    baseline: Sequence[float],
    lesion: Sequence[float],
    rescue: Sequence[float],
    truthful: Sequence[float],
    shuffled: Sequence[float],
    x: Sequence[int],
    y: Sequence[int],
    target: Sequence[int],
    driver: Sequence[int] | None,
    factorial_rows: Sequence[tuple[int, int, float]],
    seed: int = 7,
) -> Assessment:
    controls_passed: list[str] = []
    controls_failed: list[str] = []
    falsifiers: list[str] = []

    omega = factorial_omega(factorial_rows)
    omega_p = factorial_permutation_p(factorial_rows, seed)
    synergy = two_source_synergy_mmi(x, y, target)
    mi = mutual_information(x, target)
    cmi = conditional_mutual_information(x, target, driver) if driver is not None else None

    lesion_loss = None
    rescue_recovery = None
    if baseline and lesion and len(baseline) == len(lesion):
        lesion_d = [a - b for a, b in zip(baseline, lesion)]
        lesion_loss = statistics.fmean(lesion_d)
        if lesion_loss > 0.05:
            controls_passed.append("LESION")
        else:
            controls_failed.append("LESION")
            falsifiers.append("candidate outcome is insensitive to the claimed mechanism lesion")
        if rescue and len(rescue) == len(lesion):
            rescue_recovery = statistics.fmean(r - l for r, l in zip(rescue, lesion)) / max(
                1e-12, lesion_loss
            )
            if 0.5 <= rescue_recovery <= 1.5:
                controls_passed.append("RESCUE")
            else:
                controls_failed.append("RESCUE")
                falsifiers.append("rescue does not recover the predicted lesion loss")

    reentry_delta = None
    ci = None
    p = None
    if truthful and shuffled and len(truthful) == len(shuffled):
        deltas = [a - b for a, b in zip(truthful, shuffled)]
        reentry_delta = statistics.fmean(deltas)
        ci = bootstrap_ci(deltas, seed)
        p = permutation_paired_p(deltas, seed)
        if ci[0] > 0 and p <= 0.05:
            controls_passed.append("TRUTHFUL_REENTRY")
        else:
            controls_failed.append("TRUTHFUL_REENTRY")
            falsifiers.append("truthful re-entry does not beat matched shuffled re-entry")

    if driver is not None:
        ratio = cmi / max(mi, 1e-12)
        if mi > 0.02 and ratio < 0.2:
            controls_failed.append("COMMON_DRIVER")
            falsifiers.append("apparent directed dependence collapses after conditioning on a common driver")
        else:
            controls_passed.append("COMMON_DRIVER")

    if omega is not None and abs(omega) > 0.05 and omega_p is not None and omega_p <= 0.01:
        controls_passed.append("FACTORIAL_INTERACTION")
    else:
        controls_failed.append("FACTORIAL_INTERACTION")

    if synergy > 0.05:
        controls_passed.append("SYNERGY_PROXY")
    else:
        controls_failed.append("SYNERGY_PROXY")

    required = {"LESION", "RESCUE", "TRUTHFUL_REENTRY", "COMMON_DRIVER"}
    passed = set(controls_passed)
    if required <= passed and ("FACTORIAL_INTERACTION" in passed or "SYNERGY_PROXY" in passed):
        level = "COUNTERFACTUAL_REENTRY_SUPPORTED"
        status = "CAUSAL_EMERGENCE_CANDIDATE_OPEN"
    elif {"LESION", "RESCUE"} <= passed:
        level = "RESCUE_SUPPORTED"
        status = "MECHANISM_SUPPORTED_NOT_EMERGENCE"
    elif "FACTORIAL_INTERACTION" in passed or "SYNERGY_PROXY" in passed:
        level = "INTERACTION_SUPPORTED"
        status = "INTERACTION_ONLY"
    else:
        level = "OBSERVATIONAL"
        status = "NOT_SUPPORTED"

    return Assessment(
        candidate_id, omega, omega_p, synergy, mi, cmi, lesion_loss, rescue_recovery,
        reentry_delta, ci, p, sorted(set(controls_passed)),
        sorted(set(controls_failed)), level, status, falsifiers,
    )


SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS source_snapshots(
 snapshot_id TEXT PRIMARY KEY, source_uri TEXT NOT NULL, source_sha256 TEXT NOT NULL,
 created_at REAL NOT NULL, readonly_copy INTEGER NOT NULL CHECK(readonly_copy=1)
);
CREATE TABLE IF NOT EXISTS episodes(
 episode_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL REFERENCES source_snapshots(snapshot_id),
 basis_epoch TEXT NOT NULL, parent_episode_id TEXT REFERENCES episodes(episode_id),
 variant_kind TEXT NOT NULL, transform_spec_json TEXT NOT NULL, input_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS interventions(
 intervention_id TEXT PRIMARY KEY, episode_id TEXT NOT NULL REFERENCES episodes(episode_id),
 target TEXT NOT NULL, operation TEXT NOT NULL, held_fixed_json TEXT NOT NULL, seed INTEGER,
 preregistered_prediction TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS channel_samples(
 episode_id TEXT NOT NULL REFERENCES episodes(episode_id), tick INTEGER NOT NULL,
 channel TEXT NOT NULL, receiver TEXT NOT NULL DEFAULT '', value_json TEXT NOT NULL,
 provenance_hash TEXT NOT NULL, PRIMARY KEY(episode_id,tick,channel,receiver)
);
CREATE TABLE IF NOT EXISTS metric_receipts(
 receipt_id TEXT PRIMARY KEY, episode_id TEXT NOT NULL REFERENCES episodes(episode_id),
 estimator TEXT NOT NULL, estimator_version TEXT NOT NULL, value_json TEXT NOT NULL,
 uncertainty_json TEXT NOT NULL, control_kind TEXT NOT NULL, sample_count INTEGER NOT NULL,
 source_hash TEXT NOT NULL, result_hash TEXT NOT NULL, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS candidate_assessments(
 candidate_id TEXT PRIMARY KEY, contract_version TEXT NOT NULL, vector_json TEXT NOT NULL,
 evidence_level TEXT NOT NULL, status TEXT NOT NULL, result_hash TEXT NOT NULL, created_at REAL NOT NULL
);
"""


def open_lab(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    return con


def store_assessment(con: sqlite3.Connection, assessment: Assessment) -> None:
    value = asdict(assessment)
    result_hash = stable_hash(value)
    con.execute(
        "INSERT OR REPLACE INTO candidate_assessments VALUES(?,?,?,?,?,?,?)",
        (assessment.candidate_id, CONTRACT_VERSION, json.dumps(value, sort_keys=True),
         assessment.evidence_level, assessment.status, result_hash, time.time()),
    )
    con.commit()


def synthetic_case(kind: str, n: int, seed: int) -> tuple:
    rng = random.Random(seed)
    x, y, target, driver = [], [], [], []
    baseline, lesion, rescue, truthful, shuffled = [], [], [], [], []
    rows = []
    for _ in range(n):
        d = rng.randrange(2)
        a = d if kind == "common_driver" and rng.random() < 0.9 else rng.randrange(2)
        b = rng.randrange(2)
        if kind in {"xor_reentry", "xor_no_reentry"}:
            t = a ^ b
        elif kind == "common_driver":
            t = d if rng.random() < 0.9 else 1 - d
        elif kind == "additive":
            t = int((a + b + rng.random()) >= 1.5)
        else:
            t = rng.randrange(2)
        x.append(a); y.append(b); target.append(t); driver.append(d)
        base = float(t)
        les = 0.0 if kind.startswith("xor") else base
        resc = base
        # This channel is downstream task success after re-entry, not the raw
        # parity value. Truthful provenance makes the XOR state usable; a
        # shuffled receipt performs at chance despite identical volume.
        truth = 1.0 if kind == "xor_reentry" else float(rng.randrange(2))
        shift = float(rng.randrange(2))
        baseline.append(base); lesion.append(les); rescue.append(resc)
        truthful.append(truth); shuffled.append(shift)
        rows.append((a, b, base))
    return baseline, lesion, rescue, truthful, shuffled, x, y, target, driver, rows


def run_calibration(out: Path, n: int = 1200, seed: int = 11) -> dict:
    con = open_lab(out)
    results = {}
    for i, kind in enumerate(("null", "additive", "common_driver", "xor_no_reentry", "xor_reentry")):
        data = synthetic_case(kind, n, seed + i)
        a = assess(kind, *data, seed=seed + i)
        store_assessment(con, a)
        results[kind] = asdict(a)
    con.close()
    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=Path("emergence_lab.db"))
    p.add_argument("--samples", type=int, default=1200)
    p.add_argument("--seed", type=int, default=11)
    p.add_argument("--json", type=Path)
    args = p.parse_args()
    results = run_calibration(args.out, args.samples, args.seed)
    text = json.dumps(results, indent=2, sort_keys=True)
    if args.json:
        args.json.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
