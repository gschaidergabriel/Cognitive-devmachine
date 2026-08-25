#!/usr/bin/env python3
"""Compute the optional canonical #1941 cross-scope causal-effect-equivalence bridge.

Input rows must pair the same case/control-normalized effect under LAST_TOKEN_ONLY and
ALL_PROMPT_TOKENS. The bridge uses a paired two-one-sided-test (TOST) on their difference
with a preregistered equivalence ROPE. Passing establishes bounded *effect equivalence*,
never microscopic mechanistic identity.

The Student-t CDF is implemented with the regularized incomplete beta function so this
producer needs only the Python standard library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
from typing import Any

INPUT_SCHEMA = "CLAY_TRIGGER1_CROSS_SCOPE_PAIRED_TOST_INPUT/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER1_CROSS_SCOPE_PAIRED_TOST_RECEIPT/v1"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _betacf(a: float, b: float, x: float) -> float:
    max_iter = 300
    eps = 3e-14
    fpmin = 1e-300
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    raise ArithmeticError("BETA_CONTINUED_FRACTION_DID_NOT_CONVERGE")


def betai(a: float, b: float, x: float) -> float:
    if x < 0.0 or x > 1.0:
        raise ValueError("BETA_X_OUT_OF_RANGE")
    if x == 0.0 or x == 1.0:
        return x
    bt = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: int) -> float:
    if df <= 0:
        raise ValueError("DF_MUST_BE_POSITIVE")
    if not math.isfinite(t):
        return 1.0 if t > 0 else 0.0
    if t == 0.0:
        return 0.5
    x = df / (df + t * t)
    ib = betai(df / 2.0, 0.5, x)
    return 1.0 - 0.5 * ib if t > 0 else 0.5 * ib


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != INPUT_SCHEMA:
        raise ValueError("INPUT_SCHEMA_INVALID")
    if payload.get("equivalence_protocol_frozen_before_observation") is not True:
        raise ValueError("EQUIVALENCE_PROTOCOL_MUST_BE_FROZEN_BEFORE_OBSERVATION")
    if payload.get("legacy_scope") != "LAST_TOKEN_ONLY" or payload.get("native_scope") != "ALL_PROMPT_TOKENS":
        raise ValueError("EXACT_SCOPE_PAIR_REQUIRED")
    if payload.get("same_case_universe") is not True or payload.get("same_layer") is not True or payload.get("same_projected_vector_identity") is not True or payload.get("same_control_family") is not True:
        raise ValueError("MATCHED_CAUSAL_IDENTITY_FIELDS_REQUIRED")
    for field in ("equivalence_protocol_sha256", "case_universe_sha256", "projected_vector_sha256", "control_family_sha256"):
        if not is_sha(payload.get(field)):
            raise ValueError(f"{field.upper()}_REQUIRED")
    try:
        alpha = float(payload["alpha"])
        rope = float(payload["equivalence_rope_abs_standardized_effect"])
    except (KeyError, TypeError, ValueError):
        raise ValueError("ALPHA_AND_ROPE_REQUIRED")
    if not (0.0 < alpha <= 0.05):
        raise ValueError("ALPHA_TOO_WEAK_OR_INVALID")
    if not (0.0 < rope <= 0.25):
        raise ValueError("ROPE_TOO_WEAK_OR_INVALID")

    rows = payload.get("paired_effect_rows")
    if not isinstance(rows, list) or len(rows) < 6:
        raise ValueError("AT_LEAST_SIX_PAIRED_EFFECT_ROWS_REQUIRED")
    seen: set[str] = set()
    differences: list[float] = []
    sign_agree = True
    normalized_rows: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"ROW_{i}_OBJECT_REQUIRED")
        pair_id = str(row.get("pair_id") or "")
        if not pair_id or pair_id in seen:
            raise ValueError(f"ROW_{i}_PAIR_ID_INVALID_OR_DUPLICATE")
        seen.add(pair_id)
        try:
            legacy = float(row["legacy_control_normalized_effect"])
            native = float(row["native_control_normalized_effect"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"ROW_{i}_EFFECT_INVALID")
        if not (math.isfinite(legacy) and math.isfinite(native)):
            raise ValueError(f"ROW_{i}_EFFECT_NONFINITE")
        differences.append(native - legacy)
        if legacy == 0.0 or native == 0.0 or math.copysign(1.0, legacy) != math.copysign(1.0, native):
            sign_agree = False
        normalized_rows.append({"pair_id": pair_id, "legacy": legacy, "native": native, "difference": native - legacy})

    n = len(differences)
    mean = statistics.fmean(differences)
    sd = statistics.stdev(differences)
    df = n - 1
    if sd <= 1e-15:
        # Degenerate identical differences: equivalence is decidable directly.
        lower_p = 0.0 if mean > -rope else 1.0
        upper_p = 0.0 if mean < rope else 1.0
        se = 0.0
        t_lower = math.inf if mean > -rope else -math.inf
        t_upper = -math.inf if mean < rope else math.inf
    else:
        se = sd / math.sqrt(n)
        t_lower = (mean + rope) / se
        t_upper = (mean - rope) / se
        lower_p = 1.0 - t_cdf(t_lower, df)   # reject mean <= -rope
        upper_p = t_cdf(t_upper, df)         # reject mean >= +rope
    paired_tost_pass = bool(lower_p < alpha and upper_p < alpha)
    full_pass = bool(paired_tost_pass and sign_agree)

    core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "legacy_scope": "LAST_TOKEN_ONLY",
        "native_scope": "ALL_PROMPT_TOKENS",
        "comparison_claim": "CAUSAL_EFFECT_EQUIVALENCE_NOT_MECHANISTIC_IDENTITY",
        "same_case_universe": True,
        "same_layer": True,
        "same_projected_vector_identity": True,
        "same_control_family": True,
        "equivalence_protocol_frozen_before_observation": True,
        "equivalence_test_kind": "PAIRED_TOST_ON_CONTROL_NORMALIZED_EFFECT",
        "alpha": alpha,
        "equivalence_rope_abs_standardized_effect": rope,
        "pair_count": n,
        "mean_paired_difference": mean,
        "paired_difference_sd": sd,
        "paired_difference_se": se,
        "degrees_of_freedom": df,
        "t_lower": t_lower,
        "p_lower": lower_p,
        "t_upper": t_upper,
        "p_upper": upper_p,
        "paired_tost_pass": paired_tost_pass,
        "control_normalized_effect_sign_structure_agrees": sign_agree,
        "pass": full_pass,
        "equivalence_protocol_sha256": payload["equivalence_protocol_sha256"],
        "paired_effect_rows_sha256": canonical_sha(normalized_rows),
        "strict_micro_mechanistic_identity_claimed": False,
        "canonical_credit_minted": False,
        "evidence_boundary": "Paired TOST supports bounded cross-scope causal-effect equivalence only; never microscopic identity.",
    }
    return {**core, "paired_effect_receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        result = adjudicate(payload)
        rc = 0 if result["pass"] else 2
    except Exception as exc:
        result = {"schema": RECEIPT_SCHEMA, "pass": False, "error": f"{type(exc).__name__}:{str(exc)[:1000]}", "canonical_credit_minted": False}
        rc = 3
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
