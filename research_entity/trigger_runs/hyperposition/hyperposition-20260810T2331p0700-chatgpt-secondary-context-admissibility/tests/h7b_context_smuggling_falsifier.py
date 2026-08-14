#!/usr/bin/env python3
"""Synthetic H7B discriminator: contextual pairwise fit can hide n-ary semantics.

No third-party dependencies.  This is synthetic evidence only, not Frank target evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import product, combinations
import json
from typing import Callable

Vector = list[float]
Matrix = list[list[float]]


def solve_linear(a: Matrix, b: Vector, eps: float = 1e-12) -> Vector:
    n = len(a)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < eps:
            continue
        m[col], m[pivot] = m[pivot], m[col]
        div = m[col][col]
        m[col] = [x / div for x in m[col]]
        for r in range(n):
            if r == col:
                continue
            factor = m[r][col]
            if abs(factor) < eps:
                continue
            m[r] = [m[r][c] - factor * m[col][c] for c in range(n + 1)]
    x = [0.0] * n
    for i in range(n):
        if abs(m[i][i]) >= eps:
            x[i] = m[i][n]
    return x


def least_squares(x: Matrix, y: Vector, ridge: float = 1e-9) -> Vector:
    p = len(x[0])
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for row, target in zip(x, y):
        for i in range(p):
            xty[i] += row[i] * target
            for j in range(p):
                xtx[i][j] += row[i] * row[j]
    for i in range(p):
        xtx[i][i] += ridge
    return solve_linear(xtx, xty)


def mse(x: Matrix, y: Vector, beta: Vector) -> float:
    return sum((sum(v*w for v, w in zip(row, beta)) - target) ** 2 for row, target in zip(x, y)) / len(y)


def static_pairwise(xs: tuple[int, ...]) -> Vector:
    out = [1.0]
    out.extend(float(v) for v in xs)
    out.extend(float(xs[i] * xs[j]) for i, j in combinations(range(len(xs)), 2))
    return out


def full_nary(xs: tuple[int, ...]) -> Vector:
    out = static_pairwise(xs)
    for order in range(3, len(xs) + 1):
        for idx in combinations(range(len(xs)), order):
            term = 1
            for i in idx:
                term *= xs[i]
            out.append(float(term))
    return out


def member_context_pairwise(xs: tuple[int, ...]) -> Vector:
    out = static_pairwise(xs)
    # x3 is itself a member of the relation.  Multiplying pairwise terms by x3
    # can exactly re-encode x1*x2*x3 while still looking "pairwise + context".
    context = xs[2]
    out.extend(float(xs[i] * xs[j] * context) for i, j in combinations(range(len(xs)), 2))
    return out


@dataclass
class Result:
    case: str
    static_pairwise_mse: float
    member_context_pairwise_mse: float
    full_nary_mse: float
    operational_context_fit: bool
    semantic_context_admissible: bool
    nary_required_under_semantic_guard: bool


def evaluate(case: str, target: Callable[[tuple[int, ...]], float]) -> Result:
    rows = list(product((-1, 1), repeat=3))
    y = [float(target(r)) for r in rows]
    x_pair = [static_pairwise(r) for r in rows]
    x_ctx = [member_context_pairwise(r) for r in rows]
    x_full = [full_nary(r) for r in rows]
    pair_mse = mse(x_pair, y, least_squares(x_pair, y))
    ctx_mse = mse(x_ctx, y, least_squares(x_ctx, y))
    full_mse = mse(x_full, y, least_squares(x_full, y))
    tol = 1e-8

    semantic_context_admissible = False  # context source x3 is in member closure
    return Result(
        case=case,
        static_pairwise_mse=pair_mse,
        member_context_pairwise_mse=ctx_mse,
        full_nary_mse=full_mse,
        operational_context_fit=ctx_mse <= tol,
        semantic_context_admissible=semantic_context_admissible,
        nary_required_under_semantic_guard=(pair_mse > tol and full_mse <= tol and not semantic_context_admissible),
    )


def main() -> None:
    cases = {
        "pairwise_reducible": lambda x: 0.5 * (x[0] * x[1] + x[1] * x[2]),
        "triple_parity": lambda x: float(x[0] * x[1] * x[2]),
    }
    results = [evaluate(name, fn) for name, fn in cases.items()]
    print(json.dumps({"schema": "hyperposition-h7b-context-smuggling-v1", "results": [asdict(r) for r in results]}, indent=2))

    by_name = {r.case: r for r in results}
    assert by_name["pairwise_reducible"].static_pairwise_mse < 1e-8
    assert not by_name["pairwise_reducible"].nary_required_under_semantic_guard
    assert abs(by_name["triple_parity"].static_pairwise_mse - 1.0) < 1e-8
    assert by_name["triple_parity"].full_nary_mse < 1e-8
    assert by_name["triple_parity"].operational_context_fit
    assert not by_name["triple_parity"].semantic_context_admissible
    assert by_name["triple_parity"].nary_required_under_semantic_guard


if __name__ == "__main__":
    main()
