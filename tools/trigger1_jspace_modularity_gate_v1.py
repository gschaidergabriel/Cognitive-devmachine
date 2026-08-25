#!/usr/bin/env python3
"""Additive fail-closed modularity gate above Trigger-1 scientific-specificity v5.

The v5 promotion gate answers whether a vector candidate has the required mechanism,
identity, semantic-independence, nuisance, calibration, off-target and token-scope
evidence. This companion gate asks a different question: is an otherwise valid semantic
control candidate sufficiently *modular* to be represented as a reusable HCU/J-Space
control primitive?

Modularity requires structured intervention-by-sentinel cross-effect evidence. If the
semantic control geometry is rank-2, it additionally requires held-out compositionality
evidence for coefficient combinations. The gate is adjudication only: it runs no model,
opens no holdout, changes no EffectGate authority, and mints no canonical/J-Space/HCU/
training/whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v5 as v5

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_GATE/v1"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_BATCH_SCAN/v1"
ALLOWED_RANKS = {1, 2}
REQUIRED_SENTINELS = {
    "GENERIC_INSTRUCTION_CODE_COMPLIANCE",
    "CONFIDENCE_OR_DECISIVENESS_PROXY",
    "NONSEMANTIC_CODEBOOK_ACCURACY",
    "LEXICALLY_MATCHED_UNRELATED_CLASSIFICATION",
    "BOUNDED_SAFETY_OR_PROTOCOL_BEHAVIOR",
}


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _positive_int(value: Any, minimum: int = 1) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


def _finite_nonnegative(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    number = float(value)
    return number >= 0.0 and number not in {float("inf"), float("-inf")} and number == number


def _cross_effect_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    modularity = candidate.get("modularity_evidence")
    if not isinstance(modularity, dict):
        return False, ["MODULARITY_EVIDENCE_REQUIRED"]

    if modularity.get("sentinel_set_preregistered") is not True:
        failures.append("SENTINEL_SET_MUST_BE_PREREGISTERED")
    if not _sha256(modularity.get("sentinel_set_receipt_sha256")):
        failures.append("SENTINEL_SET_RECEIPT_REQUIRED")
    sentinels = modularity.get("sentinel_behaviors")
    normalized = {str(value).strip().upper() for value in sentinels} if isinstance(sentinels, list) else set()
    if not REQUIRED_SENTINELS.issubset(normalized):
        failures.append("REQUIRED_SENTINEL_BEHAVIOR_SET_MISSING")
    if not _positive_int(modularity.get("sentinel_behavior_count"), len(REQUIRED_SENTINELS)):
        failures.append("SUFFICIENT_SENTINEL_BEHAVIOR_COUNT_REQUIRED")
    if not _positive_int(modularity.get("heldout_scenario_family_count"), 3):
        failures.append("AT_LEAST_THREE_HELDOUT_SCENARIO_FAMILIES_REQUIRED")

    if modularity.get("cross_effect_matrix_test") is not True:
        failures.append("CROSS_EFFECT_MATRIX_TEST_REQUIRED")
    if not _sha256(modularity.get("cross_effect_matrix_receipt_sha256")):
        failures.append("CROSS_EFFECT_MATRIX_RECEIPT_REQUIRED")
    if modularity.get("equal_family_weighting") is not True:
        failures.append("CROSS_EFFECT_EQUAL_FAMILY_WEIGHTING_REQUIRED")
    if modularity.get("per_family_signed_cross_effects_recorded") is not True:
        failures.append("PER_FAMILY_SIGNED_CROSS_EFFECTS_REQUIRED")
    if modularity.get("per_family_cross_effect_stability_test") is not True:
        failures.append("PER_FAMILY_CROSS_EFFECT_STABILITY_TEST_REQUIRED")
    if modularity.get("target_selectivity_preserved_across_families") is not True:
        failures.append("TARGET_SELECTIVITY_NOT_FAMILY_STABLE")

    if modularity.get("cross_effect_thresholds_selected_on_calibration_only") is not True:
        failures.append("CROSS_EFFECT_THRESHOLDS_MUST_BE_CALIBRATION_ONLY")
    if modularity.get("cross_effect_thresholds_frozen_before_holdout") is not True:
        failures.append("CROSS_EFFECT_THRESHOLDS_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(modularity.get("cross_effect_threshold_receipt_sha256")):
        failures.append("CROSS_EFFECT_THRESHOLD_RECEIPT_REQUIRED")

    max_drift = modularity.get("max_abs_standardized_sentinel_drift")
    threshold = modularity.get("preregistered_max_abs_standardized_sentinel_drift")
    if not _finite_nonnegative(max_drift):
        failures.append("FINITE_NONNEGATIVE_MAX_SENTINEL_DRIFT_REQUIRED")
    if not _finite_nonnegative(threshold):
        failures.append("FINITE_NONNEGATIVE_SENTINEL_DRIFT_THRESHOLD_REQUIRED")
    if (
        _finite_nonnegative(max_drift)
        and _finite_nonnegative(threshold)
        and float(max_drift) > float(threshold)
    ):
        failures.append("SENTINEL_CROSS_EFFECT_EXCEEDS_PREREGISTERED_BOUND")
    if modularity.get("all_sentinel_effects_within_preregistered_bounds") is not True:
        failures.append("ALL_SENTINEL_EFFECTS_MUST_BE_WITHIN_PREREGISTERED_BOUNDS")
    if modularity.get("structured_nuisance_control_reproduces_target_matrix") is not False:
        failures.append("STRUCTURED_NUISANCE_CONTROL_MUST_NOT_REPRODUCE_TARGET_MATRIX")

    forecast = modularity.get("pre_intervention_forecast")
    if forecast is not None:
        if not isinstance(forecast, dict):
            failures.append("PRE_INTERVENTION_FORECAST_MUST_BE_OBJECT")
        else:
            if forecast.get("diagnostic_only") is not True:
                failures.append("SIDE_EFFECT_FORECAST_MUST_BE_DIAGNOSTIC_ONLY")
            if forecast.get("used_to_select_holdout_thresholds") is not False:
                failures.append("SIDE_EFFECT_FORECAST_MUST_NOT_SELECT_HOLDOUT_THRESHOLDS")
            if forecast.get("uses_holdout_outcomes_for_fit") is not False:
                failures.append("SIDE_EFFECT_FORECAST_MUST_NOT_FIT_ON_HOLDOUT_OUTCOMES")
            if not _sha256(forecast.get("receipt_sha256")):
                failures.append("SIDE_EFFECT_FORECAST_RECEIPT_REQUIRED")

    return not failures, sorted(set(failures))


def _composition_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], int | None]:
    failures: list[str] = []
    subspace = candidate.get("semantic_subspace")
    if not isinstance(subspace, dict):
        return False, ["SEMANTIC_SUBSPACE_EVIDENCE_REQUIRED"], None

    rank = subspace.get("rank")
    if rank not in ALLOWED_RANKS:
        return False, ["SEMANTIC_SUBSPACE_RANK_MUST_BE_1_OR_2"], None
    if not _sha256(subspace.get("rank_decision_receipt_sha256")):
        failures.append("SEMANTIC_SUBSPACE_RANK_DECISION_RECEIPT_REQUIRED")
    if subspace.get("rank_selected_before_holdout") is not True:
        failures.append("SEMANTIC_SUBSPACE_RANK_MUST_BE_SELECTED_BEFORE_HOLDOUT")

    if rank == 1:
        return not failures, sorted(set(failures)), 1

    composition = candidate.get("composition_evidence")
    if not isinstance(composition, dict):
        failures.append("RANK2_COMPOSITION_EVIDENCE_REQUIRED")
        return False, sorted(set(failures)), 2

    if composition.get("combination_grid_frozen_before_holdout") is not True:
        failures.append("RANK2_COMBINATION_GRID_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(composition.get("combination_grid_receipt_sha256")):
        failures.append("RANK2_COMBINATION_GRID_RECEIPT_REQUIRED")
    if composition.get("composition_model_fit_on_calibration_only") is not True:
        failures.append("RANK2_COMPOSITION_MODEL_MUST_BE_CALIBRATION_ONLY")
    if not _sha256(composition.get("composition_model_receipt_sha256")):
        failures.append("RANK2_COMPOSITION_MODEL_RECEIPT_REQUIRED")
    if composition.get("same_residual_norm_relative_dose") is not True:
        failures.append("RANK2_COMPOSITION_DOSE_MUST_BE_NORM_MATCHED")
    if not _sha256(composition.get("combined_intervention_receipt_sha256")):
        failures.append("RANK2_COMBINED_INTERVENTION_RECEIPT_REQUIRED")
    if composition.get("heldout_compositional_residual_test") is not True:
        failures.append("RANK2_HELDOUT_COMPOSITIONAL_RESIDUAL_TEST_REQUIRED")
    if not _sha256(composition.get("compositional_residual_metric_sha256")):
        failures.append("RANK2_COMPOSITIONAL_RESIDUAL_METRIC_RECEIPT_REQUIRED")
    if composition.get("target_and_sentinel_endpoints_included") is not True:
        failures.append("RANK2_TARGET_AND_SENTINEL_ENDPOINTS_REQUIRED")
    if composition.get("per_family_residuals_recorded") is not True:
        failures.append("RANK2_PER_FAMILY_RESIDUALS_REQUIRED")
    if not _sha256(composition.get("compositional_residual_receipt_sha256")):
        failures.append("RANK2_COMPOSITIONAL_RESIDUAL_RECEIPT_REQUIRED")

    max_residual = composition.get("max_abs_standardized_compositional_residual")
    residual_threshold = composition.get("preregistered_max_abs_standardized_compositional_residual")
    if not _finite_nonnegative(max_residual):
        failures.append("FINITE_NONNEGATIVE_COMPOSITIONAL_RESIDUAL_REQUIRED")
    if not _finite_nonnegative(residual_threshold):
        failures.append("FINITE_NONNEGATIVE_COMPOSITIONAL_RESIDUAL_THRESHOLD_REQUIRED")
    if (
        _finite_nonnegative(max_residual)
        and _finite_nonnegative(residual_threshold)
        and float(max_residual) > float(residual_threshold)
    ):
        failures.append("RANK2_COMPOSITIONAL_RESIDUAL_EXCEEDS_PREREGISTERED_BOUND")
    if composition.get("compositional_residuals_within_preregistered_bounds") is not True:
        failures.append("RANK2_COMPOSITIONAL_RESIDUALS_MUST_BE_WITHIN_PREREGISTERED_BOUNDS")
    if composition.get("systematic_sign_interaction_missed_by_model") is not False:
        failures.append("RANK2_SYSTEMATIC_SIGN_INTERACTION_MUST_BE_ABSENT")
    if composition.get("family_consistency_pass") is not True:
        failures.append("RANK2_COMPOSITION_NOT_FAMILY_STABLE")

    return not failures, sorted(set(failures)), 2


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v5.adjudicate(candidate)
    cross_ok, cross_failures = _cross_effect_evidence(candidate)
    composition_ok, composition_failures, rank = _composition_evidence(candidate)

    v5_scientific = base.get("scientifically_independent_vector_candidate") is True
    modular = bool(v5_scientific and cross_ok and composition_ok)
    failures = sorted(set(cross_failures + composition_failures))

    if modular:
        classification = "BOUNDED_MODULAR_CONTROL_CANDIDATE"
    elif v5_scientific and any(
        item in cross_failures
        for item in (
            "SENTINEL_CROSS_EFFECT_EXCEEDS_PREREGISTERED_BOUND",
            "ALL_SENTINEL_EFFECTS_MUST_BE_WITHIN_PREREGISTERED_BOUNDS",
        )
    ):
        classification = "ENTANGLED_CONTROL_WITH_STRUCTURED_CROSS_EFFECTS"
    elif v5_scientific and rank == 2 and any(item.startswith("RANK2_") for item in composition_failures):
        classification = "RANK2_NONLINEAR_OR_COMPOSITION_UNRESOLVED"
    else:
        classification = "MODULARITY_UNRESOLVED_OR_UPSTREAM_BLOCKED"

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v5_scientifically_independent_vector_candidate": bool(v5_scientific),
        "cross_effect_controls_pass": bool(cross_ok),
        "composition_controls_pass": bool(composition_ok),
        "semantic_subspace_rank": rank,
        "modular_jspace_control_candidate": modular,
        "modularity_classification": classification,
        "modularity_failures": failures,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "effect_authority_changed": False,
        "evidence_boundary": (
            "This companion composes Trigger-1 v5 without weakening it. A modular control candidate must first "
            "be a v5 scientifically independent vector candidate, then pass a preregistered structured held-out "
            "sentinel cross-effect matrix with explicit numerical bounds and family stability. Rank-2 candidates "
            "additionally require exact rank-decision provenance plus calibration-frozen held-out compositional "
            "residual evidence at norm-matched dose. The verdict is bounded control-architecture metrology only "
            "and never mints canonical semantics, J-Space model-runtime, HCU, EntityOS, training, whole-product, "
            "or real-effect authority."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "modular_jspace_control_candidate": False,
            "modularity_classification": "MODULARITY_UNRESOLVED_OR_UPSTREAM_BLOCKED",
            "modularity_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "effect_authority_changed": False,
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "modular_jspace_control_candidate": False,
            "modularity_classification": "MODULARITY_UNRESOLVED_OR_UPSTREAM_BLOCKED",
            "modularity_failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "effect_authority_changed": False,
        }
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "modular_jspace_control_candidate": any(
            item.get("modular_jspace_control_candidate") is True for item in verdicts
        ),
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
