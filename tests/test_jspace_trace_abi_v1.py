import copy
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import jspace_trace_abi_v1 as abi


def h(text):
    return hashlib.sha256(text.encode()).hexdigest()


def row(*, invocation, control, split, case_id=None, label_map_id=None, score=1.0):
    material = {
        "invocation": invocation,
        "prompt_sha256": h(f"prompt-{split}-{case_id or 'cal'}"),
        "layer": 12,
        "vector_layer": 12,
        "gain": 4.0,
        "control": control,
        "mode": "control",
        "seed": 2718 if split == "holdout" else 1701,
        "positive_label": "A",
        "negative_label": "B",
        "target_score": score,
        "hook_calls": 1,
        "pre_activation_sha256": h(f"pre-{invocation}"),
        "post_activation_sha256": h(f"post-{invocation}"),
        "applied_vector_sha256": h(f"vec-{control}"),
    }
    runtime_sha = abi.canonical_sha(material)
    out = {**material, "runtime_receipt_sha256": runtime_sha, "split": split, "case_id": case_id}
    if label_map_id is not None:
        out["label_map_id"] = label_map_id
    return out


def result_fixture():
    base = {
        "schema": abi.SOURCE_SCHEMA,
        "status": "PASS",
        "started_at": "volatile-a",
        "finished_at": "volatile-b",
        "source": {"repo_head": h("head"), "repo_tree": h("tree")},
        "model": "Qwen/Qwen3-0.6B",
        "model_revision": h("revision")[:40],
        "checkpoint_sha256": h("checkpoint"),
        "tokenizer_sha256": h("tokenizer"),
        "runtime_build_sha256": h("runtime"),
        "credit_scope": "MODEL_SPECIFIC_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE_ONLY",
        "derivation": {"label_independence": {"derivation_input_family_sha256": h("derivation-family")}},
        "verdict": {"classification": "SYNTHETIC_PASS"},
        "calibration_rows": [row(invocation=1, control="BASELINE", split="calibration", score=0.0)],
        "holdout_rows": [
            row(invocation=2, control="BASELINE", split="holdout", case_id="hold-2718", label_map_id="MAP_AB", score=0.1),
            row(invocation=3, control="+VECTOR", split="holdout", case_id="hold-2718", label_map_id="MAP_AB", score=1.1),
        ],
    }
    base["result_sha256"] = abi.canonical_sha({k: v for k, v in base.items() if k != "result_sha256"})
    return base


def test_matched_controls_share_causal_event_but_not_admission():
    traces, manifest = abi.normalize_result(result_fixture())
    hold = [t for t in traces if t["split_id"] == "CAUSAL_HOLDOUT"]
    assert len(hold) == 2
    assert hold[0]["causal_event_id"] == hold[1]["causal_event_id"]
    assert hold[0]["admission_id"] != hold[1]["admission_id"]
    assert manifest["trace_count"] == 3
    assert all(t["truth_status"] == "CANDIDATE_MEASUREMENT_ONLY" for t in traces)


def test_volatile_run_timestamps_do_not_rekey_traces():
    a = result_fixture()
    b = copy.deepcopy(a)
    b["started_at"] = "different"
    b["finished_at"] = "different-again"
    b["snapshot_path"] = "/different/local/path"
    ta, _ = abi.normalize_result(a)
    tb, _ = abi.normalize_result(b)
    assert [t["trace_sha256"] for t in ta] == [t["trace_sha256"] for t in tb]


def test_measured_row_mutation_without_receipt_update_fails_closed():
    obj = result_fixture()
    obj["holdout_rows"][1]["target_score"] = 9.9
    try:
        abi.normalize_result(obj)
    except abi.TraceNormalizationError as exc:
        assert "RUNTIME_RECEIPT_DIGEST_MISMATCH" in str(exc)
    else:
        raise AssertionError("expected fail-closed receipt mismatch")


def test_blocked_source_emits_zero_credit_manifest():
    obj = result_fixture()
    obj["status"] = "BLOCKED_LOCAL_INTERMEDIATE"
    obj.pop("checkpoint_sha256")
    traces, manifest = abi.normalize_result(obj)
    assert traces == []
    assert manifest["trace_count"] == 0
    assert manifest["credit_scope"] == "NONE"


def test_holdout_requires_label_map_identity():
    obj = result_fixture()
    del obj["holdout_rows"][0]["label_map_id"]
    try:
        abi.normalize_result(obj)
    except abi.TraceNormalizationError as exc:
        assert "label_map_id_MUST_BE_NONEMPTY_STRING" in str(exc)
    else:
        raise AssertionError("expected missing label map rejection")
