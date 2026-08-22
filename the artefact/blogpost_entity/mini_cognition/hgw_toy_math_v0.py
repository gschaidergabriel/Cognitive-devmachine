"""Deterministic toy calculations for GRF/Hyperposition x GWT research.

RESEARCH_CANDIDATE ONLY.
These calculations sanity-check equations and illustrate falsifiable interaction patterns.
They are not product-runtime evidence and do not establish architectural superiority.
"""
from __future__ import annotations

import math


def entropy(p: list[float]) -> float:
    return -sum(x * math.log(x) for x in p if x > 0.0)


def normalized_entropy(p: list[float]) -> float:
    if len(p) <= 1:
        return 0.0
    return entropy(p) / math.log(len(p))


def effective_count(p: list[float]) -> float:
    return math.exp(entropy(p))


def bayes_update(prior: list[float], likelihood: list[float]) -> list[float]:
    z = sum(p * l for p, l in zip(prior, likelihood, strict=True))
    if z <= 0.0:
        raise ValueError("non-positive evidence normalization")
    return [p * l / z for p, l in zip(prior, likelihood, strict=True)]


def softmax(scores: list[float], beta: float) -> list[float]:
    scaled = [beta * x for x in scores]
    m = max(scaled)
    ex = [math.exp(x - m) for x in scaled]
    z = sum(ex)
    return [x / z for x in ex]


def count_uncertainty(k: int) -> float:
    if k <= 0:
        raise ValueError("k must be positive")
    return min(1.0, (k - 1) / k)


def factorial_synergy(j00: float, j10: float, j01: float, j11: float) -> float:
    return j11 - j10 - j01 + j00


def main() -> None:
    # 1) Count-only uncertainty counterexample.
    p_equal = [1.0 / 3.0] * 3
    p_near = [0.98, 0.01, 0.01]
    assert math.isclose(count_uncertainty(3), 2.0 / 3.0)
    assert math.isclose(normalized_entropy(p_equal), 1.0, rel_tol=1e-12)
    assert math.isclose(effective_count(p_equal), 3.0, rel_tol=1e-12)
    assert math.isclose(normalized_entropy(p_near), 0.10185764172235329, rel_tol=1e-12)
    assert math.isclose(effective_count(p_near), 1.1184033153826292, rel_tol=1e-12)

    print("COUNT_ONLY_COUNTEREXAMPLE")
    print("U_count(equal)=", count_uncertainty(3))
    print("U_count(near)=", count_uncertainty(3))
    print("S_norm(equal)=", normalized_entropy(p_equal))
    print("S_norm(near)=", normalized_entropy(p_near))
    print("N_eff(equal)=", effective_count(p_equal))
    print("N_eff(near)=", effective_count(p_near))

    # 2) Reversal under contradictory evidence.
    posterior = bayes_update([0.5, 0.5], [0.8, 0.2])
    assert all(math.isclose(a, b, rel_tol=1e-12) for a, b in zip(posterior, [0.8, 0.2], strict=True))
    posterior = bayes_update(posterior, [0.1, 0.9])
    expected = [0.3076923076923077, 0.6923076923076923]
    assert all(math.isclose(a, b, rel_tol=1e-12) for a, b in zip(posterior, expected, strict=True))
    print("REVERSAL_POSTERIOR=", posterior)

    # 3) Workspace temperature / collapse pressure.
    print("TEMPERATURE_SCAN")
    for beta in (1.0, 5.0, 20.0):
        alpha = softmax([0.6, 0.4], beta)
        print("beta=", beta, "alpha=", alpha, "H=", entropy(alpha), "N_eff=", effective_count(alpha))

    # 4) Designed interaction toy: preserving uncertainty plus workspace-routed
    # discriminator has value only when both components are present.
    # This is an existence/sanity example, NOT an empirical Clay result.
    r1 = 0.65
    r2 = 0.90
    print("FACTORIAL_VOI_SCAN")
    for cost in (0.00, 0.05, 0.10, 0.20, 0.25, 0.30, 0.40):
        j00 = r1
        j10 = r1
        j01 = r1
        j11 = max(r1, r2 - cost)
        delta = factorial_synergy(j00, j10, j01, j11)
        print("cost=", cost, "J11=", j11, "Delta_synergy=", delta)

    # The crossover is exactly r2-r1 in this simplified model.
    assert math.isclose(r2 - r1, 0.25, rel_tol=1e-12)
    assert math.isclose(factorial_synergy(r1, r1, r1, max(r1, r2 - 0.10)), 0.15, rel_tol=1e-12)
    assert math.isclose(factorial_synergy(r1, r1, r1, max(r1, r2 - 0.25)), 0.0, abs_tol=1e-12)


if __name__ == "__main__":
    main()
