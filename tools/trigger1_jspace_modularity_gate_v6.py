#!/usr/bin/env python3
"""Fail-closed modularity companion gate above Trigger-1 scientific specificity v5.

v5 answers whether a bound steering result is scientifically specific enough to remain a
semantic causal candidate. v6 asks a different, stricter systems question: is that
semantic actuator sufficiently modular to be considered a reusable coefficient-controlled
HCU/J-Space primitive? Target success alone is not enough.

The gate requires a structured intervention-by-sentinel cross-effect matrix. If the
retained semantic representation is rank-2, it additionally requires held-out
composition residuals against a calibration-frozen composition model. Forecasting side
effects is diagnostic only and can never repair a failed modularity bound.

This adjudicator never executes a model and never mints canonical truth, real-effect,
J-Space model runtime, HCU, EntityOS, training, BASE, or whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v5 as v5

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_GATE/v6"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_BATCH_SCAN/v6"
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


def _cross_effect_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    modularity = candidate.get("modularity_evidence")
    if not isinstance(modularity, dict):
        return False, ["MODULARITY_EVIDENCE_OBJECT_REQUIRED"]

    sentinels = modularity.get("sentinel_behaviors")
    normalized = {str(x).strip().upper() for x in sentinels} if isinstance(sentinels, list) else set()
    if not REQUIRED_SENTINELS.issubset(normalized):
        failures.append("REQUIRED_SENTINEL_BEHAVIOR_SET_MISSING")
    if not _sha256(modularity.get("cross_effect_matrix_receipt_sha256")):
        failures.append("CROSS_EFFECT_MATRIX_RECEIPT_REQUIRED")
    if modularity.get("equal_family_weighting") is not True:
        failures.append("CROSS_EFFECT_EQUAL_FAMILY_WEIGHTING_REQUIRED")
    if modularity.get("per_family_signed_cross_effects_preserved") is not True:
        failures.append("PER_FAMILY_SIGNED_CROSS_EFFECTS_REQUIRED")
    if not _positive_int(modularity.get("fresh_holdout_family_count"), 3):
        failures.append("AT_LEAST_THREE_FRESH_HOLDOUT_FAMILIES_REQUIRED")
    if modularity.get("cross_effect_thresholds_selected_on_calibration_only") is not True:
        failures.append("CROSS_EFFECT_THRESHOLDS_MUST_BE_CALIBRATION_ONLY")
    if not _sha256(modularity.get("cross_effect_threshold_rule_sha256")):
        failures.append("CROSS_EFFECT_THRESHOLD_RULE_RECEIPT_REQUIRED")
    if modularity.get("max_abs_standardized_drift_within_preregistered_bounds") is not True:
        failures.append("SENTINEL_CROSS_EFFECT_BOUND_EXCEEDED")
    if modularity.get("no_structured_nuisance_reproduces_target_matrix") is not True:
        failures.append("STRUCTURED_NUISANCE_REPRODUCES_TARGET_MATRIX")
    if modularity.get("target_selectivity_preserved_across_families") is not True:
        failures.append("TARGET_SELECTIVITY_NOT_FAMILY_STABLE")

    forecast = modularity.get("pre_intervention_forecast")
    if forecast is not None:
        if not isinstance(forecast, dict):
            failures.append("PRE_INTERVENTION_FORECAST_OBJECT_INVALID")
        else:
            if forecast.get("diagnostic_only") is not True:
                failures.append("FORECAST_MUST_BE_DIAGNOSTIC_ONLY")
            if forecast.get("used_to_adapt_holdout_thresholds") is not False:
                failures.append("FORECAST_MUST_NOT_ADAPT_HOLDOUT_THRESHOLDS")
            if forecast.get("performed") is True and not _sha256(forecast.get("receipt_sha256")):
                failures.append("FORECAST_RECEIPT_REQUIRED_WHEN_PERFORMED")

    return not failures, sorted(set(failures))


def _composition_evidence(candidate: dict[str, Any]) -> tuple[bool, bool, list[str]]:
    """Return (applicable, pass, failures). Rank-1 candidates do not need rank-2 composition."""
    failures: list[str] = []
    modularity = candidate.get("modularity_evidence")
    if not isinstance(modularity, dict):
        return False, False, ["MODULARITY_EVIDENCE_OBJECT_REQUIRED"]

    rank = modularity.get("representation_rank")
    if rank not in {1, 2}:
        return False, False, ["REPRESENTATION_RANK_1_OR_2_REQUIRED"]
    if rank == 1:
        return False, True, []

    comp = modularity.get("rank2_composition")
    if not isinstance(comp, dict):
        return True, False, ["RANK2_COMPOSITION_EVIDENCE_REQUIRED"]
    if comp.get("composition_model_fit_on_calibration_only") is not True:
        failures.append("COMPOSITION_MODEL_MUST_BE_CALIBRATION_ONLY")
    if comp.get("coefficient_grid_frozen_before_holdout") is not True:
        failures.append("COEFFICIENT_GRID_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if comp.get("same_residual_norm_relative_dose") is not True:
        failures.append("RANK2_COMPOSITION_DOSE_MUST_BE_NORM_MATCHED")
    if not _sha256(comp.get("composition_model_receipt_sha256")):
        failures.append("COMPOSITION_MODEL_RECEIPT_REQUIRED")
    if not _sha256(comp.get("combined_intervention_receipt_sha256")):
        failures.append("COMBINED_INTERVENTION_RECEIPT_REQUIRED")
    if not _sha256(comp.get("compositional_residual_metric_sha256")):
        failures.append("COMPOSITIONAL_RESIDUAL_METRIC_RECEIPT_REQUIRED")
    if comp.get("residual_tolerance_selected_on_calibration_only") is not True:
        failures.append("COMPOSITION_RESIDUAL_TOLERANCE_MUST_BE_CALIBRATION_ONLY")
    if comp.get("heldout_residuals_within_frozen_tolerance") is not True:
        failures.append("RANK2_HELDOUT_COMPOSITION_RESIDUAL_EXCEEDS_TOLERANCE")
    if comp.get("no_systematic_sign_interaction_missed") is not True:
        failures.append("RANK2_SYSTEMATIC_SIGN_INTERACTION_DETECTED")
    if comp.get("family_consistency_pass") is not True:
        failures.append("RANK2_COMPOSITION_NOT_FAMILY_STABLE")
    return True, not failures, sorted(set(failures))


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v5.adjudicate(candidate)
    cross_ok, cross_failures = _cross_effect_evidence(candidate)
    rank2_applicable, composition_ok, composition_failures = _composition_evidence(candidate)

    semantic_specific = base.get("scientifically_independent_vector_candidate") is True
    owner_goal = base.get("owner_trigger1_goal_credit_candidate") is True
    modular = bool(semantic_specific and owner_goal and cross_ok and composition_ok)
    rank2_abi = bool(modular and rank2_applicable and composition_ok)

    modularity = candidate.get("modularity_evidence") if isinstance(candidate.get("modularity_evidence"), dict) else {}
    forecast = modularity.get("pre_intervention_forecast") if isinstance(modularity.get("pre_intervention_forecast"), dict) else {}
    forecast_utility = bool(
        forecast.get("performed") is True
        and forecast.get("better_than_preregistered_null") is True
        and _sha256(forecast.get("receipt_sha256"))
    )

    failures = sorted(set(cross_failures + composition_failures))
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v5_semantic_specificity_candidate": bool(semantic_specific),
        "v5_owner_trigger1_goal_candidate": bool(owner_goal),
        "cross_effect_modularity_controls_pass": bool(cross_ok),
        "rank2_composition_applicable": bool(rank2_applicable),
        "rank2_composition_controls_pass": bool(composition_ok),
        "modular_hcu_jspace_control_candidate": modular,
        "linear_rank2_coefficient_abi_candidate": rank2_abi,
        "pre_intervention_cross_effect_forecast_utility_candidate": forecast_utility,
        "modularity_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v6 does not redefine Trigger-1 semantic causality: v5 remains the prerequisite. v6 only asks whether a "
            "scientifically specific actuator is sufficiently bounded and compositional to be a reusable HCU/J-Space "
            "control primitive. Large but forecastable side effects still fail modular promotion. Rank-2 activation-space "
            "linearity is insufficient without held-out behavioral composition residuals. No verdict mints canonical "
            "truth, real-effect authority, model-runtime, training, HCU, EntityOS, BASE, or whole-product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "modular_hcu_jspace_control_candidate": False,
            "linear_rank2_coefficient_abi_candidate": False,
            "canonical_credit_minted": False,
            "modularity_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "evidence_boundary": "Invalid candidate files fail closed."
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "modular_hcu_jspace_control_candidate": False,
            "linear_rank2_coefficient_abi_candidate": False,
            "canonical_credit_minted": False,
            "modularity_failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "evidence_boundary": "Invalid candidate files fail closed."
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
        "modular_hcu_jspace_control_candidate": any(
            item.get("modular_hcu_jspace_control_candidate") is True for item in verdicts
        ),
        "linear_rank2_coefficient_abi_candidate": any(
            item.get("linear_rank2_coefficient_abi_candidate") is True for item in verdicts
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
