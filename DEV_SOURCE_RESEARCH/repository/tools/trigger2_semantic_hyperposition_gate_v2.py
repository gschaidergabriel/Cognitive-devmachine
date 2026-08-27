#!/usr/bin/env python3
"""Successor fail-closed admission gate for Trigger-2 semantic Hyperposition.

v2 composes three already-current pieces instead of inventing another ontology:
1) the generic ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1 gate,
2) XENO_SEMANTIC_HYPERPOSITION/v2 latent episodes, and
3) the deterministic Trigger-2 Hyperposition reference labelers v1.

Every integrated candidate episode must carry the full branch-local operating frame and,
for transition/resolution/ranking episodes, reproduce the deterministic reference result
exactly. Deterministic task-local action/resolution never mints canonical world truth.

SOURCE/CANDIDATE VALIDATION ONLY. This module cannot admit the canonical dataset and cannot
mint runtime, J-Space, HCU, EntityOS, provider, effect, or training credit.
"""
from __future__ import annotations

import importlib.util
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_GATE/v2"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
SHP_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION/v2"

REQUIRED_ANTI_COLLAPSE = {
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
}
REQUIRED_BRANCH_FIELDS = {
    "branch_id",
    "value",
    "context_predicate",
    "evidence_for",
    "evidence_against",
    "falsifier",
    "validity",
    "provenance",
    "epistemic_status",
    "projection_visibility",
}
ALLOWED_EPISODE_KINDS = {
    "STATE_ONLY",
    "UPDATE",
    "RESOLUTION",
    "DISCRIMINATOR_SELECTION",
    "SALIENCE_RANK",
}
PROJECTION_OPERATION = "NONDESTRUCTIVE_VIEW"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base_gate = _load_sibling(
    "entityos_hcu_trainingtrace_candidate_gate_v1.py",
    "trigger2_base_candidate_gate_v1",
)
lab = _load_sibling(
    "trigger2_semantic_hyperposition_reference_labelers_v1.py",
    "trigger2_semantic_hyperposition_reference_labelers_v1",
)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _branch_ids(state: Any) -> list[str]:
    if not isinstance(state, dict):
        return []
    out = []
    for branch in state.get("branches", []):
        if isinstance(branch, dict) and _nonempty_string(branch.get("branch_id")):
            out.append(branch["branch_id"])
    return out


