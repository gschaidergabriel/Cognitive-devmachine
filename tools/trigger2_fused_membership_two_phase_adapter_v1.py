#!/usr/bin/env python3
"""Source-only adapter from proof-carrying GRID10 membership envelopes to Trigger-2 two-phase invocation authority.

This module composes two existing authorities instead of replacing either one:

* ``PROOF_CARRYING_NODE_RESULT/v1`` remains the fused GRID10 membership/process/snapshot
  envelope consumed by the existing atomic coordinator.
* ``CLAY_TRIGGER2_NODE_RESULT_MODEL_CALL_TWO_PHASE_AUTHORITY/v1`` remains the retained
  phase-separated invocation provenance around the immutable NODE_RESULT packet.

The adapter adds one controller-owned authority extension to the proof envelope and reseals
its existing ``envelope_digest`` with the same canonical JSON SHA-256 function used by the
fused coordinator. The existing fused cohort id therefore commits to the extension through
its envelope digest; this module deliberately does NOT mint a second coordinator cohort id.

Physical evidence admission is deliberately split from deterministic source-fixture
composition. ``atomic_fused_two_phase_commit`` is the physical front door and rejects raw
caller-supplied proof mappings. It reuses the retained V70 ``PhysicalCohortWitness``
capability and requires a witness-aware fabric commit method. The current legacy
``FusedFabric.atomic_fused_cohort_commit(proof=dict)`` is not accepted through that front
door. ``atomic_fused_two_phase_source_fixture_commit`` is the explicit zero-credit
compatibility path for deterministic persistence/replay tests and reuses the retained
``SOURCE_FIXTURE_ONLY`` receipt type.

No provider/model/physical GRID10/training/effect execution occurs here. A later admitted
runtime must still attest that launch commitment happened before execution and executor
observation after it. Source/component PASS grants zero runtime or promotion credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Mapping, Sequence

try:
    from tools.trigger2_node_result_model_call_two_phase_authority_v1 import (
        GateError as TwoPhaseGateError,
        derive_authority_cohort_id,
        validate_authority_envelope,
        validate_node_result,
    )
    from tools.trigger2_physical_witness_capability_v1 import (
        PhysicalWitnessError,
        require_physical_witness,
        source_fixture_receipt,
    )
except ModuleNotFoundError:  # direct script/tool execution compatibility
    from trigger2_node_result_model_call_two_phase_authority_v1 import (
        GateError as TwoPhaseGateError,
        derive_authority_cohort_id,
        validate_authority_envelope,
        validate_node_result,
    )
    from trigger2_physical_witness_capability_v1 import (
        PhysicalWitnessError,
        require_physical_witness,
        source_fixture_receipt,
    )

SCHEMA = "CLAY_TRIGGER2_FUSED_MEMBERSHIP_TWO_PHASE_ADAPTER/v1"
PROOF_ENVELOPE_SCHEMA = "PROOF_CARRYING_NODE_RESULT/v1"
EXTENSIONS_SCHEMA = "CLAY_TRIGGER2_PROOF_ENVELOPE_AUTHORITY_EXTENSIONS/v1"
N = 10


class AdapterError(RuntimeError):
    pass


def cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dg(value: Any) -> str:
    return sha256(cj(value).encode()).hexdigest()


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise AdapterError(code)


def _mapping(value: Any, code: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), code)
    return value


def _zero_credit_boundary() -> dict[str, int]:
    return {
        "model_call_runtime_credit": 0,
        "physical_grid10_runtime_credit": 0,
        "checkpoint_selection_credit": 0,
        "jspace_model_credit": 0,
        "training_credit": 0,
        "whole_hcu_runtime_credit": 0,
        "whole_entityos_runtime_credit": 0,
    }


def validate_proof_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the structural membership/process envelope without mutating its packet."""
    _require(envelope.get("schema") == PROOF_ENVELOPE_SCHEMA, "PROOF_ENVELOPE_SCHEMA_INVALID")
    packet = _mapping(envelope.get("node_result"), "PROOF_ENVELOPE_NODE_RESULT_REQUIRED")
    packet_digest = packet.get("packet_digest")
    _require(isinstance(packet_digest, str) and packet_digest, "NODE_RESULT_PACKET_DIGEST_REQUIRED")
    _require(envelope.get("node_result_digest") == packet_digest, "PROOF_ENVELOPE_PACKET_REFERENCE_MISMATCH")
    _require(packet.get("s1_write_intent") is False, "NODE_RESULT_SELF_WRITE_INTENT_REJECTED")
    try:
        raw = validate_node_result(packet)
    except TwoPhaseGateError as exc:
        raise AdapterError(f"NODE_RESULT_TWO_PHASE_VALIDATION_FAILED:{exc}") from exc
    _require(
        packet.get("producer_pid") == raw["raw_process_pid"],
        "NODE_RESULT_PRODUCER_PID_PAYLOAD_MISMATCH",
    )

    core = {key: envelope[key] for key in envelope if key != "envelope_digest"}
    _require(envelope.get("envelope_digest") == dg(core), "PROOF_ENVELOPE_DIGEST_MISMATCH")

    membership_id = envelope.get("source_membership_id")
    _require(isinstance(membership_id, str) and membership_id, "SOURCE_MEMBERSHIP_ID_REQUIRED")
    receipt = _mapping(envelope.get("membership_receipt"), "MEMBERSHIP_RECEIPT_REQUIRED")
    _require(receipt.get("membership_id") == membership_id, "MEMBERSHIP_RECEIPT_ID_MISMATCH")
    _require(receipt.get("node_id") == raw["raw_source_node_id"], "MEMBERSHIP_RECEIPT_NODE_MISMATCH")
    _require(receipt.get("valid") == 1, "MEMBERSHIP_RECEIPT_NOT_VALID")
    _require(receipt.get("healthy") == 1, "MEMBERSHIP_RECEIPT_NOT_HEALTHY")
    serial = receipt.get("serial")
    _require(isinstance(serial, int) and serial > 0, "MEMBERSHIP_RECEIPT_SERIAL_INVALID")
    membership_generation = receipt.get("generation")
    _require(
        isinstance(membership_generation, int) and membership_generation >= 0,
        "MEMBERSHIP_RECEIPT_GENERATION_INVALID",
    )
    _require(
        membership_generation == raw["raw_generation"],
        "MEMBERSHIP_RECEIPT_PACKET_GENERATION_MISMATCH",
    )
    producer_pid = envelope.get("producer_pid")
    _require(producer_pid == raw["raw_process_pid"], "PROOF_ENVELOPE_PRODUCER_PID_MISMATCH")
    return {
        "node_result_packet_digest": raw["raw_node_result_packet_digest"],
        "source_node_id": raw["raw_source_node_id"],
        "producer_pid": raw["raw_process_pid"],
        "generation": raw["raw_generation"],
        "state_epoch": raw["raw_state_epoch"],
        "state_digest": raw["raw_state_digest"],
        "source_membership_id": membership_id,
        "source_membership_serial": serial,
        "proof_envelope_digest": envelope["envelope_digest"],
    }


