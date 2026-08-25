from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_node_result_model_call_lineage_gate_v1.py"
spec = importlib.util.spec_from_file_location("gate", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def h(ch: str) -> str:
    return ch * 64


def h40(ch: str) -> str:
    return ch * 40


def packet(node="x01", pid=101, generation=4, observation="same-semantic"):
    payload = {
        "node": node,
        "process_pid": pid,
        "task_id": "task-1",
        "observation": observation,
        "useful": True,
    }
    core = {
        "schema": gate.NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "scope": "GLOBAL",
        "generation": generation,
        "state_epoch": 9,
        "state_digest": h("a"),
        "producer_pid": pid,
        "consumed_state_epoch": 9,
        "consumed_state_digest": h("a"),
        "consumed_generation": generation,
        "consumed_task_digest": h("b"),
        "read_receipt_digest": h("c"),
        "payload": payload,
    }
    return {**core, "packet_digest": gate.canonical_sha256(core), "s1_write_intent": False}


def node_envelope(node="x01", pid=101, membership="membership-x01-r1", observation="same-semantic"):
    p = packet(node=node, pid=pid, observation=observation)
    membership_receipt = {
        "membership_id": membership,
        "node_id": node,
        "capability": "reason",
        "generation": p["generation"],
        "serial": 1,
        "valid": 1,
        "healthy": 1,
    }
    core = {
        "schema": gate.NODE_AUTHORITY_ENVELOPE_SCHEMA,
        "node_result_digest": p["packet_digest"],
        "node_result": p,
        "source_membership_id": membership,
        "membership_receipt": membership_receipt,
        "producer_pid": pid,
    }
    return {**core, "envelope_digest": gate.canonical_sha256(core)}


def model_call_receipt(call_seed="d", output_seed="e", head="1", tree="2"):
    source_identity_sha = h("f") if head == "1" else h("9")
    source_bound = {
        "schema": gate.SOURCE_BOUND_CALL_SCHEMA,
        "abi_v2_receipt_sha256": h("3"),
        "abi_v2_model_call_binding_sha256": h(call_seed),
        "model_output_identity_sha256": h(output_seed),
        "source_identity_sha256": source_identity_sha,
        "candidate_id": "BASE",
        "checkpoint_manifest_sha256": h("4"),
        "rendered_utf8_sha256": h("5"),
    }
    call_id = gate.canonical_sha256(source_bound)
    return {
        "schema": gate.MODEL_CALL_GATE_SCHEMA,
        "pass": True,
        "status": "PASS_SOURCE_BOUND_CALL_IDENTITY_COMPONENT_ONLY",
        "source_bound_model_call_identity_sha256": call_id,
        "abi_v2_receipt_sha256": h("3"),
        "abi_v2_model_call_binding_sha256": h(call_seed),
        "model_output_identity_sha256": h(output_seed),
        "source_identity": {
            "source_identity_sha256": source_identity_sha,
            "head_sha": h40(head),
            "tree_sha": h40(tree),
            "source_sha256": h("6"),
            "source_blob_sha1": h40("7"),
            "dirty": False,
        },
        "source_bound_envelope": source_bound,
    }


def controller_lineage(env=None, call=None, *, cell="cell-01", route="8", engine="a", plan="b"):
    env = env or node_envelope()
    call = call or model_call_receipt()
    p = env["node_result"]
    return {
        "schema": gate.CONTROLLER_LINEAGE_SCHEMA,
        "causal_event_id": "event-001",
        "admission_id": "admission-001",
        "route_decision_identity_sha256": h(route),
        "resolved_engine_identity_sha256": h(engine),
        "grid_plan_identity_sha256": h(plan),
        "grid_cell_id": cell,
        "controller_observed_node_id": p["source_node_id"],
        "source_membership_id": env["source_membership_id"],
        "producer_pid": p["producer_pid"],
        "runtime_generation": p["generation"],
        "raw_node_result_packet_digest": p["packet_digest"],
        "node_authority_envelope_digest": env["envelope_digest"],
        "source_bound_model_call_identity_sha256": call["source_bound_model_call_identity_sha256"],
        "model_output_identity_sha256": call["model_output_identity_sha256"],
        "source_identity_sha256": call["source_identity"]["source_identity_sha256"],
        "source_head_sha": call["source_identity"]["head_sha"],
        "source_tree_sha": call["source_identity"]["tree_sha"],
    }


def run(env=None, call=None, lineage=None):
    env = env or node_envelope()
    call = call or model_call_receipt()
    lineage = lineage or controller_lineage(env, call)
    return gate.gate_lineage(
        env,
        call,
        lineage,
        expected_model_call_identity_sha256=call["source_bound_model_call_identity_sha256"],
        expected_controller_lineage_sha256=gate.canonical_sha256(lineage),
    )


def expect_error(code, fn):
    try:
        fn()
    except gate.GateError as exc:
        assert str(exc) == code
    else:
        raise AssertionError(f"expected {code}")


def test_happy_path_reuses_existing_call_identity_and_keeps_all_promotion_credit_zero():
    call = model_call_receipt()
    out = run(call=call)
    assert out["pass"] is True
    assert out["source_bound_model_call_identity_sha256"] == call["source_bound_model_call_identity_sha256"]
    assert len(out["lineage_authority_envelope_digest"]) == 64
    assert out["credit_boundary"]["training_credit"] == 0
    assert out["credit_boundary"]["whole_entityos_runtime_credit"] == 0


def test_same_semantic_payload_different_exact_model_call_is_not_interchangeable():
    env = node_envelope(observation="same-semantic")
    call_a = model_call_receipt(call_seed="d", output_seed="e")
    call_b = model_call_receipt(call_seed="8", output_seed="9")
    out_a = run(env=env, call=call_a, lineage=controller_lineage(env, call_a))
    out_b = run(env=env, call=call_b, lineage=controller_lineage(env, call_b))
    assert out_a["node_result_packet_digest"] == out_b["node_result_packet_digest"]
    assert out_a["source_bound_model_call_identity_sha256"] != out_b["source_bound_model_call_identity_sha256"]
    assert out_a["lineage_authority_envelope_digest"] != out_b["lineage_authority_envelope_digest"]


def test_model_call_reference_transplant_to_precommitted_node_lineage_is_rejected():
    env = node_envelope()
    call_a = model_call_receipt(call_seed="d")
    call_b = model_call_receipt(call_seed="8", output_seed="9")
    lineage = controller_lineage(env, call_a)
    expect_error(
        "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED",
        lambda: gate.gate_lineage(
            env,
            call_b,
            lineage,
            expected_model_call_identity_sha256=call_b["source_bound_model_call_identity_sha256"],
            expected_controller_lineage_sha256=gate.canonical_sha256(lineage),
        ),
    )


def test_call_cell_transplant_is_rejected_by_precommitted_controller_lineage():
    env = node_envelope(node="x01", pid=101)
    call = model_call_receipt()
    lineage = controller_lineage(env, call, cell="cell-01")
    transplanted = copy.deepcopy(lineage)
    transplanted["grid_cell_id"] = "cell-02"
    expect_error(
        "CONTROLLER_LINEAGE_COMMITMENT_MISMATCH",
        lambda: gate.gate_lineage(
            env,
            call,
            transplanted,
            expected_model_call_identity_sha256=call["source_bound_model_call_identity_sha256"],
            expected_controller_lineage_sha256=gate.canonical_sha256(lineage),
        ),
    )


def test_packet_transplant_under_unchanged_lineage_is_rejected():
    env_a = node_envelope(node="x01", pid=101, observation="A")
    env_b = node_envelope(node="x01", pid=101, observation="B")
    call = model_call_receipt()
    lineage = controller_lineage(env_a, call)
    expect_error(
        "CALL_PACKET_BINDING_MISMATCH",
        lambda: gate.gate_lineage(
            env_b,
            call,
            lineage,
            expected_model_call_identity_sha256=call["source_bound_model_call_identity_sha256"],
            expected_controller_lineage_sha256=gate.canonical_sha256(lineage),
        ),
    )


def test_model_output_identity_mismatch_inside_call_receipt_is_rejected():
    env = node_envelope()
    call = model_call_receipt()
    bad = copy.deepcopy(call)
    bad["model_output_identity_sha256"] = h("0")
    expect_error(
        "MODEL_OUTPUT_IDENTITY_CALL_MISMATCH",
        lambda: gate.gate_lineage(
            env,
            bad,
            controller_lineage(env, call),
            expected_model_call_identity_sha256=call["source_bound_model_call_identity_sha256"],
            expected_controller_lineage_sha256=gate.canonical_sha256(controller_lineage(env, call)),
        ),
    )


def test_source_head_drift_yields_distinct_call_and_lineage_and_old_lineage_rejects_new_call():
    env = node_envelope()
    call_a = model_call_receipt(head="1", tree="2")
    call_b = model_call_receipt(head="6", tree="7")
    lineage_a = controller_lineage(env, call_a)
    lineage_b = controller_lineage(env, call_b)
    out_a = run(env=env, call=call_a, lineage=lineage_a)
    out_b = run(env=env, call=call_b, lineage=lineage_b)
    assert out_a["source_bound_model_call_identity_sha256"] != out_b["source_bound_model_call_identity_sha256"]
    assert out_a["lineage_authority_envelope_digest"] != out_b["lineage_authority_envelope_digest"]
    expect_error(
        "MODEL_CALL_REFERENCE_TRANSPLANT_REJECTED",
        lambda: gate.gate_lineage(
            env,
            call_b,
            lineage_a,
            expected_model_call_identity_sha256=call_b["source_bound_model_call_identity_sha256"],
            expected_controller_lineage_sha256=gate.canonical_sha256(lineage_a),
        ),
    )


def test_raw_packet_unchanged_but_call_reference_changed_changes_authority_digest():
    env = node_envelope()
    call_a = model_call_receipt(call_seed="d", output_seed="e")
    call_b = model_call_receipt(call_seed="8", output_seed="9")
    out_a = run(env=env, call=call_a, lineage=controller_lineage(env, call_a))
    out_b = run(env=env, call=call_b, lineage=controller_lineage(env, call_b))
    assert out_a["node_result_packet_digest"] == out_b["node_result_packet_digest"]
    assert out_a["lineage_authority_envelope_digest"] != out_b["lineage_authority_envelope_digest"]


def test_model_or_process_minted_authority_fields_in_raw_node_result_are_rejected():
    env = node_envelope()
    p = env["node_result"]
    p["source_bound_model_call_identity_sha256"] = h("d")
    core = {k: p[k] for k in p if k not in ("packet_digest", "s1_write_intent")}
    p["packet_digest"] = gate.canonical_sha256(core)
    env["node_result_digest"] = p["packet_digest"]
    env_core = {k: env[k] for k in env if k != "envelope_digest"}
    env["envelope_digest"] = gate.canonical_sha256(env_core)
    expect_error(
        "MODEL_OR_PROCESS_MINTED_AUTHORITY_FIELD_REJECTED:source_bound_model_call_identity_sha256",
        lambda: run(env=env),
    )


def test_one_invalid_call_authority_member_rejects_whole_cohort():
    results = []
    for i in range(10):
        node = f"x{i+1:02d}"
        env = node_envelope(node=node, pid=101 + i, membership=f"membership-{node}-r1", observation=f"obs-{i}")
        call = model_call_receipt(call_seed=hex((i % 6) + 10)[2:], output_seed=hex((i % 6) + 3)[2:])
        lineage = controller_lineage(env, call, cell=f"cell-{i+1:02d}")
        results.append(run(env=env, call=call, lineage=lineage))
    good = gate.validate_lineage_bound_cohort(results, expected_member_count=10)
    assert good["pass"] is True

    bad_results = copy.deepcopy(results)
    bad_results[4]["lineage_authority_envelope"]["model_output_identity_sha256"] = h("0")
    expect_error(
        "LINEAGE_COHORT_AUTHORITY_ENVELOPE_DIGEST_MISMATCH",
        lambda: gate.validate_lineage_bound_cohort(bad_results, expected_member_count=10),
    )


def test_cohort_order_is_transport_order_independent_and_duplicate_cell_fails_closed():
    results = []
    for i in range(10):
        node = f"x{i+1:02d}"
        env = node_envelope(node=node, pid=201 + i, membership=f"membership-{node}-r1", observation=f"obs-{i}")
        call = model_call_receipt(call_seed=hex((i % 6) + 10)[2:], output_seed=hex((i % 6) + 3)[2:])
        results.append(run(env=env, call=call, lineage=controller_lineage(env, call, cell=f"cell-{i+1:02d}")))
    a = gate.validate_lineage_bound_cohort(results, expected_member_count=10)
    b = gate.validate_lineage_bound_cohort(list(reversed(results)), expected_member_count=10)
    assert a["cohort_lineage_digest"] == b["cohort_lineage_digest"]

    duplicate = copy.deepcopy(results)
    duplicate[1]["grid_cell_id"] = duplicate[0]["grid_cell_id"]
    expect_error(
        "LINEAGE_COHORT_DUPLICATE_GRID_CELL",
        lambda: gate.validate_lineage_bound_cohort(duplicate, expected_member_count=10),
    )
