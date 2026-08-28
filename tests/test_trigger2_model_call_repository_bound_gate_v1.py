from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_model_call_repository_bound_gate_v1.py"
spec = importlib.util.spec_from_file_location("gate", MODULE_PATH)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)


def h(ch: str) -> str:
    return ch * 64


def h40(ch: str) -> str:
    return ch * 40


def tensor(digest: str, shape=None):
    return {"dtype": "torch.float32", "shape": shape or [1, 4], "numel": 4, "raw_nbytes": 16, "raw_bytes_sha256": digest}


def child(candidate="BASE", logits_digest=None, top1=7):
    logits_digest = logits_digest or h("a")
    value = {
        "schema": gate.CHILD_V2_SCHEMA,
        "pass": True,
        "candidate_id": candidate,
        "checkpoint_manifest_sha256": h("b"),
        "state_reconciliation": {
            "pass": True,
            "checkpoint_state_digest": h("c"),
            "loaded_state_digest": h("d"),
        },
        "persistent_state_stable_across_forward": True,
        "rendered_utf8_sha256": h("e"),
        "input_ids": tensor(h("f"), [1, 3]),
        "attention_mask": tensor(h("1"), [1, 3]),
        "runtime": {"python": "3.12", "torch": "2.x", "transformers": "x", "platform": "linux"},
        "forward_observed": True,
        "forward_output": {
            "full_logits_shape": [1, 3, 4],
            "last_logits": tensor(logits_digest, [1, 4]),
            "top1_token_id": top1,
        },
    }
    envelope = {
        "schema": gate.V2_BINDING_SCHEMA,
        "candidate_id": value["candidate_id"],
        "checkpoint_manifest_sha256": value["checkpoint_manifest_sha256"],
        "checkpoint_state_digest": value["state_reconciliation"]["checkpoint_state_digest"],
        "loaded_state_digest": value["state_reconciliation"]["loaded_state_digest"],
        "rendered_utf8_sha256": value["rendered_utf8_sha256"],
        "input_ids": value["input_ids"],
        "attention_mask": value["attention_mask"],
        "runtime": value["runtime"],
        "forward_output": value["forward_output"],
    }
    value["model_call_binding_sha256"] = gate.canonical_sha256(envelope)
    return value


def receipt(c=None):
    c = c or child()
    return {
        "schema": gate.ABI_V2_SCHEMA,
        "pass": True,
        "status": "PASS_COMPONENT_ONLY",
        "candidate_id": c["candidate_id"],
        "selection_grade_consumed_model_state_component_eligible": True,
        "manifest_to_loaded_state_reconciled": True,
        "forward_bound_to_loaded_state_and_input": True,
        "child": c,
    }


def source(head="2", tree="3", dirty=False):
    return {
        "schema": gate.SOURCE_IDENTITY_SCHEMA,
        "repository_full_name": gate.CANONICAL_REPOSITORY,
        "head_sha": h40(head),
        "tree_sha": h40(tree),
        "source_path": gate.PROBE_SOURCE_PATH,
        "source_blob_sha1": h40("4"),
        "source_sha256": h("5"),
        "dirty": dirty,
    }


def run(r=None, s=None):
    r = r or receipt()
    s = s or source()
    return gate.gate_receipt(r, s, expected_source_identity_sha256=gate.canonical_sha256(s))


def test_happy_path_binds_receipt_output_and_source():
    out = run()
    assert out["pass"] is True
    assert len(out["source_bound_model_call_identity_sha256"]) == 64
    assert out["credit_boundary"]["training_credit"] == 0


def test_same_top1_different_logits_produces_distinct_v2_and_source_bound_identity():
    a = run(receipt(child(logits_digest=h("a"), top1=7)))
    b = run(receipt(child(logits_digest=h("9"), top1=7)))
    assert a["abi_v2_model_call_binding_sha256"] != b["abi_v2_model_call_binding_sha256"]
    assert a["source_bound_model_call_identity_sha256"] != b["source_bound_model_call_identity_sha256"]


def test_output_transplant_without_rebinding_is_rejected():
    r = receipt(child(candidate="BASE"))
    transplanted = copy.deepcopy(r)
    transplanted["child"]["forward_output"]["last_logits"]["raw_bytes_sha256"] = h("8")
    try:
        run(transplanted)
    except gate.GateError as exc:
        assert str(exc) == "MODEL_CALL_BINDING_RECOMPUTE_MISMATCH"
    else:
        raise AssertionError("transplant must fail")


def test_candidate_transplant_parent_child_mismatch_rejected():
    r = receipt(child(candidate="BASE"))
    r["candidate_id"] = "POSTTRAINED"
    try:
        run(r)
    except gate.GateError as exc:
        assert str(exc) == "PARENT_CHILD_CANDIDATE_MISMATCH"
    else:
        raise AssertionError("candidate transplant must fail")


def test_source_head_change_changes_identity_when_separately_precommitted():
    a = run(s=source(head="2"))
    b = run(s=source(head="6"))
    assert a["source_identity"]["source_identity_sha256"] != b["source_identity"]["source_identity_sha256"]
    assert a["source_bound_model_call_identity_sha256"] != b["source_bound_model_call_identity_sha256"]


def test_source_commitment_transplant_rejected():
    s1 = source(head="2")
    s2 = source(head="6")
    try:
        gate.gate_receipt(receipt(), s2, expected_source_identity_sha256=gate.canonical_sha256(s1))
    except gate.GateError as exc:
        assert str(exc) == "SOURCE_IDENTITY_COMMITMENT_MISMATCH"
    else:
        raise AssertionError("source commitment transplant must fail")


def test_dirty_repository_rejected_even_if_commitment_matches():
    s = source(dirty=True)
    try:
        gate.gate_receipt(receipt(), s, expected_source_identity_sha256=gate.canonical_sha256(s))
    except gate.GateError as exc:
        assert str(exc) == "SOURCE_REPOSITORY_DIRTY_OR_UNKNOWN"
    else:
        raise AssertionError("dirty source must fail")


def test_missing_last_logits_digest_rejected():
    r = receipt()
    del r["child"]["forward_output"]["last_logits"]["raw_bytes_sha256"]
    try:
        run(r)
    except gate.GateError as exc:
        assert str(exc) == "LAST_LOGITS_RAW_BYTES_SHA256_INVALID"
    else:
        raise AssertionError("missing output identity must fail")
