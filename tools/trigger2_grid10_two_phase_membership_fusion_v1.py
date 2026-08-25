#!/usr/bin/env python3
"""Source-only bridge from proof-carrying GRID10 membership to two-phase invocation authority.

This module does not create a second state, effect, model-call, invocation, or cohort authority.
It cross-validates two already-existing evidence surfaces before delegating any state-changing
cohort commit to the existing FusedFabric.atomic_fused_cohort_commit path:

  PROOF_CARRYING_NODE_RESULT/v1
    <-> CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_TWO_PHASE_AUTHORITY/v1

The bridge is deliberately strict about membership-incarnation provenance while preserving the
V61/V62 semantic split: source_bound_model_call_identity_sha256 is content/evidence identity,
not invocation-event identity, so equal call/output content across independently frozen
launch/observation chains remains valid.

Source/local deterministic validation only. This module executes no model/provider/VPS/training
and mints zero physical GRID10/HCU/EntityOS/J-Space/training/canonical-truth/effect credit.
"""
from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

from trigger2_node_result_model_call_two_phase_authority_v1 import (
    derive_authority_cohort_id,
    validate_authority_envelope,
)

SCHEMA = "CLAY_TRIGGER2_GRID10_TWO_PHASE_MEMBERSHIP_FUSION/v1"
PROOF_SCHEMA = "PROOF_CARRYING_NODE_RESULT/v1"
NODE_RESULT_SCHEMA = "NODE_RESULT/v1"
VALIDATION_SCHEMA = "CLAY_TRIGGER2_GRID10_TWO_PHASE_MEMBERSHIP_CROSS_BINDING/v1"


