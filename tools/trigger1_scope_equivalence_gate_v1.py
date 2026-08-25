#!/usr/bin/env python3
"""Three-way token-scope discriminator for Qwen3-0.6B Trigger-1 steering.

The earlier PyTorch witness perturbs only the final prompt token at the selected residual
site.  llama.cpp cvec adds the layer direction to every prompt position present in the
decode batch.  Those interventions must not be called causally identical by default.

This gate consumes preregistered, case/control-bound observations from:
  PYTORCH_LAST_TOKEN
  PYTORCH_ALL_PROMPT_TOKENS
  NATIVE_CVEC_ALL_PROMPT_TOKENS

It first tests PyTorch LAST vs ALL (pure token-scope change), then PyTorch ALL vs native
ALL (runtime/quantization/carrier transfer with scope matched).  A strict three-way scope-
invariant replication requires both comparisons.  Native ALL matching PyTorch ALL alone
is explicitly classified only as BROADCAST_SCOPE_CARRIER_REPLICATION.

Execution-free, fail-closed, non-minting.
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
    if na <= 1e-15 or nb <= 1e-15:
        return float("nan")
    return dot / (na * nb)


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
    if not isinstance(thresholds, dict):
        return _fail("PREREGISTERED_THRESHOLDS_REQUIRED")
    try:
        min_cos = float(thresholds["min_effect_pattern_cosine"])
        max_rel = float(thresholds["max_effect_pattern_relative_l2"])
        max_null = float(thresholds["max_null_drift"])
    except (KeyError, TypeError, ValueError):
        return _fail("THRESHOLD_FIELDS_INVALID")
    if not (0.0 <= min_cos <= 1.0 and 0.0 <= max_rel <= 2.0 and max_null >= 0.0):
        return _fail("THRESHOLD_RANGE_INVALID")

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
    case_universe: set[str] = set()
    for i, row in enumerate(raw):
        prefix = f"ROW_{i}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        condition = str(row.get("condition") or "")
        case_id = str(row.get("case_identity_sha256") or "")
        control = str(row.get("control") or "")
        if condition not in CONDITIONS:
            failures.append(f"{prefix}_CONDITION_INVALID")
            continue
        if not is_sha(case_id):
            failures.append(f"{prefix}_CASE_IDENTITY_SHA256_INVALID")
            continue
        if control not in CONTROLS:
            failures.append(f"{prefix}_CONTROL_INVALID")
            continue
        if row.get("basis_vector_sha256") != identity["basis_vector_sha256"]:
            failures.append(f"{prefix}_BASIS_VECTOR_IDENTITY_MISMATCH")
        if int(row.get("layer", -1)) != layer:
            failures.append(f"{prefix}_LAYER_MISMATCH")
        if abs(float(row.get("gain", float("nan"))) - gain) > 1e-12:
            failures.append(f"{prefix}_GAIN_MISMATCH")
        try:
            score = float(row["target_score"])
        except (KeyError, TypeError, ValueError):
            failures.append(f"{prefix}_TARGET_SCORE_INVALID")
            continue
        if not math.isfinite(score):
            failures.append(f"{prefix}_TARGET_SCORE_NONFINITE")
            continue
        if condition == "PYTORCH_LAST_TOKEN" and row.get("intervention_scope") != "LAST_TOKEN_ONLY_AT_SELECTED_BLOCK_OUTPUT":
            failures.append(f"{prefix}_PYTORCH_LAST_SCOPE_ATTESTATION_INVALID")
        if condition == "PYTORCH_ALL_PROMPT_TOKENS" and row.get("intervention_scope") != "ALL_PROMPT_TOKEN_POSITIONS_AT_SELECTED_BLOCK_OUTPUT":
            failures.append(f"{prefix}_PYTORCH_ALL_SCOPE_ATTESTATION_INVALID")
        if condition == "NATIVE_CVEC_ALL_PROMPT_TOKENS":
            if row.get("intervention_scope") != "ALL_PROMPT_TOKEN_POSITIONS_PRESENT_IN_DECODE_BATCH":
                failures.append(f"{prefix}_NATIVE_SCOPE_ATTESTATION_INVALID")
            if control != "BASELINE" and row.get("native_cvec_rc") != 0:
                failures.append(f"{prefix}_NATIVE_CVEC_RC_NOT_ZERO")
        key = (condition, case_id, control)
        if key in rows:
            failures.append(f"{prefix}_DUPLICATE_OBSERVATION")
        rows[key] = {**row, "target_score": score}
        case_universe.add(case_id)

    if not case_universe:
        failures.append("EMPTY_CASE_UNIVERSE")
    expected = {(c, case, k) for c in CONDITIONS for case in case_universe for k in CONTROLS}
    missing = expected - set(rows)
    extra = set(rows) - expected
    if missing:
        failures.append(f"MISSING_MATCHED_OBSERVATIONS:{len(missing)}")
    if extra:
        failures.append(f"EXTRA_MATCHED_OBSERVATIONS:{len(extra)}")

    effect_patterns: dict[str, list[float]] = {c: [] for c in CONDITIONS}
    control_specificity: dict[str, bool] = {}
    if not missing:
        for condition in CONDITIONS:
            cond_ok = True
            for case in sorted(case_universe):
                vals = {k: rows[(condition, case, k)]["target_score"] for k in CONTROLS}
                plus = vals["+VECTOR"] - vals["BASELINE"]
                sign = vals["BASELINE"] - vals["SIGN_FLIP"]
                null = abs(vals["NULL_VECTOR"] - vals["BASELINE"])
                orth = vals["+VECTOR"] - vals["ORTHOGONAL_SAME_NORM"]
                perm = vals["+VECTOR"] - vals["PERMUTED_SAME_NORM"]
                # Pattern excludes the numerically-near-zero null term from cosine geometry,
                # but null is independently thresholded.
                effect_patterns[condition].extend([plus, sign, orth, perm])
                if not (plus > 0 and sign > 0 and orth > 0 and perm > 0 and null <= max_null):
                    cond_ok = False
            control_specificity[condition] = cond_ok
            if not cond_ok:
                failures.append(f"{condition}_SIX_CONTROL_SPECIFICITY_FAIL")

    comparisons: dict[str, Any] = {}
    def compare(name: str, left: str, right: str) -> bool:
        a, b = effect_patterns[left], effect_patterns[right]
        if not a or len(a) != len(b):
            comparisons[name] = {"pass": False, "cosine": None, "relative_l2": None}
            return False
        c = cosine(a, b)
        r = relative_l2(a, b)
        ok = bool(math.isfinite(c) and c >= min_cos and r <= max_rel)
        comparisons[name] = {"pass": ok, "cosine": c, "relative_l2": r, "left": left, "right": right}
        return ok

    last_vs_all = compare("PYTORCH_LAST_VS_ALL", "PYTORCH_LAST_TOKEN", "PYTORCH_ALL_PROMPT_TOKENS")
    all_vs_native = compare("PYTORCH_ALL_VS_NATIVE_ALL", "PYTORCH_ALL_PROMPT_TOKENS", "NATIVE_CVEC_ALL_PROMPT_TOKENS")

    broadcast_replication = bool(all_vs_native and all(control_specificity.get(c) is True for c in ("PYTORCH_ALL_PROMPT_TOKENS", "NATIVE_CVEC_ALL_PROMPT_TOKENS")))
    strict_three_way = bool(broadcast_replication and last_vs_all and control_specificity.get("PYTORCH_LAST_TOKEN") is True)
    if not all_vs_native:
        failures.append("PYTORCH_ALL_NATIVE_ALL_EFFECT_PATTERN_MISMATCH")
    if not last_vs_all:
        failures.append("PYTORCH_LAST_ALL_SCOPE_INVARIANCE_NOT_ESTABLISHED")

    if strict_three_way:
        classification = "SCOPE_INVARIANT_THREE_WAY_REPLICATION"
    elif broadcast_replication:
        classification = "BROADCAST_SCOPE_CARRIER_REPLICATION"
    else:
        classification = "INTERVENTION_SCOPE_EQUIVALENCE_NOT_ESTABLISHED"

    # `pass` is deliberately the strongest claim: it means the old last-token witness and
    # the broadcast carrier survived the preregistered scope-isolation comparison.
    core = {
        "schema": RECEIPT_SCHEMA,
        "input_sha256": canonical_sha(payload),
        "preregistration_receipt_sha256": prereg["receipt_sha256"],
        "frozen_identity": identity,
        "case_count": len(case_universe),
        "observation_count": len(raw),
        "control_specificity": control_specificity,
        "comparisons": comparisons,
        "broadcast_scope_carrier_replication": broadcast_replication,
        "strict_last_token_native_identity": strict_three_way,
        "pass": strict_three_way and not any(x.endswith("INVALID") or "MISMATCH" in x or "MISSING_" in x for x in failures),
        "classification": classification,
        "failures": sorted(set(failures)),
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "BROADCAST_SCOPE_CARRIER_REPLICATION means PyTorch ALL_PROMPT_TOKENS and native cvec ALL_PROMPT_TOKENS "
            "match under preregistered controls; it does not identify the old last-token intervention. Only "
            "SCOPE_INVARIANT_THREE_WAY_REPLICATION additionally survives PyTorch LAST_TOKEN vs ALL_PROMPT_TOKENS."
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
