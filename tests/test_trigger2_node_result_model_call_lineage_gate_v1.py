from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_node_result_model_call_lineage_gate_v1.py"
spec = importlib.util.spec_from_file_location("lineage", MODULE_PATH)
lineage = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(lineage)


def h(ch: str) -> str:
    return ch * 64


def call_receipt(call="a", output="b", source="c"):
    return {
        "schema": lineage.CALL_GATE_SCHEMA,
        "pass": True,
        "status": lineage.CALL_GATE_STATUS,
        "source_bound_model_call_identity_sha256": h(call),
        "model_output_identity_sha256": h(output),
        "source_identity": {"source_identity_sha256": h(source)},
        "credit_boundary": {"training_credit": 0},
    }


def chain(route="d", engine="e", cell="f"):
    return {
        "schema": lineage.CHAIN_SCHEMA,
        "authority_semantics": "REFERENCE_ONLY_NO_EFFECT_OR_TRUTH_AUTHORITY",
        "route_identity_sha256": h(route),
        "engine_identity_sha256": h(engine),
        "cell_identity_sha256": h(cell),
    }


def packet(answer="yes", task="t01", node="x01", scope="GLOBAL"):
    core = {
        "schema": lineage.NODE_RESULT_SCHEMA,
        "source_kind": "ORDINARY_NODE",
        "source_node_id": node,
        "scope": scope,
        "generation": 7,
        "state_epoch": 11,
        "state_digest": h("1"),
        "payload": {"task_id": task, "answer": answer, "process_pid": 1234},
    }
    return {**core, "packet_digest": lineage.canonical_sha256(core), "s1_write_intent": False}


def bind(p=None, r=None, c=None):
    p = p or packet()
    r = r or call_receipt()
    c = c or chain()
    return lineage.bind_node_result(
        p, r, c,
        expected_call_gate_receipt_sha256=lineage.canonical_sha256(r),
        expected_route_engine_cell_chain_sha256=lineage.canonical_sha256(c),
    )


def validate(p, r=None, c=None, expected_r=None, expected_c=None):
    r = r or call_receipt()
    c = c or chain()
    return lineage.validate_bound_node_result(
        p, r, c,
        expected_call_gate_receipt_sha256=expected_r or lineage.canonical_sha256(r),
        expected_route_engine_cell_chain_sha256=expected_c or lineage.canonical_sha256(c),
    )


def repack(p):
    q = copy.deepcopy(p)
    q["packet_digest"] = lineage.canonical_sha256({k: q[k] for k in q if k not in ("packet_digest", "s1_write_intent")})
    return q


def test_happy_path_reuses_existing_call_id_and_zero_credit():
    r = call_receipt()
    p = bind(r=r)
    out = validate(p, r=r)
    assert out["pass"] is True
    assert out["model_call_identity_sha256"] == r["source_bound_model_call_identity_sha256"]
    assert p["payload"]["model_call_lineage"]["identity_semantics"] == "REFERENCE_EXISTING_CALL_ID_NO_SECOND_CALL_AUTHORITY"
    assert out["credit_boundary"]["training_credit"] == 0


def test_call_identity_transplant_rejected_even_if_packet_digest_repacked():
    p = bind()
    p["payload"]["model_call_lineage"]["model_call_identity_sha256"] = h("9")
    p = repack(p)
    try:
        validate(p)
    except lineage.LineageError as exc:
        assert str(exc) in {"MODEL_CALL_LINEAGE_IDENTITY_MISMATCH", "MODEL_CALL_LINEAGE_TRANSPLANT_OR_MUTATION"}
    else:
        raise AssertionError("call transplant must fail")


def test_output_identity_transplant_rejected_even_if_packet_digest_repacked():
    p = bind()
    p["payload"]["model_call_lineage"]["model_output_identity_sha256"] = h("8")
    p = repack(p)
    try:
        validate(p)
    except lineage.LineageError as exc:
        assert str(exc) in {"MODEL_CALL_LINEAGE_IDENTITY_MISMATCH", "MODEL_CALL_LINEAGE_TRANSPLANT_OR_MUTATION"}
    else:
        raise AssertionError("output transplant must fail")


def test_cell_chain_transplant_rejected_by_precommitment():
    p = bind()
    original = chain()
    changed = chain(cell="7")
    try:
        validate(p, c=changed, expected_c=lineage.canonical_sha256(original))
    except lineage.LineageError as exc:
        assert str(exc) == "ROUTE_ENGINE_CELL_CHAIN_COMMITMENT_MISMATCH"
    else:
        raise AssertionError("cell-chain transplant must fail")


def test_call_gate_receipt_transplant_rejected_by_precommitment():
    original = call_receipt()
    p = bind(r=original)
    changed = call_receipt(call="7")
    try:
        validate(p, r=changed, expected_r=lineage.canonical_sha256(original))
    except lineage.LineageError as exc:
        assert str(exc) == "CALL_GATE_RECEIPT_COMMITMENT_MISMATCH"
    else:
        raise AssertionError("call-receipt transplant must fail")


def test_base_payload_transplant_rejected_even_if_outer_packet_repacked():
    p = bind()
    p["payload"]["answer"] = "transplanted"
    p = repack(p)
    try:
        validate(p)
    except lineage.LineageError as exc:
        assert str(exc) in {"MODEL_CALL_LINEAGE_IDENTITY_MISMATCH", "MODEL_CALL_LINEAGE_TRANSPLANT_OR_MUTATION"}
    else:
        raise AssertionError("base payload transplant must fail")


def test_existing_lineage_cannot_be_silently_overwritten():
    p = packet()
    p["payload"]["model_call_lineage"] = {"fake": True}
    p = repack(p)
    try:
        bind(p)
    except lineage.LineageError as exc:
        assert str(exc) == "NODE_RESULT_LINEAGE_ALREADY_PRESENT"
    else:
        raise AssertionError("pre-existing lineage must fail")


def test_invalid_original_node_result_digest_rejected():
    p = packet()
    p["packet_digest"] = h("0")
    try:
        bind(p)
    except lineage.LineageError as exc:
        assert str(exc) == "NODE_RESULT_PACKET_DIGEST_MISMATCH"
    else:
        raise AssertionError("bad packet digest must fail")


def test_task_identity_transplant_rejected_even_if_outer_packet_repacked():
    p = bind()
    p["payload"]["task_id"] = "t99"
    p = repack(p)
    try:
        validate(p)
    except lineage.LineageError as exc:
        assert str(exc) in {"MODEL_CALL_LINEAGE_IDENTITY_MISMATCH", "MODEL_CALL_LINEAGE_TRANSPLANT_OR_MUTATION"}
    else:
        raise AssertionError("task transplant must fail")
