from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
GATE_PATH = HERE / "check_qwen35_jlens_admission.py"


def _gate_module():
    spec = importlib.util.spec_from_file_location("qwen35_jlens_admission_gate", GATE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("phase", ["forward", "jacobian"])
def test_weighted_phases_fail_before_model_loading_without_exact_tree_hash(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], phase: str
) -> None:
    gate = _gate_module()
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_qwen35_jlens_admission.py", "--phase", phase, "--model", "Qwen/Qwen3.5-0.8B"],
    )

    assert gate.main() == 1
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "FAIL"
    assert receipt["authority"]["exact_model_bytes_bound"] is False
    assert receipt["failure"]["message"] == "EXACT_WEIGHTED_PHASE_REQUIRES_HASHED_LOCAL_MODEL_TREE"
    assert "observed" not in receipt


def test_receipt_exposes_exact_model_byte_binding_state(monkeypatch: pytest.MonkeyPatch) -> None:
    gate = _gate_module()
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_qwen35_jlens_admission.py", "--phase", "layout", "--hash-local-tree"],
    )
    args = gate.parse_args()
    receipt = gate._base_receipt(args)
    assert receipt["authority"]["exact_model_bytes_bound"] is True
