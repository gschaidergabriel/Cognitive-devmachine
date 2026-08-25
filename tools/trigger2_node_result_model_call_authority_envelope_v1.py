#!/usr/bin/env python3
"""Source-only Trigger-2 NODE_RESULT -> model-call authority envelope gate.

This deterministic gate does not execute a model/provider and mints no runtime or training
credit. It composes the existing immutable NODE_RESULT/v1 evidence with the already-derived
source-bound Trigger-2 model-call identity. It deliberately does NOT invent a second call ID.

Controller-owned launch binding freezes the expected node/cell/call/output identities before
acceptance. Model-generated cognitive payloads are forbidden from self-asserting those
authority fields. The resulting envelope can be consumed by GRID10 cohort/J-Space lineage.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping

SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_AUTHORITY_ENVELOPE/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
CALL_GATE_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
CALL_GATE_STATUS = "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY"
SOURCE_BOUND_CALL_SCHEMA = "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1"
LAUNCH_BINDING_SCHEMA = "CLAY_TRIGGER2_NODE_MODEL_CALL_LAUNCH_BINDING/v1"
AUTHORITY_ENVELOPE_SCHEMA = "NODE_RESULT_AUTHORITY_ENVELOPE/v2-model-call"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
FORBIDDEN_MODEL_AUTHORITY_FIELDS = {
    "source_bound_model_call_identity_sha256",
    "model_output_identity_sha256",
    "source_identity_sha256",
    "source_head_sha",
    "source_tree_sha",
    "grid_cell_id",
    "launch_binding_digest",
    "authority_envelope_digest",
}


class GateError(ValueError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise GateError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _hex64(value: Any, code: str) -> str:
    _require(isinstance(value, str) and HEX64.fullmatch(value) is not None, code)
    return value


def recompute_node_result_digest(packet: Mapping[str, Any]) -> str:
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
    _require(packet.get("source_kind") == "ORDINARY_NODE", "NODE_RESULT_SOURCE_KIND_MISMATCH")
    _require(packet.get("s1_write_intent") is False, "NODE_RESULT_MUST_NOT_SELF_WRITE")
    forbidden_present = sorted(FORBIDDEN_MODEL_AUTHORITY_FIELDS.intersection(packet.keys()))
    _require(not forbidden_present, "MODEL_GENERATED_AUTHORITY_FIELD_FORBIDDEN:" + ",".join(forbidden_present))
    payload = _mapping(packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    _require(isinstance(packet.get("source_node_id"), str) and packet["source_node_id"], "SOURCE_NODE_ID_REQUIRED")
    _require(isinstance(packet.get("producer_pid"), int), "PRODUCER_PID_REQUIRED")
    _require(payload.get("process_pid") == packet.get("producer_pid"), "PRODUCER_PID_PAYLOAD_MISMATCH")
    core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    observed = canonical_sha256(core)
    _hex64(packet.get("packet_digest"), "NODE_RESULT_PACKET_DIGEST_INVALID")
    _require(observed == packet.get("packet_digest"), "NODE_RESULT_PACKET_DIGEST_MISMATCH")
    return observed


def validate_call_gate(call_gate: Mapping[str, Any]) -> dict[str, str]:
    _require(call_gate.get("schema") == CALL_GATE_SCHEMA, "CALL_GATE_SCHEMA_MISMATCH")
    _require(call_gate.get("pass") is True, "CALL_GATE_NOT_PASS")
    _require(call_gate.get("status") == CALL_GATE_STATUS, "CALL_GATE_STATUS_MISMATCH")
    call_id = _hex64(call_gate.get("source_bound_model_call_identity_sha256"), "SOURCE_BOUND_CALL_ID_INVALID")
    output_id = _hex64(call_gate.get("model_output_identity_sha256"), "MODEL_OUTPUT_ID_INVALID")
    envelope = _mapping(call_gate.get("source_bound_envelope"), "SOURCE_BOUND_CALL_ENVELOPE_REQUIRED")
    _require(envelope.get("schema") == SOURCE_BOUND_CALL_SCHEMA, "SOURCE_BOUND_CALL_ENVELOPE_SCHEMA_MISMATCH")
    _require(envelope.get("model_output_identity_sha256") == output_id, "MODEL_OUTPUT_ID_ENVELOPE_MISMATCH")
    recomputed_call_id = canonical_sha256(dict(envelope))
    _require(recomputed_call_id == call_id, "SOURCE_BOUND_CALL_ID_RECOMPUTE_MISMATCH")
    source_identity_sha256 = _hex64(envelope.get("source_identity_sha256"), "SOURCE_IDENTITY_SHA256_INVALID")
    return {
        "source_bound_model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_id,
        "source_identity_sha256": source_identity_sha256,
    }


def validate_launch_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
    _require(binding.get("schema") == LAUNCH_BINDING_SCHEMA, "LAUNCH_BINDING_SCHEMA_MISMATCH")
    node_id = binding.get("source_node_id")
    cell_id = binding.get("grid_cell_id")
    pid = binding.get("producer_pid")
    _require(isinstance(node_id, str) and node_id, "LAUNCH_SOURCE_NODE_ID_REQUIRED")
    _require(isinstance(cell_id, str) and cell_id, "GRID_CELL_ID_REQUIRED")
    _require(isinstance(pid, int) and pid > 0, "LAUNCH_PRODUCER_PID_REQUIRED")
    call_id = _hex64(binding.get("expected_source_bound_model_call_identity_sha256"), "EXPECTED_CALL_ID_INVALID")
    output_id = _hex64(binding.get("expected_model_output_identity_sha256"), "EXPECTED_MODEL_OUTPUT_ID_INVALID")
    packet_digest = _hex64(binding.get("expected_node_result_digest"), "EXPECTED_NODE_RESULT_DIGEST_INVALID")
    core = {
        "schema": LAUNCH_BINDING_SCHEMA,
        "source_node_id": node_id,
        "grid_cell_id": cell_id,
        "producer_pid": pid,
        "expected_node_result_digest": packet_digest,
        "expected_source_bound_model_call_identity_sha256": call_id,
        "expected_model_output_identity_sha256": output_id,
    }
    claimed = _hex64(binding.get("launch_binding_digest"), "LAUNCH_BINDING_DIGEST_INVALID")
    observed = canonical_sha256(core)
    _require(observed == claimed, "LAUNCH_BINDING_DIGEST_MISMATCH")
    return {**core, "launch_binding_digest": observed}


def build_authority_envelope(
    packet: Mapping[str, Any],
    call_gate: Mapping[str, Any],
    launch_binding: Mapping[str, Any],
) -> dict[str, Any]:
    packet_digest = recompute_node_result_digest(packet)
    call = validate_call_gate(call_gate)
    launch = validate_launch_binding(launch_binding)

    _require(packet.get("source_node_id") == launch["source_node_id"], "CALL_NODE_TRANSPLANT_REJECTED")
    _require(packet.get("producer_pid") == launch["producer_pid"], "CALL_PROCESS_TRANSPLANT_REJECTED")
    _require(packet_digest == launch["expected_node_result_digest"], "NODE_RESULT_TRANSPLANT_REJECTED")
    _require(
        call["source_bound_model_call_identity_sha256"]
        == launch["expected_source_bound_model_call_identity_sha256"],
        "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED",
    )
    _require(
        call["model_output_identity_sha256"] == launch["expected_model_output_identity_sha256"],
        "MODEL_OUTPUT_REFERENCE_TRANSPLANT_REJECTED",
    )

    core = {
        "schema": AUTHORITY_ENVELOPE_SCHEMA,
        "node_result_digest": packet_digest,
        "source_node_id": launch["source_node_id"],
        "producer_pid": launch["producer_pid"],
        "grid_cell_id": launch["grid_cell_id"],
        "launch_binding_digest": launch["launch_binding_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "source_identity_sha256": call["source_identity_sha256"],
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
    }
    digest = canonical_sha256(core)
    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_LINEAGE_ENVELOPE",
        "authority_envelope": {**core, "authority_envelope_digest": digest},
        "authority_envelope_digest": digest,
        "credit_boundary": {
            "checkpoint_selection_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def verify_authority_envelope(result: Mapping[str, Any]) -> dict[str, Any]:
    _require(result.get("schema") == SCHEMA, "RESULT_SCHEMA_MISMATCH")
    _require(result.get("pass") is True, "RESULT_NOT_PASS")
    envelope = _mapping(result.get("authority_envelope"), "AUTHORITY_ENVELOPE_REQUIRED")
    claimed = _hex64(envelope.get("authority_envelope_digest"), "AUTHORITY_ENVELOPE_DIGEST_INVALID")
    core = {key: envelope[key] for key in envelope if key != "authority_envelope_digest"}
    observed = canonical_sha256(core)
    _require(observed == claimed, "AUTHORITY_ENVELOPE_DIGEST_MISMATCH")
    _require(result.get("authority_envelope_digest") == claimed, "RESULT_ENVELOPE_DIGEST_MISMATCH")
    _require(envelope.get("model_generated") is False, "AUTHORITY_ENVELOPE_MODEL_GENERATED_INVALID")
    _require(envelope.get("canonical_truth") is False, "AUTHORITY_ENVELOPE_TRUTH_CREDIT_INVALID")
    _require(envelope.get("effect_authority") is False, "AUTHORITY_ENVELOPE_EFFECT_CREDIT_INVALID")
    return dict(envelope)