class FusionError(RuntimeError):
    pass


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FusionError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def validate_proof_carrying_member(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate immutable proof-envelope structure before cross-binding.

    Current-membership liveness is intentionally *not* inferred from this embedded receipt.
    The existing fused commit path remains responsible for checking the receipt against the
    live deterministic membership table and physical barrier/process proof.
    """
    _require(envelope.get("schema") == PROOF_SCHEMA, "PROOF_ENVELOPE_SCHEMA_INVALID")
    packet = _mapping(envelope.get("node_result"), "PROOF_NODE_RESULT_REQUIRED")
    _require(packet.get("schema") == NODE_RESULT_SCHEMA, "PROOF_NODE_RESULT_SCHEMA_INVALID")
    _require(
        envelope.get("node_result_digest") == packet.get("packet_digest"),
        "PROOF_PACKET_REFERENCE_MISMATCH",
    )

    packet_core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    _require(packet.get("packet_digest") == digest(packet_core), "PROOF_PACKET_DIGEST_MISMATCH")
    _require(packet.get("s1_write_intent") is False, "PROOF_PACKET_SELF_WRITE_FORBIDDEN")

    envelope_core = {key: envelope[key] for key in envelope if key != "envelope_digest"}
    _require(
        envelope.get("envelope_digest") == digest(envelope_core),
        "PROOF_ENVELOPE_DIGEST_MISMATCH",
    )

    membership_id = envelope.get("source_membership_id")
    _require(isinstance(membership_id, str) and membership_id, "PROOF_MEMBERSHIP_ID_REQUIRED")
    membership = _mapping(envelope.get("membership_receipt"), "PROOF_MEMBERSHIP_RECEIPT_REQUIRED")
    _require(membership.get("membership_id") == membership_id, "PROOF_MEMBERSHIP_ID_MISMATCH")

    node_id = packet.get("source_node_id")
    _require(isinstance(node_id, str) and node_id, "PROOF_NODE_ID_REQUIRED")
    _require(membership.get("node_id") == node_id, "PROOF_MEMBERSHIP_NODE_MISMATCH")

    producer_pid = packet.get("producer_pid")
    payload = _mapping(packet.get("payload"), "PROOF_NODE_RESULT_PAYLOAD_REQUIRED")
    _require(isinstance(producer_pid, int) and producer_pid >= 0, "PROOF_PRODUCER_PID_INVALID")
    _require(payload.get("process_pid") == producer_pid, "PROOF_PRODUCER_PID_PAYLOAD_MISMATCH")
    _require(envelope.get("producer_pid") == producer_pid, "PROOF_ENVELOPE_PID_MISMATCH")

    serial = membership.get("serial")
    generation = membership.get("generation")
    _require(isinstance(serial, int) and serial > 0, "PROOF_MEMBERSHIP_SERIAL_INVALID")
    _require(isinstance(generation, int) and generation >= 0, "PROOF_MEMBERSHIP_GENERATION_INVALID")
    _require(membership.get("valid") == 1, "PROOF_MEMBERSHIP_EMBEDDED_INVALID")
    _require(membership.get("healthy") == 1, "PROOF_MEMBERSHIP_EMBEDDED_UNHEALTHY")

    packet_generation = packet.get("generation")
    _require(
        isinstance(packet_generation, int) and packet_generation >= 0,
        "PROOF_PACKET_GENERATION_INVALID",
    )

    return {
        "proof_envelope_digest": envelope["envelope_digest"],
        "raw_node_result_packet_digest": packet["packet_digest"],
        "source_node_id": node_id,
        "source_membership_id": membership_id,
        "membership_serial": serial,
        "membership_generation": generation,
        "packet_generation": packet_generation,
        "producer_pid": producer_pid,
    }


def cross_validate_member_pair(
    proof_envelope: Mapping[str, Any],
    invocation_authority_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    """Cross-bind one proof-carrying membership/process member to one invocation authority."""
    proof = validate_proof_carrying_member(proof_envelope)
    invocation = validate_authority_envelope(invocation_authority_envelope)

    _require(
        invocation.get("raw_node_result_packet_digest") == proof["raw_node_result_packet_digest"],
        "FUSION_RAW_PACKET_MISMATCH",
    )
    _require(
        invocation.get("controller_observed_node_id") == proof["source_node_id"],
        "FUSION_NODE_ID_MISMATCH",
    )
    _require(
        invocation.get("controller_observed_pid") == proof["producer_pid"],
        "FUSION_PROCESS_PID_MISMATCH",
    )
    _require(
        invocation.get("source_node_admission_id") == proof["source_membership_id"],
        "FUSION_MEMBERSHIP_ADMISSION_ID_MISMATCH",
    )
    _require(
        invocation.get("source_node_admission_revision") == proof["membership_serial"],
        "FUSION_MEMBERSHIP_ADMISSION_REVISION_MISMATCH",
    )
    _require(
        invocation.get("source_runtime_generation") == proof["membership_generation"],
        "FUSION_MEMBERSHIP_GENERATION_MISMATCH",
    )
    _require(
        invocation.get("raw_generation") == proof["packet_generation"],
        "FUSION_RAW_GENERATION_MISMATCH",
    )
    _require(
        proof["membership_generation"] == proof["packet_generation"],
        "FUSION_MEMBERSHIP_PACKET_GENERATION_MISMATCH",
    )

    return {
        "source_node_id": proof["source_node_id"],
        "source_membership_id": proof["source_membership_id"],
        "membership_serial": proof["membership_serial"],
        "runtime_generation": proof["membership_generation"],
        "producer_pid": proof["producer_pid"],
        "raw_node_result_packet_digest": proof["raw_node_result_packet_digest"],
        "proof_envelope_digest": proof["proof_envelope_digest"],
        "launch_descriptor_sha256": invocation["launch_descriptor_sha256"],
        "executor_observation_sha256": invocation["executor_observation_sha256"],
        "authority_envelope_sha256": invocation["authority_envelope_sha256"],
        "source_bound_model_call_identity_sha256": invocation[
            "source_bound_model_call_identity_sha256"
        ],
        "model_output_identity_sha256": invocation["model_output_identity_sha256"],
    }


def validate_cohort_cross_binding(
    proof_envelopes: Sequence[Mapping[str, Any]],
    invocation_authority_envelopes: Sequence[Mapping[str, Any]],
    *,
    expected_member_count: int = 10,
) -> dict[str, Any]:
    """Validate one-to-one membership/incarnation/process/invocation pairing for a cohort."""
    _require(expected_member_count > 0, "FUSION_EXPECTED_MEMBER_COUNT_INVALID")
    _require(
        len(proof_envelopes) == expected_member_count,
        "FUSION_PROOF_MEMBER_COUNT_INVALID",
    )
    _require(
        len(invocation_authority_envelopes) == expected_member_count,
        "FUSION_INVOCATION_MEMBER_COUNT_INVALID",
    )

    proof_by_node: dict[str, Mapping[str, Any]] = {}
    for envelope in proof_envelopes:
        checked = validate_proof_carrying_member(envelope)
        node = checked["source_node_id"]
        _require(node not in proof_by_node, "FUSION_DUPLICATE_PROOF_NODE")
        proof_by_node[node] = envelope

    invocation_by_node: dict[str, Mapping[str, Any]] = {}
    for envelope in invocation_authority_envelopes:
        checked = validate_authority_envelope(envelope)
        node = checked.get("controller_observed_node_id")
        _require(isinstance(node, str) and node, "FUSION_INVOCATION_NODE_REQUIRED")
        _require(node not in invocation_by_node, "FUSION_DUPLICATE_INVOCATION_NODE")
        invocation_by_node[node] = envelope

    _require(set(proof_by_node) == set(invocation_by_node), "FUSION_NODE_SET_MISMATCH")

    members = [
        cross_validate_member_pair(proof_by_node[node], invocation_by_node[node])
        for node in sorted(proof_by_node)
    ]

    # Invocation uniqueness belongs to admission incarnation + launch + executor observation,
    # not to deterministic model call-content/output equality.
    for field, code in (
        ("source_membership_id", "FUSION_DUPLICATE_MEMBERSHIP_ADMISSION"),
        ("producer_pid", "FUSION_DUPLICATE_PROCESS_PID"),
        ("raw_node_result_packet_digest", "FUSION_DUPLICATE_RAW_PACKET"),
        ("proof_envelope_digest", "FUSION_DUPLICATE_PROOF_ENVELOPE"),
        ("launch_descriptor_sha256", "FUSION_DUPLICATE_LAUNCH"),
        ("executor_observation_sha256", "FUSION_DUPLICATE_EXECUTOR_OBSERVATION"),
        ("authority_envelope_sha256", "FUSION_DUPLICATE_INVOCATION_AUTHORITY"),
    ):
        _require(len({member[field] for member in members}) == expected_member_count, code)

    two_phase_cohort_id = derive_authority_cohort_id(
        list(invocation_authority_envelopes),
        expected_member_count=expected_member_count,
    )
    body = {
        "schema": VALIDATION_SCHEMA,
        "member_count": expected_member_count,
        "two_phase_authority_cohort_id": two_phase_cohort_id,
        "members": members,
    }
    return {
        **body,
        "cross_binding_validation_digest": digest(body),
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


def commit_cross_bound_cohort(
    fabric: Any,
    *,
    proof_envelopes: Sequence[Mapping[str, Any]],
    invocation_authority_envelopes: Sequence[Mapping[str, Any]],
    expected_member_count: int = 10,
    **fused_commit_kwargs: Any,
) -> dict[str, Any]:
    """Fail closed on cross-binding, then delegate to the existing fused commit path.

    This adapter deliberately owns no database/effect implementation. The only state-changing
    call is the existing ``fabric.atomic_fused_cohort_commit`` supplied by the caller.
    """
    validation = validate_cohort_cross_binding(
        proof_envelopes,
        invocation_authority_envelopes,
        expected_member_count=expected_member_count,
    )
    fused_receipt = fabric.atomic_fused_cohort_commit(
        envelopes=list(proof_envelopes),
        **fused_commit_kwargs,
    )
    return {
        "schema": SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_ONLY_CROSS_BOUND_DELEGATION",
        "cross_binding_validation_digest": validation["cross_binding_validation_digest"],
        "two_phase_authority_cohort_id": validation["two_phase_authority_cohort_id"],
        "fused_commit_receipt": fused_receipt,
        "delegated_effect_path": "EXISTING_FUSED_FABRIC_ATOMIC_COHORT_COMMIT_ONLY",
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": validation["credit_boundary"],
    }
