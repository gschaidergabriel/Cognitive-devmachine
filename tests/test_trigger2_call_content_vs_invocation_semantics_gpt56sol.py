from __future__ import annotations

from copy import deepcopy
import hashlib
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from trigger2_node_result_model_call_two_phase_authority_v1 import (
    CALL_GATE_SCHEMA,
    CALL_IDENTITY_SCHEMA,
    EXECUTOR_OBSERVATION_SCHEMA,
    GateError,
    LAUNCH_SCHEMA,
    NODE_RESULT_SCHEMA,
    build_authority_envelope,
    canonical_sha256,
    derive_authority_cohort_id,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def shared_call() -> dict:
    source_bound = {
        "schema": CALL_IDENTITY_SCHEMA,
        "abi_v2_receipt_sha256": h("abi-shared"),
        "abi_v2_model_call_binding_sha256": h("binding-shared"),
        "model_output_identity_sha256": h("output-shared"),
        "source_identity_sha256": h("source-shared"),
        "candidate_id": "qwen35-08b-a",
        "checkpoint_manifest_sha256": h("checkpoint-shared"),
        "rendered_utf8_sha256": h("rendered-shared"),
    }
    return {
        "schema": CALL_GATE_SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": canonical_sha256(source_bound),
        "abi_v2_receipt_sha256": source_bound["abi_v2_receipt_sha256"],
        "abi_v2_model_call_binding_sha256": source_bound["abi_v2_model_call_binding_sha256"],
        "model_output_identity_sha256": source_bound["model_output_identity_sha256"],
        "source_identity": {
            "source_identity_sha256": source_bound["source_identity_sha256"],
            "head_sha": "a" * 40,
            "tree_sha": "b" * 40,
            "source_sha256": h("probe-source-shared"),
            "source_blob_sha1": "c" * 40,
            "dirty": False,
        },
        "source_bound_envelope": source_bound,
    }


def raw_packet(*, node: str, pid: int) -> dict:
    packet = {
        "schema": NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "scope": "GLOBAL",
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("state"),
        "payload": {"process_pid": pid, "value": "identical-semantic-content"},
        "s1_write_intent": False,
    }
    core = {k: packet[k] for k in packet if k not in ("packet_digest", "s1_write_intent")}
    packet["packet_digest"] = canonical_sha256(core)
    return packet


def invocation(*, idx: int, call: dict) -> dict:
    node = f"x{idx:02d}"
    pid = 7000 + idx
    launch = {
        "schema": LAUNCH_SCHEMA,
        "cohort_plan_id": h("semantic-freeze-plan"),
        "grid_cell_id": f"cell-{idx:02d}",
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
    observation = {
        "schema": EXECUTOR_OBSERVATION_SCHEMA,
        "launch_descriptor_sha256": launch_id,
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "abi_v2_receipt_sha256": call["abi_v2_receipt_sha256"],
        "executor_observed_pid": pid,
    }
    observation_id = canonical_sha256(observation)
    return build_authority_envelope(
        packet=raw_packet(node=node, pid=pid),
        call_gate_receipt=call,
        launch_descriptor=launch,
        expected_launch_descriptor_sha256=launch_id,
        executor_observation=observation,
        expected_executor_observation_sha256=observation_id,
    )


def test_equal_call_content_identity_can_back_two_distinct_invocations():
    call = shared_call()
    a = invocation(idx=1, call=call)
    b = invocation(idx=2, call=call)

    assert a["source_bound_model_call_identity_sha256"] == b["source_bound_model_call_identity_sha256"]
    assert a["model_output_identity_sha256"] == b["model_output_identity_sha256"]
    assert a["launch_descriptor_sha256"] != b["launch_descriptor_sha256"]
    assert a["executor_observation_sha256"] != b["executor_observation_sha256"]
    assert a["authority_envelope_sha256"] != b["authority_envelope_sha256"]
    assert len(derive_authority_cohort_id([a, b], expected_member_count=2)) == 64


def test_replayed_single_invocation_cannot_count_as_second_member():
    call = shared_call()
    a = invocation(idx=1, call=call)
    replay = deepcopy(a)

    try:
        derive_authority_cohort_id([a, replay], expected_member_count=2)
    except GateError as exc:
        assert str(exc) in {
            "AUTHORITY_COHORT_CELL_DUPLICATE",
            "AUTHORITY_COHORT_NODE_DUPLICATE",
            "AUTHORITY_COHORT_PID_DUPLICATE",
            "AUTHORITY_COHORT_LAUNCH_DUPLICATE",
            "AUTHORITY_COHORT_EXECUTOR_OBSERVATION_DUPLICATE",
            "AUTHORITY_COHORT_RAW_PACKET_DUPLICATE",
        }
    else:
        raise AssertionError("replayed single invocation was counted as a second cohort member")
