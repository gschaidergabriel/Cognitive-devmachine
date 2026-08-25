#!/usr/bin/env python3
"""Fail-closed transition gate for Trigger-2 semantic Hyperposition (v1).

This successor gate recomputes deterministic reference labels instead of trusting
stored transition targets. It validates candidate/source rows only and mints no
canonical dataset, runtime, J-Space, HCU, EntityOS, or training credit.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
LABELER_PATH = HERE / "trigger2_semantic_hyperposition_reference_labelers_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_shp_labelers_v1", LABELER_PATH)
L = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(L)

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_TRANSITION_GATE/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
TRANSITION_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_TRANSITION/v1"
MAX_EXHAUSTIVE_BRANCHES = 6

REQUIRED_BRANCH_FIELDS = {
    "branch_id",
    "v_semantic_value",
    "K_context_predicate",
    "evidence_for",
    "evidence_against",
    "F_falsifier",
    "T_validity_scope",
    "A_origin_provenance",
    "sigma_epistemic_status",
    "projection_visibility",
    "validity",
}


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_state(state: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(_canon(state))
    out["branches"] = sorted(out["branches"], key=lambda b: b["branch_id"])
    return out


def _full_branch_tuple_failures(state: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(state, dict) or state.get("schema") != L.STATE_SCHEMA:
        return [f"{prefix}:STATE_SCHEMA_MISMATCH"]
    branches = state.get("branches")
    if not isinstance(branches, list):
        return [f"{prefix}:BRANCH_LIST_REQUIRED"]
    for i, branch in enumerate(branches):
        if not isinstance(branch, dict):
            failures.append(f"{prefix}:BRANCH_{i}:OBJECT_REQUIRED")
            continue
        missing = REQUIRED_BRANCH_FIELDS - set(branch)
        if missing:
            failures.append(f"{prefix}:BRANCH_{i}:MISSING:" + ",".join(sorted(missing)))
    return failures


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    metrics: dict[str, Any] = {}

    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")
    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("ROW_CANONICAL_TRUTH_MUST_BE_FALSE")
    if row.get("direct_effect_authority") is not False:
        failures.append("ROW_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")

    tr = row.get("semantic_hyperposition_transition")
    if not isinstance(tr, dict):
        failures.append("TRANSITION_OBJECT_REQUIRED")
        return _result(failures, metrics)
    if tr.get("schema") != TRANSITION_SCHEMA:
        failures.append("TRANSITION_SCHEMA_MISMATCH")
    if tr.get("canonical_truth_allowed") is not False:
        failures.append("TRANSITION_CANONICAL_TRUTH_MUST_BE_FALSE")
    if tr.get("direct_effect_authority") is not False:
        failures.append("TRANSITION_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")

    before = tr.get("state_before")
    observation = tr.get("observation")
    after = tr.get("state_after")
    failures.extend(_full_branch_tuple_failures(before, "STATE_BEFORE"))
    failures.extend(_full_branch_tuple_failures(after, "STATE_AFTER"))
    if failures:
        return _result(failures, metrics)

    before_ids = [b["branch_id"] for b in before["branches"]]
    after_ids = [b["branch_id"] for b in after["branches"]]
    if set(before_ids) != set(after_ids) or len(before_ids) != len(after_ids):
        failures.append("BRANCH_SET_CHANGED_OR_SILENTLY_DROPPED")

    update = L.U_update(before, observation)
    if not update.get("pass"):
        failures.append("REFERENCE_U_UPDATE_FAIL:" + str(update.get("failure")))
        return _result(failures, metrics)
    computed_after = update["state_after"]
    if _canon(_canonical_state(computed_after)) != _canon(_canonical_state(after)):
        failures.append("STATE_AFTER_NOT_REFERENCE_LABELER_DERIVABLE")

    discriminator_outcome = tr.get("discriminator_outcome")
    resolve = L.D_resolve(computed_after, discriminator_outcome)
    if not resolve.get("pass"):
        failures.append("REFERENCE_D_RESOLVE_FAIL:" + str(resolve.get("failure")))
    elif _canon(resolve.get("resolution")) != _canon(tr.get("resolution")):
        failures.append("RESOLUTION_NOT_REFERENCE_LABELER_DERIVABLE")

    discriminators = tr.get("discriminators")
    if discriminators is not None:
        order = L.U_d_test_order(computed_after, discriminators)
        if not order.get("pass"):
            failures.append("REFERENCE_U_D_TEST_ORDER_FAIL:" + str(order.get("failure")))
        elif _canon(order.get("ordering")) != _canon(tr.get("discriminator_order")):
            failures.append("DISCRIMINATOR_ORDER_NOT_REFERENCE_LABELER_DERIVABLE")
        else:
            metrics["discriminator_count"] = len(discriminators)

    salience_items = tr.get("salience_items")
    if salience_items is not None:
        salience = L.f_salience_rank(salience_items)
        if not salience.get("pass"):
            failures.append("REFERENCE_F_SALIENCE_RANK_FAIL:" + str(salience.get("failure")))
        elif _canon(salience.get("ranking")) != _canon(tr.get("salience_order")):
            failures.append("SALIENCE_ORDER_NOT_REFERENCE_LABELER_DERIVABLE")
        else:
            metrics["salience_item_count"] = len(salience_items)

    replay = L.U_update(computed_after, observation)
    if not replay.get("pass"):
        failures.append("REFERENCE_REPLAY_FAIL:" + str(replay.get("failure")))
    else:
        replay_updates = replay.get("updates", [])
        if any(u.get("independent_for_update") is not False for u in replay_updates):
            failures.append("SAME_ANCESTRY_REPLAY_COUNTED_AS_INDEPENDENT")
        if any(u.get("validity_before") != u.get("validity_after") for u in replay_updates):
            failures.append("SAME_ANCESTRY_REPLAY_CHANGED_VALIDITY")
        metrics["replay_updates"] = len(replay_updates)

    n = len(before["branches"])
    if n > MAX_EXHAUSTIVE_BRANCHES:
        failures.append("TOO_MANY_BRANCHES_FOR_EXHAUSTIVE_V1_PERMUTATION_GATE")
    else:
        reference_canon = _canon(_canonical_state(computed_after))
        checked = 0
        for perm in itertools.permutations(before["branches"]):
            pstate = json.loads(_canon(before))
            pstate["branches"] = list(perm)
            pu = L.U_update(pstate, observation)
            if not pu.get("pass"):
                failures.append("BRANCH_PERMUTATION_REFERENCE_UPDATE_FAIL")
                break
            if _canon(_canonical_state(pu["state_after"])) != reference_canon:
                failures.append("BRANCH_PERMUTATION_CHANGED_SEMANTIC_UPDATE")
                break
            checked += 1
        metrics["branch_permutations_checked"] = checked

    if tr.get("projection_operation") != "NONDESTRUCTIVE_VIEW":
        failures.append("PROJECTION_MUST_BE_NONDESTRUCTIVE_VIEW")
    anti = set(tr.get("anti_collapse", [])) if isinstance(tr.get("anti_collapse"), list) else set()
    required_anti = {
        "NO_MAJORITY_AS_TRUTH",
        "NO_SALIENCE_AS_PROBABILITY",
        "NO_RECURRENCE_AS_EVIDENCE",
        "NO_SILENT_BRANCH_DROP",
        "PROJECTION_IS_NOT_DELETION",
    }
    missing_anti = required_anti - anti
    if missing_anti:
        failures.append("ANTI_COLLAPSE_MISSING:" + ",".join(sorted(missing_anti)))

    metrics["branch_count"] = n
    metrics["reference_update_count"] = len(update.get("updates", []))
    return _result(failures, metrics)


def _result(failures: list[str], metrics: dict[str, Any]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "semantic_hyperposition_transition_pass": not failures,
        "failures": failures,
        "metrics": metrics,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": "Deterministic candidate transition validation only. Stored targets are accepted only when independently recomputable from the reference labelers.",
    }
