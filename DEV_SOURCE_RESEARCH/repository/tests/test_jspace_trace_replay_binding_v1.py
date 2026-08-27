import copy
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import jspace_execution_identity_v1 as execution_id
import jspace_trace_abi_v1 as abi


def h(text): return hashlib.sha256(text.encode()).hexdigest()


def row(*, invocation, control, split, session="session-a", case_id=None, label_map_id=None, score=1.0):
    material = {
        "invocation": invocation, "prompt_sha256": h(f"prompt-{split}-{case_id or 'cal'}"),
        "layer": 12, "vector_layer": 12, "gain": 4.0, "control": control, "mode": "control",
        "seed": 2718 if split == "holdout" else 1701, "positive_label": "A", "negative_label": "B",
        "target_score": score, "hook_calls": 1,
        "pre_activation_sha256": h(f"pre-{invocation}-{session}"),
        "post_activation_sha256": h(f"post-{invocation}-{session}"),
        "applied_vector_sha256": h(f"vec-{control}"),
    }
    runtime_sha = abi.canonical_sha(material)
    out = {**material, "runtime_receipt_sha256": runtime_sha, "split": split, "case_id": case_id, "runtime_session_id": session}
    if label_map_id is not None: out["label_map_id"] = label_map_id
    out["model_execution_id"] = execution_id.derive_model_execution_id(session, out)
    return out


def result_fixture(session="session-a"):
    base = {
        "schema": abi.SOURCE_SCHEMA, "status": "PASS", "started_at": "volatile-a", "finished_at": "volatile-b",
        "source": {"repo_head": h("head"), "repo_tree": h("tree")}, "model": "Qwen/Qwen3-0.6B",
        "model_revision": h("revision")[:40], "checkpoint_sha256": h("checkpoint"), "tokenizer_sha256": h("tokenizer"),
        "runtime_build_sha256": h("runtime"), "credit_scope": "MODEL_SPECIFIC_INTERMEDIATE_JSPACE_CAUSAL_CANDIDATE_ONLY",
        "derivation": {"label_independence": {"derivation_input_family_sha256": h("derivation-family")}},
        "verdict": {"classification": "SYNTHETIC_PASS"},
        "calibration_rows": [row(invocation=1, control="BASELINE", split="calibration", session=session, score=0.0)],
        "holdout_rows": [
            row(invocation=2, control="BASELINE", split="holdout", session=session, case_id="hold-2718", label_map_id="MAP_AB", score=0.1),
            row(invocation=3, control="+VECTOR", split="holdout", session=session, case_id="hold-2718", label_map_id="MAP_AB", score=1.1),
        ],
    }
    base["result_sha256"] = abi.canonical_sha({k: v for k, v in base.items() if k != "result_sha256"})
    return base


def test_matched_controls_share_family_but_have_distinct_execution_replay_identity():
    traces, manifest = abi.normalize_result(result_fixture())
    hold = [t for t in traces if t["split_id"] == "CAUSAL_HOLDOUT"]
    assert len(hold) == 2
    assert hold[0]["causal_event_id"] == hold[1]["causal_event_id"]
    assert hold[0]["control_family_id"] == hold[1]["control_family_id"]
    assert hold[0]["execution_replay_identity_sha256"] != hold[1]["execution_replay_identity_sha256"]
    assert manifest["trace_count"] == 3
    assert manifest["dataset_admission_eligible"] is False


def test_posthoc_classification_mutation_does_not_change_replay_or_measured_identity():
    a = result_fixture(); b = copy.deepcopy(a)
    b["started_at"] = "different"; b["finished_at"] = "different-again"; b["verdict"]["classification"] = "POSTHOC_LABEL_CHANGE"
    ta, _ = abi.normalize_result(a); tb, _ = abi.normalize_result(b)
    pairs = zip(sorted(ta, key=lambda x: x["model_execution_id"]), sorted(tb, key=lambda x: x["model_execution_id"]))
    for x, y in pairs:
        assert x["execution_replay_identity_sha256"] == y["execution_replay_identity_sha256"]
        assert x["measured_evidence_sha256"] == y["measured_evidence_sha256"]
        assert x["observation_envelope_sha256"] != y["observation_envelope_sha256"]
        assert abi.classify_reemission(x, y) == "DUPLICATE_REEMISSION"


def test_measured_mutation_without_receipt_update_fails_closed():
    obj = result_fixture(); obj["holdout_rows"][1]["target_score"] = 9.9
    try: abi.normalize_result(obj)
    except abi.TraceNormalizationError as exc: assert "RUNTIME_RECEIPT_DIGEST_MISMATCH" in str(exc)
    else: raise AssertionError("expected fail-closed receipt mismatch")


def test_same_execution_identity_with_changed_measured_evidence_classifies_conflict():
    a = result_fixture(); ta, _ = abi.normalize_result(a)
    b = copy.deepcopy(a); r = b["holdout_rows"][1]; r["target_score"] = 9.9
    material = {k: r[k] for k in abi.RUNTIME_RECEIPT_KEYS}; r["runtime_receipt_sha256"] = abi.canonical_sha(material)
    tb, _ = abi.normalize_result(b)
    xa = next(t for t in ta if t["model_execution_id"] == r["model_execution_id"])
    xb = next(t for t in tb if t["model_execution_id"] == r["model_execution_id"])
    assert xa["execution_replay_identity_sha256"] == xb["execution_replay_identity_sha256"]
    assert xa["measured_evidence_sha256"] != xb["measured_evidence_sha256"]
    assert abi.classify_reemission(xa, xb) == "JSPACE_REPLAY_IDENTITY_CONFLICT"


def test_genuinely_new_runtime_session_is_new_execution_identity():
    a, _ = abi.normalize_result(result_fixture("session-a")); b, _ = abi.normalize_result(result_fixture("session-b"))
    xa = next(t for t in a if t["control_class"] == "+VECTOR"); xb = next(t for t in b if t["control_class"] == "+VECTOR")
    assert abi.classify_reemission(xa, xb) == "NEW_EXECUTION_IDENTITY"


def test_blocked_source_emits_zero_credit_manifest():
    obj = result_fixture(); obj["status"] = "BLOCKED_LOCAL_INTERMEDIATE"; obj.pop("checkpoint_sha256")
    traces, manifest = abi.normalize_result(obj)
    assert traces == [] and manifest["trace_count"] == 0 and manifest["credit_scope"] == "NONE"


def test_holdout_requires_label_map_identity():
    obj = result_fixture(); del obj["holdout_rows"][0]["label_map_id"]
    try: abi.normalize_result(obj)
    except abi.TraceNormalizationError as exc: assert "label_map_id_MUST_BE_NONEMPTY_STRING" in str(exc)
    else: raise AssertionError("expected missing label map rejection")
