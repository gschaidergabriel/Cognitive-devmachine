#!/usr/bin/env python3
"""Successor fail-closed scientific-specificity gate for Trigger-1 J-Space claims.

This v5 layer composes the current v4 promotion gate instead of weakening or rewriting it.
It adds the measurement/confound controls required by the 2026-08-25 Forschungsrun-1
fusion: model-facing label-free / lexically disjoint vector derivation, a label-only
nuisance control, calibration-only residual-norm operating-point selection, target x
output-code factorial structure, cross-family direction-coherence evidence, frozen
holdout measurement, off-target drift control, explicit token-scope classification, and
case-bound semantic-factorial evidence whose interaction summary is recomputed from the
same digest-bound case/control universe.

The tool is adjudication only. It does not run a model, open a holdout, mint canonical
truth, or create EntityOS/HCU/J-Space/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as v4

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v5"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v5"
LABEL_NUISANCE_CONTROL = "LABEL_ONLY_NUISANCE_VECTOR"
TOKEN_SCOPES = {"LAST_TOKEN_ONLY", "ALL_PROMPT_TOKENS"}
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
CASE_ATTESTATION_SCHEMA = "CLAY_TRIGGER1_CASE_BOUND_SEMANTIC_FACTORIAL_ATTESTATION/v1"
REQUIRED_SEMANTIC_TARGETS = {"AFFIRMATIVE", "NEGATIVE", "NEUTRAL"}
REQUIRED_OUTPUT_CODES = {"A", "B", "C"}
REQUIRED_SPLITS = ("CALIBRATION", "HOLDOUT")


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite_positive_number(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value > 0 and value != float("inf")


def _finite_number(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
    )


def _canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _extra_specificity_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    """Check only the v5 successor controls; v4 remains authoritative underneath."""
    failures: list[str] = []
    derivation = candidate.get("vector_derivation")
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    intervention = candidate.get("intervention")
    controls = candidate.get("controls")
    measurement = candidate.get("measurement_protocol")

    if not isinstance(derivation, dict):
        derivation = {}
    if not isinstance(calibration, dict):
        calibration = {}
    if not isinstance(holdout, dict):
        holdout = {}
    if not isinstance(intervention, dict):
        intervention = {}
    if not isinstance(controls, dict):
        controls = {}
    if not isinstance(measurement, dict):
        measurement = {}

    # A model-facing basis that contains target names/synonyms can reconstruct a lexical
    # axis even when output A/B/C codes are counterbalanced. Require an explicitly bound,
    # label-free and cross-family lexical design plus a nuisance-control receipt.
    if derivation.get("model_facing_label_free") is not True:
        failures.append("MODEL_FACING_LABEL_FREE_BASIS_REQUIRED")
    if derivation.get("lexically_disjoint_basis_families") is not True:
        failures.append("LEXICALLY_DISJOINT_BASIS_FAMILIES_REQUIRED")
    if derivation.get("lexical_nuisance_projection_or_control") is not True:
        failures.append("LEXICAL_NUISANCE_PROJECTION_OR_CONTROL_REQUIRED")
    if not _sha256(derivation.get("lexical_nuisance_receipt_sha256")):
        failures.append("LEXICAL_NUISANCE_RECEIPT_REQUIRED")

    nuisance = controls.get(LABEL_NUISANCE_CONTROL)
    if not isinstance(nuisance, dict):
        failures.append(f"CONTROL_REQUIRED:{LABEL_NUISANCE_CONTROL}")
    elif not _sha256(nuisance.get("runtime_receipt_sha256")):
        failures.append(f"CONTROL_RUNTIME_RECEIPT_REQUIRED:{LABEL_NUISANCE_CONTROL}")

    # Target semantics and output code must vary independently in both calibration and
    # fresh holdout. v4 already requires target counterbalance; v5 makes the factorial
    # relation and per-family interaction explicit.
    for split_name, split in (("CALIBRATION", calibration), ("HOLDOUT", holdout)):
        if split.get("semantic_target_x_output_code_factorial") is not True:
            failures.append(f"{split_name}_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_REQUIRED")
    if holdout.get("per_family_semantic_target_interaction") is not True:
        failures.append("HOLDOUT_PER_FAMILY_SEMANTIC_TARGET_INTERACTION_REQUIRED")

    # Raw steering gain is not a comparable intervention strength. Select the operating
    # point using calibration-only residual-norm-relative magnitude and freeze it before
    # any holdout observation.
    if calibration.get("residual_norm_relative_intervention") is not True:
        failures.append("CALIBRATION_RESIDUAL_NORM_RELATIVE_INTERVENTION_REQUIRED")
    if calibration.get("operating_point_selected_on_calibration_only") is not True:
        failures.append("OPERATING_POINT_MUST_BE_SELECTED_ON_CALIBRATION_ONLY")
    if not _sha256(calibration.get("operating_point_receipt_sha256")):
        failures.append("CALIBRATION_OPERATING_POINT_RECEIPT_REQUIRED")
    if holdout.get("operating_point_frozen_before_holdout") is not True:
        failures.append("OPERATING_POINT_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _finite_positive_number(intervention.get("residual_norm_ratio")):
        failures.append("POSITIVE_RESIDUAL_NORM_RATIO_REQUIRED")

    # Reliability/generalization checks: stable direction geometry across lexical families
    # and an independently preregistered off-target bound.
    if holdout.get("cross_family_direction_coherence_test") is not True:
        failures.append("CROSS_FAMILY_DIRECTION_COHERENCE_TEST_REQUIRED")
    if not _sha256(holdout.get("cross_family_direction_coherence_receipt_sha256")):
        failures.append("CROSS_FAMILY_DIRECTION_COHERENCE_RECEIPT_REQUIRED")
    if holdout.get("off_target_drift_test") is not True:
        failures.append("OFF_TARGET_DRIFT_TEST_REQUIRED")
    if holdout.get("off_target_drift_within_preregistered_threshold") is not True:
        failures.append("OFF_TARGET_DRIFT_MUST_BE_WITHIN_PREREGISTERED_THRESHOLD")
    if not _sha256(holdout.get("off_target_drift_receipt_sha256")):
        failures.append("OFF_TARGET_DRIFT_RECEIPT_REQUIRED")

    # llama.cpp cvec broadcasts over prompt positions in the active decode batch. Scope
    # must therefore be explicit; native evidence cannot silently masquerade as strict
    # last-token replication of an earlier PyTorch intervention.
    token_scope = intervention.get("token_scope")
    if token_scope not in TOKEN_SCOPES:
        failures.append("TOKEN_SCOPE_CLASSIFICATION_REQUIRED")
    if candidate.get("runtime_intervention_class") == NATIVE_CVEC_CLASS and token_scope != "ALL_PROMPT_TOKENS":
        failures.append("NATIVE_CVEC_REQUIRES_ALL_PROMPT_TOKENS_SCOPE_CLASSIFICATION")
    if not isinstance(intervention.get("scope_classification"), str) or not intervention.get("scope_classification", "").strip():
        failures.append("INTERVENTION_SCOPE_CLASSIFICATION_REQUIRED")
    if intervention.get("strict_last_token_replication_claimed") is True and token_scope == "ALL_PROMPT_TOKENS":
        failures.append("ALL_PROMPT_TOKEN_CVEC_CANNOT_CLAIM_STRICT_LAST_TOKEN_REPLICATION")

    # Freeze the complete measurement contract before holdout so operating-point and
    # threshold choices cannot be selected after seeing the result.
    if measurement.get("frozen_before_holdout") is not True:
        failures.append("MEASUREMENT_PROTOCOL_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(measurement.get("protocol_sha256")):
        failures.append("MEASUREMENT_PROTOCOL_RECEIPT_REQUIRED")
    threshold = measurement.get("preregistered_off_target_drift_threshold")
    if not _finite_positive_number(threshold):
        failures.append("PREREGISTERED_OFF_TARGET_DRIFT_THRESHOLD_REQUIRED")

    return not failures, sorted(set(failures))


def _case_bound_semantic_factorial_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    """Reconstruct factorial and interaction bindings from exact candidate case rows.

    Summary booleans such as ``semantic_target_x_output_code_factorial`` remain useful
    declarations but are insufficient for promotion. This layer requires the candidate
    to carry the exact case/control universe and then deterministically recomputes the
    3x3 contingency tables plus a per-family +VECTOR-minus-BASELINE interaction summary.
    """
    failures: list[str] = []
    attestation = candidate.get("semantic_factorial_attestation")
    calibration = candidate.get("calibration")
    holdout = candidate.get("holdout")
    if not isinstance(attestation, dict):
        return False, ["CASE_BOUND_SEMANTIC_FACTORIAL_ATTESTATION_REQUIRED"]
    if not isinstance(calibration, dict):
        calibration = {}
    if not isinstance(holdout, dict):
        holdout = {}

    if attestation.get("schema") != CASE_ATTESTATION_SCHEMA:
        failures.append("CASE_BOUND_SEMANTIC_FACTORIAL_ATTESTATION_SCHEMA_INVALID")

    family_by_split = {
        "CALIBRATION": calibration.get("family_id"),
        "HOLDOUT": holdout.get("family_id"),
    }
    for split, family_id in family_by_split.items():
        if not isinstance(family_id, str) or not family_id.strip():
            failures.append(f"{split}_FAMILY_ID_REQUIRED_FOR_CASE_ATTESTATION")

    rows = attestation.get("rows")
    if not isinstance(rows, list) or not rows:
        return False, sorted(set(failures + ["CASE_BOUND_SEMANTIC_FACTORIAL_ROWS_REQUIRED"]))

    normalized_rows: list[dict[str, Any]] = []
    seen_case_ids: set[tuple[str, str]] = set()
    for index, row in enumerate(rows):
        prefix = f"CASE_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        split = str(row.get("split") or "").strip().upper()
        if split not in REQUIRED_SPLITS:
            failures.append(f"{prefix}_SPLIT_INVALID")
        family_id = row.get("family_id")
        if split in family_by_split and family_id != family_by_split[split]:
            failures.append(f"{prefix}_FAMILY_ID_MISMATCH")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
        elif split in REQUIRED_SPLITS:
            identity = (split, case_id)
            if identity in seen_case_ids:
                failures.append(f"{prefix}_DUPLICATE_CASE_ID")
            seen_case_ids.add(identity)
        if "seed" not in row:
            failures.append(f"{prefix}_SEED_REQUIRED")
        if not _sha256(row.get("prompt_sha256")):
            failures.append(f"{prefix}_PROMPT_SHA256_REQUIRED")

        semantic_target = str(row.get("semantic_target") or "").strip().upper()
        if semantic_target not in REQUIRED_SEMANTIC_TARGETS:
            failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
        output_code = str(row.get("output_code_identity") or "").strip().upper()
        if output_code not in REQUIRED_OUTPUT_CODES:
            failures.append(f"{prefix}_OUTPUT_CODE_IDENTITY_INVALID")

        receipts = row.get("control_runtime_receipts")
        scores = row.get("control_target_scores")
        if not isinstance(receipts, dict):
            failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPTS_REQUIRED")
            receipts = {}
        if not isinstance(scores, dict):
            failures.append(f"{prefix}_CONTROL_TARGET_SCORES_REQUIRED")
            scores = {}
        for control in v4.REQUIRED_CONTROLS:
            if not _sha256(receipts.get(control)):
                failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPT_REQUIRED:{control}")
            if not _finite_number(scores.get(control)):
                failures.append(f"{prefix}_FINITE_CONTROL_TARGET_SCORE_REQUIRED:{control}")

        normalized_rows.append(row)

    # Bind the full row universe independent of input ordering.
    sorted_rows = sorted(
        normalized_rows,
        key=lambda row: (
            str(row.get("split") or ""),
            str(row.get("family_id") or ""),
            str(row.get("case_id") or ""),
        ),
    )
    case_universe_sha = _canonical_sha256(sorted_rows)
    if attestation.get("case_universe_sha256") != case_universe_sha:
        failures.append("CASE_UNIVERSE_SHA256_MISMATCH")

    contingency: dict[str, dict[str, int]] = {split: {} for split in REQUIRED_SPLITS}
    treatment_effects: dict[str, dict[str, list[float]]] = {split: {} for split in REQUIRED_SPLITS}
    for row in normalized_rows:
        split = str(row.get("split") or "").strip().upper()
        target = str(row.get("semantic_target") or "").strip().upper()
        code = str(row.get("output_code_identity") or "").strip().upper()
        scores = row.get("control_target_scores")
        if split not in REQUIRED_SPLITS or target not in REQUIRED_SEMANTIC_TARGETS or code not in REQUIRED_OUTPUT_CODES:
            continue
        cell = f"{target}|{code}"
        contingency[split][cell] = contingency[split].get(cell, 0) + 1
        if isinstance(scores, dict) and _finite_number(scores.get("+VECTOR")) and _finite_number(scores.get("BASELINE")):
            treatment_effects[split].setdefault(target, []).append(
                float(scores["+VECTOR"]) - float(scores["BASELINE"])
            )

    expected_cells = {f"{target}|{code}" for target in REQUIRED_SEMANTIC_TARGETS for code in REQUIRED_OUTPUT_CODES}
    for split in REQUIRED_SPLITS:
        counts = contingency[split]
        if set(counts) != expected_cells:
            failures.append(f"{split}_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_INCOMPLETE")
        elif len(set(counts.values())) != 1 or next(iter(counts.values()), 0) <= 0:
            failures.append(f"{split}_SEMANTIC_TARGET_X_OUTPUT_CODE_FACTORIAL_UNBALANCED")

    factorial_material = {
        "schema": CASE_ATTESTATION_SCHEMA,
        "case_universe_sha256": case_universe_sha,
        "families": family_by_split,
        "contingency": {
            split: {key: contingency[split][key] for key in sorted(contingency[split])}
            for split in REQUIRED_SPLITS
        },
    }
    factorial_receipt_sha = _canonical_sha256(factorial_material)
    if attestation.get("factorial_receipt_sha256") != factorial_receipt_sha:
        failures.append("FACTORIAL_RECEIPT_SHA256_MISMATCH")

    recomputed_summary: dict[str, Any] = {}
    for split in REQUIRED_SPLITS:
        family_id = family_by_split.get(split)
        means: dict[str, float] = {}
        for target in sorted(REQUIRED_SEMANTIC_TARGETS):
            values = treatment_effects[split].get(target, [])
            if not values:
                failures.append(f"{split}_TREATMENT_EFFECT_MISSING:{target}")
                continue
            means[target] = sum(values) / len(values)
        if len(means) == len(REQUIRED_SEMANTIC_TARGETS):
            recomputed_summary[str(family_id)] = {
                "split": split,
                "mean_plus_minus_baseline_by_semantic_target": means,
                "interaction_span": max(means.values()) - min(means.values()),
            }

    analysis = attestation.get("interaction_analysis")
    if not isinstance(analysis, dict):
        failures.append("INTERACTION_ANALYSIS_OBJECT_REQUIRED")
        analysis = {}
    if analysis.get("case_universe_sha256") != case_universe_sha:
        failures.append("INTERACTION_ANALYSIS_CASE_UNIVERSE_MISMATCH")
    if analysis.get("factorial_receipt_sha256") != factorial_receipt_sha:
        failures.append("INTERACTION_ANALYSIS_FACTORIAL_RECEIPT_MISMATCH")
    metric_sha = holdout.get("metric_definition_sha256")
    if not _sha256(metric_sha) or analysis.get("metric_definition_sha256") != metric_sha:
        failures.append("INTERACTION_ANALYSIS_METRIC_DEFINITION_MISMATCH")
    if not _sha256(analysis.get("analysis_implementation_sha256")):
        failures.append("INTERACTION_ANALYSIS_IMPLEMENTATION_SHA256_REQUIRED")
    if analysis.get("semantic_target_interaction_test") is not True:
        failures.append("INTERACTION_ANALYSIS_SEMANTIC_TARGET_TEST_REQUIRED")
    if analysis.get("per_family_semantic_target_interaction") is not True:
        failures.append("INTERACTION_ANALYSIS_PER_FAMILY_TEST_REQUIRED")

    declared_summary = analysis.get("family_interaction_summary")
    if declared_summary != recomputed_summary:
        failures.append("INTERACTION_ANALYSIS_RECOMPUTED_SUMMARY_MISMATCH")

    analysis_core = {key: value for key, value in analysis.items() if key != "interaction_analysis_receipt_sha256"}
    expected_analysis_receipt = _canonical_sha256(analysis_core)
    if analysis.get("interaction_analysis_receipt_sha256") != expected_analysis_receipt:
        failures.append("INTERACTION_ANALYSIS_RECEIPT_SHA256_MISMATCH")

    return not failures, sorted(set(failures))


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v4.adjudicate(candidate)
    extra_ok, extra_failures = _extra_specificity_evidence(candidate)
    case_bound_ok, case_bound_failures = _case_bound_semantic_factorial_evidence(candidate)

    mechanism = base.get("mechanism_runtime_vector_credit_candidate") is True
    v4_scientific = base.get("scientifically_independent_vector_candidate") is True
    v4_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    scientific = bool(mechanism and v4_scientific and extra_ok and case_bound_ok)
    owner = bool(v4_owner and extra_ok and case_bound_ok)

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v4_scientific_independence_candidate": bool(v4_scientific),
        "v5_specificity_controls_pass": bool(extra_ok),
        "case_bound_semantic_factorial_evidence_pass": bool(case_bound_ok),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "v5_specificity_failures": extra_failures,
        "case_bound_semantic_factorial_failures": case_bound_failures,
        "owner_target_failures": sorted(
            set(base.get("owner_target_failures", []) + extra_failures + case_bound_failures)
        ),
        "evidence_boundary": (
            "v5 composes v4 and adds scientific-promotion metrology plus case-bound evidence authenticity. "
            "A positive v5 candidate must survive label-free/lexically-disjoint derivation, label-only nuisance "
            "control, semantic-target x output-code factorial evaluation reconstructed from exact case rows, "
            "calibration-only residual-norm operating-point selection, cross-family coherence, frozen holdout/"
            "off-target thresholds, explicit intervention scope, all-six-control per-case receipt binding, and "
            "a per-family treatment-by-semantic-target summary recomputed from the same case universe. The "
            "verdict never mints canonical semantics, J-Space model runtime, training, HCU, EntityOS, or "
            "whole-product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "v5_specificity_failures": [],
            "case_bound_semantic_factorial_failures": [],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "v5_specificity_failures": [],
            "case_bound_semantic_factorial_failures": [],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    goal = any(item.get("owner_trigger1_goal_credit_candidate") is True for item in verdicts)
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "mechanism_runtime_vector_credit_candidate": any(
            item.get("mechanism_runtime_vector_credit_candidate") is True for item in verdicts
        ),
        "scientifically_independent_vector_candidate": any(
            item.get("scientifically_independent_vector_candidate") is True for item in verdicts
        ),
        "owner_trigger1_goal_credit_candidate": goal,
        "owner_trigger1_direct_free_api_model_credit_candidate": goal,
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
