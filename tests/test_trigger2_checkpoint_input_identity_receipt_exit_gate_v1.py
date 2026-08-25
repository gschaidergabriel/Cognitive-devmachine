import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_checkpoint_input_identity_receipt_exit_gate_v1.py"
spec = importlib.util.spec_from_file_location("exit_gate", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def _receipt():
    return {
        "schema": "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1",
        "pass": True,
        "candidate_id": "QWEN35_08B_BASE",
        "local_dir": "/models/base",
        "render_mode": "canonical",
        "selection_identity_abi_component_status": "PASS_COMPONENT_ONLY",
        "consumed_identity_match": True,
        "prompt_input_identity_complete": True,
        "postload_manifest_match": True,
        "consumed_identity": {"pass": True},
        "child_process": {"returncode": 0, "stderr_tail": ""},
        "child": {
            "schema": "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_CHILD/v1",
            "pass": True,
            "forward_observed": True,
            "candidate_local_dir": "/models/base",
            "render_mode": "canonical",
            "loader": {
                "local_files_only": True,
                "trust_remote_code": False,
            },
            "runtime": {
                "HF_HUB_OFFLINE": "1",
                "TRANSFORMERS_OFFLINE": "1",
            },
        },
    }


def test_valid_receipt_passes_without_minting_credit():
    result = gate.adjudicate(_receipt())
    assert result["pass"] is True
    assert result["failures"] == []
    assert all(v == 0 for v in result["credit_boundary"].values())


def test_nonzero_child_exit_fails_closed_even_with_embedded_pass():
    receipt = _receipt()
    receipt["child_process"]["returncode"] = 137
    result = gate.adjudicate(receipt)
    assert result["pass"] is False
    assert "CHILD_PROCESS_EXIT_NONZERO" in result["failures"]


def test_child_path_and_render_transplant_fail_closed():
    receipt = _receipt()
    receipt["child"]["candidate_local_dir"] = "/models/other"
    receipt["child"]["render_mode"] = "native"
    result = gate.adjudicate(receipt)
    assert result["pass"] is False
    assert "CHILD_LOCAL_DIR_MISMATCH" in result["failures"]
    assert "CHILD_RENDER_MODE_MISMATCH" in result["failures"]


def test_offline_or_loader_boundary_drift_fails_closed():
    receipt = _receipt()
    receipt["child"]["runtime"]["HF_HUB_OFFLINE"] = "0"
    receipt["child"]["loader"]["local_files_only"] = False
    receipt["child"]["loader"]["trust_remote_code"] = True
    result = gate.adjudicate(receipt)
    assert result["pass"] is False
    assert "HF_HUB_OFFLINE_REQUIRED" in result["failures"]
    assert "CHILD_LOCAL_FILES_ONLY_REQUIRED" in result["failures"]
    assert "CHILD_TRUST_REMOTE_CODE_MUST_BE_FALSE" in result["failures"]


def test_wrong_child_schema_fails_closed():
    receipt = _receipt()
    receipt["child"]["schema"] = "OTHER"
    result = gate.adjudicate(receipt)
    assert result["pass"] is False
    assert "CHILD_SCHEMA_MISMATCH" in result["failures"]
