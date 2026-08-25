from __future__ import annotations

import copy
from hashlib import sha256
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_node_result_model_call_authority_envelope_v1.py"
spec = importlib.util.spec_from_file_location("gate", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def h(ch: str) -> str:
    return ch * 64


def packet(node="x01", pid=101, generation=7, epoch=11, payload_extra=None):
    payload = {"process_pid": pid, "semantic": "same-payload"}
    if payload_extra:
        payload.update(payload_extra)
    value = {
        "schema": gate.NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "scope": "GLOBAL",
        "source_node_id": node,
        "generation": generation,
        "state_epoch": epoch,
        "state_digest": h("a"),
        "payload": payload,
        "s1_write_intent": False,
    }
    core = {k: value[k] for k in value if k not in ("packet_digest", "s1_write_intent")}
    value["packet_digest"] = gate.canonical_sha256(core)
    return value


def call_receipt(seed="b"):
    source_identity_sha = sha256(("source:" + seed).encode()).hexdigest()
    output_sha = sha256(("output:" + seed).encode()).hexdigest()
    source_bound = {
        "schema": gate.CALL_IDENTITY_SCHEMA,
        "abi_v2_receipt_sha256": h("1"),
        "abi_v2_model_call_binding_sha256": h("2"),
        "model_output_identity_sha256": output_sha,
        "source_identity_sha256": source_identity_sha,
        "candidate_id": "BASE",
        "checkpoint_manifest_sha256": h("3"),
        "rendered_utf8_sha256": h("4"),
    }
    call_id = gate.canonical_sha256(source_bound)
    return {
        "schema": gate.CALL_GATE_SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": call_id,
        "model_output_identity_sha256": output_sha,
        "source_identity": {
            "source_identity_sha256": source_identity_sha,
            "head_sha": "2" * 40,
            "tree_sha": "3" * 40,
            "source_sha256": h("5"),
            "source_blob_sha1": "4" * 40,
            "dirty": False,
        },
        "source_bound_envelope": source_bound,
    }


def binding(call, node="x01", pid=101, cell="cell-01", revision=1, generation=7, plan=None):
    return {
        "schema": gate.CONTROLLER_BINDING_SCHEMA,
        "causal_event_id": "evt-001",
        "admission_id": "admit-001",
        "route_decision_identity_sha256": h("6"),
        "resolved_engine_identity_sha256": h("7"),
        "grid_plan_identity_sha256": plan or h("8"),
        "grid_cell_id": cell,
        "source_node_admission_id": f"member-{node}-{revision}",
        "source_node_admission_revision": revision,
        "source_runtime_generation": generation,
        "source_process_witness_digest": h("9"),
        "controller_observed_node_id": node,
        "controller_observed_pid": pid,
        "expected_source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "expected_model_output_identity_sha256": call["model_output_identity_sha256"],
        "expected_source_identity_sha256": call["source_identity"]["source_identity_sha256"],
    }


def gate_build(p, c, b, expected_binding_sha=None):
    return gate.build_authority_envelope(
        p,
        c,
        b,
        expected_controller_binding_sha256=expected_binding_sha or gate.canonical_sha256(b),
    )


def build(node="x01", pid=101, cell="cell-01", seed="b", revision=1, generation=7, plan=None):
    p = packet(node=node, pid=pid, generation=generation)
    c = call_receipt(seed)
    b = binding(c, node=node, pid=pid, cell=cell, revision=revision, generation=generation, plan=plan)
    return p, c, b, gate_build(p, c, b)


def assert_error(expected, fn):
    try:
        fn()
    except gate.GateError as exc:
        assert str(exc) == expected
    else:
        raise AssertionError(f"expected {expected}")


def test_happy_path_preserves_raw_packet_and_reuses_exact_call_identity():
    p, c, b, out = build()
    before = copy.deepcopy(p)
    assert out["pass"] is True
    assert p == before
    assert out["raw_packet_unchanged"] is True
    assert out["source_bound_model_call_identity_sha256"] == c["source_bound_model_call_identity_sha256"]
    assert out["node_result_authority_envelope"]["grid_cell_id"] == b["grid_cell_id"]
    assert out["credit_boundary"]["training_credit"] == 0


def test_same_semantic_payload_different_model_call_is_not_interchangeable():
    p = packet()
    c1 = call_receipt("b")
    c2 = call_receipt("d")
    b1 = binding(c1)
    b2 = binding(c2)
    o1 = gate_build(p, c1, b1)
    o2 = gate_build(p, c2, b2)
    assert o1["raw_packet_digest"] == o2["raw_packet_digest"]
    assert o1["source_bound_model_call_identity_sha256"] != o2["source_bound_model_call_identity_sha256"]
    assert o1["node_result_authority_envelope_sha256"] != o2["node_result_authority_envelope_sha256"]


def test_call_reference_transplant_rejected_against_frozen_controller_binding():
    p = packet()
    c1 = call_receipt("b")
    c2 = call_receipt("d")
    b = binding(c1)
    assert_error("MODEL_CALL_REFERENCE_TRANSPLANT", lambda: gate_build(p, c2, b))


def test_model_output_identity_mismatch_rejected():
    p = packet()
    c = call_receipt("b")
    b = binding(c)
    b["expected_model_output_identity_sha256"] = h("f")
    assert_error("MODEL_OUTPUT_IDENTITY_MISMATCH_WITH_REFERENCED_CALL", lambda: gate_build(p, c, b))


def test_node_transplant_rejected():
    p = packet(node="x01")
    c = call_receipt("b")
    b = binding(c, node="x02")
    assert_error("MODEL_CALL_REFERENCE_TRANSPLANTED_TO_DIFFERENT_NODE", lambda: gate_build(p, c, b))


def test_process_transplant_rejected():
    p = packet(pid=101)
    c = call_receipt("b")
    b = binding(c, pid=202)
    assert_error("MODEL_CALL_REFERENCE_TRANSPLANTED_TO_DIFFERENT_PROCESS", lambda: gate_build(p, c, b))


def test_source_identity_transplant_rejected():
    p = packet()
    c = call_receipt("b")
    b = binding(c)
    b["expected_source_identity_sha256"] = h("f")
    assert_error("SOURCE_IDENTITY_REFERENCE_TRANSPLANT", lambda: gate_build(p, c, b))


def test_raw_packet_cannot_self_mint_authority_fields():
    p = packet()
    p["grid_cell_id"] = "cell-01"
    core = {k: p[k] for k in p if k not in ("packet_digest", "s1_write_intent")}
    p["packet_digest"] = gate.canonical_sha256(core)
    c = call_receipt("b")
    b = binding(c)
    assert_error("RAW_PACKET_AUTHORITY_FIELD_FORBIDDEN", lambda: gate_build(p, c, b))


def test_raw_packet_tamper_rejected_even_with_unchanged_claimed_digest():
    p = packet()
    c = call_receipt("b")
    b = binding(c)
    p["payload"]["semantic"] = "tampered"
    assert_error("NODE_RESULT_PACKET_DIGEST_MISMATCH", lambda: gate_build(p, c, b))


def test_controller_cell_transplant_rejected_against_frozen_binding_commitment():
    p = packet()
    c = call_receipt("b")
    b1 = binding(c, cell="cell-01")
    frozen = gate.canonical_sha256(b1)
    b2 = copy.deepcopy(b1)
    b2["grid_cell_id"] = "cell-02"
    assert_error(
        "CONTROLLER_BINDING_COMMITMENT_MISMATCH",
        lambda: gate_build(p, c, b2, expected_binding_sha=frozen),
    )


def test_authority_envelope_digest_changes_if_cell_changes():
    p = packet()
    c = call_receipt("b")
    o1 = gate_build(p, c, binding(c, cell="cell-01"))
    o2 = gate_build(p, c, binding(c, cell="cell-02"))
    assert o1["node_result_authority_envelope_sha256"] != o2["node_result_authority_envelope_sha256"]


def test_cohort_requires_unique_call_packet_node_pid_cell_and_membership_identity():
    results = []
    for i in range(10):
        node = f"x{i+1:02d}"
        pid = 1000 + i
        cell = f"cell-{i+1:02d}"
        p = packet(node=node, pid=pid)
        c = call_receipt(chr(ord("b") + i))
        b = binding(c, node=node, pid=pid, cell=cell, revision=i + 1)
        b["causal_event_id"] = f"evt-{i:02d}"
        b["admission_id"] = f"admit-{i:02d}"
        results.append(gate_build(p, c, b))
    cohort = gate.validate_atomic_cohort_envelopes(results)
    assert cohort["pass"] is True
    assert cohort["member_count"] == 10

    bad = copy.deepcopy(results)
    bad[9]["node_result_authority_envelope"]["grid_cell_id"] = bad[0]["node_result_authority_envelope"]["grid_cell_id"]
    bad[9]["node_result_authority_envelope_sha256"] = gate.canonical_sha256(bad[9]["node_result_authority_envelope"])
    assert_error("COHORT_DUPLICATE_GRID_CELL_ID", lambda: gate.validate_atomic_cohort_envelopes(bad))


def test_cohort_valid_raw_packet_but_invalid_call_envelope_rejects_whole_batch():
    results = []
    for i in range(10):
        node = f"x{i+1:02d}"
        pid = 2000 + i
        p = packet(node=node, pid=pid)
        c = call_receipt(chr(ord("b") + i))
        b = binding(c, node=node, pid=pid, cell=f"cell-{i+1:02d}", revision=i + 1)
        b["causal_event_id"] = f"evt-x-{i:02d}"
        b["admission_id"] = f"admit-x-{i:02d}"
        results.append(gate_build(p, c, b))
    results[5]["node_result_authority_envelope"]["source_bound_model_call_identity_sha256"] = h("f")
    assert_error("COHORT_MEMBER_ENVELOPE_DIGEST_MISMATCH", lambda: gate.validate_atomic_cohort_envelopes(results))
