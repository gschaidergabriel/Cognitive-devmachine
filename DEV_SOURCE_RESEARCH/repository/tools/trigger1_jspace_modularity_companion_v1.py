#!/usr/bin/env python3
"""Fail-closed modularity companion for Trigger-1 J-Space steering candidates.

This companion composes the current promotion-v6 semantic-specificity adjudicator without weakening it.
It asks a strictly narrower downstream question: is an already semantic-specific steering
candidate also a bounded, reusable HCU/J-Space control primitive?

A scalar off-target PASS is not enough. The companion requires a preregistered structured
intervention-by-sentinel cross-effect matrix with equal family weighting and family-level
receipts. If calibration-only rank metrology requires two semantic dimensions, v6 also
requires a frozen held-out compositionality test before exposing a simple coefficient ABI.

The gate never runs a model and never mints canonical truth, real-effect authority,
J-Space model runtime, HCU-full, EntityOS-whole, or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v6 as promotion_v6

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_COMPANION/v1"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_COMPANION_BATCH/v1"
RANK_DECISIONS = {"ONE_DIMENSIONAL_SUPPORTED", "TWO_DIMENSIONAL_REQUIRED", "UNRESOLVED"}
MANDATORY_SENTINELS = {
    "GENERIC_INSTRUCTION_CODE_COMPLIANCE",
    "RESPONSE_CONFIDENCE_DECISIVENESS",
    "NONSEMANTIC_CODEBOOK_ACCURACY",
    "LEXICALLY_MATCHED_UNRELATED_CLASSIFICATION",
}


def canonical_json_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _finite_positive(value: Any) -> bool:
    return _finite(value) and float(value) > 0.0


def _finite_nonnegative(value: Any) -> bool:
    return _finite(value) and float(value) >= 0.0


def _nonempty_unique_strings(value: Any) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    out: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            return None
        out.append(item.strip())
    if len(set(out)) != len(out):
        return None
    return out


def _extra_modularity_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    protocol = candidate.get("modularity_protocol")
    if not isinstance(protocol, dict):
        protocol = {}

    if protocol.get("frozen_before_holdout") is not True:
        failures.append("MODULARITY_PROTOCOL_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(protocol.get("protocol_sha256")):
        failures.append("MODULARITY_PROTOCOL_RECEIPT_REQUIRED")
    if protocol.get("equal_family_weighting") is not True:
        failures.append("EQUAL_FAMILY_WEIGHTING_REQUIRED")
    if protocol.get("family_level_signed_effects_preserved") is not True:
        failures.append("FAMILY_LEVEL_SIGNED_EFFECTS_REQUIRED")

    sentinels = _nonempty_unique_strings(protocol.get("sentinel_endpoints"))
    sentinel_set: set[str] = set(sentinels or [])
    if sentinels is None:
        failures.append("UNIQUE_SENTINEL_ENDPOINTS_REQUIRED")
    else:
        missing = sorted(MANDATORY_SENTINELS - sentinel_set)
        failures.extend(f"MANDATORY_SENTINEL_REQUIRED:{name}" for name in missing)
        expected_sentinel_sha = canonical_json_sha(sorted(sentinels))
        if protocol.get("sentinel_set_sha256") != expected_sentinel_sha:
            failures.append("SENTINEL_SET_DIGEST_MISMATCH")

    intervention_ids = _nonempty_unique_strings(protocol.get("modular_intervention_ids"))
    if intervention_ids is None:
        failures.append("UNIQUE_MODULAR_INTERVENTION_IDS_REQUIRED")
        intervention_ids = []

    rank = candidate.get("semantic_rank_decision")
    if rank not in RANK_DECISIONS:
        failures.append("SEMANTIC_RANK_DECISION_REQUIRED")
    elif rank == "UNRESOLVED":
        failures.append("SEMANTIC_RANK_MUST_BE_RESOLVED_BEFORE_MODULARITY_PROMOTION")
    elif rank == "TWO_DIMENSIONAL_REQUIRED" and len(intervention_ids) < 2:
        failures.append("RANK2_REQUIRES_AT_LEAST_TWO_MODULAR_INTERVENTION_IDS")

    threshold = protocol.get("preregistered_max_abs_standardized_cross_effect")
    if not _finite_positive(threshold):
        failures.append("PREREGISTERED_CROSS_EFFECT_THRESHOLD_REQUIRED")
        threshold_value: float | None = None
    else:
        threshold_value = float(threshold)

    cells = protocol.get("cross_effect_matrix")
    if not isinstance(cells, list) or not cells:
        failures.append("STRUCTURED_CROSS_EFFECT_MATRIX_REQUIRED")
        cells = []

    seen_pairs: set[tuple[str, str]] = set()
    observed_max = 0.0
    valid_cell_count = 0
    for cell in cells:
        if not isinstance(cell, dict):
            failures.append("CROSS_EFFECT_CELL_OBJECT_REQUIRED")
            continue
        intervention_id = cell.get("intervention_id")
        sentinel_id = cell.get("sentinel_id")
        pair = (str(intervention_id), str(sentinel_id))
        if intervention_id not in intervention_ids:
            failures.append(f"CROSS_EFFECT_UNKNOWN_INTERVENTION:{intervention_id}")
        if sentinel_id not in sentinel_set:
            failures.append(f"CROSS_EFFECT_UNKNOWN_SENTINEL:{sentinel_id}")
        if pair in seen_pairs:
            failures.append(f"DUPLICATE_CROSS_EFFECT_CELL:{pair[0]}:{pair[1]}")
        seen_pairs.add(pair)

        mean_delta = cell.get("equal_family_weighted_standardized_delta")
        max_family = cell.get("max_abs_family_standardized_delta")
        family_count = cell.get("family_count")
        if not _finite(mean_delta):
            failures.append(f"CROSS_EFFECT_MEAN_FINITE_REQUIRED:{pair[0]}:{pair[1]}")
        if not _finite_nonnegative(max_family):
            failures.append(f"CROSS_EFFECT_FAMILY_MAX_FINITE_REQUIRED:{pair[0]}:{pair[1]}")
        if isinstance(family_count, bool) or not isinstance(family_count, int) or family_count < 3:
            failures.append(f"CROSS_EFFECT_AT_LEAST_THREE_FAMILIES_REQUIRED:{pair[0]}:{pair[1]}")
        if not _sha256(cell.get("per_family_effects_receipt_sha256")):
            failures.append(f"CROSS_EFFECT_FAMILY_RECEIPT_REQUIRED:{pair[0]}:{pair[1]}")
        if _finite(mean_delta) and _finite_nonnegative(max_family):
            abs_mean = abs(float(mean_delta))
            max_family_value = float(max_family)
            observed_max = max(observed_max, abs_mean, max_family_value)
            if max_family_value + 1e-12 < abs_mean:
                failures.append(f"CROSS_EFFECT_FAMILY_MAX_BELOW_POOLED_MEAN:{pair[0]}:{pair[1]}")
            if threshold_value is not None and (abs_mean > threshold_value or max_family_value > threshold_value):
                failures.append(f"CROSS_EFFECT_EXCEEDS_PREREGISTERED_BOUND:{pair[0]}:{pair[1]}")
            valid_cell_count += 1

    if sentinels is not None and intervention_ids:
        expected_pairs = {(i, s) for i in intervention_ids for s in sentinels}
        missing_pairs = sorted(expected_pairs - seen_pairs)
        extra_pairs = sorted(seen_pairs - expected_pairs)
        failures.extend(f"CROSS_EFFECT_CELL_MISSING:{i}:{s}" for i, s in missing_pairs)
        failures.extend(f"CROSS_EFFECT_CELL_UNDECLARED:{i}:{s}" for i, s in extra_pairs)

    if protocol.get("cross_effects_within_preregistered_bounds") is not True:
        failures.append("CROSS_EFFECTS_WITHIN_PREREGISTERED_BOUNDS_REQUIRED")
    if not _sha256(protocol.get("cross_effect_matrix_receipt_sha256")):
        failures.append("CROSS_EFFECT_MATRIX_RECEIPT_REQUIRED")

    composition_required = rank == "TWO_DIMENSIONAL_REQUIRED"
    composition = candidate.get("rank2_composition")
    composition_observed_max: float | None = None
    if composition_required:
        if not isinstance(composition, dict):
            composition = {}
            failures.append("RANK2_COMPOSITION_EVIDENCE_REQUIRED")
        if composition.get("preregistered_before_holdout") is not True:
            failures.append("RANK2_COMPOSITION_MUST_BE_PREREGISTERED")
        if composition.get("calibration_only_model_fit") is not True:
            failures.append("RANK2_COMPOSITION_MODEL_MUST_BE_CALIBRATION_ONLY")
        if composition.get("coefficient_grid_frozen_before_holdout") is not True:
            failures.append("RANK2_COEFFICIENT_GRID_MUST_BE_FROZEN_BEFORE_HOLDOUT")
        if not _sha256(composition.get("coefficient_grid_sha256")):
            failures.append("RANK2_COEFFICIENT_GRID_RECEIPT_REQUIRED")
        if composition.get("fresh_scenario_family_holdout") is not True:
            failures.append("RANK2_COMPOSITION_FRESH_SCENARIO_HOLDOUT_REQUIRED")
        combinations = composition.get("combinations_evaluated")
        if isinstance(combinations, bool) or not isinstance(combinations, int) or combinations < 4:
            failures.append("RANK2_AT_LEAST_FOUR_COMBINATIONS_REQUIRED")
        residual_threshold = composition.get("preregistered_max_abs_standardized_residual")
        residual_observed = composition.get("max_abs_standardized_residual")
        if not _finite_positive(residual_threshold):
            failures.append("RANK2_PREREGISTERED_RESIDUAL_THRESHOLD_REQUIRED")
        if not _finite_nonnegative(residual_observed):
            failures.append("RANK2_OBSERVED_RESIDUAL_REQUIRED")
        if _finite_positive(residual_threshold) and _finite_nonnegative(residual_observed):
            composition_observed_max = float(residual_observed)
            if float(residual_observed) > float(residual_threshold):
                failures.append("RANK2_COMPOSITION_RESIDUAL_EXCEEDS_PREREGISTERED_BOUND")
        if composition.get("systematic_sign_interaction_absent") is not True:
            failures.append("RANK2_SYSTEMATIC_SIGN_INTERACTION_MUST_BE_ABSENT")
        if not _sha256(composition.get("composition_receipt_sha256")):
            failures.append("RANK2_COMPOSITION_RECEIPT_REQUIRED")

    forecast = candidate.get("pre_intervention_cross_effect_forecast")
    if forecast is not None:
        if not isinstance(forecast, dict):
            failures.append("FORECAST_DIAGNOSTIC_OBJECT_REQUIRED")
        else:
            if forecast.get("used_to_adjust_holdout_thresholds") is not False:
                failures.append("FORECAST_MUST_NOT_ADJUST_HOLDOUT_THRESHOLDS")
            if forecast.get("used_to_relabel_holdout") is not False:
                failures.append("FORECAST_MUST_NOT_RELABEL_HOLDOUT")
            if forecast.get("diagnostic_only") is not True:
                failures.append("FORECAST_MUST_REMAIN_DIAGNOSTIC_ONLY")

    summary = {
        "semantic_rank_decision": rank,
        "sentinel_count": len(sentinels or []),
        "intervention_count": len(intervention_ids),
        "cross_effect_cells_seen": len(cells),
        "cross_effect_cells_numerically_valid": valid_cell_count,
        "observed_max_abs_standardized_cross_effect": observed_max,
        "preregistered_max_abs_standardized_cross_effect": threshold_value,
        "rank2_composition_required": composition_required,
        "rank2_observed_max_abs_standardized_residual": composition_observed_max,
    }
    return not failures, sorted(set(failures)), summary


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = promotion_v6.adjudicate(candidate)
    modularity_ok, modularity_failures, modularity_summary = _extra_modularity_evidence(candidate)
    semantic_specific = base.get("scientifically_independent_vector_candidate") is True
    modular = bool(semantic_specific and modularity_ok)
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "promotion_v6_scientifically_independent_vector_candidate": semantic_specific,
        "modularity_companion_controls_pass": bool(modularity_ok),
        "modular_hcu_jspace_control_candidate": modular,
        "modularity_failures": modularity_failures,
        "modularity_summary": modularity_summary,
        # Preserve the current promotion-v6 semantic adjudication as a separate question. The companion can only
        # reduce the stronger modular-control claim; it does not rewrite promotion-v6 history.
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "hcu_full_runtime_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "This companion is a modular-control adjudicator above current promotion-v6 semantic specificity. A PASS means only that the "
            "candidate has bounded preregistered structured cross-effects and, when rank-2 is required, "
            "bounded held-out composition residuals. It does not mint canonical semantics, model-runtime, "
            "HCU-full, EntityOS-whole, training, or real-effect authority."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "hcu_full_runtime_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "modularity_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "hcu_full_runtime_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "modularity_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
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
        "semantic_specific_candidate": any(v.get("scientifically_independent_vector_candidate") is True for v in verdicts),
        "modular_hcu_jspace_control_candidate": any(v.get("modular_hcu_jspace_control_candidate") is True for v in verdicts),
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
