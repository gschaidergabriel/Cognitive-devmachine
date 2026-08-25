#!/usr/bin/env python3
"""Trigger-2 source-only pilot for executable cognitive state-transition supervision.

The predecessor trajectory generator can teach a model to narrate rules. This successor
pilot instead constructs concrete, machine-adjudicable transitions:

    typed state_before + decisive_delta
      -> concrete COGNITIVE_RESULT_PACKET/v1 + process payload
      -> expected state_after / workspace re-entry candidate

The pilot is deliberately QUARANTINED_METHOD_ONLY. It cannot admit training rows, mint
accepted dataset tokens, choose a checkpoint, grant J-Space causal credit, or authorize
canonical state/effects. Deterministic/store authority processes are evaluator/oracle
boundaries and are never model targets.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from claycode_cognitive_protocol_adapter_v1 import (
    ClayCodeCognitiveProtocolError,
    roundtrip,
)

SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_PILOT/v1"
ROW_SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_ROW/v1"
TARGET_SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_TARGET/v1"
ADJUDICATION_SCHEMA = "CLAY_TRIGGER2_EXECUTABLE_COGNITIVE_TRANSITION_ADJUDICATION/v1"
CENSUS_PATH = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
ADAPTER_PATH = ROOT / "tools/claycode_cognitive_protocol_adapter_v1.py"

TRAINABLE_IMPLEMENTATION_CLASSES = {
    "SIMULATE_ON_GRID",
    "EXTERNAL_STRONG_MODEL_BRIDGE",
    "OPTIONAL_CAUSAL_RESEARCH",
}
DETERMINISTIC_OR_STORE_CLASSES = {
    "DETERMINISTIC_BOUNDARY",
    "STORE_IN_DB",
}
EXPECTED_TRAINABLE_PROCESS_IDS = {
    "ZECP03", "ZECP04", "ZECP05", "ZECP06", "ZECP07", "ZECP08", "ZECP09", "ZECP10",
    "ZECP12", "ZECP13", "ZECP14", "ZECP15", "ZECP16", "ZECP18", "ZECP19", "ZECP20",
}

FORBIDDEN_TARGET_KEYS = {
    "canonical_truth",
    "canonical_truth_authority",
    "truth_authority",
    "capability_grant",
    "capability_authority",
    "effect_authority",
    "real_effect_executed",
    "direct_effect_execution",
    "scheduler_lease_grant",
    "coordinator_lease_grant",
    "canonical_commit",
    "global_jspace_causal_credit",
}
FORBIDDEN_RESULT_CLASSES = {"DETERMINISTIC_CONTROL_RESULT", "EFFECT_RECEIPT"}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"OBJECT_REQUIRED:{path}")
    return value


def _process_map() -> dict[str, dict[str, Any]]:
    census = _load_json(CENSUS_PATH)
    if census.get("schema") != "ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS/v1":
        raise ValueError("COGNITIVE_CENSUS_SCHEMA_DRIFT")
    processes = census.get("processes")
    if not isinstance(processes, list):
        raise ValueError("COGNITIVE_CENSUS_PROCESSES_REQUIRED")
    out: dict[str, dict[str, Any]] = {}
    for process in processes:
        if not isinstance(process, dict) or not isinstance(process.get("id"), str):
            raise ValueError("COGNITIVE_CENSUS_PROCESS_INVALID")
        out[process["id"]] = process
    trainable = {
        pid for pid, process in out.items()
        if process.get("implementation_class") in TRAINABLE_IMPLEMENTATION_CLASSES
    }
    if trainable != EXPECTED_TRAINABLE_PROCESS_IDS:
        missing = sorted(EXPECTED_TRAINABLE_PROCESS_IDS - trainable)
        added = sorted(trainable - EXPECTED_TRAINABLE_PROCESS_IDS)
        raise ValueError(f"TRAINABLE_PROCESS_CENSUS_DRIFT:missing={missing}:added={added}")
    return out


def _ref(kind: str, process_id: str, suffix: str) -> str:
    return f"{kind}://trigger2-exec-v1/{process_id.lower()}/{suffix}"


def _base_work_packet(process_id: str) -> dict[str, Any]:
    state_ref = _ref("db-state", process_id, "snapshot-0042")
    return {
        "schema": "COGNITIVE_WORK_PACKET/v1",
        "causal_event_id": f"evt-trigger2-{process_id.lower()}-001",
        "admission_id": f"adm-bound-{process_id.lower()}-001",
        "generation": 7,
        "work_id": f"work-{process_id.lower()}-001",
        "process_id": process_id,
        "parent_work_ids": [],
        "workspace_epoch": 42,
        "state_snapshot_ref": state_ref,
        "input_refs": [
            {
                "ref": _ref("input", process_id, "primary"),
                "digest": hashlib.sha256(f"{process_id}:primary".encode()).hexdigest(),
                "provenance": "BOUND_EVALUATOR_FIXTURE",
            }
        ],
        "epistemic_inputs": [
            {
                "status": "OBSERVED",
                "ref": _ref("evidence", process_id, "observed-1"),
            },
            {
                "status": "UNKNOWN",
                "ref": _ref("evidence", process_id, "missing-1"),
            },
        ],
        "capability_scope_ref": _ref("capability", process_id, "read-candidate-only"),
        "resource_budget": {"max_output_tokens": 256, "wall_ms": 5000},
        "grid_runtime": {
            "requested_N": 10,
            "observed_available_N": 7,
            "executor_id": "node_runtime_alpha",
        },
        "route_policy_ref": "policy://zecp11/bound-oracle-route-001",
        "completion_contract": {
            "success": "STRUCTURED_TARGET_MATCH",
            "failure": "AUTHORITY_OR_IDENTITY_VIOLATION",
            "unknown": "PRESERVE_UNKNOWN",
        },
        "reserved_result_id": f"result-bound-{process_id.lower()}-001",
        "reserved_executor_binding": {
            "grid_instance_id": "grid-fixture-001",
            "executor_id": "node_runtime_alpha",
            "lease_id": "lease-bound-oracle-001",
        },
        "runtime_receipt_ref": "runtime://unobserved/source-pilot",
    }


def _case(process_id: str) -> dict[str, Any]:
    e = lambda n: _ref("evidence", process_id, n)
    s = lambda n: _ref("state", process_id, n)
    cases: dict[str, dict[str, Any]] = {
        "ZECP03": {
            "delta": {"type": "MISSING_WORKING_DETAIL", "observed_ref": e("task"), "missing": ["tool_result"]},
            "payload": {
                "working_state_candidate": {"task_ref": e("task"), "tool_result": "UNKNOWN", "status": "CANDIDATE"},
                "missing_state_questions": ["tool_result"],
            },
            "unknowns": ["tool_result"],
        },
        "ZECP04": {
            "delta": {"type": "CAPACITY_PRESSURE", "active_budget": 2, "contradictory_ref": e("minority")},
            "payload": {
                "attention_slice": [e("primary"), e("support")],
                "deferred_refs": [e("minority")],
                "uncertainty_set": [e("minority")],
            },
            "unknowns": [],
        },
        "ZECP05": {
            "delta": {"type": "SUBGOAL_PROGRESS", "durable_goal_ref": s("goal"), "completed": ["collect"], "open": ["validate"]},
            "payload": {
                "goal_state_candidate": {"durable_goal_ref": s("goal"), "active_subgoal": "validate", "status": "CANDIDATE"},
                "completion_tests": [{"id": "validate", "required": True, "status": "PENDING"}],
            },
            "unknowns": [],
        },
        "ZECP06": {
            "delta": {"type": "PREREQUISITE_FALSIFIED", "work_unit": "unit-2", "falsifier_ref": e("falsifier")},
            "payload": {
                "work_graph_candidate": {"branch": "replan-1", "preserved_prior_branch_ref": s("plan-old")},
                "work_units": [{"id": "unit-2b", "depends_on": ["unit-1"], "status": "CANDIDATE"}],
                "replan_conditions": [{"because_ref": e("falsifier"), "old_unit": "unit-2"}],
            },
            "unknowns": [],
        },
        "ZECP07": {
            "delta": {"type": "UNRESOLVED_ALTERNATIVES", "votes": {"A": 8, "B": 2}, "causal_discriminator": "ABSENT"},
            "payload": {
                "alternative_set": [
                    {"id": "A", "status": "LIVE", "evidence_ref": e("a")},
                    {"id": "B", "status": "LIVE", "evidence_ref": e("b")},
                ],
                "uncertainty_readout": {"resolved": False, "reason": "NO_CAUSAL_DISCRIMINATOR"},
                "discriminator_candidates": [{"probe_ref": _ref("probe", process_id, "d1")}],
            },
            "unknowns": ["truth_of_A_vs_B"],
        },
        "ZECP08": {
            "delta": {"type": "BOUNDED_INFERENCE_REQUEST", "premise_refs": [e("p1"), e("p2")]},
            "payload": {
                "candidate_result": {"value": "candidate-conclusion-1", "evidence_refs": [e("p1"), e("p2")]},
                "candidate_action": {"action": "REQUEST_DISCRIMINATOR", "status": "CANDIDATE"},
                "confidence_readout": 0.61,
            },
            "unknowns": ["canonical_truth_of_candidate_conclusion"],
        },
        "ZECP09": {
            "delta": {"type": "STALE_EPOCH_DETECTED_BY_ORACLE", "oracle_status": "STALE_REJECTED", "stale_epoch": 41, "current_epoch": 42},
            "payload": {
                "quality_readout": {"status": "REVISION_REQUIRED"},
                "contradiction_flags": ["STALE_STATE"],
                "revision_request": {"action": "REREAD_RECOMPUTE", "current_state_ref": s("snapshot-0042")},
            },
            "unknowns": [],
        },
        "ZECP10": {
            "delta": {"type": "WORKSPACE_SELECTION", "selected_result_ref": _ref("result", process_id, "winner"), "nonwinner_refs": [_ref("result", process_id, "alt")]},
            "payload": {
                "workspace_selection": {"selected_ref": _ref("result", process_id, "winner"), "status": "CANDIDATE"},
                "broadcast_packet": {"payload_ref": _ref("workspace", process_id, "broadcast"), "truth_claim": "NONE"},
                "reentry_refs": [_ref("workspace", process_id, "reentry")],
            },
            "unknowns": ["observed_downstream_change"],
        },
        "ZECP12": {
            "delta": {"type": "COMPRESSION_BUDGET", "target_tokens": 64, "minority_ref": e("minority")},
            "payload": {
                "compressed_state_packet": {"summary_ref": _ref("compressed", process_id, "v1"), "minority_ref": e("minority")},
                "loss_manifest": {"dropped": ["surface_repetition"], "preserved_refs": [e("minority"), e("primary")]},
                "reentry_binding": {"source_epoch": 42, "payload_ref": _ref("compressed", process_id, "v1")},
            },
            "unknowns": [],
        },
        "ZECP13": {
            "delta": {"type": "CLAUDE_HANDOFF_REQUIRED", "tool_scope_ref": _ref("tool-scope", process_id, "bounded")},
            "payload": {
                "claude_handoff_packet": {
                    "direction": "GRID_TO_CLAUDE",
                    "interface_class": "STRUCTURED_TEXT",
                    "state_refs": [s("snapshot-0042")],
                    "tool_scope_ref": _ref("tool-scope", process_id, "bounded"),
                },
                "bridge_request_receipt": {"request_ref": _ref("bridge", process_id, "request-1"), "status": "CANDIDATE_PREPARED"},
            },
            "unknowns": ["claude_hidden_activation_state"],
        },
        "ZECP14": {
            "delta": {"type": "CLAUDE_RETURN", "request_ref": _ref("bridge", process_id, "request-1"), "tool_result_ref": e("tool-result")},
            "payload": {
                "bridge_return_packet": {"request_ref": _ref("bridge", process_id, "request-1"), "assertion_status": "CANDIDATE"},
                "evidence_candidates": [{"ref": e("tool-result"), "class": "TOOL_RESULT"}, {"ref": e("claude-text"), "class": "MODEL_ASSERTION"}],
                "workspace_reentry_candidate": {"payload_ref": _ref("workspace", process_id, "reentry"), "acceptance": "UNKNOWN"},
            },
            "unknowns": ["claude_assertion_truth"],
        },
        "ZECP15": {
            "delta": {"type": "VERIFIED_OUTCOME_AVAILABLE", "outcome_ref": e("verified-outcome")},
            "payload": {
                "state_update_proposal": {"target_ref": s("memory"), "value_ref": e("verified-outcome"), "status": "PROPOSAL"},
                "memory_update_proposal": {"memory_key": "episode-result", "source_ref": e("verified-outcome"), "status": "PROPOSAL"},
                "provenance_refs": [e("verified-outcome")],
            },
            "unknowns": [],
        },
        "ZECP16": {
            "delta": {"type": "EFFECT_INTENT_SELECTED", "capability_oracle_ref": _ref("capability", process_id, "allowed-scope")},
            "payload": {
                "effect_request_candidate": {
                    "action": "TOOL_CALL",
                    "capability_ref": _ref("capability", process_id, "allowed-scope"),
                    "status": "CANDIDATE",
                },
                "precondition_refs": [e("precondition")],
            },
            "unknowns": ["real_effect_outcome"],
        },
        "ZECP18": {
            "delta": {"type": "UNKNOWN_EFFECT_OUTCOME", "effect_receipt_ref": e("effect-timeout"), "verification_status": "UNKNOWN"},
            "payload": {
                "reconciled_state_candidate": {"effect_outcome": "UNKNOWN", "blind_replay": False},
                "next_work_units": [{"action": "VERIFY_OUTCOME", "receipt_ref": e("effect-timeout")}],
                "rejoin_plan": {"preserve_process_identity": True, "resume_after": "OUTCOME_VERIFICATION"},
            },
            "unknowns": ["effect_outcome"],
        },
        "ZECP19": {
            "delta": {"type": "CLAYCODE_TRANSFORM_REQUEST", "typed_packet_ref": _ref("typed-packet", process_id, "input")},
            "payload": {
                "claycode_packet": {"source_ref": _ref("claycode", process_id, "candidate"), "status": "CANDIDATE"},
                "transform_receipt": {"input_ref": _ref("typed-packet", process_id, "input"), "semantic_equivalence": "EVALUATOR_REQUIRED"},
            },
            "unknowns": [],
        },
        "ZECP20": {
            "delta": {"type": "JSPACE_CONTROL_WITHOUT_CAUSAL_RECEIPT", "exact_model_runtime_identity": "UNKNOWN", "probe_ref": _ref("probe", process_id, "sign-flip")},
            "payload": {
                "jspace_measurement": {"status": "UNKNOWN_NO_EXACT_RUNTIME_IDENTITY", "behavioral_observation": "NOT_PROMOTED"},
                "causal_probe_receipt": {"probe_ref": _ref("probe", process_id, "sign-flip"), "status": "NOT_EXECUTED_IN_SOURCE_PILOT"},
                "credit_scope": {"behavioral": 0, "representation_level": 0, "causal": 0},
            },
            "unknowns": ["model_specific_jspace_causality"],
        },
    }
    return copy.deepcopy(cases[process_id])


def _result_packet(work: dict[str, Any], payload: dict[str, Any], unknowns: list[str]) -> dict[str, Any]:
    process_id = work["process_id"]
    result_id = work["reserved_result_id"]
    payload_digest = _digest(payload)
    db_write_proposals: list[dict[str, Any]] = []
    effect_request_candidates: list[dict[str, Any]] = []
    if process_id == "ZECP15":
        db_write_proposals = [copy.deepcopy(payload["memory_update_proposal"])]
    if process_id == "ZECP16":
        effect_request_candidates = [copy.deepcopy(payload["effect_request_candidate"])]
    return {
        "schema": "COGNITIVE_RESULT_PACKET/v1",
        "causal_event_id": work["causal_event_id"],
        "admission_id": work["admission_id"],
        "generation": work["generation"],
        "work_id": work["work_id"],
        "process_id": process_id,
        "executor_binding": copy.deepcopy(work["reserved_executor_binding"]),
        "result_id": result_id,
        "result_class": "CANDIDATE",
        "result_payload_ref": f"inline-sha256:{payload_digest}",
        "result_digest": payload_digest,
        "evidence_refs": [item["ref"] for item in work["epistemic_inputs"] if item["status"] == "OBSERVED"],
        "unknowns": list(unknowns),
        "db_write_proposals": db_write_proposals,
        "effect_request_candidates": effect_request_candidates,
        "workspace_reentry": {
            "source_result_id": result_id,
            "source_process_id": process_id,
            "causal_event_id": work["causal_event_id"],
            "from_workspace_epoch": work["workspace_epoch"],
            "to_workspace_epoch": work["workspace_epoch"] + 1,
            "reentry_payload_ref": f"inline-sha256:{payload_digest}",
            "reentry_digest": payload_digest,
            "acceptance": "UNKNOWN",
        },
        "runtime_receipt": {
            "status": "UNOBSERVED_IN_SOURCE_PILOT",
            "runtime_ref": work["runtime_receipt_ref"],
        },
    }


def _state_after(work: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_state_snapshot_ref": work["state_snapshot_ref"],
        "source_workspace_epoch": work["workspace_epoch"],
        "candidate_workspace_epoch": work["workspace_epoch"] + 1,
        "process_id": work["process_id"],
        "result_id": result["result_id"],
        "result_digest": result["result_digest"],
        "canonical_commit_status": "NOT_REQUESTED",
        "effect_execution_status": "NOT_EXECUTED",
        "workspace_reentry_acceptance": "UNKNOWN",
    }


def _find_forbidden_key(value: Any, path: str = "$") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_TARGET_KEYS:
                return f"{path}.{key}"
            nested = _find_forbidden_key(child, f"{path}.{key}")
            if nested:
                return nested
    elif isinstance(value, list):
        for index, child in enumerate(value):
            nested = _find_forbidden_key(child, f"{path}[{index}]")
            if nested:
                return nested
    return None


def _source_bindings() -> dict[str, Any]:
    return {
        "census": {
            "path": str(CENSUS_PATH.relative_to(ROOT)),
            "sha256": _file_sha256(CENSUS_PATH),
        },
        "abi": {
            "path": str(ABI_PATH.relative_to(ROOT)),
            "sha256": _file_sha256(ABI_PATH),
        },
        "claycode_adapter": {
            "path": str(ADAPTER_PATH.relative_to(ROOT)),
            "sha256": _file_sha256(ADAPTER_PATH),
        },
    }


def build_row(process: dict[str, Any]) -> dict[str, Any]:
    process_id = process["id"]
    work = _base_work_packet(process_id)
    case = _case(process_id)
    payload = case["payload"]
    census_outputs = process.get("outputs")
    if not isinstance(census_outputs, list) or set(payload) != set(census_outputs):
        raise ValueError(f"PAYLOAD_CENSUS_OUTPUT_MISMATCH:{process_id}")
    result = _result_packet(work, payload, case["unknowns"])
    clay_envelope, decoded = roundtrip("COGNITIVE_RESULT_PACKET/v1", result)
    if decoded != result:
        raise ValueError(f"CLAYCODE_ROUNDTRIP_MISMATCH:{process_id}")
    target = {
        "schema": TARGET_SCHEMA,
        "result_payload": payload,
        "result_packet": result,
        "state_after": _state_after(work, result),
    }
    row = {
        "schema": ROW_SCHEMA,
        "row_id": f"TR2EXECV1_{process_id}",
        "process_id_evaluator_only": process_id,
        "implementation_class_evaluator_only": process["implementation_class"],
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2_GENERATED_CANDIDATE",
        "split": "QUARANTINED_PILOT_NOT_TRAINING_ADMITTED",
        "accepted_for_training": False,
        "accepted_dataset_tokens": 0,
        "state_before": work,
        "decisive_delta": case["delta"],
        "target": target,
        "evaluator_only": {
            "expected_payload_digest": result["result_digest"],
            "claycode_packet_digest": clay_envelope.packet_digest,
            "claycode_source_sha256": clay_envelope.clay_source_sha256,
            "claycode_semantic_hash": clay_envelope.clay_semantic_hash,
            "claycode_grammar_sha256": clay_envelope.clay_grammar_sha256,
            "deterministic_authority_outputs_are_oracle_inputs_only": True,
            "checkpoint_selection_credit": 0,
            "jspace_causal_credit": 0,
            "training_credit": 0,
        },
        "source_bindings": _source_bindings(),
    }
    verdict = adjudicate(row, target, process_map={process_id: process})
    if not verdict["pass"]:
        raise ValueError(f"SELF_ADJUDICATION_FAILED:{process_id}:{verdict['failures']}")
    return row


def build_pilot_rows() -> list[dict[str, Any]]:
    processes = _process_map()
    rows = [
        build_row(processes[process_id])
        for process_id in sorted(EXPECTED_TRAINABLE_PROCESS_IDS)
    ]
    return rows


def adjudicate(
    row: Any,
    candidate_target: Any,
    *,
    process_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        row = {}
        failures.append("ROW_OBJECT_REQUIRED")
    if not isinstance(candidate_target, dict):
        candidate_target = {}
        failures.append("TARGET_OBJECT_REQUIRED")

    if row.get("schema") != ROW_SCHEMA:
        failures.append("ROW_SCHEMA_MISMATCH")
    if candidate_target.get("schema") != TARGET_SCHEMA:
        failures.append("TARGET_SCHEMA_MISMATCH")
    if row.get("accepted_for_training") is not False or row.get("accepted_dataset_tokens") != 0:
        failures.append("SOURCE_PILOT_CANNOT_ADMIT_TRAINING")

    forbidden = _find_forbidden_key(candidate_target)
    if forbidden:
        failures.append("MODEL_TARGET_AUTHORITY_SMUGGLING:" + forbidden)

    expected = row.get("target")
    if not isinstance(expected, dict):
        failures.append("EXPECTED_TARGET_REQUIRED")
        expected = {}

    state_before = row.get("state_before")
    if not isinstance(state_before, dict):
        failures.append("STATE_BEFORE_REQUIRED")
        state_before = {}

    process_id = row.get("process_id_evaluator_only")
    if not isinstance(process_id, str):
        failures.append("PROCESS_ID_REQUIRED")
        process_id = ""
    if state_before.get("process_id") != process_id:
        failures.append("STATE_BEFORE_PROCESS_MISMATCH")

    process_map = process_map or _process_map()
    process = process_map.get(process_id)
    if not isinstance(process, dict):
        failures.append("PROCESS_NOT_IN_CENSUS")
    else:
        impl = process.get("implementation_class")
        if impl not in TRAINABLE_IMPLEMENTATION_CLASSES:
            failures.append("DETERMINISTIC_OR_STORE_PROCESS_CANNOT_BE_MODEL_TARGET")

    result = candidate_target.get("result_packet")
    payload = candidate_target.get("result_payload")
    state_after = candidate_target.get("state_after")
    if not isinstance(result, dict):
        failures.append("RESULT_PACKET_REQUIRED")
        result = {}
    if not isinstance(payload, dict):
        failures.append("RESULT_PAYLOAD_REQUIRED")
        payload = {}
    if not isinstance(state_after, dict):
        failures.append("STATE_AFTER_REQUIRED")
        state_after = {}

    if result.get("process_id") != process_id:
        failures.append("RESULT_PROCESS_MISMATCH")
    if result.get("result_class") in FORBIDDEN_RESULT_CLASSES:
        failures.append("MODEL_TARGET_RESULT_CLASS_FORBIDDEN")
    if result.get("result_class") != "CANDIDATE":
        failures.append("MODEL_TARGET_MUST_REMAIN_CANDIDATE")

    if process:
        outputs = process.get("outputs")
        if not isinstance(outputs, list) or set(payload) != set(outputs):
            failures.append("RESULT_PAYLOAD_CENSUS_OUTPUT_MISMATCH")

    payload_digest = _digest(payload)
    if result.get("result_digest") != payload_digest:
        failures.append("RESULT_DIGEST_MISMATCH")
    if result.get("result_payload_ref") != f"inline-sha256:{payload_digest}":
        failures.append("RESULT_PAYLOAD_REF_MISMATCH")

    for copied in ("causal_event_id", "admission_id", "generation", "work_id"):
        if result.get(copied) != state_before.get(copied):
            failures.append("BOUND_IDENTITY_NOT_COPIED:" + copied)
    if result.get("result_id") != state_before.get("reserved_result_id"):
        failures.append("RESULT_ID_MUST_COPY_ORACLE_RESERVATION")
    if result.get("executor_binding") != state_before.get("reserved_executor_binding"):
        failures.append("EXECUTOR_BINDING_MUST_COPY_ORACLE_RESERVATION")

    expected_after = expected.get("state_after") if isinstance(expected, dict) else None
    if state_after != expected_after:
        failures.append("STATE_AFTER_SEMANTIC_MISMATCH")

    if candidate_target != expected:
        failures.append("TARGET_SEMANTIC_MISMATCH")

    if process_id == "ZECP07":
        try:
            if payload["uncertainty_readout"]["resolved"] is not False:
                failures.append("MAJORITY_CANNOT_RESOLVE_HYPERPOSITION")
        except Exception:
            failures.append("HYPERPOSITION_PAYLOAD_INVALID")
    if process_id == "ZECP16" and result.get("effect_request_candidates"):
        if state_after.get("effect_execution_status") != "NOT_EXECUTED":
            failures.append("EFFECT_CANDIDATE_CANNOT_IMPLY_EXECUTION")
    if process_id == "ZECP20":
        scope = payload.get("credit_scope")
        if not isinstance(scope, dict) or any(scope.get(k) != 0 for k in ("behavioral", "representation_level", "causal")):
            failures.append("JSPACE_SOURCE_PILOT_CANNOT_MINT_CAUSAL_CREDIT")
        if "model_specific_jspace_causality" not in result.get("unknowns", []):
            failures.append("JSPACE_CAUSALITY_UNKNOWN_MUST_BE_PRESERVED")

    try:
        envelope, decoded = roundtrip("COGNITIVE_RESULT_PACKET/v1", result)
        if decoded != result:
            failures.append("CLAYCODE_ROUNDTRIP_SEMANTIC_MISMATCH")
        expected_eval = row.get("evaluator_only")
        if isinstance(expected_eval, dict):
            if envelope.packet_digest != expected_eval.get("claycode_packet_digest"):
                failures.append("CLAYCODE_PACKET_DIGEST_MISMATCH")
            if envelope.clay_semantic_hash != expected_eval.get("claycode_semantic_hash"):
                failures.append("CLAYCODE_SEMANTIC_HASH_MISMATCH")
    except (ClayCodeCognitiveProtocolError, ValueError, TypeError) as exc:
        failures.append("CLAYCODE_ROUNDTRIP_REJECTED:" + type(exc).__name__)

    failures = sorted(set(failures))
    return {
        "schema": ADJUDICATION_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "training_row_admitted": False,
        "accepted_dataset_tokens_delta": 0,
        "checkpoint_selection_credit_minted": False,
        "jspace_causal_credit_minted": False,
        "training_credit_minted": False,
    }


def summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [row["process_id_evaluator_only"] for row in rows]
    return {
        "schema": SCHEMA,
        "status": "PASS_SOURCE_ONLY_QUARANTINED_PILOT" if set(ids) == EXPECTED_TRAINABLE_PROCESS_IDS else "FAIL",
        "rows": len(rows),
        "trainable_process_ids": ids,
        "deterministic_or_store_process_ids_excluded": ["ZECP01", "ZECP02", "ZECP11", "ZECP17"],
        "target_semantics": "CONCRETE_TYPED_TRANSITION_NOT_META_RULE_NARRATION",
        "accepted_positive_rows": 0,
        "accepted_dataset_tokens": 0,
        "training_executed": False,
        "training_credit": 0,
        "checkpoint_selection_credit": 0,
        "jspace_causal_credit": 0,
        "source_bindings": _source_bindings(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    rows = build_pilot_rows()
    result = summary(rows)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(_canonical_json(row) + "\n")
        result["output_path"] = str(args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
