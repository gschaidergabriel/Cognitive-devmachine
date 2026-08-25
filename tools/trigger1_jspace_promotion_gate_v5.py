#!/usr/bin/env python3
"""Successor fail-closed scientific-specificity gate for Trigger-1 J-Space claims.

This v5 layer composes the current v4 promotion gate instead of weakening or rewriting it.
It adds the measurement/confound controls required by the 2026-08-25 Forschungsrun-1
fusion: model-facing label-free / lexically disjoint vector derivation, a label-only
nuisance control, calibration-only residual-norm operating-point selection, target x
output-code factorial structure, cross-family direction-coherence evidence, frozen
holdout measurement, off-target drift control, and explicit token-scope classification.

The tool is adjudication only. It does not run a model, open a holdout, mint canonical
truth, or create EntityOS/HCU/J-Space/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate as v4

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v5"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v5"
LABEL_NUISANCE_CONTROL = "LABEL_ONLY_NUISANCE_VECTOR"
TOKEN_SCOPES = {"LAST_TOKEN_ONLY", "ALL_PROMPT_TOKENS"}
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"


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


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v4.adjudicate(candidate)
    extra_ok, extra_failures = _extra_specificity_evidence(candidate)

    mechanism = base.get("mechanism_runtime_vector_credit_candidate") is True
    v4_scientific = base.get("scientifically_independent_vector_candidate") is True
    v4_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    scientific = bool(mechanism and v4_scientific and extra_ok)
    owner = bool(v4_owner and extra_ok)

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v4_scientific_independence_candidate": bool(v4_scientific),
        "v5_specificity_controls_pass": bool(extra_ok),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "v5_specificity_failures": extra_failures,
        "owner_target_failures": sorted(set(base.get("owner_target_failures", []) + extra_failures)),
        "evidence_boundary": (
            "v5 composes v4 and adds scientific-promotion metrology only. A positive v5 candidate must "
            "survive label-free/lexically-disjoint derivation, label-only nuisance control, semantic-target "
            "x output-code factorial evaluation, calibration-only residual-norm operating-point selection, "
            "cross-family coherence, frozen holdout/off-target thresholds, and explicit intervention scope. "
            "The verdict never mints canonical semantics, J-Space model runtime, training, HCU, EntityOS, "
            "or whole-product credit."
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
