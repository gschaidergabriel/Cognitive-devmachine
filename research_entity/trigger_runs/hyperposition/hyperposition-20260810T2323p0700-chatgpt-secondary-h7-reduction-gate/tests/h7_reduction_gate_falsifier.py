#!/usr/bin/env python3
"""Synthetic H7 discriminator.

Tests two intentionally separate claims:
1) semantic n-ary relation identity can be losslessly reified as relation-node + typed incidence edges;
2) that structural fact does NOT imply a higher-order interaction kernel is reducible to
   member-member pairwise additive interactions.

Synthetic only; not Frank target evidence.
"""
from __future__ import annotations

import itertools
import random
import time
import numpy as np

SEED = 20260810
ROUNDTRIPS = 100_000


def reification_roundtrip() -> tuple[int, float]:
    random.seed(SEED)
    mismatches = 0
    t0 = time.perf_counter()
    for i in range(ROUNDTRIPS):
        arity = random.randint(2, 8)
        rel = {
            "id": f"r{i}",
            "type": random.choice(["joint_support", "context_bind", "goal_action", "percept_memory"]),
            "members": [
                {
                    "logical_id": f"n{random.randint(0, 10000)}",
                    "role": f"role{j}",
                    "ordinal": j,
                    "scope": random.choice(["local", "episode", "global"]),
                }
                for j in range(arity)
            ],
            "provenance": f"ev{random.randint(0, 1000)}",
            "source_epoch": random.randint(1, 1000),
            "status": random.choice(["CURRENT", "UNKNOWN", "CONFLICT"]),
        }
        relation_node = {k: rel[k] for k in ["id", "type", "provenance", "source_epoch", "status"]}
        edges = [{"relation_id": rel["id"], **m} for m in rel["members"]]
        reconstructed = {
            **relation_node,
            "members": [
                {k: e[k] for k in ["logical_id", "role", "ordinal", "scope"]}
                for e in sorted(edges, key=lambda x: x["ordinal"])
            ],
        }
        mismatches += reconstructed != rel
    return mismatches, time.perf_counter() - t0


def interaction_reduction() -> dict[str, float | int]:
    # Full interaction: y=x1*x2*x3 on all {-1,+1}^3 states.
    # Reduced class: constant + all unary + all pairwise polynomial terms only.
    states = np.array(list(itertools.product([-1.0, 1.0], repeat=3)))
    x1, x2, x3 = states[:, 0], states[:, 1], states[:, 2]
    y = x1 * x2 * x3

    pair = np.column_stack([np.ones(8), x1, x2, x3, x1 * x2, x1 * x3, x2 * x3])
    beta = np.linalg.lstsq(pair, y, rcond=None)[0]
    p = pair @ beta

    nary = np.column_stack([pair, x1 * x2 * x3])
    beta3 = np.linalg.lstsq(nary, y, rcond=None)[0]
    p3 = nary @ beta3

    return {
        "pairwise_mse": float(np.mean((p - y) ** 2)),
        "pairwise_max_abs_error": float(np.max(np.abs(p - y))),
        "pairwise_exact_states": int(np.isclose(p, y).sum()),
        "nary_mse": float(np.mean((p3 - y) ** 2)),
        "nary_max_abs_error": float(np.max(np.abs(p3 - y))),
        "nary_exact_states": int(np.isclose(p3, y).sum()),
    }


def main() -> None:
    mismatches, seconds = reification_roundtrip()
    r = interaction_reduction()
    print(f"ROUNDTRIP n={ROUNDTRIPS} mismatches={mismatches} seconds={seconds:.4f}")
    print(r)

    assert mismatches == 0
    assert r["pairwise_exact_states"] == 0
    assert abs(r["pairwise_mse"] - 1.0) < 1e-12
    assert r["nary_exact_states"] == 8
    assert r["nary_mse"] < 1e-24


if __name__ == "__main__":
    main()
