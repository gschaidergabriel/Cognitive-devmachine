#!/usr/bin/env python3
"""Fail-closed three-way token-scope discriminator for Trigger-1 Qwen3-0.6B steering.

The credited PyTorch witness perturbs the selected block output at the final prompt token.
llama.cpp cvec broadcasts the layer direction over prompt positions present in the decode
batch.  This adjudicator therefore requires matched observations for:

  PYTORCH_LAST_TOKEN
  PYTORCH_ALL_PROMPT_TOKENS
  NATIVE_CVEC_ALL_PROMPT_TOKENS

PyTorch LAST vs ALL isolates token-scope.  PyTorch ALL vs native ALL isolates carrier /
runtime / quantization transfer with token scope matched.  Native-ALL agreement alone is
classified BROADCAST_SCOPE_CARRIER_REPLICATION, never strict last-token replication.
Execution-free, fail-closed and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_SCOPE_EQUIVALENCE_INPUT/v1"
RECEIPT_SCHEMA = "CLAY_TRIGGER1_SCOPE_EQUIVALENCE_RECEIPT/v1"
CONDITIONS = (
    "PYTORCH_LAST_TOKEN",
    "PYTORCH_ALL_PROMPT_TOKENS",
    "NATIVE_CVEC_ALL_PROMPT_TOKENS",
)
CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
SCOPES = {
    "PYTORCH_LAST_TOKEN": "LAST_TOKEN_ONLY_AT_SELECTED_BLOCK_OUTPUT",
    "PYTORCH_ALL_PROMPT_TOKENS": "ALL_PROMPT_TOKEN_POSITIONS_AT_SELECTED_BLOCK_OUTPUT",
    "NATIVE_CVEC_ALL_PROMPT_TOKENS": "ALL_PROMPT_TOKEN_POSITIONS_PRESENT_IN_DECODE_BATCH",
}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def is_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na > 1e-15 and nb > 1e-15 else float("nan")


def relative_l2(a: list[float], b: list[float]) -> float:
    num = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    den = max(math.sqrt(sum(x * x for x in a)), math.sqrt(sum(y * y for y in b)), 1e-15)
    return num / den


def _fail(reason: str) -> dict[str, Any]:
    core = {
        "schema": RECEIPT_SCHEMA,
        "pass": False,
        "classification": "INTERVENTION_SCOPE_EQUIVALENCE_NOT_ESTABLISHED",
        "failures": [reason],
        "strict_last_token_native_identity": False,
        "broadcast_scope_carrier_replication": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return _fail("INPUT_SCHEMA_INVALID")

    prereg = payload.get("preregistration")
    if not isinstance(prereg, dict) or not is_sha(prereg.get("receipt_sha256")):
        return _fail("PREREGISTRATION_RECEIPT_SHA256_REQUIRED")
    if prereg.get("thresholds_frozen_before_holdout") is not True:
        return _fail("THRESHOLDS_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    thresholds = prereg.get("thresholds")
    try:
        min_cos = float(thresholds["min_effect_pattern_cosine"])
        max_rel = float(thresholds["max_effect_pattern_relative_l2"])
        max_null = float(thresholds["max_null_drift"])
    except (KeyError, TypeError, ValueError):
        return _fail("PREREGISTERED_THRESHOLDS_INVALID")
    if not (0 <= min_cos <= 1 and 0 <= max_rel <= 2 and max_null >= 0):
        return _fail("PREREGISTERED_THRESHOLD_RANGE_INVALID")

    identity = payload.get("frozen_identity")
    if not isinstance(identity, dict):
        return _fail("FROZEN_IDENTITY_REQUIRED")
    for field in ("basis_vector_sha256", "case_plan_sha256", "control_family_sha256"):
        if not is_sha(identity.get(field)):
            return _fail(f"{field.upper()}_REQUIRED")
    try:
        layer = int(identity["layer"])
        gain = float(identity["gain"])
    except (KeyError, TypeError, ValueError):
        return _fail("LAYER_GAIN_IDENTITY_REQUIRED")
    if layer < 0 or not math.isfinite(gain) or gain <= 0:
        return _fail("LAYER_GAIN_IDENTITY_INVALID")

    raw = payload.get("observations")
    if not isinstance(raw, list) or not raw:
        return _fail("OBSERVATIONS_REQUIRED")

    failures: list[str] = []
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    cases: set[str] = set()
    for i, row in enumerate(raw):
        prefix = f"ROW_{i}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        condition = str(row.get("condition") or "")
        case = str(row.get("case_identity_sha256") or "")
        control = str(row.get("control") or "")
        if condition not in CONDITIONS:
            failures.append(f"{prefix}_CONDITION_INVALID")
            continue
        if not is_sha(case):
            failures.append(f"{prefix}_CASE_IDENTITY_SHA256_INVALID")
            continue
        if control not in CONTROLS:
            failures.append(f"{prefix}_CONTROL_INVALID")
            continue
        if row.get("basis_vector_sha256") != identity["basis_vector_sha256"]:
            failures.append(f"{prefix}_BASIS_VECTOR_IDENTITY_MISMATCH")
        try:
            if int(row.get("layer")) != layer:
                failures.append(f"{prefix}_LAYER_MISMATCH")
            if abs(float(row.get("gain")) - gain) > 1e-12:
                failures.append(f"{prefix}_GAIN_MISMATCH")
            score = float(row["target_score"])
        except (KeyError, TypeError, ValueError):
            failures.append(f"{prefix}_NUMERIC_FIELD_INVALID")
            continue
        if not math.isfinite(score):
            failures.append(f"{prefix}_TARGET_SCORE_NONFINITE")
            continue
        if row.get("intervention_scope") != SCOPES[condition]:
            failures.append(f"{prefix}_SCOPE_ATTESTATION_INVALID")
        if condition == "NATIVE_CVEC_ALL_PROMPT_TOKENS" and control != "BASELINE" and row.get("native_cvec_rc") != 0:
            failures.append(f"{prefix}_NATIVE_CVEC_RC_NOT_ZERO")
        key = (condition, case, control)
        if key in rows:
            failures.append(f"{prefix}_DUPLICATE_OBSERVATION")
        else:
            rows[key] = {**row, "target_score": score}
        cases.add(case)

    expected = {(condition, case, control) for condition in CONDITIONS for case in cases for control in CONTROLS}
    if set(rows) != expected:
        missing = expected - set(rows)
        extra = set(rows) - expected
        if missing:
            failures.append(f"MISSING_MATCHED_OBSERVATIONS:{len(missing)}")
        if extra:
            failures.append(f"EXTRA_MATCHED_OBSERVATIONS:{len(extra)}")

    patterns = {condition: [] for condition in CONDITIONS}
    specificity: dict[str, bool] = {}
    if set(rows) == expected and expected:
        for condition in CONDITIONS:
            good = True
            for case in sorted(cases):
                vals = {control: rows[(condition, case, control)]["target_score"] for control in CONTROLS}
                effect = (
                    vals["+VECTOR"] - vals["BASELINE"],
                    vals["BASELINE"] - vals["SIGN_FLIP"],
                    vals["+VECTOR"] - vals["ORTHOGONAL_SAME_NORM"],
                    vals["+VECTOR"] - vals["PERMUTED_SAME_NORM"],
                )
                null = abs(vals["NULL_VECTOR"] - vals["BASELINE"])
                patterns[condition].extend(effect)
                if not (all(x > 0 for x in effect) and null <= max_null):
                    good = False
            specificity[condition] = good
            if not good:
                failures.append(f"{condition}_SIX_CONTROL_SPECIFICITY_FAIL")

    def compare(left: str, right: str) -> dict[str, Any]:
        a, b = patterns[left], patterns[right]
        if not a or len(a) != len(b):
            return {"pass": False, "cosine": None, "relative_l2": None, "left": left, "right": right}
        c = cosine(a, b)
        r = relative_l2(a, b)
        return {
            "pass": bool(math.isfinite(c) and c >= min_cos and r <= max_rel),
            "cosine": c,
            "relative_l2": r,
            "left": left,
            "right": right,
        }

    last_all = compare("PYTORCH_LAST_TOKEN", "PYTORCH_ALL_PROMPT_TOKENS")
    all_native = compare("PYTORCH_ALL_PROMPT_TOKENS", "NATIVE_CVEC_ALL_PROMPT_TOKENS")
    comparisons = {"PYTORCH_LAST_VS_ALL": last_all, "PYTORCH_ALL_VS_NATIVE_ALL": all_native}

    broadcast = bool(
        all_native["pass"]
        and specificity.get("PYTORCH_ALL_PROMPT_TOKENS") is True
        and specificity.get("NATIVE_CVEC_ALL_PROMPT_TOKENS") is True
    )
    strict = bool(broadcast and last_all["pass"] and specificity.get("PYTORCH_LAST_TOKEN") is True)
    if not all_native["pass"]:
        failures.append("PYTORCH_ALL_NATIVE_ALL_EFFECT_PATTERN_MISMATCH")
    if not last_all["pass"]:
        failures.append("PYTORCH_LAST_ALL_SCOPE_INVARIANCE_NOT_ESTABLISHED")

    classification = (
        "SCOPE_INVARIANT_THREE_WAY_REPLICATION"
        if strict
        else "BROADCAST_SCOPE_CARRIER_REPLICATION"
        if broadcast
        else "INTERVENTION_SCOPE_EQUIVALENCE_NOT_ESTABLISHED"
    )
    core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "preregistration_receipt_sha256": prereg["receipt_sha256"],
        "frozen_identity": identity,
        "case_count": len(cases),
        "observation_count": len(raw),
        "control_specificity": specificity,
        "comparisons": comparisons,
        "broadcast_scope_carrier_replication": broadcast,
        "strict_last_token_native_identity": strict,
        "pass": bool(strict and not failures),
        "classification": classification,
        "failures": sorted(set(failures)),
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "BROADCAST_SCOPE_CARRIER_REPLICATION binds PyTorch-all to native-all only. "
            "SCOPE_INVARIANT_THREE_WAY_REPLICATION additionally requires PyTorch-last vs PyTorch-all."
        ),
    }
    return {**core, "receipt_sha256": canonical_sha(core)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        receipt = adjudicate(payload)
    except (OSError, json.JSONDecodeError) as exc:
        receipt = _fail(f"INPUT_FILE_INVALID:{type(exc).__name__}")
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
