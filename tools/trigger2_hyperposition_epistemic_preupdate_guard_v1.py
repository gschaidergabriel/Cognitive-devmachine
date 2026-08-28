#!/usr/bin/env python3
"""Fail-closed epistemic pre-update guard for Trigger-2 Hyperposition proof rows.

This wrapper closes one narrow P0 class discovered by the Trigger-2 v10 audit:
non-observational epistemic objects must not reach the retained state-history gate's
u_state evidence-mutation path merely because they carry outcome-shaped payloads.

It is deliberately NOT a second semantic authority. It delegates all allowed
OBSERVED/SYNTHETIC_PROOF rows to trigger2_hyperposition_state_history_proof_gate_v1
and mints no dataset, runtime, J-Space, HCU, EntityOS, or training credit.

SOURCE/CANDIDATE PRE-ADMISSION ONLY.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_EPISTEMIC_PREUPDATE_GUARD/v1"
BASE_GATE_FILENAME = "trigger2_hyperposition_state_history_proof_gate_v1.py"

# Evidence-bearing types permitted to reach the retained update gate.
# OBSERVED still requires the base gate's typed observation receipt.
# SYNTHETIC_PROOF still requires the independent generation/source-root closure
# tracked by the current Trigger-2 ledger; this guard does not create that proof.
EVIDENCE_ADMISSIBLE_TYPES = frozenset({"OBSERVED", "SYNTHETIC_PROOF"})


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_sibling(BASE_GATE_FILENAME, "trigger2_hp_state_history_gate_v1_for_epistemic_guard")


def _event_id(event: Any, fallback: str) -> str:
    if isinstance(event, dict):
        value = event.get("event_id")
        if isinstance(value, str) and value:
            return value
    return fallback


def _epistemic_failures(event: Any, *, location: str) -> list[str]:
    if not isinstance(event, dict):
        return [f"EPISTEMIC_EVENT_OBJECT_REQUIRED:{location}"]
    event_id = _event_id(event, location)
    epistemic_type = event.get("epistemic_type")
    if not isinstance(epistemic_type, str) or not epistemic_type:
        return [f"EPISTEMIC_TYPE_REQUIRED:{event_id}"]
    if epistemic_type not in EVIDENCE_ADMISSIBLE_TYPES:
        return [f"EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:{event_id}:{epistemic_type}"]
    return []


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
        "positive_D_E_promotion_ready": False,
        "remaining_p0": [
            "generation/output source-root provenance is still independently required",
            "SYNTHETIC_PROOF needs source-bound proof authority rather than a caller string",
            "exact-current focused execution remains required before promotion",
        ],
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "epistemic pre-update guard + retained state-history candidate gate only",
    }


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"], underlying_gate_called=False)

    failures: list[str] = []
    history = row.get("synthetic_event_history_evaluator_only")
    if history is None:
        failures.append("SYNTHETIC_EVENT_HISTORY_LIST_REQUIRED")
        history = []
    elif not isinstance(history, list):
        failures.append("SYNTHETIC_EVENT_HISTORY_LIST_REQUIRED")
        history = []

    for idx, event in enumerate(history):
        failures.extend(_epistemic_failures(event, location=f"history:{idx}"))

    current = row.get("synthetic_test_event_evaluator_only")
    failures.extend(_epistemic_failures(current, location="current"))

    # Critical ordering invariant: unsafe epistemic objects never reach u_state.
    if failures:
        return _result(failures, underlying_gate_called=False)

    try:
        base_result = base.adjudicate(row)
    except Exception as exc:
        return _result(
            ["UNDERLYING_STATE_HISTORY_GATE_EXCEPTION:" + type(exc).__name__],
            underlying_gate_called=True,
        )

    if not isinstance(base_result, dict):
        return _result(["UNDERLYING_STATE_HISTORY_GATE_RESULT_INVALID"], underlying_gate_called=True)

    if not base_result.get("pass"):
        base_failures = base_result.get("failures")
        if isinstance(base_failures, list) and base_failures:
            failures.extend("STATE_HISTORY:" + str(x) for x in base_failures)
        else:
            failures.append("UNDERLYING_STATE_HISTORY_GATE_REJECTED")

    return _result(
        failures,
        underlying_gate_called=True,
        underlying_gate_result=base_result,
    )


if __name__ == "__main__":
    # Deliberately no positive fixture or promotion path here.
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY",
        "positive_D_E_promotion_ready": False,
        "allowed_epistemic_types_for_evidence_update": sorted(EVIDENCE_ADMISSIBLE_TYPES),
    })
