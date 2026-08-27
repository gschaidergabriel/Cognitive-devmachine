#!/usr/bin/env python3
"""Authority-masked SFT view for Trigger-2 executable cognitive transitions.

Issue #2022 requires the small model to learn candidate cognition, not to self-mint
deterministic scheduler/database/effect authority. This adapter converts the eval-only
executable-transition pilot into a *still quarantined* SFT-shaped candidate:

  model input:
    state_before + decisive_semantic_delta + bound oracle envelope
  model target:
    learned cognitive body only
  deterministic post-wrap:
    authoritative packet/envelope fields excluded from model loss/output

This file does not admit rows and mints zero accepted-dataset/training credit.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from tools import trigger2_executable_transition_pilot_v1 as pilot

SCHEMA = "TRIGGER2_EXECUTABLE_TRANSITION_AUTHORITY_MASKED_SFT_CANDIDATE/v1"
AUDIT_SCHEMA = "TRIGGER2_EXECUTABLE_TRANSITION_AUTHORITY_MASK_AUDIT/v1"

FORBIDDEN_MODEL_TARGET_KEYS = {
    "causal_event_id",
    "admission_id",
    "generation",
    "work_id",
    "process_id",
    "grid_instance_id",
    "requested_N",
    "available_N",
    "executor_id",
    "lease_id",
    "runtime_identity",
    "started_at",
    "ended_at",
    "result_id",
    "result_digest",
    "reentry_digest",
    "runtime_receipt",
    "canonical_truth_minted",
    "effect_executed",
}

POSTWRAP_FIELDS = [
    "schema",
    "causal_event_id",
    "admission_id",
    "generation",
    "work_id",
    "process_id",
    "executor_binding",
    "result_id",
    "result_class",
    "result_digest",
    "workspace_reentry.source_result_id",
    "workspace_reentry.source_process_id",
    "workspace_reentry.causal_event_id",
    "workspace_reentry.from_workspace_epoch",
    "workspace_reentry.to_workspace_epoch",
    "workspace_reentry.reentry_payload_ref",
    "workspace_reentry.reentry_digest",
    "runtime_receipt",
]


def _forbidden_paths(value: Any, prefix: str = "") -> list[str]:
    out: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            if key in FORBIDDEN_MODEL_TARGET_KEYS:
                out.append(path)
            out.extend(_forbidden_paths(child, path))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            out.extend(_forbidden_paths(child, f"{prefix}[{i}]"))
    return out


def _oracle_envelope(target: dict[str, Any]) -> dict[str, Any]:
    return {
        "causal_event_id": target["causal_event_id"],
        "admission_id": target["admission_id"],
        "generation": target["generation"],
        "work_id": target["work_id"],
        "process_id": target["process_id"],
        "executor_binding": copy.deepcopy(target["executor_binding"]),
        "result_class_constraint": target["result_class"],
        "authority_constraints": {
            "result_is_candidate_only": True,
            "canonical_truth_minting_forbidden": True,
            "direct_effect_execution_forbidden": True,
            "deterministic_envelope_override_forbidden": True,
        },
    }


def _learned_body(target: dict[str, Any]) -> dict[str, Any]:
    workspace = target.get("workspace_reentry")
    workspace_body: dict[str, Any] | None = None
    if isinstance(workspace, dict):
        workspace_body = {
            "requested": True,
            "observed_downstream_change": workspace.get("observed_downstream_change"),
            "acceptance": workspace.get("acceptance"),
        }
    payload_ref = target.get("result_payload_ref")
    payload = payload_ref.get("payload") if isinstance(payload_ref, dict) else None
    return {
        "result_payload": copy.deepcopy(payload),
        "evidence_refs": copy.deepcopy(target.get("evidence_refs", [])),
        "unknowns": copy.deepcopy(target.get("unknowns", [])),
        "db_write_proposals": copy.deepcopy(target.get("db_write_proposals", [])),
        "effect_request_candidates": copy.deepcopy(target.get("effect_request_candidates", [])),
        "workspace_reentry_proposal": workspace_body,
    }


def adapt_row(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("schema") != pilot.ROW_SCHEMA:
        raise ValueError("SOURCE_ROW_SCHEMA_MISMATCH")
    if row.get("training_eligible") is not False:
        raise ValueError("SOURCE_ROW_MUST_REMAIN_QUARANTINED")
    target = row.get("target")
    if not isinstance(target, dict) or target.get("schema") != pilot.TARGET_KIND:
        raise ValueError("COGNITIVE_RESULT_PACKET_TARGET_REQUIRED")

    learned = _learned_body(target)
    forbidden = _forbidden_paths(learned)
    if forbidden:
        raise ValueError("FORBIDDEN_AUTHORITY_IN_MODEL_TARGET:" + ",".join(sorted(forbidden)))

    return {
        "schema": SCHEMA,
        "case_id": row["case_id"],
        "source_transition_semantic_digest": row["transition_semantic_digest"],
        "status": "CANDIDATE_EVAL_ONLY_NOT_TRAINING_ELIGIBLE",
        "model_input": {
            "state_before": copy.deepcopy(row["state_before"]),
            "decisive_semantic_delta": copy.deepcopy(row["decisive_semantic_delta"]),
            "bound_oracle_envelope": _oracle_envelope(target),
        },
        "model_target": learned,
        "deterministic_postwrap": {
            "source_target_schema": target["schema"],
            "fields_excluded_from_model_loss_output": POSTWRAP_FIELDS,
            "wrapper_derives_result_and_reentry_digests": True,
            "wrapper_rejects_envelope_override": True,
        },
        "expected_state_after_evaluator_only": copy.deepcopy(row["expected_state_after"]),
        "expected_state_after_digest_evaluator_only": row["expected_state_after_digest"],
        "process_id_evaluator_only": row["process_id_evaluator_only"],
        "transition_semantic_digest_evaluator_only": row["transition_semantic_digest"],
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


def audit_row(row: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if row.get("schema") != SCHEMA:
        failures.append("SCHEMA_MISMATCH")
    model_input = row.get("model_input")
    target = row.get("model_target")
    postwrap = row.get("deterministic_postwrap")
    if not isinstance(model_input, dict):
        failures.append("MODEL_INPUT_REQUIRED")
    if not isinstance(target, dict):
        failures.append("MODEL_TARGET_REQUIRED")
        target = {}
    forbidden = _forbidden_paths(target)
    failures.extend("FORBIDDEN_AUTHORITY_IN_MODEL_TARGET:" + p for p in forbidden)
    if not isinstance(postwrap, dict):
        failures.append("DETERMINISTIC_POSTWRAP_REQUIRED")
    else:
        if postwrap.get("wrapper_rejects_envelope_override") is not True:
            failures.append("ENVELOPE_OVERRIDE_MUST_BE_REJECTED")
        if postwrap.get("wrapper_derives_result_and_reentry_digests") is not True:
            failures.append("DIGEST_DERIVATION_MUST_BE_POSTWRAP")
    envelope = model_input.get("bound_oracle_envelope") if isinstance(model_input, dict) else None
    if not isinstance(envelope, dict):
        failures.append("BOUND_ORACLE_ENVELOPE_REQUIRED")
    else:
        for key in ("causal_event_id", "admission_id", "generation", "work_id", "process_id", "executor_binding"):
            if key not in envelope:
                failures.append("BOUND_ORACLE_FIELD_MISSING:" + key)
    if row.get("training_eligible") is not False:
        failures.append("TRAINING_ELIGIBILITY_MUST_REMAIN_FALSE")
    if row.get("accepted_dataset_tokens_minted") != 0:
        failures.append("ACCEPTED_DATASET_TOKENS_MUST_REMAIN_ZERO")
    if row.get("training_credit_minted") != 0:
        failures.append("TRAINING_CREDIT_MUST_REMAIN_ZERO")
    failures = sorted(set(failures))
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "authority_masked": not forbidden,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }


def rows() -> list[dict[str, Any]]:
    return [adapt_row(row) for row in pilot.rows()]


def audit_all() -> dict[str, Any]:
    adapted = rows()
    audits = [audit_row(row) for row in adapted]
    failures = [
        {"case_id": row["case_id"], "failures": audit["failures"]}
        for row, audit in zip(adapted, audits)
        if not audit["pass"]
    ]
    return {
        "schema": AUDIT_SCHEMA,
        "pass": not failures,
        "row_count": len(adapted),
        "failures": failures,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "evidence_boundary": (
            "Authority-envelope masking only. This does not prove semantic transition correctness, "
            "shortcut independence, corpus admission, model benefit, or training readiness."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(audit_all(), indent=2, sort_keys=True))
