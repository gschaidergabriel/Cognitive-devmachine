from copy import deepcopy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "tools" / "trigger2_node_result_model_call_authority_envelope_v1.py"
spec = importlib.util.spec_from_file_location("lineage_gate", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def h(label: str) -> str:
    return mod.canonical_sha256({"label": label})


def packet(node="x01", pid=1234, observation="result:x01"):
    payload = {"node": node, "process_pid": pid, "task_id": "t01", "observation": observation, "useful": True}
    core = {
        "schema": "NODE_RESULT/v1",
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "scope": "GLOBAL",
        "generation": 1,
        "state_epoch": 7,
        "state_digest": h("state"),
        "producer_pid": pid,
        "consumed_state_epoch": 7,
        "consumed_state_digest": h("state"),
        "consumed_generation": 1,
        "consumed_task_digest": h("task"),
        "read_receipt_digest": h("read"),
        "payload": payload,
    }
    return {**core, "packet_digest": mod.canonical_sha256(core), "s1_write_intent": False}


def call_gate(label="a", output_label="out-a", source_label="source-a"):
    envelope = {
        "schema": "CLAY_TRIGGER2_SOURCE_BOUND_MODEL_CALL_IDENTITY/v1",
        "abi_v2_receipt_sha256": h("receipt-" + label),
        "abi_v2_model_call_binding_sha256": h("binding-" + label),
        "model_output_identity_sha256": h(output_label),
        "source_identity_sha256": h(source_label),
        "candidate_id": "base",
        "checkpoint_manifest_sha256": h("manifest-" + label),
        "rendered_utf8_sha256": h("render-" + label),
    }
    return {
        "schema": "CLAY_TRIGGER2_MODEL_CALL_REPOSITORY_BOUND_GATE/v1",
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": mod.canonical_sha256(envelope),
        "model_output_identity_sha256": envelope["model_output_identity_sha256"],
        "source_bound_envelope": envelope,
    }


def launch(p, g, cell="cell-01"):
    core = {
        "schema": "CLAY_TRIGGER2_NODE_MODEL_CALL_LAUNCH_BINDING/v1",
        "source_node_id": p["source_node_id"],
        "grid_cell_id": cell,
        "producer_pid": p["producer_pid"],
        "expected_node_result_digest": p["packet_digest"],
        "expected_source_bound_model_call_identity_sha256": g["source_bound_model_call_identity_sha256"],
        "expected_model_output_identity_sha256": g["model_output_identity_sha256"],
    }
    return {**core, "launch_binding_digest": mod.canonical_sha256(core)}


def test_happy_path_and_verify():
    p = packet()
    g = call_gate()
    result = mod.build_authority_envelope(p, g, launch(p, g))
    env = mod.verify_authority_envelope(result)
    assert result["pass"] is True
    assert env["source_bound_model_call_identity_sha256"] == g["source_bound_model_call_identity_sha256"]
    assert env["model_output_identity_sha256"] == g["model_output_identity_sha256"]
    assert result["credit_boundary"]["training_credit"] == 0


def test_same_semantic_payload_different_call_not_interchangeable():
    p = packet()
    g1 = call_gate("a")
    g2 = call_gate("b")
    frozen = launch(p, g1)
    try:
        mod.build_authority_envelope(p, g2, frozen)
    except mod.GateError as exc:
        assert str(exc) == "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED"
    else:
        raise AssertionError("transplanted call accepted")


def test_model_output_identity_mismatch_rejected():
    p = packet()
    g = call_gate()
    bad = deepcopy(g)
    bad["model_output_identity_sha256"] = h("other-output")
    try:
        mod.build_authority_envelope(p, bad, launch(p, g))
    except mod.GateError as exc:
        assert str(exc) == "MODEL_OUTPUT_ID_ENVELOPE_MISMATCH"
    else:
        raise AssertionError("mismatched output accepted")


def test_call_node_or_cell_transplant_rejected_by_frozen_launch_binding():
    p1 = packet("x01", 1234)
    p2 = packet("x02", 2234, "result:x02")
    g = call_gate()
    frozen = launch(p1, g, "cell-01")
    try:
        mod.build_authority_envelope(p2, g, frozen)
    except mod.GateError as exc:
        assert str(exc) == "CALL_NODE_TRANSPLANT_REJECTED"
    else:
        raise AssertionError("node transplant accepted")

    bad_cell = deepcopy(frozen)
    bad_cell["grid_cell_id"] = "cell-09"
    try:
        mod.build_authority_envelope(p1, g, bad_cell)
    except mod.GateError as exc:
        assert str(exc) == "LAUNCH_BINDING_DIGEST_MISMATCH"
    else:
        raise AssertionError("cell transplant accepted")


def test_source_head_drift_requires_distinct_call_and_old_freeze_rejects_it():
    p = packet()
    old = call_gate("same", source_label="source-head-a")
    new = call_gate("same", source_label="source-head-b")
    assert old["source_bound_model_call_identity_sha256"] != new["source_bound_model_call_identity_sha256"]
    try:
        mod.build_authority_envelope(p, new, launch(p, old))
    except mod.GateError as exc:
        assert str(exc) == "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED"
    else:
        raise AssertionError("source-drifted call accepted under old freeze")


def test_raw_packet_unchanged_but_call_reference_changes_envelope_digest():
    p = packet()
    g1 = call_gate("a")
    g2 = call_gate("b")
    r1 = mod.build_authority_envelope(p, g1, launch(p, g1))
    r2 = mod.build_authority_envelope(p, g2, launch(p, g2))
    assert p["packet_digest"] == r1["authority_envelope"]["node_result_digest"] == r2["authority_envelope"]["node_result_digest"]
    assert r1["authority_envelope_digest"] != r2["authority_envelope_digest"]


def test_model_generated_authority_field_rejected():
    p = packet()
    p["source_bound_model_call_identity_sha256"] = h("forged")
    g = call_gate()
    try:
        mod.build_authority_envelope(p, g, launch(packet(), g))
    except mod.GateError as exc:
        assert str(exc).startswith("MODEL_GENERATED_AUTHORITY_FIELD_FORBIDDEN")
    else:
        raise AssertionError("model authority field accepted")


def test_envelope_tamper_rejected():
    p = packet()
    g = call_gate()
    result = mod.build_authority_envelope(p, g, launch(p, g))
    tampered = deepcopy(result)
    tampered["authority_envelope"]["grid_cell_id"] = "cell-99"
    try:
        mod.verify_authority_envelope(tampered)
    except mod.GateError as exc:
        assert str(exc) == "AUTHORITY_ENVELOPE_DIGEST_MISMATCH"
    else:
        raise AssertionError("tampered envelope accepted")
