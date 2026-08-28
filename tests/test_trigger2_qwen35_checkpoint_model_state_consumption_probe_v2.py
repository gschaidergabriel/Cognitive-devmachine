from __future__ import annotations
import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger2_qwen35_checkpoint_model_state_consumption_probe_v2.py"
spec = importlib.util.spec_from_file_location("t2_state_v2", MODULE_PATH)
assert spec and spec.loader
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def rec(h: str, shape=(2, 2), dtype="torch.float32"):
    return {"dtype": dtype, "shape": list(shape), "numel": 4, "raw_nbytes": 16, "raw_bytes_sha256": h}

def clean():
    return {"missing_keys": [], "unexpected_keys": [], "mismatched_keys": [], "error_msgs": []}

def test_exact_reconciliation_and_byte_identical_alias_pass():
    a, b = "a"*64, "b"*64
    r = m._reconcile_state_records({"x": rec(a), "y": rec(b)}, {"x": rec(a), "y": rec(b), "lm_head.weight": rec(a)}, clean())
    assert r["pass"] is True and r["unexplained_extra_loaded_keys"] == []
    assert r["byte_identical_extra_aliases"][0]["loaded_key"] == "lm_head.weight"

def test_loaded_tensor_mutation_fails():
    r = m._reconcile_state_records({"x": rec("a"*64)}, {"x": rec("c"*64)}, clean())
    assert r["pass"] is False and any("CHECKPOINT_LOADED_TENSOR_MISMATCH" in x for x in r["failures"])

def test_missing_checkpoint_key_fails():
    r = m._reconcile_state_records({"x": rec("a"*64), "y": rec("b"*64)}, {"x": rec("a"*64)}, clean())
    assert r["pass"] is False and any("CHECKPOINT_KEYS_MISSING" in x for x in r["failures"])

def test_unexplained_extra_persistent_state_fails_closed():
    r = m._reconcile_state_records({"x": rec("a"*64)}, {"x": rec("a"*64), "new_buffer": rec("d"*64)}, clean())
    assert r["pass"] is False and r["unexplained_extra_loaded_keys"] == ["new_buffer"]

def test_loading_info_failure_is_not_ignored():
    info = clean(); info["unexpected_keys"] = ["rogue.weight"]
    r = m._reconcile_state_records({"x": rec("a"*64)}, {"x": rec("a"*64)}, info)
    assert r["pass"] is False and any("LOADING_INFO_UNEXPECTED_KEYS_NONEMPTY" in x for x in r["failures"])

def test_model_call_binding_detects_token_transplant():
    common = dict(candidate_id="C", checkpoint_manifest_sha256="1"*64, checkpoint_state_digest="2"*64, loaded_state_digest="3"*64, rendered_utf8_sha256="4"*64, attention_mask=None, runtime={"transformers":"x","safetensors":"y"}, forward_output={"top1_token_id":7})
    a = m._call_binding_digest(**common, input_ids={"dtype":"torch.int64","shape":[1,2],"raw_bytes_sha256":"a"*64})
    b = m._call_binding_digest(**common, input_ids={"dtype":"torch.int64","shape":[1,2],"raw_bytes_sha256":"b"*64})
    assert a != b

def test_state_digest_detects_post_load_parameter_mutation():
    assert m._state_digest({"x": rec("a"*64)}) != m._state_digest({"x": rec("f"*64)})

def test_same_top1_different_logits_changes_call_identity():
    common = dict(candidate_id="C", checkpoint_manifest_sha256="1"*64, checkpoint_state_digest="2"*64, loaded_state_digest="3"*64, rendered_utf8_sha256="4"*64, input_ids={"raw_bytes_sha256":"5"*64}, attention_mask=None, runtime={"transformers":"x"})
    a = m._call_binding_digest(**common, forward_output={"top1_token_id":7, "last_logits":{"raw_bytes_sha256":"a"*64}})
    b = m._call_binding_digest(**common, forward_output={"top1_token_id":7, "last_logits":{"raw_bytes_sha256":"b"*64}})
    assert a != b

def test_output_transplant_across_candidate_identity_changes_call_identity():
    common = dict(checkpoint_manifest_sha256="1"*64, checkpoint_state_digest="2"*64, loaded_state_digest="3"*64, rendered_utf8_sha256="4"*64, input_ids={"raw_bytes_sha256":"5"*64}, attention_mask=None, runtime={"transformers":"x"}, forward_output={"top1_token_id":7, "last_logits":{"raw_bytes_sha256":"a"*64}})
    a = m._call_binding_digest(candidate_id="BASE", **common)
    b = m._call_binding_digest(candidate_id="TARGET", **common)
    assert a != b
