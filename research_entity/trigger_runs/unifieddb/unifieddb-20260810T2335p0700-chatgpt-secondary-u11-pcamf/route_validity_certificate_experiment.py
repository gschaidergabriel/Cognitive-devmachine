#!/usr/bin/env python3
"""Reproducible U11 RouteValidityCertificate falsifier.

Local/synthetic research harness. It demonstrates that an IID finite-sample
risk certificate can hold on IID heldout data and still fail under a constructed
same-index query-distribution shift. It is not a target-VPS acceptance test.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

SEED = 20260810
M = 128
DHALF = 16
TOPK = 4
NOISE = 0.10
CONFIDENCE = 0.99
TARGET_RISK = 0.005
CAL_EACH = 1500
TEST_EACH = 1500
SHIFT_N = 500
OUT = Path("ROUTE_VALIDITY_CERTIFICATE_EXPERIMENT.reproduced.json")


def normalize(x: np.ndarray) -> np.ndarray:
    return x / np.linalg.norm(x, axis=1, keepdims=True)


def stats_us(ns: list[int]) -> dict:
    a = np.asarray(ns, dtype=np.float64) / 1000.0
    return {
        "n": int(len(a)),
        "p50": float(np.quantile(a, 0.50)),
        "p95": float(np.quantile(a, 0.95)),
        "p99": float(np.quantile(a, 0.99)),
        "mean": float(a.mean()),
    }


def zero_error_upper_bound(n: int, confidence: float) -> float:
    # Exact one-sided Clopper-Pearson upper bound for zero observed errors:
    # P(X=0 | p) = (1-p)^n = 1-confidence.
    return 1.0 - (1.0 - confidence) ** (1.0 / n)


def array_hash(*arrays: np.ndarray) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(str(a.dtype).encode())
        h.update(str(a.shape).encode())
        h.update(a.tobytes(order="C"))
    return h.hexdigest()


def pkm_predict(q: np.ndarray, a: np.ndarray, b: np.ndarray) -> tuple[int, float]:
    q1 = q[:DHALF] * math.sqrt(2.0)
    q2 = q[DHALF:] * math.sqrt(2.0)
    s1 = a @ q1
    s2 = b @ q2
    i1 = np.argpartition(s1, -TOPK)[-TOPK:]
    i2 = np.argpartition(s2, -TOPK)[-TOPK:]
    best_score = -1e30
    best = -1
    for x in i1:
        for y in i2:
            score = float((s1[x] + s2[y]) / math.sqrt(2.0))
            if score > best_score:
                best_score = score
                best = int(x * M + y)
    return best, float(np.max(s1) + np.max(s2))


def make_queries(rng, keys: np.ndarray, n: int, offset: int = 0):
    target_local = rng.integers(0, len(keys), size=n)
    q = keys[target_local] + rng.normal(scale=NOISE, size=(n, 2 * DHALF)).astype(np.float32)
    q = normalize(q)
    return q, target_local + offset


def main() -> None:
    rng = np.random.default_rng(SEED)
    a = normalize(rng.normal(size=(M, DHALF)).astype(np.float32))
    b = normalize(rng.normal(size=(M, DHALF)).astype(np.float32))
    product = np.concatenate([np.repeat(a, M, axis=0), np.tile(b, (M, 1))], axis=1) / math.sqrt(2.0)
    random_keys = normalize(rng.normal(size=product.shape).astype(np.float32))
    all_keys = np.concatenate([product, random_keys], axis=0)
    index_hash = array_hash(all_keys)

    # Calibration mixture.
    qp, _ = make_queries(rng, product, CAL_EACH, 0)
    qr, _ = make_queries(rng, random_keys, CAL_EACH, len(product))
    cal_q = np.concatenate([qp, qr], axis=0)
    cal_kind = np.concatenate([np.ones(CAL_EACH, dtype=np.int8), np.zeros(CAL_EACH, dtype=np.int8)])
    cal_scores = np.asarray([pkm_predict(q, a, b)[1] for q in cal_q])

    # Threshold chosen so the selected calibration region contains no known random-key cases.
    threshold = float(np.max(cal_scores[cal_kind == 0]) + 1e-6)
    selected = cal_scores > threshold
    selected_n = int(np.sum(selected))
    calibration_errors = int(np.sum((cal_kind == 0) & selected))
    risk_upper = zero_error_upper_bound(selected_n, CONFIDENCE) if calibration_errors == 0 else 1.0

    # IID heldout mixture. Compare routed PKM prediction against exact brute top-1.
    tp_q, _ = make_queries(rng, product, TEST_EACH, 0)
    tr_q, _ = make_queries(rng, random_keys, TEST_EACH, len(product))
    test_q = np.concatenate([tp_q, tr_q], axis=0)
    perm = rng.permutation(len(test_q))
    test_q = test_q[perm]
    routed_n = routed_errors = hybrid_errors = 0
    brute_lat, pkm_lat = [], []
    for q in test_q:
        t0 = time.perf_counter_ns()
        brute = int(np.argmax(all_keys @ q))
        brute_lat.append(time.perf_counter_ns() - t0)
        t0 = time.perf_counter_ns()
        pkm, score = pkm_predict(q, a, b)
        pkm_lat.append(time.perf_counter_ns() - t0)
        if score > threshold:
            routed_n += 1
            routed_errors += int(pkm != brute)
            hybrid = pkm
        else:
            hybrid = brute
        hybrid_errors += int(hybrid != brute)

    # Same-index tail shift: choose stored RANDOM keys with highest product-manifold gate score.
    random_scores = np.asarray([pkm_predict(q, a, b)[1] for q in random_keys])
    tail = np.argpartition(random_scores, -SHIFT_N)[-SHIFT_N:]
    tail = tail[np.argsort(random_scores[tail])[::-1]]
    shifted_q = random_keys[tail]  # exact stored-key queries; brute self-match is exact.
    shifted_routed = shifted_errors = 0
    for local_idx, q in zip(tail, shifted_q):
        brute = int(np.argmax(all_keys @ q))
        expected = int(len(product) + local_idx)
        assert brute == expected
        pkm, score = pkm_predict(q, a, b)
        if score > threshold:
            shifted_routed += 1
            shifted_errors += int(pkm != brute)

    # Index mutation must revoke the certificate by exact hash binding.
    extra = normalize(rng.normal(size=(16, 2 * DHALF)).astype(np.float32))
    updated_index_hash = array_hash(np.concatenate([all_keys, extra], axis=0))

    shift_route_rate = shifted_routed / SHIFT_N
    sentinel = []
    iid_route_rate = routed_n / len(test_q)
    for fraction in (0.02, 0.05, 0.10, 0.25, 0.50, 1.00):
        detection_prob_per_query = shift_route_rate * fraction
        sentinel.append({
            "shadow_fraction_of_routed": fraction,
            "iid_exact_shadow_fraction_of_all_queries": iid_route_rate * fraction,
            "constructed_shift_expected_queries_to_first_checked_mismatch": (1.0 / detection_prob_per_query) if detection_prob_per_query else None,
        })

    result = {
        "schema_version": "1.0",
        "evidence_class": "LOCAL_SYNTHETIC_NOT_TARGET_VPS",
        "seed": SEED,
        "certificate": {
            "threshold": threshold,
            "calibration_selected_n": selected_n,
            "calibration_errors": calibration_errors,
            "one_sided_confidence": CONFIDENCE,
            "zero_error_binomial_upper_bound": risk_upper,
            "target_risk": TARGET_RISK,
            "certificate_meets_target": bool(calibration_errors == 0 and risk_upper <= TARGET_RISK),
            "calibration_route_rate": selected_n / len(cal_q),
            "index_hash": index_hash,
            "validity_scope": "exchangeable calibration regime + exact index hash; not arbitrary distribution shift",
        },
        "iid_test": {
            "queries": len(test_q),
            "route_rate": iid_route_rate,
            "routed_errors": routed_errors,
            "routed_n": routed_n,
            "routed_error_rate": routed_errors / routed_n if routed_n else 0.0,
            "overall_hybrid_error_vs_brute": hybrid_errors / len(test_q),
            "brute_latency_us": stats_us(brute_lat),
            "pkm_component_latency_us": stats_us(pkm_lat),
        },
        "adversarial_same_index_shift": {
            "queries": SHIFT_N,
            "construction": "highest product-gate-score random stored keys queried exactly",
            "score_min": float(random_scores[tail].min()),
            "score_max": float(random_scores[tail].max()),
            "route_rate": shift_route_rate,
            "routed_n": shifted_routed,
            "routed_errors": shifted_errors,
            "routed_error_rate": shifted_errors / shifted_routed if shifted_routed else 0.0,
        },
        "index_version_binding": {
            "original_index_hash": index_hash,
            "updated_index_hash": updated_index_hash,
            "certificate_valid_after_index_change": bool(index_hash == updated_index_hash),
        },
        "shadow_sentinel_tradeoff": sentinel,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
