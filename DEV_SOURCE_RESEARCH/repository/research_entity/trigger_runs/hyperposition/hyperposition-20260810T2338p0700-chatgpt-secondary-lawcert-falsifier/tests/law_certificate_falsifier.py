#!/usr/bin/env python3
"""Synthetic falsifier for HyperMath LawCertificate declarations.

This is bounded executable evidence only. Passing a finite-domain property suite does not
prove a law over an unbounded carrier; failing it is sufficient to reject the declaration.
"""
from __future__ import annotations

import itertools
import json

DOMAIN = (-2.0, -1.0, 0.0, 1.0, 2.0)
TOL = 1e-12


def associative(op):
    for a, b, c in itertools.product(DOMAIN, repeat=3):
        left = op(op(a, b), c)
        right = op(a, op(b, c))
        if abs(left - right) > TOL:
            return False, {"a": a, "b": b, "c": c, "left": left, "right": right}
    return True, None


def commutative(op):
    for a, b in itertools.product(DOMAIN, repeat=2):
        left, right = op(a, b), op(b, a)
        if abs(left - right) > TOL:
            return False, {"a": a, "b": b, "left": left, "right": right}
    return True, None


def distributive(add, mul):
    for a, b, c in itertools.product(DOMAIN, repeat=3):
        left = mul(a, add(b, c))
        right = add(mul(a, b), mul(a, c))
        if abs(left - right) > TOL:
            return False, {"a": a, "b": b, "c": c, "left": left, "right": right}
    return True, None


def run_probe():
    min_op = min
    plus_op = lambda a, b: a + b
    mean_op = lambda a, b: (a + b) / 2.0

    min_assoc, min_assoc_w = associative(min_op)
    min_comm, min_comm_w = commutative(min_op)
    plus_assoc, plus_assoc_w = associative(plus_op)
    plus_comm, plus_comm_w = commutative(plus_op)
    plus_over_min, plus_over_min_w = distributive(min_op, plus_op)
    mean_assoc, mean_assoc_w = associative(mean_op)

    checks = {
        "min_associative_on_bounded_domain": min_assoc,
        "min_commutative_on_bounded_domain": min_comm,
        "plus_associative_on_bounded_domain": plus_assoc,
        "plus_commutative_on_bounded_domain": plus_comm,
        "plus_distributes_over_min_on_bounded_domain": plus_over_min,
        "false_mean_associativity_certificate_is_rejected": not mean_assoc,
    }
    if not all(checks.values()):
        raise SystemExit(json.dumps({"status": "FAIL", "checks": checks}, sort_keys=True))

    return {
        "status": "PASS",
        "evidence_class": "VERIFIED_LOCAL_SYNTHETIC_EXECUTION",
        "domain": list(DOMAIN),
        "checks": checks,
        "counterexample_false_associativity": mean_assoc_w,
        "witnesses_unexpected": {
            "min_assoc": min_assoc_w,
            "min_comm": min_comm_w,
            "plus_assoc": plus_assoc_w,
            "plus_comm": plus_comm_w,
            "plus_over_min": plus_over_min_w,
        },
        "interpretation": (
            "Law declarations used by HyperMath rewrite planning must be validated/proved and "
            "bound to the exact carrier implementation/version. Bounded testing can falsify a "
            "bad certificate but cannot promote a universal proof."
        ),
        "promotion": "VALIDATOR_ONLY",
        "target_live_evidence": False,
    }


if __name__ == "__main__":
    print(json.dumps(run_probe(), indent=2, sort_keys=True))
