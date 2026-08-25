#!/usr/bin/env python3
"""Fail-closed Trigger-1 modular-control companion gate.

This gate composes the current semantic-specificity promotion gate (v5) but does not
redefine semantic causality.  It asks a strictly stronger, architecture-level question:
can a semantically valid steering direction/subspace be treated as a reusable modular
J-Space/HCU control primitive without hidden structured cross-effects, and, for rank-2,
without unmodelled nonlinear composition?

The gate is adjudication only.  It runs no model, opens no holdout, and mints no
canonical/J-Space/HCU/training/whole-product credit.  A candidate can therefore remain
v5-semantically valid while failing modular-control promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v5 as v5

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_MODULARITY_GATE/v1"
EVIDENCE_SCHEMA = "CLAY_TRIGGER1_CROSS_EFFECT_AND_COMPOSITION_EVIDENCE/v1"
RANK_DECISIONS = {"ONE_DIMENSIONAL_SUPPORTED", "TWO_DIMENSIONAL_REQUIRED"}
MIN_SENTINELS = 4
MIN_FAMILIES = 3


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


def _positive(value: Any) -> bool:
    return _finite(value) and float(value) > 0.0


def _string_list(value: Any, *, minimum: int = 1) -> list[str] | None:
    if not isinstance(value, list) or len(value) < minimum:
        return None
    if not all(isinstance(item, str) and item.strip() for item in value):
        return None
    normalized = [item.strip() for item in value]
    if len(set(normalized)) != len(normalized):
        return None
    return normalized


def _cross_effect_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    failures: list[str] = []
    evidence = candidate.get("control_modularity")
    if not isinstance(evidence, dict) or evidence.get("schema") != EVIDENCE_SCHEMA:
        return False, ["CONTROL_MODULARITY_EVIDENCE_SCHEMA_REQUIRED"], {}

    if evidence.get("frozen_before_holdout") is not True:
        failures.append("MODULARITY_PROTOCOL_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(evidence.get("protocol_sha256")):
        failures.append("MODULARITY_PROTOCOL_RECEIPT_REQUIRED")
    if evidence.get("target_selectivity_preserved") is not True:
        failures.append("TARGET_SELECTIVITY_MUST_REMAIN_PRESERVED")
    if evidence.get("structured_nuisance_control_not_reproduced") is not True:
        failures.append("STRUCTURED_NUISANCE_CONTROL_REJECTION_REQUIRED")

    rank = evidence.get("rank_selection")
    if not isinstance(rank, dict):
        rank = {}
        failures.append("RANK_SELECTION_EVIDENCE_REQUIRED")
    rank_decision = rank.get("decision")
    if rank_decision not in RANK_DECISIONS:
        failures.append("RESOLVED_RANK_DECISION_REQUIRED")
    if not _sha256(rank.get("receipt_sha256")):
        failures.append("RANK_SELECTION_RECEIPT_REQUIRED")
    if rank.get("holdout_opened_during_rank_selection") is not False:
        failures.append("RANK_SELECTION_MUST_BE_CALIBRATION_ONLY")

    interventions = _string_list(evidence.get("intervention_ids"), minimum=1)
    if interventions is None:
        interventions = []
        failures.append("UNIQUE_INTERVENTION_IDS_REQUIRED")
    elif rank_decision == "TWO_DIMENSIONAL_REQUIRED" and len(interventions) < 2:
        failures.append("RANK2_REQUIRES_AT_LEAST_TWO_BASIS_INTERVENTIONS")

    families = _string_list(evidence.get("family_ids"), minimum=MIN_FAMILIES)
    if families is None:
        families = []
        failures.append("AT_LEAST_THREE_UNIQUE_FAMILY_IDS_REQUIRED")

    raw_sentinels = evidence.get("sentinels")
    sentinels: dict[str, float] = {}
    if not isinstance(raw_sentinels, list) or len(raw_sentinels) < MIN_SENTINELS:
        failures.append("AT_LEAST_FOUR_SENTINELS_REQUIRED")
    else:
        for index, item in enumerate(raw_sentinels):
            if not isinstance(item, dict):
                failures.append(f"SENTINEL_OBJECT_REQUIRED:{index}")
                continue
            sentinel_id = item.get("sentinel_id")
            threshold = item.get("threshold_abs_standardized")
            if not isinstance(sentinel_id, str) or not sentinel_id.strip():
                failures.append(f"SENTINEL_ID_REQUIRED:{index}")
                continue
            sentinel_id = sentinel_id.strip()
            if sentinel_id in sentinels:
                failures.append(f"SENTINEL_ID_DUPLICATE:{sentinel_id}")
                continue
            if not _positive(threshold):
                failures.append(f"SENTINEL_POSITIVE_THRESHOLD_REQUIRED:{sentinel_id}")
                continue
            if item.get("threshold_frozen_before_holdout") is not True:
                failures.append(f"SENTINEL_THRESHOLD_NOT_FROZEN:{sentinel_id}")
            sentinels[sentinel_id] = float(threshold)

    if not _sha256(evidence.get("cross_effect_matrix_receipt_sha256")):
        failures.append("CROSS_EFFECT_MATRIX_RECEIPT_REQUIRED")

    rows = evidence.get("cross_effect_rows")
    seen: set[tuple[str, str, str]] = set()
    max_abs_by_sentinel = {sentinel_id: 0.0 for sentinel_id in sentinels}
    if not isinstance(rows, list):
        failures.append("CROSS_EFFECT_ROWS_REQUIRED")
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"CROSS_EFFECT_ROW_OBJECT_REQUIRED:{index}")
            continue
        intervention_id = row.get("intervention_id")
        sentinel_id = row.get("sentinel_id")
        family_id = row.get("family_id")
        key = (str(intervention_id), str(sentinel_id), str(family_id))
        if intervention_id not in interventions:
            failures.append(f"CROSS_EFFECT_UNKNOWN_INTERVENTION:{index}")
            continue
        if sentinel_id not in sentinels:
            failures.append(f"CROSS_EFFECT_UNKNOWN_SENTINEL:{index}")
            continue
        if family_id not in families:
            failures.append(f"CROSS_EFFECT_UNKNOWN_FAMILY:{index}")
            continue
        if key in seen:
            failures.append(f"CROSS_EFFECT_DUPLICATE_CELL:{intervention_id}:{sentinel_id}:{family_id}")
            continue
        seen.add(key)
        delta = row.get("standardized_delta")
        if not _finite(delta):
            failures.append(f"CROSS_EFFECT_FINITE_DELTA_REQUIRED:{intervention_id}:{sentinel_id}:{family_id}")
            continue
        if not _sha256(row.get("runtime_receipt_sha256")):
            failures.append(f"CROSS_EFFECT_RUNTIME_RECEIPT_REQUIRED:{intervention_id}:{sentinel_id}:{family_id}")
        max_abs_by_sentinel[sentinel_id] = max(max_abs_by_sentinel[sentinel_id], abs(float(delta)))

    expected = {
        (intervention_id, sentinel_id, family_id)
        for intervention_id in interventions
        for sentinel_id in sentinels
        for family_id in families
    }
    missing = expected - seen
    if missing:
        failures.append(f"CROSS_EFFECT_MATRIX_INCOMPLETE:{len(missing)}")
    for sentinel_id, threshold in sentinels.items():
        if max_abs_by_sentinel[sentinel_id] > threshold + 1e-12:
            failures.append(f"SENTINEL_BOUND_EXCEEDED:{sentinel_id}")

    summary = {
        "rank_decision": rank_decision,
        "intervention_count": len(interventions),
        "family_count": len(families),
        "sentinel_count": len(sentinels),
        "cross_effect_cells_expected": len(expected),
        "cross_effect_cells_seen": len(seen),
        "max_abs_standardized_effect_by_sentinel": max_abs_by_sentinel,
    }
    return not failures, sorted(set(failures)), summary


def _composition_evidence(candidate: dict[str, Any], rank_decision: Any) -> tuple[bool, list[str], dict[str, Any]]:
    if rank_decision != "TWO_DIMENSIONAL_REQUIRED":
        return True, [], {"required": False, "reason": "RANK1_CONTROL"}

    failures: list[str] = []
    evidence = candidate.get("control_modularity")
    if not isinstance(evidence, dict):
        return False, ["CONTROL_MODULARITY_EVIDENCE_REQUIRED_FOR_COMPOSITION"], {}
    composition = evidence.get("composition")
    if not isinstance(composition, dict):
        return False, ["RANK2_COMPOSITION_EVIDENCE_REQUIRED"], {"required": True}

    if composition.get("model_frozen_on_calibration_only") is not True:
        failures.append("COMPOSITION_MODEL_MUST_BE_FROZEN_ON_CALIBRATION_ONLY")
    if composition.get("coefficient_grid_frozen_before_holdout") is not True:
        failures.append("COMPOSITION_COEFFICIENT_GRID_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if composition.get("no_systematic_sign_interaction_missed") is not True:
        failures.append("COMPOSITION_SYSTEMATIC_SIGN_INTERACTION_REJECTION_REQUIRED")
    if not _sha256(composition.get("composition_receipt_sha256")):
        failures.append("COMPOSITION_RECEIPT_REQUIRED")

    tolerance = composition.get("tolerance_abs_standardized_residual")
    if not _positive(tolerance):
        failures.append("POSITIVE_COMPOSITION_RESIDUAL_TOLERANCE_REQUIRED")
        tolerance_value = None
    else:
        tolerance_value = float(tolerance)

    combinations = _string_list(composition.get("combination_ids"), minimum=1)
    if combinations is None:
        combinations = []
        failures.append("UNIQUE_COMBINATION_IDS_REQUIRED")
    endpoints = _string_list(composition.get("endpoint_ids"), minimum=1)
    if endpoints is None:
        endpoints = []
        failures.append("UNIQUE_COMPOSITION_ENDPOINT_IDS_REQUIRED")
    target_endpoint = composition.get("target_endpoint_id")
    if target_endpoint not in endpoints:
        failures.append("TARGET_ENDPOINT_MUST_BE_IN_COMPOSITION_ENDPOINTS")

    families = _string_list(evidence.get("family_ids"), minimum=MIN_FAMILIES) or []
    sentinel_ids = {
        item.get("sentinel_id")
        for item in evidence.get("sentinels", [])
        if isinstance(item, dict) and isinstance(item.get("sentinel_id"), str)
    }
    if sentinel_ids and not sentinel_ids.issubset(set(endpoints)):
        failures.append("ALL_SENTINELS_MUST_BE_COMPOSITION_ENDPOINTS")

    rows = composition.get("rows")
    seen: set[tuple[str, str, str]] = set()
    max_abs_residual = 0.0
    if not isinstance(rows, list):
        failures.append("COMPOSITION_ROWS_REQUIRED")
        rows = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            failures.append(f"COMPOSITION_ROW_OBJECT_REQUIRED:{index}")
            continue
        combination_id = row.get("combination_id")
        endpoint_id = row.get("endpoint_id")
        family_id = row.get("family_id")
        if combination_id not in combinations:
            failures.append(f"COMPOSITION_UNKNOWN_COMBINATION:{index}")
            continue
        if endpoint_id not in endpoints:
            failures.append(f"COMPOSITION_UNKNOWN_ENDPOINT:{index}")
            continue
        if family_id not in families:
            failures.append(f"COMPOSITION_UNKNOWN_FAMILY:{index}")
            continue
        key = (combination_id, endpoint_id, family_id)
        if key in seen:
            failures.append(f"COMPOSITION_DUPLICATE_CELL:{combination_id}:{endpoint_id}:{family_id}")
            continue
        seen.add(key)
        predicted = row.get("predicted_delta")
        observed = row.get("observed_delta")
        if not _finite(predicted) or not _finite(observed):
            failures.append(f"COMPOSITION_FINITE_DELTAS_REQUIRED:{combination_id}:{endpoint_id}:{family_id}")
            continue
        if not _sha256(row.get("runtime_receipt_sha256")):
            failures.append(f"COMPOSITION_RUNTIME_RECEIPT_REQUIRED:{combination_id}:{endpoint_id}:{family_id}")
        residual = abs(float(observed) - float(predicted))
        max_abs_residual = max(max_abs_residual, residual)
        if tolerance_value is not None and residual > tolerance_value + 1e-12:
            failures.append(f"COMPOSITION_RESIDUAL_BOUND_EXCEEDED:{combination_id}:{endpoint_id}:{family_id}")

    expected = {
        (combination_id, endpoint_id, family_id)
        for combination_id in combinations
        for endpoint_id in endpoints
        for family_id in families
    }
    missing = expected - seen
    if missing:
        failures.append(f"COMPOSITION_MATRIX_INCOMPLETE:{len(missing)}")

    summary = {
        "required": True,
        "combination_count": len(combinations),
        "endpoint_count": len(endpoints),
        "family_count": len(families),
        "cells_expected": len(expected),
        "cells_seen": len(seen),
        "max_abs_standardized_residual": max_abs_residual,
        "tolerance_abs_standardized_residual": tolerance_value,
    }
    return not failures, sorted(set(failures)), summary


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v5.adjudicate(candidate)
    cross_ok, cross_failures, cross_summary = _cross_effect_evidence(candidate)
    rank_decision = cross_summary.get("rank_decision")
    composition_ok, composition_failures, composition_summary = _composition_evidence(candidate, rank_decision)

    v5_scientific = base.get("scientifically_independent_vector_candidate") is True
    modular = bool(v5_scientific and cross_ok and composition_ok)
    failures = sorted(set(cross_failures + composition_failures))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v5_scientifically_independent_vector_candidate": v5_scientific,
        "semantic_scientific_candidate_preserved_from_v5": v5_scientific,
        "structured_cross_effect_controls_pass": bool(cross_ok),
        "rank2_composition_controls_pass": bool(composition_ok),
        "modular_jspace_control_candidate": modular,
        "modular_hcu_control_primitive_candidate": modular,
        "modularity_failures": failures,
        "cross_effect_summary": cross_summary,
        "composition_summary": composition_summary,
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "This companion gate preserves v5 semantic-causality adjudication and separately tests the stronger "
            "claim that the intervention is a reusable modular J-Space/HCU control primitive. A modular candidate "
            "requires a complete preregistered intervention-by-sentinel-by-family cross-effect matrix within bounds; "
            "rank-2 additionally requires a frozen held-out composition matrix within residual tolerance. Passing this "
            "gate still mints no canonical semantics, J-Space model runtime, HCU, training, EffectGate, or whole-product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "semantic_scientific_candidate_preserved_from_v5": False,
            "modular_jspace_control_candidate": False,
            "modular_hcu_control_primitive_candidate": False,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "modularity_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        candidate = {}
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    print(json.dumps(adjudicate_file(Path(args.candidate)), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
