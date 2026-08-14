#!/usr/bin/env python3
"""Synthetic proof-of-principle: intervention equivalence under implementation fusion.

Two implementations realize the same semantic two-state recurrent system:
- H1 representation x = [a, b]
- H3 representation z = T @ x, with invertible orthonormal mixing T

The test compares:
1) baseline trajectory equivalence,
2) semantic lesion a:=0 lowered correctly through T,
3) naive physical lesion z0:=0 incorrectly treated as the same lesion.

Scope: synthetic proof-of-principle only; not live FRANK/H1/H3 evidence.
"""
from __future__ import annotations

import json
import numpy as np

N_TRIALS = 200
N_STEPS = 40
LESION_T = 6
T = np.array([[1.0, 1.0], [1.0, -1.0]], dtype=float) / np.sqrt(2.0)
T_INV = T.T


def semantic_step(x: np.ndarray, u: float) -> np.ndarray:
    a, b = x
    return np.array([0.62 * a + u, 0.48 * b + 0.83 * a], dtype=float)


def semantic_output(x: np.ndarray) -> float:
    a, b = x
    return float(0.35 * a + 1.10 * b)


def h3_step(z: np.ndarray, u: float) -> np.ndarray:
    x = T_INV @ z
    return T @ semantic_step(x, u)


def lesion_h1(x: np.ndarray) -> np.ndarray:
    out = x.copy()
    out[0] = 0.0
    return out


def lesion_h3_semantic(z: np.ndarray) -> np.ndarray:
    x = T_INV @ z
    x[0] = 0.0
    return T @ x


def lesion_h3_naive_physical(z: np.ndarray) -> np.ndarray:
    out = z.copy()
    out[0] = 0.0
    return out


def run_trial(seed: int) -> dict:
    rng = np.random.default_rng(seed)
    inputs = rng.normal(0.0, 0.55, size=N_STEPS)
    x0 = rng.normal(0.0, 0.7, size=2)

    x_base = x0.copy()
    z_base = T @ x0
    x_sem = x0.copy()
    z_sem = T @ x0
    z_naive = T @ x0

    y_h1_base, y_h3_base = [], []
    y_h1_sem, y_h3_sem, y_h3_naive = [], [], []

    for t, u in enumerate(inputs):
        x_base = semantic_step(x_base, float(u))
        z_base = h3_step(z_base, float(u))

        x_sem = semantic_step(x_sem, float(u))
        z_sem = h3_step(z_sem, float(u))
        z_naive = h3_step(z_naive, float(u))

        if t >= LESION_T:
            x_sem = lesion_h1(x_sem)
            z_sem = lesion_h3_semantic(z_sem)
            z_naive = lesion_h3_naive_physical(z_naive)

        y_h1_base.append(semantic_output(x_base))
        y_h3_base.append(semantic_output(T_INV @ z_base))
        y_h1_sem.append(semantic_output(x_sem))
        y_h3_sem.append(semantic_output(T_INV @ z_sem))
        y_h3_naive.append(semantic_output(T_INV @ z_naive))

    y_h1_base = np.asarray(y_h1_base)
    y_h3_base = np.asarray(y_h3_base)
    y_h1_sem = np.asarray(y_h1_sem)
    y_h3_sem = np.asarray(y_h3_sem)
    y_h3_naive = np.asarray(y_h3_naive)

    h1_effect = float(np.mean(y_h1_base - y_h1_sem))
    h3_sem_effect = float(np.mean(y_h3_base - y_h3_sem))
    h3_naive_effect = float(np.mean(y_h3_base - y_h3_naive))

    return {
        "baseline_equiv_max_abs": float(np.max(np.abs(y_h1_base - y_h3_base))),
        "semantic_lesion_equiv_max_abs": float(np.max(np.abs(y_h1_sem - y_h3_sem))),
        "naive_lesion_divergence_mean_abs": float(np.mean(np.abs(y_h1_sem - y_h3_naive))),
        "h1_effect": h1_effect,
        "h3_semantic_effect": h3_sem_effect,
        "h3_naive_effect": h3_naive_effect,
        "effect_abs_error_semantic": abs(h1_effect - h3_sem_effect),
        "effect_abs_error_naive": abs(h1_effect - h3_naive_effect),
    }


def summarize(values: list[float]) -> dict:
    a = np.asarray(values, dtype=float)
    return {
        "mean": float(np.mean(a)),
        "median": float(np.median(a)),
        "max": float(np.max(a)),
        "sd": float(np.std(a)),
    }


def main() -> None:
    rows = [run_trial(seed) for seed in range(N_TRIALS)]
    summary = {
        "experiment_id": "EXP-SPAWN-EM-INTERVENTION-EQUIV-001",
        "design": {
            "trials": N_TRIALS,
            "steps": N_STEPS,
            "lesion_t": LESION_T,
            "semantic_state": ["a", "b"],
            "h3_representation": "z = orthonormal_mix([a,b])",
            "semantic_intervention": "a := 0 from lesion_t onward",
            "incorrect_low_level_intervention": "z0 := 0 from lesion_t onward"
        },
        "summary": {key: summarize([row[key] for row in rows]) for key in rows[0]},
        "interpretation_boundary": "Synthetic proof-of-principle only. Observational equivalence between two implementations does not guarantee intervention equivalence. A semantic intervention must be lowered through the implementation mapping and validated counterfactually before cross-implementation causal readouts are compared."
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