def _validate_evidence_item(item: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(item, dict):
        failures.append(prefix + ":EVIDENCE_OBJECT_REQUIRED")
        return
    for key in ("evidence_id", "provenance_ancestry_id", "independence_group", "epistemic_type"):
        if not _nonempty_string(item.get(key)):
            failures.append(prefix + ":EVIDENCE_FIELD_REQUIRED:" + key)


def _validate_state(state: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(state, dict):
        failures.append(prefix + ":STATE_OBJECT_REQUIRED")
        return
    if state.get("schema") != lab.STATE_SCHEMA:
        failures.append(prefix + ":STATE_SCHEMA_MISMATCH")
    if state.get("canonical_truth_allowed") is not False:
        failures.append(prefix + ":STATE_CANONICAL_TRUTH_MUST_BE_FALSE")
    if state.get("direct_effect_authority") is not False:
        failures.append(prefix + ":STATE_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")

    branches = state.get("branches")
    if not isinstance(branches, list) or len(branches) < 2:
        failures.append(prefix + ":AT_LEAST_TWO_BRANCHES_REQUIRED")
        return

    seen: set[str] = set()
    for idx, branch in enumerate(branches):
        bp = f"{prefix}:BRANCH_{idx}"
        if not isinstance(branch, dict):
            failures.append(bp + ":OBJECT_REQUIRED")
            continue
        missing = REQUIRED_BRANCH_FIELDS - set(branch)
        if missing:
            failures.append(bp + ":MISSING_FIELDS:" + ",".join(sorted(missing)))
            continue

        bid = branch.get("branch_id")
        if not _nonempty_string(bid):
            failures.append(bp + ":BRANCH_ID_INVALID")
        elif bid in seen:
            failures.append(prefix + ":DUPLICATE_BRANCH_ID")
        else:
            seen.add(bid)

        for key in ("value", "context_predicate", "validity", "provenance", "epistemic_status"):
            if not _nonempty_string(branch.get(key)):
                failures.append(bp + ":" + key.upper() + "_INVALID")

        if branch.get("falsifier") is None:
            failures.append(bp + ":FALSIFIER_EXPLICIT_VALUE_REQUIRED")
        if not isinstance(branch.get("projection_visibility"), bool):
            failures.append(bp + ":PROJECTION_VISIBILITY_BOOL_REQUIRED")

        for side in ("evidence_for", "evidence_against"):
            items = branch.get(side)
            if not isinstance(items, list):
                failures.append(bp + ":" + side.upper() + "_LIST_REQUIRED")
            else:
                for eidx, item in enumerate(items):
                    _validate_evidence_item(item, f"{bp}:{side}:{eidx}", failures)


def _validate_projection(projection: Any, state: Any, failures: list[str]) -> None:
    if not isinstance(projection, dict):
        failures.append("PROJECTION_OBJECT_REQUIRED")
        return
    if projection.get("operation") != PROJECTION_OPERATION:
        failures.append("PROJECTION_MUST_BE_NONDESTRUCTIVE_VIEW")
    if "context" not in projection:
        failures.append("PROJECTION_CONTEXT_REQUIRED")
    visible = projection.get("visible_branch_ids")
    if not isinstance(visible, list):
        failures.append("PROJECTION_VISIBLE_BRANCH_IDS_LIST_REQUIRED")
        return
    state_ids = set(_branch_ids(state))
    if not set(visible).issubset(state_ids):
        failures.append("PROJECTION_REFERENCES_UNKNOWN_BRANCH")
    if projection.get("deletes_hidden_branches") is not False:
        failures.append("PROJECTION_CANNOT_DELETE_HIDDEN_BRANCHES")


def _validate_permutation_case(case: Any, failures: list[str]) -> None:
    if not isinstance(case, dict):
        failures.append("PERMUTATION_CASE_OBJECT_REQUIRED")
        return
    for key in ("group_id", "permutation_id", "semantic_equivalence_key", "target_semantic_key"):
        if not _nonempty_string(case.get(key)):
            failures.append("PERMUTATION_CASE_FIELD_REQUIRED:" + key)
    if case.get("branch_order_is_nuisance") is not True:
        failures.append("BRANCH_ORDER_MUST_BE_DECLARED_NUISANCE")


def _resolution_semantic_value(row: dict[str, Any]) -> Any:
    hp = row["semantic_hyperposition"]
    resolution = hp.get("reference_resolution")
    if not isinstance(resolution, dict):
        return None
    bid = resolution.get("resolved_branch")
    if bid is None:
        return None
    state = hp.get("state_after") if isinstance(hp.get("state_after"), dict) else hp.get("state_before")
    if not isinstance(state, dict):
        return None
    for branch in state.get("branches", []):
        if isinstance(branch, dict) and branch.get("branch_id") == bid:
            return branch.get("value")
    return None


def _branch_multiset(state: Any) -> Counter:
    """Branch-content multiset for permutation controls, deliberately ignoring branch_id/order."""
    out: Counter = Counter()
    if not isinstance(state, dict):
        return out
    for branch in state.get("branches", []):
        if not isinstance(branch, dict):
            continue
        frozen = (
            branch.get("value"),
            branch.get("context_predicate"),
            repr(branch.get("evidence_for")),
            repr(branch.get("evidence_against")),
            repr(branch.get("falsifier")),
            branch.get("validity"),
            branch.get("provenance"),
            branch.get("epistemic_status"),
            branch.get("projection_visibility"),
        )
        out[frozen] += 1
    return out


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")

    base = base_gate.adjudicate(row)
    if not base.get("candidate_admission_pass"):
        failures.extend("BASE_GATE:" + x for x in base.get("failures", []))

    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")

    hp = row.get("semantic_hyperposition")
    if not isinstance(hp, dict):
        failures.append("SEMANTIC_HYPERPOSITION_OBJECT_REQUIRED")
        return _result(failures)

    if hp.get("schema") != SHP_SCHEMA:
        failures.append("SEMANTIC_HYPERPOSITION_SCHEMA_MISMATCH")
    if hp.get("canonical_truth_allowed") is not False:
        failures.append("SEMANTIC_HYPERPOSITION_CANNOT_MINT_CANONICAL_TRUTH")
    if hp.get("direct_effect_authority") is not False:
        failures.append("SEMANTIC_HYPERPOSITION_CANNOT_HAVE_DIRECT_EFFECT_AUTHORITY")

    anti = hp.get("anti_collapse")
    if not isinstance(anti, list):
        failures.append("ANTI_COLLAPSE_LIST_REQUIRED")
    else:
        missing = REQUIRED_ANTI_COLLAPSE - {str(x) for x in anti}
        if missing:
            failures.append("ANTI_COLLAPSE_MISSING:" + ",".join(sorted(missing)))

    kind = hp.get("episode_kind")
    if kind not in ALLOWED_EPISODE_KINDS:
        failures.append("EPISODE_KIND_INVALID")
    if not _nonempty_string(hp.get("query_id")):
        failures.append("QUERY_ID_REQUIRED")

    before = hp.get("state_before")
    _validate_state(before, "STATE_BEFORE", failures)
    _validate_projection(hp.get("projection"), before, failures)
    _validate_permutation_case(hp.get("permutation_case"), failures)

    if kind == "UPDATE":
        observation = hp.get("observation")
        expected = lab.U_update(before, observation)
        if not expected.get("pass"):
            failures.append("REFERENCE_U_UPDATE_REJECTED:" + str(expected.get("failure")))
        else:
            if hp.get("state_after") != expected.get("state_after"):
                failures.append("STATE_AFTER_DOES_NOT_MATCH_REFERENCE_U_UPDATE")
            if hp.get("reference_update") != expected.get("updates"):
                failures.append("REFERENCE_UPDATE_RECEIPT_MISMATCH")
            after = hp.get("state_after")
            _validate_state(after, "STATE_AFTER", failures)
            if Counter(_branch_ids(before)) != Counter(_branch_ids(after)):
                failures.append("UPDATE_MUST_PRESERVE_BRANCH_ID_SET")
            expected_resolution = lab.D_resolve(after)
            if not expected_resolution.get("pass"):
                failures.append("REFERENCE_D_RESOLVE_REJECTED_AFTER_UPDATE")
            elif hp.get("reference_resolution") != expected_resolution.get("resolution"):
                failures.append("REFERENCE_RESOLUTION_AFTER_UPDATE_MISMATCH")

    elif kind == "RESOLUTION":
        outcome = hp.get("discriminator_outcome")
        expected = lab.D_resolve(before, outcome)
        if not expected.get("pass"):
            failures.append("REFERENCE_D_RESOLVE_REJECTED:" + str(expected.get("failure")))
        elif hp.get("reference_resolution") != expected.get("resolution"):
            failures.append("REFERENCE_RESOLUTION_MISMATCH")
        if hp.get("state_after") is not None:
            failures.append("RESOLUTION_EPISODE_MUST_NOT_MUTATE_BRANCH_STATE")

    elif kind == "DISCRIMINATOR_SELECTION":
        expected = lab.U_d_test_order(before, hp.get("discriminators"))
        if not expected.get("pass"):
            failures.append("REFERENCE_DISCRIMINATOR_ORDER_REJECTED:" + str(expected.get("failure")))
        elif hp.get("reference_discriminator_order") != expected.get("ordering"):
            failures.append("REFERENCE_DISCRIMINATOR_ORDER_MISMATCH")
        if expected.get("probability_output") is not False or expected.get("truth_output") is not False:
            failures.append("DISCRIMINATOR_ORDER_CANNOT_OUTPUT_TRUTH_OR_PROBABILITY")

    elif kind == "SALIENCE_RANK":
        expected = lab.f_salience_rank(hp.get("salience_items"))
        if not expected.get("pass"):
            failures.append("REFERENCE_SALIENCE_REJECTED:" + str(expected.get("failure")))
        elif hp.get("reference_salience_ranking") != expected.get("ranking"):
            failures.append("REFERENCE_SALIENCE_RANKING_MISMATCH")
        if (
            expected.get("probability_output") is not False
            or expected.get("truth_output") is not False
            or expected.get("evidence_strength_output") is not False
        ):
            failures.append("SALIENCE_CANNOT_OUTPUT_TRUTH_PROBABILITY_OR_EVIDENCE_STRENGTH")

    elif kind == "STATE_ONLY":
        expected = lab.D_resolve(before)
        if not expected.get("pass"):
            failures.append("REFERENCE_D_RESOLVE_REJECTED_FOR_STATE")
        elif hp.get("reference_resolution") != expected.get("resolution"):
            failures.append("REFERENCE_STATE_RESOLUTION_MISMATCH")
        if hp.get("state_after") is not None:
            failures.append("STATE_ONLY_EPISODE_MUST_NOT_MUTATE_BRANCH_STATE")

    if hp.get("canonical_truth_allowed") is not False:
        failures.append("TASK_LOCAL_RESOLUTION_TRUTH_LEAK")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("ROW_TRUTH_LEAK")
    if row.get("direct_effect_authority") is not False:
        failures.append("ROW_EFFECT_AUTHORITY_LEAK")

    return _result(failures)


def adjudicate_permutation_group(rows: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(rows, list) or len(rows) < 2:
        return _group_result(["PERMUTATION_GROUP_REQUIRES_AT_LEAST_TWO_ROWS"])

    base_results = [adjudicate(row) for row in rows]
    for idx, result in enumerate(base_results):
        if not result.get("semantic_hyperposition_pass"):
            failures.append(f"ROW_{idx}_FAILS_V2_GATE")

    cases = [
        row.get("semantic_hyperposition", {}).get("permutation_case", {})
        if isinstance(row, dict)
        else {}
        for row in rows
    ]
    group_ids = {c.get("group_id") for c in cases}
    equiv = {c.get("semantic_equivalence_key") for c in cases}
    target_keys = {c.get("target_semantic_key") for c in cases}
    permutation_ids = [c.get("permutation_id") for c in cases]

    if len(group_ids) != 1:
        failures.append("PERMUTATION_GROUP_ID_MISMATCH")
    if len(equiv) != 1:
        failures.append("SEMANTIC_EQUIVALENCE_KEY_MISMATCH")
    if len(target_keys) != 1:
        failures.append("TARGET_SEMANTIC_KEY_MISMATCH")
    if len(permutation_ids) != len(set(permutation_ids)):
        failures.append("PERMUTATION_ID_NOT_UNIQUE")
    if any(c.get("branch_order_is_nuisance") is not True for c in cases):
        failures.append("BRANCH_ORDER_NOT_NUISANCE_IN_ALL_ROWS")

    before_multisets = [
        _branch_multiset(row["semantic_hyperposition"].get("state_before"))
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("semantic_hyperposition"), dict)
    ]
    if before_multisets and any(x != before_multisets[0] for x in before_multisets[1:]):
        failures.append("BRANCH_CONTENT_CHANGED_ACROSS_PERMUTATION")

    after_multisets = [
        _branch_multiset(row["semantic_hyperposition"].get("state_after"))
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("semantic_hyperposition"), dict)
        and row["semantic_hyperposition"].get("state_after") is not None
    ]
    if after_multisets and any(x != after_multisets[0] for x in after_multisets[1:]):
        failures.append("STATE_AFTER_CONTENT_CHANGED_ACROSS_PERMUTATION")

    resolution_status = {
        row.get("semantic_hyperposition", {}).get("reference_resolution", {}).get("status")
        for row in rows
        if isinstance(row, dict)
    }
    if len(resolution_status) > 1:
        failures.append("RESOLUTION_STATUS_CHANGED_ACROSS_PERMUTATION")

    resolved_values = {_resolution_semantic_value(row) for row in rows if isinstance(row, dict)}
    if len(resolved_values) > 1:
        failures.append("RESOLVED_SEMANTIC_VALUE_CHANGED_ACROSS_PERMUTATION")

    return _group_result(failures)


def _result(failures: list[str]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "semantic_hyperposition_pass": not failures,
        "failures": failures,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "Successor Trigger-2 candidate admission only. Exact deterministic reference "
            "label agreement and permutation controls do not themselves create canonical "
            "dataset, model, runtime, HCU, EntityOS, provider, effect, or training credit."
        ),
    }


def _group_result(failures: list[str]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA + "/PERMUTATION_GROUP",
        "permutation_group_pass": not failures,
        "failures": failures,
        "canonical_dataset_write_performed": False,
        "training_credit_minted": False,
    }
