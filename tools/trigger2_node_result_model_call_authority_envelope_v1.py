#!/usr/bin/env python3
"""Source-only Trigger-2 NODE_RESULT -> model-call authority envelope gate.

This module closes one deterministic provenance subgap without executing a model/provider.
It preserves the raw NODE_RESULT cognitive packet unchanged and wraps it with controller-owned
references to the already-existing source-bound model call identity and model-output identity.

No new model-call identity is invented here. The call identity MUST be the exact identity
emitted by CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1 and MUST match an upstream-frozen
controller binding. The resulting NODE_RESULT authority-envelope digest is a distinct fabric
identity for packet provenance, not a competing model-call identity.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_AUTHORITY_ENVELOPE/v1"
CALL_GATE_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
CALL_IDENTITY_SCHEMA = "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1"
CONTROLLER_BINDING_SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_CONTROLLER_BINDING/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
ENVELOPE_SCHEMA = "NODE_RESULT_AUTHORITY_ENVELOPE/v2"
HEX64 = re.compile(r"^[0-9a-f]{64}$")

FORBIDDEN_RAW_AUTHORITY_FIELDS = {
    "source_bound_model_call_identity_sha256",
    "model_output_identity_sha256",
    "source_identity_sha256",
    "route_decision_identity_sha256",
    "resolved_engine_identity_sha256",
    "grid_plan_identity_sha256",
    "grid_cell_id",
    "source_node_admission_id",
    "source_node_admission_revision",
    "source_process_witness_digest",
    "node_result_authority_envelope_sha256",
}


class GateError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _hex64(value: Any, code: str) -> str:
    _require(isinstance(value, str) and bool(HEX64.fullmatch(value)), code)
    return value


def validate_raw_node_result(packet: Mapping[str, Any]) -> dict[str, Any]:
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
    _require(packet.get("source_kind") == "ORDINARY_NODE", "NODE_RESULT_SOURCE_KIND_INVALID")
    _require(packet.get("s1_write_intent") is False, "NODE_RESULT_MUST_NOT_SELF_WRITE")
    leaked = sorted(FORBIDDEN_RAW_AUTHORITY_FIELDS.intersection(packet.keys()))
    _require(not leaked, "RAW_PACKET_AUTHORITY_FIELD_FORBIDDEN")
    node_id = packet.get("source_node_id")
    _require(isinstance(node_id, str) and node_id, "NODE_RESULT_SOURCE_NODE_ID_INVALID")
    generation = packet.get("generation")
    epoch = packet.get("state_epoch")
    state_digest = packet.get("state_digest")
    _require(isinstance(generation, int) and generation >= 0, "NODE_RESULT_GENERATION_INVALID")
    _require(isinstance(epoch, int) and epoch >= 0, "NODE_RESULT_STATE_EPOCH_INVALID")
    _hex64(state_digest, "NODE_RESULT_STATE_DIGEST_INVALID")
    payload = _mapping(packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    pid = payload.get("process_pid")
    _require(isinstance(pid, int) and pid > 0, "NODE_RESULT_PROCESS_PID_INVALID")
    if "producer_pid" in packet:
        _require(packet.get("producer_pid") == pid, "NODE_RESULT_PRODUCER_PID_PAYLOAD_MISMATCH")
    claimed_digest = _hex64(packet.get("packet_digest"), "NODE_RESULT_PACKET_DIGEST_INVALID")
    core = {key: packet[key] for key in packet if key not in ("packet_digest", "s1_write_intent")}
    observed_digest = canonical_sha256(core)
    _require(observed_digest == claimed_digest, "NODE_RESULT_PACKET_DIGEST_MISMATCH")
    return {
        "raw_node_result_packet_digest": claimed_digest,
        "raw_source_node_id": node_id,
        "raw_process_pid": pid,
        "raw_generation": generation,
        "raw_state_epoch": epoch,
        "raw_state_digest": state_digest,
    }


def validate_call_gate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _require(receipt.get("schema") == CALL_GATE_SCHEMA, "CALL_GATE_SCHEMA_MISMATCH")
    _require(receipt.get("pass") is True, "CALL_GATE_NOT_PASS")
    _require(receipt.get("status") == "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY", "CALL_GATE_STATUS_INVALID")
    call_id = _hex64(receipt.get("source_bound_model_call_identity_sha256"), "SOURCE_BOUND_MODEL_CALL_IDENTITY_INVALID")
    output_id = _hex64(receipt.get("model_output_identity_sha256"), "MODEL_OUTPUT_IDENTITY_INVALID")
    source_identity = _mapping(receipt.get("source_identity"), "SOURCE_IDENTITY_REQUIRED")
    source_identity_id = _hex64(source_identity.get("source_identity_sha256"), "SOURCE_IDENTITY_SHA256_INVALID")
    source_bound = _mapping(receipt.get("source_bound_envelope"), "SOURCE_BOUND_ENVELOPE_REQUIRED")
    _require(source_bound.get("schema") == CALL_IDENTITY_SCHEMA, "SOURCE_BOUND_ENVELOPE_SCHEMA_INVALID")
    _require(source_bound.get("model_output_identity_sha256") == output_id, "CALL_GATE_OUTPUT_IDENTITY_INTERNAL_MISMATCH")
    _require(source_bound.get("source_identity_sha256") == source_identity_id, "CALL_GATE_SOURCE_IDENTITY_INTERNAL_MISMATCH")
    _require(canonical_sha256(dict(source_bound)) == call_id, "SOURCE_BOUND_MODEL_CALL_IDENTITY_RECOMPUTE_MISMATCH")
    return {
        "source_bound_model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_id,
        "source_identity_sha256": source_identity_id,
    }


def validate_controller_binding(binding: Mapping[str, Any], *, expected_sha256: str) -> dict[str, Any]:
    _hex64(expected_sha256, "EXPECTED_CONTROLLER_BINDING_SHA256_INVALID")
    _require(binding.get("schema") == CONTROLLER_BINDING_SCHEMA, "CONTROLLER_BINDING_SCHEMA_MISMATCH")
    node_id = binding.get("controller_observed_node_id")
    pid = binding.get("controller_observed_pid")
    cell = binding.get("grid_cell_id")
    membership_id = binding.get("source_node_admission_id")
    membership_revision = binding.get("source_node_admission_revision")
    runtime_generation = binding.get("source_runtime_generation")
    causal_event_id = binding.get("causal_event_id")
    admission_id = binding.get("admission_id")
    _require(isinstance(node_id, str) and node_id, "CONTROLLER_NODE_ID_INVALID")
    _require(isinstance(pid, int) and pid > 0, "CONTROLLER_PID_INVALID")
    _require(isinstance(cell, str) and cell, "GRID_CELL_ID_INVALID")
    _require(isinstance(membership_id, str) and membership_id, "SOURCE_NODE_ADMISSION_ID_INVALID")
    _require(isinstance(membership_revision, int) and membership_revision > 0, "SOURCE_NODE_ADMISSION_REVISION_INVALID")
    _require(isinstance(runtime_generation, int) and runtime_generation >= 0, "SOURCE_RUNTIME_GENERATION_INVALID")
    _require(isinstance(causal_event_id, str) and causal_event_id, "CAUSAL_EVENT_ID_INVALID")
    _require(isinstance(admission_id, str) and admission_id, "ADMISSION_ID_INVALID")
    for key, code in (
        ("source_process_witness_digest", "SOURCE_PROCESS_WITNESS_DIGEST_INVALID"),
        ("route_decision_identity_sha256", "ROUTE_DECISION_IDENTITY_INVALID"),
        ("resolved_engine_identity_sha256", "RESOLVED_ENGINE_IDENTITY_INVALID"),
        ("grid_plan_identity_sha256", "GRID_PLAN_IDENTITY_INVALID"),
        ("expected_source_bound_model_call_identity_sha256", "EXPECTED_SOURCE_BOUND_CALL_IDENTITY_INVALID"),
        ("expected_model_output_identity_sha256", "EXPECTED_MODEL_OUTPUT_IDENTITY_INVALID"),
        ("expected_source_identity_sha256", "EXPECTED_SOURCE_IDENTITY_INVALID"),
    ):
        _hex64(binding.get(key), code)
    observed = canonical_sha256(dict(binding))
    _require(observed == expected_sha256, "CONTROLLER_BINDING_COMMITMENT_MISMATCH")
    return dict(binding)


def build_authority_envelope(raw_packet: Mapping[str, Any], call_gate_receipt: Mapping[str, Any], controller_binding: Mapping[str, Any], *, expected_controller_binding_sha256: str) -> dict[str, Any]:
    raw = validate_raw_node_result(raw_packet)
    call = validate_call_gate_receipt(call_gate_receipt)
    binding = validate_controller_binding(controller_binding, expected_sha256=expected_controller_binding_sha256)
    _require(binding["expected_source_bound_model_call_identity_sha256"] == call["source_bound_model_call_identity_sha256"], "MODEL_CALL_REFERENCE_TRANSPLANT")
    _require(binding["expected_model_output_identity_sha256"] == call["model_output_identity_sha256"], "MODEL_OUTPUT_IDENTITY_MISMATCH_WITH_REFERENCED_CALL")
    _require(binding["expected_source_identity_sha256"] == call["source_identity_sha256"], "SOURCE_IDENTITY_REFERENCE_TRANSPLANT")
    _require(binding["controller_observed_node_id"] == raw["raw_source_node_id"], "MODEL_CALL_REFERENCE_TRANSPLANTED_TO_DIFFERENT_NODE")
    _require(binding["controller_observed_pid"] == raw["raw_process_pid"], "MODEL_CALL_REFERENCE_TRANSPLANTED_TO_DIFFERENT_PROCESS")
    _require(binding["source_runtime_generation"] == raw["raw_generation"], "SOURCE_RUNTIME_GENERATION_MISMATCH")
    envelope = {
        "schema": ENVELOPE_SCHEMA,
        "raw_node_result_packet_digest": raw["raw_node_result_packet_digest"],
        "raw_source_node_id": raw["raw_source_node_id"],
        "raw_process_pid": raw["raw_process_pid"],
        "raw_generation": raw["raw_generation"],
        "raw_state_epoch": raw["raw_state_epoch"],
        "raw_state_digest": raw["raw_state_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "source_identity_sha256": call["source_identity_sha256"],
        "causal_event_id": binding["causal_event_id"],
        "admission_id": binding["admission_id"],
        "route_decision_identity_sha256": binding["route_decision_identity_sha256"],
        "resolved_engine_identity_sha256": binding["resolved_engine_identity_sha256"],
        "grid_plan_identity_sha256": binding["grid_plan_identity_sha256"],
        "grid_cell_id": binding["grid_cell_id"],
        "source_node_admission_id": binding["source_node_admission_id"],
        "source_node_admission_revision": binding["source_node_admission_revision"],
        "source_runtime_generation": binding["source_runtime_generation"],
        "source_process_witness_digest": binding["source_process_witness_digest"],
        "controller_observed_node_id": binding["controller_observed_node_id"],
        "controller_observed_pid": binding["controller_observed_pid"],
    }
    envelope_digest = canonical_sha256(envelope)
    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_NODE_RESULT_CALL_LINEAGE_COMPONENT",
        "raw_packet_unchanged": True,
        "raw_packet_digest": raw["raw_node_result_packet_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "node_result_authority_envelope": envelope,
        "node_result_authority_envelope_sha256": envelope_digest,
        "credit_boundary": {
            "model_call_runtime_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "checkpoint_selection_credit": 0,
            "jspace_model_credit": 0,
            "accepted_dataset_tokens": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def validate_atomic_cohort_envelopes(results: list[Mapping[str, Any]], *, expected_count: int = 10) -> dict[str, Any]:
    _require(len(results) == expected_count, "COHORT_AUTHORITY_ENVELOPE_COUNT_INVALID")
    envelopes: list[Mapping[str, Any]] = []
    digests: list[str] = []
    for result in results:
        _require(result.get("schema") == SCHEMA and result.get("pass") is True, "COHORT_MEMBER_AUTHORITY_ENVELOPE_INVALID")
        envelope = _mapping(result.get("node_result_authority_envelope"), "COHORT_MEMBER_ENVELOPE_REQUIRED")
        digest = _hex64(result.get("node_result_authority_envelope_sha256"), "COHORT_MEMBER_ENVELOPE_DIGEST_INVALID")
        _require(canonical_sha256(dict(envelope)) == digest, "COHORT_MEMBER_ENVELOPE_DIGEST_MISMATCH")
        envelopes.append(envelope)
        digests.append(digest)
    def values(key: str) -> list[Any]:
        return [e[key] for e in envelopes]
    _require(len(set(digests)) == expected_count, "COHORT_DUPLICATE_AUTHORITY_ENVELOPE")
    _require(len(set(values("raw_node_result_packet_digest"))) == expected_count, "COHORT_DUPLICATE_RAW_PACKET")
    _require(len(set(values("source_bound_model_call_identity_sha256"))) == expected_count, "COHORT_DUPLICATE_MODEL_CALL_IDENTITY")
    _require(len(set(values("raw_source_node_id"))) == expected_count, "COHORT_DUPLICATE_NODE_ID")
    _require(len(set(values("raw_process_pid"))) == expected_count, "COHORT_DUPLICATE_PROCESS_IDENTITY")
    _require(len(set(values("grid_cell_id"))) == expected_count, "COHORT_DUPLICATE_GRID_CELL_ID")
    _require(len(set(values("source_node_admission_id"))) == expected_count, "COHORT_DUPLICATE_NODE_ADMISSION_ID")
    snapshots = {(e["raw_generation"], e["raw_state_epoch"], e["raw_state_digest"]) for e in envelopes}
    _require(len(snapshots) == 1, "COHORT_MIXED_SNAPSHOT_AUTHORITY_ENVELOPES")
    plans = set(values("grid_plan_identity_sha256"))
    _require(len(plans) == 1, "COHORT_MIXED_GRID_PLAN_IDENTITY")
    ordered = sorted(digests)
    cohort_authority_identity = canonical_sha256({
        "schema": "GRID10_NODE_RESULT_AUTHORITY_COHORT/v1",
        "member_count": expected_count,
        "grid_plan_identity_sha256": next(iter(plans)),
        "snapshot_identity": list(next(iter(snapshots))),
        "ordered_node_result_authority_envelope_sha256": ordered,
    })
    return {
        "pass": True,
        "member_count": expected_count,
        "cohort_authority_identity_sha256": cohort_authority_identity,
        "ordered_node_result_authority_envelope_sha256": ordered,
    }
