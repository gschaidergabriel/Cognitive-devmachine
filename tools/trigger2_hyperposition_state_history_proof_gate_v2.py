#!/usr/bin/env python3
"""Epistemic-credit hardening successor for Trigger-2 Hyperposition state-history proof gate.

This module wraps the retained state-history proof gate v1 without replacing the v3
Hyperposition transition oracle. It adds one fail-closed rule that v1 does not yet
enforce: only OBSERVED events (which v1 already requires to carry a typed observation
receipt) and SYNTHETIC_PROOF events may receive independent D/E evidence credit.

UNKNOWN, HYPOTHESIS, COUNTERHYPOTHESIS, PREDICTION, MEASUREMENT_ERROR and
CONTRADICTION remain useful epistemic/model-visible states, but they cannot become
independent SUPPORTS/COUNTERS/FALSIFIES evidence merely because event identity and a
discriminator receipt are otherwise valid.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints no canonical dataset, truth, effect,
provider, runtime, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_PROOF_GATE/v2"
BASE_FILENAME = "trigger2_hyperposition_state_history_proof_gate_v1.py"
INDEPENDENT_EVIDENCE_EPISTEMIC_TYPES = {"OBSERVED", "SYNTHETIC_PROOF"}
NON_EVIDENTIAL_EPISTEMIC_TYPES = {
    "UNKNOWN",
    "HYPOTHESIS",
    "COUNTERHYPOTHESIS",
    "PREDICTION",
    "MEASUREMENT_ERROR",
    "CONTRADICTION",
}


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_sibling(BASE_FILENAME, "trigger2_hp_state_history_gate_v1_for_v2")


def _events(row: Any) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return [], None, ["ROW_OBJECT_REQUIRED"]
    raw_history = row.get("synthetic_event_history_evaluator_only")
    if not isinstance(raw_history, list):
        failures.append("SYNTHETIC_EVENT_HISTORY_LIST_REQUIRED")
        raw_history = []
    history: list[dict[str, Any]] = []
    for idx, event in enumerate(raw_history):
        if not isinstance(event, dict):
            failures.append(f"HISTORY_EVENT_OBJECT_REQUIRED:{idx}")
            continue
        history.append(event)
    current = row.get("synthetic_test_event_evaluator_only")
    if not isinstance(current, dict):
        failures.append("CURRENT_EVENT_OBJECT_REQUIRED")
        current = None
    return history, current, failures


def _derived_independence_map(base_result: Any) -> tuple[dict[str, bool], list[str]]:
    failures: list[str] = []
    out: dict[str, bool] = {}
    if not isinstance(base_result, dict):
        return out, ["BASE_V1_RESULT_OBJECT_REQUIRED"]

    for step in base_result.get("replay_steps", []) or []:
        if not isinstance(step, dict):
            failures.append("BASE_V1_REPLAY_STEP_OBJECT_REQUIRED")
            continue
        event_id = step.get("event_id")
        derived = step.get("derived_independence_qualified")
        if not isinstance(event_id, str) or not event_id:
            failures.append("BASE_V1_REPLAY_STEP_EVENT_ID_REQUIRED")
            continue
        if not isinstance(derived, bool):
            failures.append("BASE_V1_REPLAY_STEP_DERIVED_INDEPENDENCE_BOOL_REQUIRED:" + event_id)
            continue
        prior = out.get(event_id)
        if prior is not None and prior is not derived:
            failures.append("BASE_V1_DERIVED_INDEPENDENCE_CONFLICT:" + event_id)
        out[event_id] = derived

    base_v2 = base_result.get("base_derivation_gate_v2_result")
    if isinstance(base_v2, dict):
        ind = base_v2.get("independence_derivation")
        if isinstance(ind, dict):
            event_id = ind.get("registry_event_id")
            derived = ind.get("derived_independence_qualified")
            if isinstance(event_id, str) and event_id:
                if not isinstance(derived, bool):
                    failures.append("BASE_V1_CURRENT_DERIVED_INDEPENDENCE_BOOL_REQUIRED:" + event_id)
                else:
                    prior = out.get(event_id)
                    if prior is not None and prior is not derived:
                        failures.append("BASE_V1_DERIVED_INDEPENDENCE_CONFLICT:" + event_id)
                    out[event_id] = derived
    return out, sorted(set(failures))


def epistemic_credit_failures(row: Any, base_result: Any) -> list[str]:
    history, current, failures = _events(row)
    derived_by_event, derived_failures = _derived_independence_map(base_result)
    failures.extend(derived_failures)
    all_events = history + ([current] if isinstance(current, dict) else [])

    seen: set[str] = set()
    for event in all_events:
        event_id = event.get("event_id")
        epistemic_type = event.get("epistemic_type")
        if not isinstance(event_id, str) or not event_id:
            failures.append("EVENT_ID_REQUIRED_FOR_EPISTEMIC_CREDIT_GATE")
            continue
        if event_id in seen:
            # v1 owns replay/digest semantics. This layer only avoids double-reporting.
            continue
        seen.add(event_id)
        if epistemic_type not in INDEPENDENT_EVIDENCE_EPISTEMIC_TYPES | NON_EVIDENTIAL_EPISTEMIC_TYPES:
            failures.append("UNKNOWN_EPISTEMIC_TYPE_FOR_CREDIT_GATE:" + event_id + ":" + str(epistemic_type))
            continue
        if event_id not in derived_by_event:
            failures.append("DERIVED_INDEPENDENCE_MISSING_FOR_EVENT:" + event_id)
            continue
        if derived_by_event[event_id] and epistemic_type not in INDEPENDENT_EVIDENCE_EPISTEMIC_TYPES:
            failures.append(
                "NON_EVIDENTIAL_EPISTEMIC_EVENT_CANNOT_RECEIVE_INDEPENDENT_CREDIT:"
                + event_id + ":" + str(epistemic_type)
            )
    return sorted(set(failures))


def adjudicate(row: Any) -> dict[str, Any]:
    try:
        base_result = base.adjudicate(deepcopy(row))
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "pass": False,
            "candidate_pre_admission_pass": False,
            "failures": ["BASE_V1_EXCEPTION:" + type(exc).__name__],
            "base_v1_pass": False,
            "canonical_dataset_admission": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
            "runtime_credit_minted": 0,
            "jspace_runtime_credit_minted": 0,
            "hcu_runtime_credit_minted": 0,
            "entityos_runtime_credit_minted": 0,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
        }

    failures: list[str] = []
    if not isinstance(base_result, dict):
        failures.append("BASE_V1_RESULT_OBJECT_REQUIRED")
    elif not base_result.get("pass"):
        base_failures = base_result.get("failures", [])
        if isinstance(base_failures, list):
            failures.extend("BASE_V1:" + str(x) for x in base_failures)
        else:
            failures.append("BASE_V1_FAILED_WITHOUT_FAILURE_LIST")
    else:
        failures.extend(epistemic_credit_failures(row, base_result))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "base_v1_pass": bool(isinstance(base_result, dict) and base_result.get("pass")),
        "recomputed_target": base_result.get("recomputed_target") if isinstance(base_result, dict) else None,
        "epistemic_credit_rule": {
            "independent_credit_allowed_only_for": sorted(INDEPENDENT_EVIDENCE_EPISTEMIC_TYPES),
            "non_evidential_types_must_not_receive_independent_credit": sorted(NON_EVIDENTIAL_EPISTEMIC_TYPES),
            "observed_typed_receipt_enforced_by_base_v1": True,
            "caller_independence_boolean_authoritative": False,
        },
        "generation_provenance_receipt_closed": False,
        "native_seed_rebound_to_this_gate": False,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "epistemic-credit hardening over replay-bound state-history proof v1; source/candidate only",
    }
