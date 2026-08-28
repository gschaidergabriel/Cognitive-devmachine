from __future__ import annotations

from copy import deepcopy
from hashlib import sha256

import pytest

from tools.trigger2_fused_membership_two_phase_adapter_v1 import (
    AdapterError,
    PROOF_ENVELOPE_SCHEMA,
    attach_two_phase_authority,
    dg,
    validate_two_phase_cohort,
)
from tools.trigger2_node_result_model_call_two_phase_authority_v1 import (
    GateError as TwoPhaseGateError,
    SCHEMA as PHASE_SCHEMA,
    canonical_sha256,
)


def h(label: str) -> str:
    return sha256(label.encode()).hexdigest()


def proof_envelope(
    i: int,
    *,
    packet_pid: int | None = None,
    payload_pid: int | None = None,
    envelope_pid: int | None = None,
) -> dict:
    packet_pid = 8000 + i if packet_pid is None else packet_pid
    payload_pid = packet_pid if payload_pid is None else payload_pid
    envelope_pid = payload_pid if envelope_pid is None else envelope_pid
    packet = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": f"x{i:02d}",
        "scope": "GLOBAL",
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("state"),
        "producer_pid": packet_pid,
        "payload": {"process_pid": payload_pid, "value": f"obs-{i}"},
        "s1_write_intent": False,
    }
    packet_core = {
        key: packet[key]
        for key in packet
        if key not in ("packet_digest", "s1_write_intent")
    }
    packet["packet_digest"] = dg(packet_core)
    core = {
        "schema": PROOF_ENVELOPE_SCHEMA,
        "node_result_digest": packet["packet_digest"],
        "node_result": packet,
        "source_membership_id": f"member-{i:02d}",
        "membership_receipt": {
            "membership_id": f"member-{i:02d}",
            "node_id": f"x{i:02d}",
            "capability": "reason",
            "generation": 7,
            "serial": i,
            "valid": 1,
            "healthy": 1,
        },
        "producer_pid": envelope_pid,
    }
    return {**core, "envelope_digest": dg(core)}


def phase_authority(
    i: int,
    proof: dict,
    *,
    launch: str | None = None,
    observation: str | None = None,
    controller_pid: int | None = None,
    controller_node: str | None = None,
) -> dict:
    packet = proof["node_result"]
    body = {
        "schema": PHASE_SCHEMA,
        "raw_node_result_packet_digest": packet["packet_digest"],
        "source_bound_model_call_identity_sha256": h(f"call-{i}"),
        "model_output_identity_sha256": h(f"output-{i}"),
        "abi_v2_receipt_sha256": h(f"abi-{i}"),
        "source_identity_sha256": h("source"),
        "launch_descriptor_sha256": launch or h(f"launch-{i}"),
        "executor_observation_sha256": observation or h(f"executor-observation-{i}"),
        "cohort_plan_id": h("plan"),
        "grid_cell_id": f"cell-{i:02d}",
        "controller_observed_node_id": controller_node or packet["source_node_id"],
        "controller_observed_pid": (
            proof["producer_pid"] if controller_pid is None else controller_pid
        ),
        "source_node_admission_id": proof["source_membership_id"],
        "source_node_admission_revision": proof["membership_receipt"]["serial"],
        "source_runtime_generation": proof["membership_receipt"]["generation"],
        "raw_generation": packet["generation"],
        "raw_state_epoch": packet["state_epoch"],
        "raw_state_digest": packet["state_digest"],
    }
    return {
        **body,
        "authority_envelope_sha256": canonical_sha256(body),
        "model_generated": False,
        "canonical_truth": False,
        "effect_authority": False,
        "credit_boundary": {},
    }


def upgraded(i: int) -> dict:
    proof = proof_envelope(i)
    return attach_two_phase_authority(proof, phase_authority(i, proof))


def reseal_phase(phase: dict) -> dict:
    out = deepcopy(phase)
    body = {
        key: out[key]
        for key in out
        if key
        not in (
            "authority_envelope_sha256",
            "model_generated",
            "canonical_truth",
            "effect_authority",
            "credit_boundary",
        )
    }
    out["authority_envelope_sha256"] = canonical_sha256(body)
    return out


def reseal_proof(envelope: dict) -> dict:
    out = deepcopy(envelope)
    core = {key: out[key] for key in out if key != "envelope_digest"}
    out["envelope_digest"] = dg(core)
    return out


def test_packet_producer_pid_must_match_payload_process_pid_at_adapter_boundary():
    proof = proof_envelope(1, packet_pid=7001, payload_pid=8001, envelope_pid=8001)
    with pytest.raises(
        AdapterError,
        match="^NODE_RESULT_PRODUCER_PID_PAYLOAD_MISMATCH$",
    ):
        attach_two_phase_authority(proof, phase_authority(1, proof))


def test_controller_pid_and_node_transplants_are_rejected_explicitly():
    proof = proof_envelope(1)

    bad_pid = phase_authority(1, proof, controller_pid=proof["producer_pid"] + 1)
    with pytest.raises(
        AdapterError,
        match="^TWO_PHASE_PROCESS_MEMBERSHIP_BINDING_MISMATCH$",
    ):
        attach_two_phase_authority(proof, bad_pid)

    bad_node = phase_authority(1, proof, controller_node="x99")
    with pytest.raises(
        AdapterError,
        match="^TWO_PHASE_NODE_MEMBERSHIP_BINDING_MISMATCH$",
    ):
        attach_two_phase_authority(proof, bad_node)


def test_reused_launch_identity_is_rejected_at_retained_cohort_boundary():
    values = [upgraded(i) for i in range(1, 11)]
    shared_launch = values[0]["authority_extensions"]["two_phase_model_call_authority"][
        "launch_descriptor_sha256"
    ]
    phase = deepcopy(
        values[1]["authority_extensions"]["two_phase_model_call_authority"]
    )
    phase["launch_descriptor_sha256"] = shared_launch
    values[1]["authority_extensions"]["two_phase_model_call_authority"] = reseal_phase(phase)
    values[1] = reseal_proof(values[1])

    with pytest.raises(TwoPhaseGateError, match="^AUTHORITY_COHORT_LAUNCH_DUPLICATE$"):
        validate_two_phase_cohort(values)


def test_reused_executor_observation_is_rejected_at_retained_cohort_boundary():
    values = [upgraded(i) for i in range(1, 11)]
    shared_observation = values[0]["authority_extensions"]["two_phase_model_call_authority"][
        "executor_observation_sha256"
    ]
    phase = deepcopy(
        values[1]["authority_extensions"]["two_phase_model_call_authority"]
    )
    phase["executor_observation_sha256"] = shared_observation
    values[1]["authority_extensions"]["two_phase_model_call_authority"] = reseal_phase(phase)
    values[1] = reseal_proof(values[1])

    with pytest.raises(
        TwoPhaseGateError,
        match="^AUTHORITY_COHORT_EXECUTOR_OBSERVATION_DUPLICATE$",
    ):
        validate_two_phase_cohort(values)