def _cross_validate_authority(
    proof: Mapping[str, Any],
    phase: Mapping[str, Any],
) -> None:
    _require(
        phase["raw_node_result_packet_digest"] == proof["node_result_packet_digest"],
        "TWO_PHASE_RAW_PACKET_BINDING_MISMATCH",
    )
    _require(
        phase["controller_observed_node_id"] == proof["source_node_id"],
        "TWO_PHASE_NODE_MEMBERSHIP_BINDING_MISMATCH",
    )
    _require(
        phase["controller_observed_pid"] == proof["producer_pid"],
        "TWO_PHASE_PROCESS_MEMBERSHIP_BINDING_MISMATCH",
    )
    _require(
        phase["source_node_admission_id"] == proof["source_membership_id"],
        "TWO_PHASE_ADMISSION_MEMBERSHIP_ID_MISMATCH",
    )
    _require(
        phase["source_node_admission_revision"] == proof["source_membership_serial"],
        "TWO_PHASE_ADMISSION_MEMBERSHIP_REVISION_MISMATCH",
    )
    _require(
        phase["source_runtime_generation"] == proof["generation"],
        "TWO_PHASE_RUNTIME_MEMBERSHIP_GENERATION_MISMATCH",
    )
    _require(phase["raw_generation"] == proof["generation"], "TWO_PHASE_RAW_GENERATION_MISMATCH")
    _require(phase["raw_state_epoch"] == proof["state_epoch"], "TWO_PHASE_RAW_STATE_EPOCH_MISMATCH")
    _require(phase["raw_state_digest"] == proof["state_digest"], "TWO_PHASE_RAW_STATE_DIGEST_MISMATCH")


