import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import xeno_shell_model_slot_v1 as ms


def test_load_resident_identity_target_measured():
    r = ms.load_resident_identity("QWEN35_08B_TARGET_MEASURED")
    assert r["revision_matches_pinned"] is True
    assert r["identity_complete"] is True


def test_load_resident_identity_unknown_candidate_fails_closed():
    try:
        ms.load_resident_identity("NOT_A_REAL_CANDIDATE")
        assert False, "expected ModelSlotError"
    except ms.ModelSlotError as e:
        assert "IDENTITY_RECEIPT_NOT_FOUND" in str(e)


def test_resident_model_object_matches_spec_measured_values():
    m = ms.resident_model_object("QWEN35_08B_TARGET_MEASURED")
    assert m["hidden_size"] == 1024
    assert m["num_hidden_layers"] == 24
    assert m["full_attention_layer_indices"] == [3, 7, 11, 15, 19, 23]
    assert m["checkpoint_revision"] == "591852bda6e1979f59e4b0f5ee2919697b12e936"
    assert m["vector_abi_binding"] == "UNBOUND_NO_MEASURED_HRR_ARTIFACTS"


def test_bind_executor_context_roundtrip():
    ctx = ms.bind_executor_context(
        candidate_id="QWEN35_08B_TARGET_MEASURED",
        grid_instance_id="grid1", executor_id="node-3", lease_id="lease-9",
        generation=5, process_id="ZECP11", workspace_epoch=2,
    )
    assert ctx["resident_model"]["candidate_id"] == "QWEN35_08B_TARGET_MEASURED"
    assert ctx["lease_id"] == "lease-9"


def test_bind_executor_context_incomplete_identity_fails_closed():
    try:
        ms.bind_executor_context(
            candidate_id="NOT_A_REAL_CANDIDATE",
            grid_instance_id="g", executor_id="e", lease_id="l",
            generation=1, process_id="ZECP11", workspace_epoch=1,
        )
        assert False, "expected ModelSlotError"
    except ms.ModelSlotError:
        pass
