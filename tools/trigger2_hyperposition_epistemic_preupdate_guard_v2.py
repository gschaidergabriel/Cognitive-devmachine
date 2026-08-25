#!/usr/bin/env python3
"""Epistemic pre-update guard v2 using the producer-bound state-history successor.

This file preserves the v1 epistemic admission rule (only OBSERVED or SYNTHETIC_PROOF may
reach evidence mutation) while replacing the delegated state-history implementation with the
producer-authenticated v2 bounded-pilot successor.  Semantic transition authority remains in
the retained reference/state-history lane.

SOURCE/CANDIDATE PRE-ADMISSION ONLY; zero dataset/runtime/J-Space/HCU/EntityOS/training
credit is minted by PASS.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_EPISTEMIC_PREUPDATE_GUARD/v2"
LEGACY_GUARD_FILENAME = "trigger2_hyperposition_epistemic_preupdate_guard_v1.py"
BASE_GATE_FILENAME = "trigger2_hyperposition_state_history_producer_bound_gate_v2.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = _load_sibling(LEGACY_GUARD_FILENAME, "trigger2_epistemic_guard_v1_rules_for_v2")
base = _load_sibling(BASE_GATE_FILENAME, "trigger2_state_history_producer_bound_v2_for_epistemic_v2")
EVIDENCE_ADMISSIBLE_TYPES = legacy.EVIDENCE_ADMISSIBLE_TYPES


def _result(failures: list[str], *, underlying_gate_called: bool, underlying_gate_result: Any = None) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "underlying_gate_called": underlying_gate_called,
        "underlying_gate_result": underlying_gate_result,
        "allowed_epistemic_types_for_evidence_update": sorted(EVIDENCE_ADMISSIBLE_TYPES),
        "caller_epistemic_type_creates_evidence_authority": False,
        "producer_authenticated_state_history_required": True,
        "positive_D_E_promotion_ready": False,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "epistemic pre-update rule + producer-bound state-history source gate only",
    }


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"], underlying_gate_called=False)

    failures: list[str] = []
    history = row.get("synthetic_event_history_evaluator_only")
    if history is None or not isinstance(history, list):
        failures.append("SYNTHETIC_EVENT_HISTORY_LIST_REQUIRED")
        history = []

    for idx, event in enumerate(history):
        failures.extend(legacy._epistemic_failures(event, location=f"history:{idx}"))
    failures.extend(legacy._epistemic_failures(row.get("synthetic_test_event_evaluator_only"), location="current"))

    if failures:
        return _result(failures, underlying_gate_called=False)

    try:
        base_result = base.adjudicate(row)
    except Exception as exc:
        return _result(
            ["UNDERLYING_PRODUCER_BOUND_STATE_HISTORY_EXCEPTION:" + type(exc).__name__],
            underlying_gate_called=True,
        )

    if not isinstance(base_result, dict):
        return _result(["UNDERLYING_PRODUCER_BOUND_STATE_HISTORY_RESULT_INVALID"], underlying_gate_called=True)
    if not base_result.get("pass"):
        base_failures = base_result.get("failures")
        if isinstance(base_failures, list) and base_failures:
            failures.extend("STATE_HISTORY_V2:" + str(x) for x in base_failures)
        else:
            failures.append("UNDERLYING_PRODUCER_BOUND_STATE_HISTORY_REJECTED")

    return _result(failures, underlying_gate_called=True, underlying_gate_result=base_result)


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_BOUNDED_PILOT_SUCCESSOR",
        "positive_D_E_promotion_ready": False,
        "allowed_epistemic_types_for_evidence_update": sorted(EVIDENCE_ADMISSIBLE_TYPES),
    })
