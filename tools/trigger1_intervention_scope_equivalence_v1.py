#!/usr/bin/env python3
"""Deterministic three-way intervention-scope adjudicator for Trigger-1.

It compares matched causal response vectors for:
  * PyTorch last-token-only residual addition,
  * PyTorch all-prompt-token residual broadcast, and
  * native llama.cpp all-prompt-token cvec.

A PASS is deliberately called response equivalence, never mechanistic/causal identity.
This module executes no model and mints no runtime/J-Space credit by itself.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from typing import Any

SCHEMA = "CLAY_TRIGGER1_INTERVENTION_SCOPE_EQUIVALENCE_INPUT/v1"
RESULT_SCHEMA = "CLAY_TRIGGER1_INTERVENTION_SCOPE_EQUIVALENCE_RESULT/v1"
PATHS = (
    "PYTORCH_LAST_TOKEN_ONLY",
    "PYTORCH_ALL_PROMPT_TOKENS",
    "NATIVE_LLAMACPP_ALL_PROMPT_TOKENS_CVEC",
)
DEFAULT_CONFIG = {
    "min_cells": 18,
    "min_cosine": 0.95,
    "max_nrmse": 0.20,
    "min_sign_agreement": 0.95,
    "magnitude_ratio_low": 0.67,
    "magnitude_ratio_high": 1.50,
    "zero_epsilon": 1e-12,
}


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _finite(x: Any) -> float:
    value = float(x)
    if not math.isfinite(value):
        raise ValueError("NONFINITE_EFFECT")
    return value


def _cosine(a: list[float], b: list[float], eps: float) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na <= eps or nb <= eps:
        raise ValueError("DEGENERATE_EFFECT_VECTOR")
    return dot / (na * nb)


def _pair_metrics(reference: list[float], candidate: list[float], config: dict[str, float]) -> dict[str, Any]:
    eps = float(config["zero_epsilon"])
    cosine = _cosine(reference, candidate, eps)
    rmse = math.sqrt(sum((x - y) ** 2 for x, y in zip(reference, candidate)) / len(reference))
    ref_rms = math.sqrt(sum(x * x for x in reference) / len(reference))
    nrmse = rmse / max(ref_rms, eps)

    signs = []
    ratios = []
    for x, y in zip(reference, candidate):
        if abs(x) <= eps and abs(y) <= eps:
            signs.append(1.0)
            continue
        if abs(x) <= eps or abs(y) <= eps:
            signs.append(0.0)
            continue
        signs.append(1.0 if (x > 0) == (y > 0) else 0.0)
        ratios.append(abs(y) / abs(x))
    sign_agreement = sum(signs) / len(signs)
    ratios_sorted = sorted(ratios)
    if not ratios_sorted:
        raise ValueError("NO_NONZERO_EFFECTS_FOR_MAGNITUDE_RATIO")
    mid = len(ratios_sorted) // 2
    median_ratio = (
        ratios_sorted[mid]
        if len(ratios_sorted) % 2
        else 0.5 * (ratios_sorted[mid - 1] + ratios_sorted[mid])
    )
    passed = (
        cosine >= float(config["min_cosine"])
        and nrmse <= float(config["max_nrmse"])
        and sign_agreement >= float(config["min_sign_agreement"])
        and float(config["magnitude_ratio_low"]) <= median_ratio <= float(config["magnitude_ratio_high"])
    )
    return {
        "cosine": cosine,
        "nrmse": nrmse,
        "sign_agreement": sign_agreement,
        "median_abs_magnitude_ratio_candidate_over_reference": median_ratio,
        "pass": passed,
    }


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    metric_identity = str(payload.get("metric_identity") or "")
    normalizer_identity = str(payload.get("normalizer_identity") or "")
    if not metric_identity or not normalizer_identity:
        raise ValueError("METRIC_AND_NORMALIZER_IDENTITY_REQUIRED")

    config = dict(DEFAULT_CONFIG)
    user_config = payload.get("config") or {}
    if not isinstance(user_config, dict):
        raise ValueError("CONFIG_OBJECT_REQUIRED")
    for key in config:
        if key in user_config:
            config[key] = user_config[key]

    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("ROWS_ARRAY_REQUIRED")
    grouped: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("ROW_OBJECT_REQUIRED")
        path = row.get("path")
        cell = str(row.get("cell_id") or "")
        if path not in PATHS or not cell:
            raise ValueError("ROW_PATH_OR_CELL_INVALID")
        if path in grouped[cell]:
            raise ValueError(f"DUPLICATE_CELL_PATH:{cell}:{path}")
        grouped[cell][path] = _finite(row.get("semantic_effect"))

    if len(grouped) < int(config["min_cells"]):
        raise ValueError(f"INSUFFICIENT_MATCHED_CELLS:{len(grouped)}")
    for cell, values in grouped.items():
        if set(values) != set(PATHS):
            raise ValueError(f"INCOMPLETE_THREE_WAY_CELL:{cell}")

    cells = sorted(grouped)
    vectors = {path: [grouped[cell][path] for cell in cells] for path in PATHS}
    last_vs_all = _pair_metrics(
        vectors["PYTORCH_LAST_TOKEN_ONLY"],
        vectors["PYTORCH_ALL_PROMPT_TOKENS"],
        config,
    )
    all_vs_native = _pair_metrics(
        vectors["PYTORCH_ALL_PROMPT_TOKENS"],
        vectors["NATIVE_LLAMACPP_ALL_PROMPT_TOKENS_CVEC"],
        config,
    )

    if last_vs_all["pass"] and all_vs_native["pass"]:
        classification = "SCOPE_INVARIANT_SEMANTIC_RESPONSE_EQUIVALENCE"
        promotion_relevance = "TOKEN_SCOPE_BLOCKER_CLOSED_AT_DECLARED_RESPONSE_METRIC"
    elif (not last_vs_all["pass"]) and all_vs_native["pass"]:
        classification = "BROADCAST_SCOPE_CARRIER_REPLICATION_ONLY"
        promotion_relevance = "LAST_TOKEN_EQUIVALENCE_NOT_ESTABLISHED"
    elif not all_vs_native["pass"]:
        classification = "NATIVE_CARRIER_RESPONSE_DIVERGENCE"
        promotion_relevance = "NATIVE_CARRIER_TRANSFER_NOT_ESTABLISHED"
    else:
        classification = "UNRESOLVED_FAIL_CLOSED"
        promotion_relevance = "NO_PROMOTION"

    core = {
        "schema": RESULT_SCHEMA,
        "metric_identity": metric_identity,
        "normalizer_identity": normalizer_identity,
        "matched_cell_count": len(cells),
        "cell_universe_sha256": canonical_sha(cells),
        "config": config,
        "last_token_vs_pytorch_broadcast": last_vs_all,
        "pytorch_broadcast_vs_native_cvec": all_vs_native,
        "classification": classification,
        "promotion_relevance": promotion_relevance,
        # Even perfect outcome equivalence does not prove that two different
        # intervention mechanisms are literally causally identical.
        "causal_identity_claim_allowed": False,
        "response_equivalence_claim_allowed": classification == "SCOPE_INVARIANT_SEMANTIC_RESPONSE_EQUIVALENCE",
    }
    core["adjudication_receipt_sha256"] = canonical_sha(core)
    return core


if __name__ == "__main__":
    raise SystemExit("library-only: provide a bound runtime payload to adjudicate()")
