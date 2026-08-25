#!/usr/bin/env python3
"""Trigger-2 source-only NODE_RESULT -> exact model-call authority envelope.

This deterministic gate closes a source-structure gap only. It does not execute a model,
provider, VPS, GRID10 runtime, training, or effects, and it mints no runtime/promotion credit.

The existing source-bound model-call identity commits model state/input/output/repository
source but not the HCU node/cell invocation. The current single-envelope Trigger-2 lineage
gates close deterministic equality/transplant integrity, but their controller binding already
contains the model-call/output identities. Such a binding cannot literally be frozen before
the call whose output it names. It is therefore a post-call integrity commitment unless a
separate earlier invocation commitment exists.

This non-competing successor therefore requires two phase-separated externally frozen controller commitments:
1) a pre-call launch descriptor binding cell/node/membership/process/candidate/input/source;
2) a post-call executor observation binding that exact launch descriptor to the exact
   source-bound model-call identity, output identity, and ABI receipt digest.

The commitments are not self-authenticating. An admitted executor must independently attest
and freeze them at the appropriate times. This source-only layer only proves deterministic
equality and fail-closed composition.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_TWO_PHASE_AUTHORITY/v1"
CALL_GATE_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1"
CALL_IDENTITY_SCHEMA = "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1"
LAUNCH_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_LAUNCH_DESCRIPTOR/v1"
EXECUTOR_OBSERVATION_SCHEMA = "CLAY_TRIGGER2_MODEL_CALL_EXECUTOR_OBSERVATION/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
COHORT_SCHEMA = "CLAY_TRIGGER2_AUTHORITY_ENVELOPE_COHORT/v1"

HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GateError(RuntimeError):
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
    _require(isinstance(value, str) and bool(HEX64.fullmatch(value)), code)
    return value


def validate_call_gate_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _require(receipt.get("schema") == CALL_GATE_SCHEMA, "CALL_GATE_SCHEMA_MISMATCH")
    _require(receipt.get("pass") is True, "CALL_GATE_NOT_PASS")
    _require(
        receipt.get("status") == "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "CALL_GATE_STATUS_INVALID",
    )
    source_bound = _mapping(receipt.get("source_bound_envelope"), "SOURCE_BOUND_ENVELOPE_REQUIRED")
    _require(
        source_bound.get("schema") == CALL_IDENTITY_SCHEMA,
        "SOURCE_BOUND_CALL_SCHEMA_MISMATCH",
    )
    observed_call_id = canonical_sha256(dict(source_bound))
    claimed_call_id = _hex64(
        receipt.get("source_bound_model_call_identity_sha256"),
        "SOURCE_BOUND_CALL_ID_INVALID",
    )
    _require(observed_call_id == claimed_call_id, "SOURCE_BOUND_CALL_ID_RECOMPUTE_MISMATCH")

    output_id = _hex64(receipt.get("model_output_identity_sha256"), "MODEL_OUTPUT_ID_INVALID")
    _require(
        source_bound.get("model_output_identity_sha256") == output_id,
        "CALL_OUTPUT_ID_MISMATCH",
    )
    abi_receipt_id = _hex64(receipt.get("abi_v2_receipt_sha256"), "ABI_RECEIPT_ID_INVALID")
    _require(
        source_bound.get("abi_v2_receipt_sha256") == abi_receipt_id,
        "CALL_ABI_RECEIPT_ID_MISMATCH",
    )
    source = _mapping(receipt.get("source_identity"), "SOURCE_IDENTITY_REQUIRED")
    source_id = _hex64(source.get("source_identity_sha256"), "SOURCE_IDENTITY_ID_INVALID")
    _require(
        source_bound.get("source_identity_sha256") == source_id,
        "CALL_SOURCE_IDENTITY_MISMATCH",
    )
    candidate_id = source_bound.get("candidate_id")
    rendered_id = _hex64(source_bound.get("rendered_utf8_sha256"), "RENDERED_INPUT_ID_INVALID")
    _require(isinstance(candidate_id, str) and candidate_id, "CALL_CANDIDATE_ID_REQUIRED")
    return {
        "source_bound_model_call_identity_sha256": claimed_call_id,
        "model_output_identity_sha256": output_id,
        "abi_v2_receipt_sha256": abi_receipt_id,
        "source_identity_sha256": source_id,
        "candidate_id": candidate_id,
        "rendered_utf8_sha256": rendered_id,
        "call_gate_receipt_sha256": canonical_sha256(dict(receipt)),
    }


def validate_launch_descriptor(
    launch: Mapping[str, Any], *, expected_launch_descriptor_sha256: str
) -> dict[str, Any]:
    _hex64(expected_launch_descriptor_sha256, "EXPECTED_LAUNCH_DESCRIPTOR_SHA256_INVALID")
    _require(launch.get("schema") == LAUNCH_SCHEMA, "LAUNCH_SCHEMA_MISMATCH")
    for field in ("cohort_plan_id", "grid_cell_id", "node_id", "node_admission_id", "candidate_id"):
        _require(isinstance(launch.get(field), str) and launch.get(field), f"LAUNCH_{field.upper()}_REQUIRED")
    for field in ("node_admission_revision", "runtime_generation", "controller_observed_pid"):
        _require(isinstance(launch.get(field), int) and launch.get(field) >= 0, f"LAUNCH_{field.upper()}_INVALID")
    _hex64(launch.get("rendered_utf8_sha256"), "LAUNCH_RENDERED_INPUT_ID_INVALID")
    _hex64(launch.get("source_identity_sha256"), "LAUNCH_SOURCE_IDENTITY_INVALID")
    observed = canonical_sha256(dict(launch))
    _require(observed == expected_launch_descriptor_sha256, "LAUNCH_DESCRIPTOR_COMMITMENT_MISMATCH")
    return {"launch_descriptor_sha256": observed, **dict(launch)}


def validate_executor_observation(
    observation: Mapping[str, Any],
    *,
    expected_executor_observation_sha256: str,
    launch_descriptor_sha256: str,
    call: Mapping[str, Any],
) -> dict[str, Any]:
    _hex64(expected_executor_observation_sha256, "EXPECTED_EXECUTOR_OBSERVATION_SHA256_INVALID")
    _require(
        observation.get("schema") == EXECUTOR_OBSERVATION_SCHEMA,
        "EXECUTOR_OBSERVATION_SCHEMA_MISMATCH",
    )
    _require(
        observation.get("launch_descriptor_sha256") == launch_descriptor_sha256,
        "EXECUTOR_OBSERVATION_LAUNCH_MISMATCH",
    )
    _require(
        observation.get("source_bound_model_call_identity_sha256")
        == call["source_bound_model_call_identity_sha256"],
        "EXECUTOR_OBSERVATION_CALL_MISMATCH",
    )
    _require(
        observation.get("model_output_identity_sha256") == call["model_output_identity_sha256"],
        "EXECUTOR_OBSERVATION_OUTPUT_MISMATCH",
    )
    _require(
        observation.get("abi_v2_receipt_sha256") == call["abi_v2_receipt_sha256"],
        "EXECUTOR_OBSERVATION_ABI_RECEIPT_MISMATCH",
    )
    _require(
        isinstance(observation.get("executor_observed_pid"), int)
        and observation.get("executor_observed_pid") >= 0,
        "EXECUTOR_OBSERVED_PID_INVALID",
    )
    observed = canonical_sha256(dict(observation))
    _require(
        observed == expected_executor_observation_sha256,
        "EXECUTOR_OBSERVATION_COMMITMENT_MISMATCH",
    )
    return {"executor_observation_sha256": observed, **dict(observation)}


def validate_node_result(packet: Mapping[str, Any]) -> dict[str, Any]:
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "NODE_RESULT_SCHEMA_MISMATCH")
    _require(packet.get("source_kind") == "ORDINARY_NODE", "NODE_RESULT_SOURCE_KIND_INVALID")
    _require(isinstance(packet.get("source_node_id"), str) and packet.get("source_node_id"), "NODE_RESULT_NODE_ID_REQUIRED")
    payload = _mapping(packet.get("payload"), "NODE_RESULT_PAYLOAD_REQUIRED")
    _require(isinstance(payload.get("process_pid"), int) and payload.get("process_pid") >= 0, "NODE_RESULT_PROCESS_PID_INVALID")

    forbidden = {
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "source_identity_sha256",
        "node_admission_id",
        "node_admission_revision",
        "grid_cell_id",
        "launch_descriptor_sha256",
        "executor_observation_sha256",
    }
    _require(not (forbidden & set(packet.keys())), "MODEL_OR_CHILD_MUST_NOT_MINT_AUTHORITY_FIELDS")
    _require(not (forbidden & set(payload.keys())), "MODEL_OR_CHILD_PAYLOAD_MUST_NOT_MINT_AUTHORITY_FIELDS")

    core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    observed = canonical_sha256(core)
    _require(packet.get("packet_digest") == observed, "NODE_RESULT_PACKET_DIGEST_MISMATCH")
    return {
        "raw_node_result_packet_digest": observed,
        "raw_source_node_id": packet["source_node_id"],
        "raw_process_pid": payload["process_pid"],
        "raw_generation": packet.get("generation"),
        "raw_state_epoch": packet.get("state_epoch"),
        "raw_state_digest": packet.get("state_digest"),
    }


def build_authority_envelope(
    *,
    packet: Mapping[str, Any],
    call_gate_receipt: Mapping[str, Any],
    launch_descriptor: Mapping[str, Any],
    expected_launch_descriptor_sha256: str,
    executor_observation: Mapping[str, Any],
    expected_executor_observation_sha256: str,
) -> dict[str, Any]:
    raw = validate_node_result(packet)
    call = validate_call_gate_receipt(call_gate_receipt)
    launch = validate_launch_descriptor(
        launch_descriptor,
        expected_launch_descriptor_sha256=expected_launch_descriptor_sha256,
    )

    _require(launch["node_id"] == raw["raw_source_node_id"], "LAUNCH_NODE_PACKET_MISMATCH")
    _require(launch["controller_observed_pid"] == raw["raw_process_pid"], "LAUNCH_PID_PACKET_MISMATCH")
    _require(launch["candidate_id"] == call["candidate_id"], "LAUNCH_CANDIDATE_CALL_MISMATCH")
    _require(
        launch["rendered_utf8_sha256"] == call["rendered_utf8_sha256"],
        "LAUNCH_INPUT_CALL_MISMATCH",
    )
    _require(
        launch["source_identity_sha256"] == call["source_identity_sha256"],
        "LAUNCH_SOURCE_CALL_MISMATCH",
    )

    observation = validate_executor_observation(
        executor_observation,
        expected_executor_observation_sha256=expected_executor_observation_sha256,
        launch_descriptor_sha256=launch["launch_descriptor_sha256"],
        call=call,
    )
    _require(
        observation["executor_observed_pid"] == launch["controller_observed_pid"],
        "EXECUTOR_OBSERVATION_PID_LAUNCH_MISMATCH",
    )

    body = {
        "schema": SCHEMA,
        "raw_node_result_packet_digest": raw["raw_node_result_packet_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "abi_v2_receipt_sha256": call["abi_v2_receipt_sha256"],
        "source_identity_sha256": call["source_identity_sha256"],
        "launch_descriptor_sha256": launch["launch_descriptor_sha256"],
        "executor_observation_sha256": observation["executor_observation_sha256"],
        "cohort_plan_id": launch["cohort_plan_id"],
        "grid_cell_id": launch["grid_cell_id"],
        "controller_observed_node_id": launch["node_id"],
        "controller_observed_pid": launch["controller_observed_pid"],
        "source_node_admission_id": launch["node_admission_id"],
        "source_node_admission_revision": launch["node_admission_revision"],
        "source_runtime_generation": launch["runtime_generation"],
        "raw_generation": raw["raw_generation"],
        "raw_state_epoch": raw["raw_state_epoch"],
        "raw_state_digest": raw["raw_state_digest"],
    }
    return {
        **body,
        "authority_envelope_sha256": canonical_sha256(body),
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": {
            "model_call_runtime_credit": 0,
            "physical_grid10_runtime_credit": 0,
            "checkpoint_selection_credit": 0,
            "jspace_model_credit": 0,
            "training_credit": 0,
            "whole_hcu_runtime_credit": 0,
            "whole_entityos_runtime_credit": 0,
        },
    }


def validate_authority_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    _require(envelope.get("schema") == SCHEMA, "AUTHORITY_ENVELOPE_SCHEMA_MISMATCH")
    body_keys = (
        "schema",
        "raw_node_result_packet_digest",
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "abi_v2_receipt_sha256",
        "source_identity_sha256",
        "launch_descriptor_sha256",
        "executor_observation_sha256",
        "cohort_plan_id",
        "grid_cell_id",
        "controller_observed_node_id",
        "controller_observed_pid",
        "source_node_admission_id",
        "source_node_admission_revision",
        "source_runtime_generation",
        "raw_generation",
        "raw_state_epoch",
        "raw_state_digest",
    )
    for field in (
        "raw_node_result_packet_digest",
        "source_bound_model_call_identity_sha256",
        "model_output_identity_sha256",
        "abi_v2_receipt_sha256",
        "source_identity_sha256",
        "launch_descriptor_sha256",
        "executor_observation_sha256",
    ):
        _hex64(envelope.get(field), f"AUTHORITY_{field.upper()}_INVALID")
    body = {key: envelope.get(key) for key in body_keys}
    observed = canonical_sha256(body)
    _require(
        envelope.get("authority_envelope_sha256") == observed,
        "AUTHORITY_ENVELOPE_DIGEST_MISMATCH",
    )
    _require(envelope.get("model_generated") is False, "AUTHORITY_ENVELOPE_MODEL_GENERATED_FORBIDDEN")
    _require(envelope.get("canonical_truth") is False, "AUTHORITY_ENVELOPE_CANONICAL_TRUTH_FORBIDDEN")
    _require(envelope.get("effect_authority") is False, "AUTHORITY_ENVELOPE_EFFECT_AUTHORITY_FORBIDDEN")
    return dict(envelope)


def derive_authority_cohort_id(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    expected_member_count: int = 10,
) -> str:
    _require(len(envelopes) == expected_member_count, "AUTHORITY_COHORT_MEMBER_COUNT_INVALID")
    checked = [validate_authority_envelope(item) for item in envelopes]
    plans = {item["cohort_plan_id"] for item in checked}
    _require(len(plans) == 1, "AUTHORITY_COHORT_PLAN_MISMATCH")
    cells = [item["grid_cell_id"] for item in checked]
    nodes = [item["controller_observed_node_id"] for item in checked]
    pids = [item["controller_observed_pid"] for item in checked]
    launches = [item["launch_descriptor_sha256"] for item in checked]
    observations = [item["executor_observation_sha256"] for item in checked]
    raw_packets = [item["raw_node_result_packet_digest"] for item in checked]
    for values, code in (
        (cells, "AUTHORITY_COHORT_CELL_DUPLICATE"),
        (nodes, "AUTHORITY_COHORT_NODE_DUPLICATE"),
        (pids, "AUTHORITY_COHORT_PID_DUPLICATE"),
        (launches, "AUTHORITY_COHORT_LAUNCH_DUPLICATE"),
        (observations, "AUTHORITY_COHORT_EXECUTOR_OBSERVATION_DUPLICATE"),
        (raw_packets, "AUTHORITY_COHORT_RAW_PACKET_DUPLICATE"),
    ):
        _require(len(set(values)) == expected_member_count, code)

    ordered = sorted(
        (
            {
                "grid_cell_id": item["grid_cell_id"],
                "node_id": item["controller_observed_node_id"],
                "authority_envelope_sha256": item["authority_envelope_sha256"],
            }
            for item in checked
        ),
        key=lambda row: (row["grid_cell_id"], row["node_id"]),
    )
    return canonical_sha256(
        {
            "schema": COHORT_SCHEMA,
            "cohort_plan_id": next(iter(plans)),
            "member_count": expected_member_count,
            "members": ordered,
        }
    )
