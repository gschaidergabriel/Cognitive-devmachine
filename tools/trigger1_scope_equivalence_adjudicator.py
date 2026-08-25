#!/usr/bin/env python3
"""Three-way intervention-scope adjudicator for Trigger-1.

Separates two claims that must not be conflated:
1) a native all-prompt-token cvec can be a causal actuator in its own right; and
2) that actuator is functionally equivalent, at the declared metric/case universe, to the
   earlier PyTorch last-token witness.

The gate compares PYTORCH_LAST_TOKEN_ONLY vs PYTORCH_ALL_PROMPT_TOKENS first (token-scope
change only), then PYTORCH_ALL_PROMPT_TOKENS vs NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC
(runtime/carrier transfer at matched scope).  A native semantic candidate does not require
strict last-token replication; the latter is emitted as a separate status.

No model is executed and no runtime/product credit is minted.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

SCHEMA = "CLAY_TRIGGER1_SCOPE_EQUIVALENCE_EVIDENCE/v1"
SCOPES = (
    "PYTORCH_LAST_TOKEN_ONLY",
    "PYTORCH_ALL_PROMPT_TOKENS",
    "NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC",
)
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
    "LABEL_ONLY_NUISANCE_VECTOR",
)
HEX64 = 64


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != HEX64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _corr(a: list[float], b: list[float]) -> float | None:
    if len(a) != len(b) or len(a) < 2:
        return None
    ma = sum(a) / len(a)
    mb = sum(b) / len(b)
    da = [x - ma for x in a]
    db = [x - mb for x in b]
    va = sum(x * x for x in da)
    vb = sum(x * x for x in db)
    if va <= 1e-18 or vb <= 1e-18:
        return None
    return sum(x * y for x, y in zip(da, db)) / math.sqrt(va * vb)


def _rms(values: list[float]) -> float:
    return math.sqrt(sum(x * x for x in values) / max(1, len(values)))


def _nrmse(reference: list[float], other: list[float]) -> float | None:
    if len(reference) != len(other) or not reference:
        return None
    scale = _rms(reference)
    if scale <= 1e-12:
        return None
    return _rms([x - y for x, y in zip(reference, other)]) / scale


def adjudicate(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["SCHEMA_INVALID"],
            "native_all_token_causal_carrier_candidate": False,
            "strict_last_token_native_replication_candidate": False,
            "runtime_credit_minted": False,
        }

    tolerances = payload.get("tolerances") if isinstance(payload.get("tolerances"), dict) else {}
    scope_corr_min = float(tolerances.get("pytorch_scope_correlation_min", 0.90))
    scope_nrmse_max = float(tolerances.get("pytorch_scope_nrmse_max", 0.35))
    carrier_corr_min = float(tolerances.get("native_carrier_correlation_min", 0.85))
    carrier_nrmse_max = float(tolerances.get("native_carrier_nrmse_max", 0.40))
    min_effect_rms = float(tolerances.get("min_effect_rms", 1e-4))

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        failures.append("NONEMPTY_SCOPE_ROWS_REQUIRED")
        rows = []

    grouped: dict[tuple[str, str], dict[str, float]] = {}
    case_meta: dict[str, tuple[str, str]] = {}
    scope_case_sets = {scope: set() for scope in SCOPES}
    for index, row in enumerate(rows):
        prefix = f"ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        case_id = str(row.get("case_id") or "").strip()
        scope = str(row.get("scope") or "").strip().upper()
        control = str(row.get("control") or "").strip()
        family = str(row.get("family_id") or "").strip()
        target = str(row.get("semantic_target") or "").strip().upper()
        score = row.get("score")
        receipt = row.get("runtime_receipt_sha256")
        if not case_id:
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
            continue
        if scope not in SCOPES:
            failures.append(f"{prefix}_SCOPE_INVALID")
            continue
        if control not in REQUIRED_CONTROLS:
            failures.append(f"{prefix}_CONTROL_INVALID")
            continue
        if target not in {"AFFIRMATIVE", "NEGATIVE", "NEUTRAL"}:
            failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
        if not family:
            failures.append(f"{prefix}_FAMILY_ID_REQUIRED")
        if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(float(score)):
            failures.append(f"{prefix}_FINITE_SCORE_REQUIRED")
            continue
        if not _sha256(receipt):
            failures.append(f"{prefix}_RUNTIME_RECEIPT_SHA256_REQUIRED")
        key = (scope, case_id)
        slot = grouped.setdefault(key, {})
        if control in slot:
            failures.append(f"{prefix}_DUPLICATE_CONTROL")
        slot[control] = float(score)
        scope_case_sets[scope].add(case_id)
        prior = case_meta.get(case_id)
        meta = (family, target)
        if prior is None:
            case_meta[case_id] = meta
        elif prior != meta:
            failures.append(f"{prefix}_CASE_METADATA_DRIFT_ACROSS_SCOPES")

    universe = set.intersection(*(scope_case_sets[scope] for scope in SCOPES)) if rows else set()
    if not universe or any(scope_case_sets[scope] != universe for scope in SCOPES):
        failures.append("SCOPE_CASE_UNIVERSE_MISMATCH")

    deltas: dict[str, list[float]] = {scope: [] for scope in SCOPES}
    control_specificity_ok: dict[str, bool] = {scope: True for scope in SCOPES}
    ordered_cases = sorted(universe)
    for scope in SCOPES:
        for case_id in ordered_cases:
            controls = grouped.get((scope, case_id), {})
            if set(controls) != set(REQUIRED_CONTROLS):
                failures.append(f"MISSING_CONTROL_SET:{scope}:{case_id}")
                control_specificity_ok[scope] = False
                continue
            plus = controls["+VECTOR"] - controls["BASELINE"]
            sign = controls["SIGN_FLIP"] - controls["BASELINE"]
            null = abs(controls["NULL_VECTOR"] - controls["BASELINE"])
            orth = controls["ORTHOGONAL_SAME_NORM"] - controls["BASELINE"]
            perm = controls["PERMUTED_SAME_NORM"] - controls["BASELINE"]
            nuisance = controls["LABEL_ONLY_NUISANCE_VECTOR"] - controls["BASELINE"]
            deltas[scope].append(plus)
            # This is a scope-equivalence gate, not the final semantic gate.  Still require that
            # the intended vector is directionally distinguishable from its matched controls.
            if not (plus > 0 and sign < plus and abs(null) <= max(1e-5, 0.05 * abs(plus)) and plus > orth and plus > perm and plus > nuisance):
                control_specificity_ok[scope] = False

    last = deltas[SCOPES[0]]
    all_pt = deltas[SCOPES[1]]
    native = deltas[SCOPES[2]]
    scope_corr = _corr(last, all_pt)
    scope_nrmse = _nrmse(last, all_pt)
    carrier_corr = _corr(all_pt, native)
    carrier_nrmse = _nrmse(all_pt, native)
    scope_effect_nontrivial = _rms(last) >= min_effect_rms and _rms(all_pt) >= min_effect_rms
    carrier_effect_nontrivial = _rms(native) >= min_effect_rms

    pytorch_scope_equivalent = bool(
        scope_effect_nontrivial and scope_corr is not None and scope_corr >= scope_corr_min
        and scope_nrmse is not None and scope_nrmse <= scope_nrmse_max
        and control_specificity_ok[SCOPES[0]] and control_specificity_ok[SCOPES[1]]
    )
    native_carrier_matches_all_token = bool(
        carrier_effect_nontrivial and carrier_corr is not None and carrier_corr >= carrier_corr_min
        and carrier_nrmse is not None and carrier_nrmse <= carrier_nrmse_max
        and control_specificity_ok[SCOPES[1]] and control_specificity_ok[SCOPES[2]]
    )
    evidence_complete = not failures
    native_own_causal_carrier = bool(
        evidence_complete and carrier_effect_nontrivial and control_specificity_ok[SCOPES[2]]
    )
    strict_replication = bool(
        evidence_complete and pytorch_scope_equivalent and native_carrier_matches_all_token
    )

    classification = (
        "LAST_TOKEN_TO_NATIVE_FUNCTIONAL_EQUIVALENCE_SUPPORTED"
        if strict_replication
        else "BROADCAST_SCOPE_NATIVE_CARRIER_ONLY"
        if native_carrier_matches_all_token
        else "NATIVE_CAUSAL_CARRIER_WITH_SCOPE_OR_TRANSFER_DIVERGENCE"
        if native_own_causal_carrier
        else "SCOPE_EVIDENCE_INSUFFICIENT"
    )
    material = {
        "schema": SCHEMA,
        "ordered_cases": ordered_cases,
        "deltas": deltas,
        "tolerances": {
            "pytorch_scope_correlation_min": scope_corr_min,
            "pytorch_scope_nrmse_max": scope_nrmse_max,
            "native_carrier_correlation_min": carrier_corr_min,
            "native_carrier_nrmse_max": carrier_nrmse_max,
            "min_effect_rms": min_effect_rms,
        },
    }
    return {
        "schema": SCHEMA,
        "pass": not failures and native_own_causal_carrier,
        "failures": sorted(set(failures)),
        "classification": classification,
        "pytorch_last_vs_all_scope_equivalence_pass": pytorch_scope_equivalent,
        "native_vs_pytorch_all_token_carrier_match_pass": native_carrier_matches_all_token,
        "native_all_token_causal_carrier_candidate": native_own_causal_carrier,
        "strict_last_token_native_replication_candidate": strict_replication,
        "diagnostics": {
            "pytorch_last_vs_all_correlation": scope_corr,
            "pytorch_last_vs_all_nrmse": scope_nrmse,
            "pytorch_all_vs_native_correlation": carrier_corr,
            "pytorch_all_vs_native_nrmse": carrier_nrmse,
            "effect_rms": {scope: _rms(values) for scope, values in deltas.items()},
            "control_specificity": control_specificity_ok,
        },
        "scope_receipt_sha256": canonical_sha(material),
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Functional equivalence at the declared score/case/control universe only. A strict TRUE "
            "does not prove implementation identity; a strict FALSE does not invalidate an independently "
            "causal native all-token actuator."
        ),
    }
