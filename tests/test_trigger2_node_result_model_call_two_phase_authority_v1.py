from __future__ import annotations

from copy import deepcopy
import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from trigger2_node_result_model_call_two_phase_authority_v1 import (
    EXECUTOR_OBSERVATION_SCHEMA,
    GateError,
    LAUNCH_SCHEMA,
    NODE_RESULT_SCHEMA,
    CALL_GATE_SCHEMA,
    CALL_IDENTITY_SCHEMA,
    build_authority_envelope,
    canonical_sha256,
    derive_authority_cohort_id,
    validate_authority_envelope,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def call_receipt(*, n: int = 1, candidate: str = "qwen35-08b-a", rendered: str | None = None):
    rendered = rendered or h(f"rendered-{n}")
    source_id = h(f"source-{n}")
    output_id = h(f"output-{n}")
    abi_id = h(f"abi-{n}")
    source_bound = {
        "schema": CALL_IDENTITY_SCHEMA,
        "abi_v2_receipt_sha256": abi_id,
        "abi_v2_model_call_binding_sha256": h(f"binding-{n}"),
        "model_output_identity_sha256": output_id,
        "source_identity_sha256": source_id,
        "candidate_id": candidate,
        "checkpoint_manifest_sha256": h(f"checkpoint-{n}"),
        "rendered_utf8_sha256": rendered,
    }
    return {
        "schema": CALL_GATE_SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": canonical_sha256(source_bound),
        "abi_v2_receipt_sha256": abi_id,
        "abi_v2_model_call_binding_sha256": source_bound["abi_v2_model_call_binding_sha256"],
        "model_output_identity_sha256": output_id,
        "source_identity": {
            "source_identity_sha256": source_id,
            "head_sha": "a" * 40,
            "tree_sha": "b" * 40,
            "source_sha256": h(f"probe-source-{n}"),
            "source_blob_sha1": "c" * 40,
            "dirty": False,
        },
        "source_bound_envelope": source_bound,
    }


def raw_packet(*, node: str, pid: int, payload_value: str = "same-semantic"):
    packet = {
        "schema": NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "scope": "GLOBAL",
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("state"),
        "payload": {"process_pid": pid, "value": payload_value},
        "s1_write_intent": False,
    }
    core = {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}
    packet["packet_digest"] = canonical_sha256(core)
    return packet


def make_inputs(*, idx: int, packet_value: str = "same-semantic"):
    node = f"x{idx:02d}"
    cell = f"cell-{idx:02d}"
    pid = 5000 + idx
    call = call_receipt(n=idx)
    launch = {
        "schema": LAUNCH_SCHEMA,
        "cohort_plan_id": h("plan-1"),
        "grid_cell_id": cell,
        "node_id": node,
        "node_admission_id": f"member-{idx:02d}",
        "node_admission_revision": idx,
        "runtime_generation": 7,
        "controller_observed_pid": pid,
        "candidate_id": call["source_bound_envelope"]["candidate_id"],
        "rendered_utf8_sha256": call["source_bound_envelope"]["rendered_utf8_sha256"],
        "source_identity_sha256": call["source_identity"]["source_identity_sha256"],
    }
    launch_id = canonical_sha256(launch)
    obs = {
        "schema": EXECUTOR_OBSERVATION_SCHEMA,
        "launch_descriptor_sha256": launch_id,
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "abi_v2_receipt_sha256": call["abi_v2_receipt_sha256"],
        "executor_observed_pid": pid,
    }
    obs_id = canonical_sha256(obs)
    packet = raw_packet(node=node, pid=pid, payload_value=packet_value)
    return packet, call, launch, launch_id, obs, obs_id


def build(idx: int, packet_value: str = "same-semantic"):
    packet, call, launch, launch_id, obs, obs_id = make_inputs(idx=idx, packet_value=packet_value)
    return build_authority_envelope(
        packet=packet,
        call_gate_receipt=call,
        launch_descriptor=launch,
        expected_launch_descriptor_sha256=launch_id,
        executor_observation=obs,
        expected_executor_observation_sha256=obs_id,
    )


def test_positive_envelope_and_ten_member_cohort():
    env = build(1)
    assert validate_authority_envelope(env)["authority_envelope_sha256"] == env["authority_envelope_sha256"]
    cohort = [build(i) for i in range(1, 11)]
    assert len(derive_authority_cohort_id(cohort)) == 64


def test_same_semantic_payload_different_model_call_not_interchangeable():
    a = build(1, "identical")
    packet, _, launch, launch_id, _, _ = make_inputs(idx=1, packet_value="identical")
    call_b = call_receipt(n=99, candidate=launch["candidate_id"], rendered=launch["rendered_utf8_sha256"])
    launch_b = deepcopy(launch)
    launch_b["source_identity_sha256"] = call_b["source_identity"]["source_identity_sha256"]
    launch_b_id = canonical_sha256(launch_b)
    obs_b = {
        "schema": EXECUTOR_OBSERVATION_SCHEMA,
        "launch_descriptor_sha256": launch_b_id,
        "source_bound_model_call_identity_sha256": call_b["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call_b["model_output_identity_sha256"],
        "abi_v2_receipt_sha256": call_b["abi_v2_receipt_sha256"],
        "executor_observed_pid": launch_b["controller_observed_pid"],
    }
    b = build_authority_envelope(
        packet=packet,
        call_gate_receipt=call_b,
        launch_descriptor=launch_b,
        expected_launch_descriptor_sha256=launch_b_id,
        executor_observation=obs_b,
        expected_executor_observation_sha256=canonical_sha256(obs_b),
    )
    assert a["raw_node_result_packet_digest"] == b["raw_node_result_packet_digest"]
    assert a["source_bound_model_call_identity_sha256"] != b["source_bound_model_call_identity_sha256"]
    assert a["authority_envelope_sha256"] != b["authority_envelope_sha256"]


def test_model_call_reference_transplant_to_other_cell_rejected():
    packet1, call1, launch1, launch1_id, obs1, obs1_id = make_inputs(idx=1)
    _, _, launch2, launch2_id, _, _ = make_inputs(idx=2)
    transplanted_launch = deepcopy(launch2)
    try:
        build_authority_envelope(
            packet=packet1,
            call_gate_receipt=call1,
            launch_descriptor=transplanted_launch,
            expected_launch_descriptor_sha256=launch2_id,
            executor_observation=obs1,
            expected_executor_observation_sha256=obs1_id,
        )
    except GateError as exc:
        assert str(exc) in {
            "LAUNCH_NODE_PACKET_MISMATCH",
            "EXECUTOR_OBSERVATION_LAUNCH_MISMATCH",
            "LAUNCH_INPUT_CALL_MISMATCH",
            "LAUNCH_SOURCE_CALL_MISMATCH",
        }
    else:
        raise AssertionError("transplant unexpectedly accepted")


def test_model_output_identity_mismatch_rejected():
    packet, call, launch, launch_id, obs, obs_id = make_inputs(idx=1)
    bad = deepcopy(call)
    bad["model_output_identity_sha256"] = h("forged-output")
    try:
        build_authority_envelope(
            packet=packet,
            call_gate_receipt=bad,
            launch_descriptor=launch,
            expected_launch_descriptor_sha256=launch_id,
            executor_observation=obs,
            expected_executor_observation_sha256=obs_id,
        )
    except GateError as exc:
        assert str(exc) == "CALL_OUTPUT_ID_MISMATCH"
    else:
        raise AssertionError("output mismatch unexpectedly accepted")


def test_source_drift_requires_distinct_call_and_launch_commitments():
    packet, call, launch, launch_id, obs, obs_id = make_inputs(idx=1)
    changed = deepcopy(call)
    changed["source_identity"]["source_identity_sha256"] = h("new-source")
    try:
        build_authority_envelope(
            packet=packet,
            call_gate_receipt=changed,
            launch_descriptor=launch,
            expected_launch_descriptor_sha256=launch_id,
            executor_observation=obs,
            expected_executor_observation_sha256=obs_id,
        )
    except GateError as exc:
        assert str(exc) == "CALL_SOURCE_IDENTITY_MISMATCH"
    else:
        raise AssertionError("source drift unexpectedly accepted")


def test_changing_only_authority_call_reference_changes_envelope_digest():
    env = build(1)
    changed = deepcopy(env)
    changed["source_bound_model_call_identity_sha256"] = h("different-call")
    body = {k: v for k, v in changed.items() if k not in (
        "authority_envelope_sha256", "model_generated", "canonical_truth",
        "effect_authority", "credit_boundary"
    )}
    changed["authority_envelope_sha256"] = canonical_sha256(body)
    assert changed["authority_envelope_sha256"] != env["authority_envelope_sha256"]


def test_model_generated_authority_fields_rejected():
    packet, call, launch, launch_id, obs, obs_id = make_inputs(idx=1)
    packet = deepcopy(packet)
    packet["payload"]["model_output_identity_sha256"] = h("self-minted")
    core = {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}
    packet["packet_digest"] = canonical_sha256(core)
    try:
        build_authority_envelope(
            packet=packet,
            call_gate_receipt=call,
            launch_descriptor=launch,
            expected_launch_descriptor_sha256=launch_id,
            executor_observation=obs,
            expected_executor_observation_sha256=obs_id,
        )
    except GateError as exc:
        assert str(exc) == "MODEL_OR_CHILD_PAYLOAD_MUST_NOT_MINT_AUTHORITY_FIELDS"
    else:
        raise AssertionError("self-minted authority field unexpectedly accepted")


def test_invalid_member_envelope_rejects_whole_cohort():
    cohort = [build(i) for i in range(1, 11)]
    bad = deepcopy(cohort[4])
    bad["model_output_identity_sha256"] = h("tampered")
    cohort[4] = bad
    try:
        derive_authority_cohort_id(cohort)
    except GateError as exc:
        assert str(exc) == "AUTHORITY_ENVELOPE_DIGEST_MISMATCH"
    else:
        raise AssertionError("invalid cohort member unexpectedly accepted")


def test_reusing_same_call_observation_across_two_cells_is_rejected():
    cohort = [build(i) for i in range(1, 11)]
    clone = deepcopy(cohort[1])
    clone["executor_observation_sha256"] = cohort[0]["executor_observation_sha256"]
    body = {k: v for k, v in clone.items() if k not in (
        "authority_envelope_sha256", "model_generated", "canonical_truth",
        "effect_authority", "credit_boundary"
    )}
    clone["authority_envelope_sha256"] = canonical_sha256(body)
    cohort[1] = clone
    try:
        derive_authority_cohort_id(cohort)
    except GateError as exc:
        assert str(exc) == "AUTHORITY_COHORT_EXECUTOR_OBSERVATION_DUPLICATE"
    else:
        raise AssertionError("duplicated executor observation unexpectedly accepted")
