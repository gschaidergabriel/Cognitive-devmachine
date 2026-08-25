#!/usr/bin/env python3
"""Reconstruct lexical independence for Trigger-1 J-Space promotion.

This gate closes an attestation gap left by lexical-family IDs alone. It derives
semantic-discriminative token sets from the actual model-facing prompts after removing
only within-family common scaffold, then requires those discriminative sets to be disjoint
across basis families and across BASIS/CALIBRATION/HOLDOUT partitions.

Canonical semantic class names remain evaluator metadata only. A/B/C output codes are
forbidden in BASIS derivation but are allowed in CALIBRATION/HOLDOUT because those output
identities are independently counterbalanced by the enclosing factorial design.

Execution-free and non-minting: PASS is a metrology prerequisite, not semantic truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_LEXICAL_INDEPENDENCE_GATE/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
TARGET_SET = set(TARGETS)
FORBIDDEN_MODEL_LABELS = tuple(x.lower() for x in TARGETS)
TOKEN_RE = re.compile(r"[a-z]+")

SCAFFOLD = {
    "a", "an", "the", "one", "is", "are", "was", "were", "be", "being", "been",
    "and", "or", "but", "not", "no", "to", "of", "for", "from", "in", "on", "at",
    "by", "with", "without", "it", "its", "this", "that", "these", "those", "as",
    "do", "does", "did", "only", "exactly", "internally", "represent", "return",
    "answer", "output", "emit", "code", "codes", "class", "label", "labels",
    "temporary", "card", "situation", "action", "actions",
}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _model_tokens(prompt: str) -> set[str]:
    return {token for token in TOKEN_RE.findall(prompt.lower()) if token not in SCAFFOLD}


def _prompt_is_label_free(prompt: str, *, forbid_output_codes: bool) -> bool:
    lower = prompt.lower()
    if any(label in lower for label in FORBIDDEN_MODEL_LABELS):
        return False
    if forbid_output_codes and re.search(r"(?<![A-Za-z])[ABC](?![A-Za-z])", prompt):
        return False
    return True


def _matched_family_tokens(
    rows: list[dict[str, Any]],
    *,
    family_field: str,
    target_field: str,
    scope: str,
    forbid_output_codes: bool,
) -> tuple[dict[str, set[str]], list[str]]:
    failures: list[str] = []
    grouped: dict[str, dict[str, set[str]]] = {}
    for index, row in enumerate(rows):
        prefix = f"{scope}_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        family = str(row.get(family_field) or "").strip()
        target = str(row.get(target_field) or "").strip().upper()
        prompt = row.get("prompt")
        if not family:
            failures.append(f"{prefix}_FAMILY_REQUIRED")
            continue
        if target not in TARGET_SET:
            failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
            continue
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{prefix}_PROMPT_REQUIRED")
            continue
        if not _prompt_is_label_free(prompt, forbid_output_codes=forbid_output_codes):
            failures.append(f"{prefix}_MODEL_FACING_LABEL_OR_FORBIDDEN_OUTPUT_CODE_LEAK")
        bucket = grouped.setdefault(family, {})
        if target in bucket:
            failures.append(f"{prefix}_DUPLICATE_TARGET_IN_FAMILY")
            continue
        bucket[target] = _model_tokens(prompt)

    family_discriminative: dict[str, set[str]] = {}
    for family, states in sorted(grouped.items()):
        if set(states) != TARGET_SET:
            failures.append(f"{scope}_FAMILY_MUST_CONTAIN_EXACT_TARGET_TRIAD:{family}")
            continue
        common = set.intersection(*(states[target] for target in TARGETS))
        discriminative = set.union(*(states[target] - common for target in TARGETS))
        if not discriminative:
            failures.append(f"{scope}_FAMILY_DISCRIMINATIVE_LEXICON_EMPTY:{family}")
            continue
        family_discriminative[family] = discriminative
    return family_discriminative, failures


def _pairwise_disjoint(
    families: dict[str, set[str]], *, scope: str
) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    overlaps: list[dict[str, Any]] = []
    names = sorted(families)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            overlap = sorted(families[left] & families[right])
            if overlap:
                failures.append(f"{scope}_DISCRIMINATIVE_LEXICAL_OVERLAP:{left}:{right}")
                overlaps.append({"left": left, "right": right, "tokens": overlap})
    return failures, overlaps


def _partition_overlap(
    left: dict[str, set[str]], right: dict[str, set[str]], *, name: str
) -> tuple[list[str], list[str]]:
    left_union = set().union(*left.values()) if left else set()
    right_union = set().union(*right.values()) if right else set()
    overlap = sorted(left_union & right_union)
    failures = [] if not overlap else [f"{name}_DISCRIMINATIVE_LEXICON_MUST_BE_DISJOINT"]
    return failures, overlap


def _case_rows(candidate: dict[str, Any], split: str) -> list[dict[str, Any]]:
    evidence = candidate.get("preregistration_evidence")
    plans = evidence.get("case_plans") if isinstance(evidence, dict) else None
    plan = plans.get(split) if isinstance(plans, dict) else None
    rows = plan.get("cases") if isinstance(plan, dict) else None
    return rows if isinstance(rows, list) else []


def validate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("CANDIDATE_OBJECT_REQUIRED")

    evidence = candidate.get("lexical_independence_evidence")
    basis_rows = evidence.get("basis_rows") if isinstance(evidence, dict) else None
    if not isinstance(basis_rows, list):
        basis_rows = []
        failures.append("BASIS_MODEL_FACING_ROWS_REQUIRED")

    basis, f = _matched_family_tokens(
        basis_rows,
        family_field="family_group_id",
        target_field="semantic_class",
        scope="BASIS",
        forbid_output_codes=True,
    )
    failures.extend(f)
    calibration, f = _matched_family_tokens(
        _case_rows(candidate, "CALIBRATION"),
        family_field="scenario_family_sha256",
        target_field="semantic_target",
        scope="CALIBRATION",
        forbid_output_codes=False,
    )
    failures.extend(f)
    holdout, f = _matched_family_tokens(
        _case_rows(candidate, "HOLDOUT"),
        family_field="scenario_family_sha256",
        target_field="semantic_target",
        scope="HOLDOUT",
        forbid_output_codes=False,
    )
    failures.extend(f)

    if len(basis) < 6:
        failures.append("AT_LEAST_SIX_BASIS_LEXICAL_FAMILIES_REQUIRED")
    if len(calibration) < 3:
        failures.append("AT_LEAST_THREE_CALIBRATION_LEXICAL_FAMILIES_REQUIRED")
    if len(holdout) < 3:
        failures.append("AT_LEAST_THREE_HOLDOUT_LEXICAL_FAMILIES_REQUIRED")

    f, basis_overlap = _pairwise_disjoint(basis, scope="BASIS")
    failures.extend(f)
    f, cal_overlap = _pairwise_disjoint(calibration, scope="CALIBRATION")
    failures.extend(f)
    f, hold_overlap = _pairwise_disjoint(holdout, scope="HOLDOUT")
    failures.extend(f)

    cross: dict[str, list[str]] = {}
    for left, right, name in (
        (basis, calibration, "BASIS_CALIBRATION"),
        (basis, holdout, "BASIS_HOLDOUT"),
        (calibration, holdout, "CALIBRATION_HOLDOUT"),
    ):
        f, overlap = _partition_overlap(left, right, name=name)
        failures.extend(f)
        cross[name] = overlap

    hold = candidate.get("holdout") if isinstance(candidate.get("holdout"), dict) else {}
    cal = candidate.get("calibration") if isinstance(candidate.get("calibration"), dict) else {}
    if cal.get("semantic_target_x_output_code_factorial") is not True:
        failures.append("CALIBRATION_TARGET_X_CODE_FACTORIAL_REQUIRED")
    if hold.get("semantic_target_x_output_code_factorial") is not True:
        failures.append("HOLDOUT_TARGET_X_CODE_FACTORIAL_REQUIRED")
    if hold.get("semantic_target_interaction_test") is not True:
        failures.append("HOLDOUT_TREATMENT_BY_SEMANTIC_TARGET_INTERACTION_REQUIRED")
    if hold.get("per_family_semantic_target_interaction") is not True:
        failures.append("HOLDOUT_PER_FAMILY_TARGET_INTERACTION_REQUIRED")
    if hold.get("off_target_drift_test") is not True or hold.get("off_target_drift_within_preregistered_threshold") is not True:
        failures.append("GENERIC_COMPLIANCE_OFF_TARGET_FENCE_REQUIRED")
    if not _sha256(hold.get("off_target_drift_receipt_sha256")):
        failures.append("GENERIC_COMPLIANCE_OFF_TARGET_RECEIPT_REQUIRED")

    intervention = candidate.get("intervention") if isinstance(candidate.get("intervention"), dict) else {}
    if candidate.get("runtime_intervention_class") == "LOCAL_LLAMA_CPP_CVEC_APPLIED":
        if intervention.get("token_scope") != "ALL_PROMPT_TOKENS":
            failures.append("NATIVE_CVEC_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
        if intervention.get("strict_last_token_replication_claimed") is True:
            failures.append("NATIVE_CVEC_MUST_NOT_CLAIM_LAST_TOKEN_CAUSAL_IDENTITY")

    material = {
        "schema": SCHEMA,
        "basis_family_count": len(basis),
        "calibration_family_count": len(calibration),
        "holdout_family_count": len(holdout),
        "basis_discriminative_tokens": {k: sorted(v) for k, v in sorted(basis.items())},
        "calibration_discriminative_tokens": {k: sorted(v) for k, v in sorted(calibration.items())},
        "holdout_discriminative_tokens": {k: sorted(v) for k, v in sorted(holdout.items())},
        "within_partition_overlaps": {
            "basis": basis_overlap,
            "calibration": cal_overlap,
            "holdout": hold_overlap,
        },
        "cross_partition_overlap_tokens": cross,
        "basis_output_codes_forbidden": True,
        "evaluation_output_codes_allowed_only_under_counterbalanced_factorial": True,
    }
    generic_failures = {
        "HOLDOUT_TREATMENT_BY_SEMANTIC_TARGET_INTERACTION_REQUIRED",
        "HOLDOUT_PER_FAMILY_TARGET_INTERACTION_REQUIRED",
        "GENERIC_COMPLIANCE_OFF_TARGET_FENCE_REQUIRED",
        "GENERIC_COMPLIANCE_OFF_TARGET_RECEIPT_REQUIRED",
    }
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "lexical_independence_receipt_sha256": canonical_sha(material),
        "reconstructed_material": material,
        "generic_compliance_counterhypothesis_rejected_by_design_candidate": not bool(generic_failures & set(failures)),
        "native_last_token_causal_identity_required": False,
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS reconstructs label-freeness and discriminative lexical disjointness from actual model-facing text, "
            "while allowing only independently counterbalanced evaluation codes. It also requires target-interaction "
            "and off-target fences against generic compliance. It does not execute the model or establish semantic truth."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    except Exception as exc:
        candidate = {"_invalid": f"{type(exc).__name__}:{exc}"}
    verdict = validate(candidate)
    text = json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if verdict["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
