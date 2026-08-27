#!/usr/bin/env python3
"""Fail-closed structural gate for Trigger-2 semantic-Hyperposition candidate rows.

This gate validates the cross-cutting *training ontology* requested for Xeno/EntityOS-HCU.
It is deliberately separate from the existing candidate gate's reserved `hyperposition`
evidence-resolution object. `semantic_hyperposition` describes the model-facing/latent
cognitive operating frame and may contain deterministic synthetic-task resolution without
minting canonical-world truth or causal/J-Space credit.

SOURCE/CANDIDATE VALIDATION ONLY. This script does not admit canonical dataset rows and
cannot mint runtime, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_GATE/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
SHP_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION/v1"

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
}

REQUIRED_ANTI_COLLAPSE = {
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
}

ALLOWED_EPISTEMIC_STATUS = {
    "OBSERVED",
    "UNKNOWN",
    "HYPOTHESIS",
    "COUNTERHYPOTHESIS",
    "PREDICTION",
    "MEASUREMENT_ERROR",
    "CONTRADICTION",
}

ALLOWED_TASK_RESOLUTION = {"UNRESOLVED", "RESOLVED_WITHIN_SYNTHETIC_WORLD"}
COLLAPSE_RULE = "ONLY_SYNTHETIC_PROOF_OR_EXPLICIT_DISCRIMINATOR"
PROJECTION_OPERATION = "NONDESTRUCTIVE_VIEW"


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def adjudicate(row: Any, *, require_semantic_hyperposition: bool = True) -> dict[str, Any]:
    failures: list[str] = []

    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")

    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if row.get("canonical_truth_allowed") is not False:
        failures.append("ROW_CANNOT_MINT_CANONICAL_TRUTH")
    if row.get("direct_effect_authority") is not False:
        failures.append("ROW_CANNOT_HAVE_DIRECT_EFFECT_AUTHORITY")

    hp = row.get("semantic_hyperposition")
    if hp is None:
        if require_semantic_hyperposition:
            failures.append("SEMANTIC_HYPERPOSITION_REQUIRED")
        return _result(failures)

    if not isinstance(hp, dict):
        failures.append("SEMANTIC_HYPERPOSITION_OBJECT_REQUIRED")
        return _result(failures)

    if hp.get("schema") != SHP_SCHEMA:
        failures.append("SEMANTIC_HYPERPOSITION_SCHEMA_MISMATCH")
    if hp.get("canonical_truth_allowed") is not False:
        failures.append("SEMANTIC_HYPERPOSITION_CANNOT_MINT_CANONICAL_TRUTH")
    if hp.get("collapse_rule") != COLLAPSE_RULE:
        failures.append("COLLAPSE_RULE_MISMATCH")

    anti = hp.get("anti_collapse")
    if not isinstance(anti, list):
        failures.append("ANTI_COLLAPSE_LIST_REQUIRED")
    else:
        aset = {str(x) for x in anti}
        missing = REQUIRED_ANTI_COLLAPSE - aset
        if missing:
            failures.append("ANTI_COLLAPSE_MISSING:" + ",".join(sorted(missing)))

    projection = hp.get("projection")
    if not isinstance(projection, dict):
        failures.append("PROJECTION_OBJECT_REQUIRED")
    else:
        if projection.get("operation") != PROJECTION_OPERATION:
            failures.append("PROJECTION_MUST_BE_NONDESTRUCTIVE_VIEW")
        if "context" not in projection:
            failures.append("PROJECTION_CONTEXT_REQUIRED")

    branches = hp.get("branches")
    branch_ids: list[str] = []
    if not isinstance(branches, list) or len(branches) < 2:
        failures.append("AT_LEAST_TWO_BRANCHES_REQUIRED")
        branches = []

    for idx, branch in enumerate(branches):
        prefix = f"BRANCH_{idx}"
        if not isinstance(branch, dict):
            failures.append(prefix + ":OBJECT_REQUIRED")
            continue
        missing = REQUIRED_BRANCH_FIELDS - set(branch)
        if missing:
            failures.append(prefix + ":MISSING_FIELDS:" + ",".join(sorted(missing)))
            continue

        bid = branch.get("branch_id")
        if not _nonempty_string(bid):
            failures.append(prefix + ":BRANCH_ID_INVALID")
        else:
            branch_ids.append(bid)

        if not _nonempty_string(branch.get("value")):
            failures.append(prefix + ":VALUE_INVALID")
        if not _nonempty_string(branch.get("context_predicate")):
            failures.append(prefix + ":CONTEXT_PREDICATE_INVALID")
        if not isinstance(branch.get("evidence_for"), list):
            failures.append(prefix + ":EVIDENCE_FOR_LIST_REQUIRED")
        if not isinstance(branch.get("evidence_against"), list):
            failures.append(prefix + ":EVIDENCE_AGAINST_LIST_REQUIRED")
        if branch.get("falsifier") is None:
            failures.append(prefix + ":FALSIFIER_EXPLICIT_VALUE_REQUIRED")
        if not _nonempty_string(branch.get("validity")):
            failures.append(prefix + ":VALIDITY_INVALID")
        if not _nonempty_string(branch.get("provenance")):
            failures.append(prefix + ":PROVENANCE_INVALID")
        if branch.get("epistemic_status") not in ALLOWED_EPISTEMIC_STATUS:
            failures.append(prefix + ":EPISTEMIC_STATUS_INVALID")

    if len(branch_ids) != len(set(branch_ids)):
        failures.append("DUPLICATE_BRANCH_ID")

    resolution = hp.get("task_resolution")
    if not isinstance(resolution, dict):
        failures.append("TASK_RESOLUTION_OBJECT_REQUIRED")
    else:
        status = resolution.get("status")
        resolved = resolution.get("resolved_branch")
        if status not in ALLOWED_TASK_RESOLUTION:
            failures.append("TASK_RESOLUTION_STATUS_INVALID")
        elif status == "UNRESOLVED":
            if resolved is not None:
                failures.append("UNRESOLVED_CANNOT_NAME_RESOLVED_BRANCH")
        elif status == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
            if resolved not in branch_ids:
                failures.append("RESOLVED_BRANCH_NOT_IN_BRANCH_SET")

    if not _nonempty_string(hp.get("query_id")):
        failures.append("QUERY_ID_REQUIRED")

    # Explicit separation from the existing candidate gate's evidence-level
    # `hyperposition` field: task-local synthetic resolution never grants causal truth.
    if hp.get("canonical_truth_allowed") is not False:
        failures.append("SYNTHETIC_TASK_RESOLUTION_TRUTH_LEAK")

    return _result(failures)


def _result(failures: list[str]) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "semantic_hyperposition_pass": not failures,
        "failures": failures,
        "canonical_dataset_write_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "canonical_truth_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "Structural candidate-row semantic-Hyperposition validation only. "
            "Canonical admission and executable/model acceptance remain separate."
        ),
    }