def attach_two_phase_authority(
    proof_envelope: Mapping[str, Any],
    two_phase_authority: Mapping[str, Any],
) -> dict[str, Any]:
    """Attach one retained two-phase authority extension and reseal the existing proof envelope."""
    _require("authority_extensions" not in proof_envelope, "PROOF_ENVELOPE_ALREADY_EXTENDED")
    proof = validate_proof_envelope(proof_envelope)
    try:
        phase = validate_authority_envelope(two_phase_authority)
    except TwoPhaseGateError as exc:
        raise AdapterError(f"TWO_PHASE_AUTHORITY_INVALID:{exc}") from exc
    _cross_validate_authority(proof, phase)

    upgraded = deepcopy(dict(proof_envelope))
    upgraded.pop("envelope_digest", None)
    upgraded["authority_extensions"] = {
        "schema": EXTENSIONS_SCHEMA,
        "two_phase_model_call_authority": deepcopy(phase),
    }
    upgraded["envelope_digest"] = dg(upgraded)
    return upgraded


def validate_two_phase_proof_envelope(envelope: Mapping[str, Any]) -> dict[str, Any]:
    proof = validate_proof_envelope(envelope)
    extensions = _mapping(envelope.get("authority_extensions"), "TWO_PHASE_AUTHORITY_EXTENSIONS_REQUIRED")
    _require(extensions.get("schema") == EXTENSIONS_SCHEMA, "TWO_PHASE_AUTHORITY_EXTENSIONS_SCHEMA_INVALID")
    _require(
        set(extensions.keys()) == {"schema", "two_phase_model_call_authority"},
        "TWO_PHASE_AUTHORITY_EXTENSIONS_AMBIGUOUS",
    )
    phase_raw = _mapping(
        extensions.get("two_phase_model_call_authority"),
        "TWO_PHASE_AUTHORITY_EXTENSION_REQUIRED",
    )
    try:
        phase = validate_authority_envelope(phase_raw)
    except TwoPhaseGateError as exc:
        raise AdapterError(f"TWO_PHASE_AUTHORITY_INVALID:{exc}") from exc
    _cross_validate_authority(proof, phase)
    return {
        **proof,
        "two_phase_authority_envelope_sha256": phase["authority_envelope_sha256"],
        "source_bound_model_call_identity_sha256": phase["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": phase["model_output_identity_sha256"],
        "launch_descriptor_sha256": phase["launch_descriptor_sha256"],
        "executor_observation_sha256": phase["executor_observation_sha256"],
        "cohort_plan_id": phase["cohort_plan_id"],
        "grid_cell_id": phase["grid_cell_id"],
        "phase_authority": phase,
    }


def validate_two_phase_cohort(
    envelopes: Sequence[Mapping[str, Any]],
    *,
    expected_member_count: int = N,
) -> dict[str, Any]:
    _require(len(envelopes) == expected_member_count, "TWO_PHASE_COHORT_MEMBER_COUNT_INVALID")
    members = [validate_two_phase_proof_envelope(item) for item in envelopes]
    phase_id = derive_authority_cohort_id(
        [member["phase_authority"] for member in members],
        expected_member_count=expected_member_count,
    )
    proof_digests = [member["proof_envelope_digest"] for member in members]
    _require(
        len(set(proof_digests)) == expected_member_count,
        "TWO_PHASE_COHORT_PROOF_ENVELOPE_DUPLICATE",
    )
    ordered = sorted(
        [
            {
                "proof_envelope_digest": member["proof_envelope_digest"],
                "two_phase_authority_envelope_sha256": member["two_phase_authority_envelope_sha256"],
                "source_membership_id": member["source_membership_id"],
                "grid_cell_id": member["grid_cell_id"],
            }
            for member in members
        ],
        key=lambda row: (row["grid_cell_id"], row["source_membership_id"]),
    )
    validation_digest = dg(
        {
            "schema": SCHEMA,
            "member_count": expected_member_count,
            "phase_authority_cohort_validation_sha256": phase_id,
            "members": ordered,
        }
    )
    return {
        "schema": SCHEMA,
        "pass": True,
        "member_count": expected_member_count,
        "phase_authority_cohort_validation_sha256": phase_id,
        "validation_digest_sha256": validation_digest,
        "ordered_members": ordered,
        "credit_boundary": _zero_credit_boundary(),
    }


def atomic_fused_two_phase_commit(
    fabric: Any,
    *,
    envelopes: Sequence[Mapping[str, Any]],
    physical_witness: Any | None = None,
    **commit_kwargs: Any,
) -> dict[str, Any]:
    """Physical front door: validate once, then require the retained V70 witness capability."""
    frozen_envelopes = [deepcopy(envelope) for envelope in envelopes]
    validation = validate_two_phase_cohort(frozen_envelopes, expected_member_count=N)

    _require("proof" not in commit_kwargs, "RAW_PHYSICAL_COHORT_PROOF_NOT_ADMITTED")
    _require(physical_witness is not None, "PHYSICAL_COHORT_WITNESS_REQUIRED")
    try:
        witness = require_physical_witness(physical_witness)
    except PhysicalWitnessError as exc:
        raise AdapterError(f"PHYSICAL_COHORT_WITNESS_INVALID:{exc}") from exc
    witness_commit = getattr(fabric, "atomic_fused_cohort_witness_commit", None)
    _require(callable(witness_commit), "PHYSICAL_COHORT_WITNESS_COMMIT_UNAVAILABLE")

    receipt = witness_commit(
        envelopes=frozen_envelopes,
        physical_witness=witness,
        **commit_kwargs,
    )
    return {
        "fused_coordinator_receipt": receipt,
        "two_phase_validation": validation,
        "physical_witness_admitted": True,
        "adapter_created_second_coordinator_cohort_id": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": _zero_credit_boundary(),
    }


def atomic_fused_two_phase_source_fixture_commit(
    fabric: Any,
    *,
    envelopes: Sequence[Mapping[str, Any]],
    proof: Mapping[str, Any],
    **commit_kwargs: Any,
) -> dict[str, Any]:
    """Explicit zero-credit compatibility path for deterministic persistence/replay tests."""
    _require(isinstance(proof, Mapping), "SOURCE_FIXTURE_PROOF_REQUIRED")
    _require(
        proof.get("synthetic_source_fixture_only") is True,
        "SOURCE_FIXTURE_EXPLICIT_MARKER_REQUIRED",
    )
    frozen_envelopes = [deepcopy(envelope) for envelope in envelopes]
    frozen_proof = deepcopy(dict(proof))
    validation = validate_two_phase_cohort(frozen_envelopes, expected_member_count=N)
    receipt = fabric.atomic_fused_cohort_commit(
        envelopes=frozen_envelopes,
        proof=frozen_proof,
        **commit_kwargs,
    )
    fixture_receipt = source_fixture_receipt(
        state_delta=int(receipt["state_delta"]),
        cohort_id=str(receipt["cohort_id"]),
    )
    return {
        "fused_coordinator_receipt": receipt,
        "two_phase_validation": validation,
        "source_fixture_receipt": fixture_receipt,
        "physical_witness_admitted": False,
        "adapter_created_second_coordinator_cohort_id": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": _zero_credit_boundary(),
    }
