from __future__ import annotations

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v3 as gate


def _pass_result():
    return {"pass": True, "failures": []}


def _fail_result(reason: str):
    return {"pass": False, "failures": [reason]}


def test_generation_failure_short_circuits_epistemic_and_state_update_path(monkeypatch):
    calls = []

    def generation_fail(row):
        calls.append("generation")
        return _fail_result("BAD_GENERATION")

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic/state-history path must be short-circuited")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation"]
    assert "GENERATION:BAD_GENERATION" in result["failures"]


def test_epistemic_rejection_occurs_only_after_generation_pass(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return _pass_result()

    def epistemic_fail(row):
        calls.append("epistemic")
        return _fail_result("EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e1:HYPOTHESIS")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_fail)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation", "epistemic"]
    assert (
        "EPISTEMIC_STATE_HISTORY:EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e1:HYPOTHESIS"
        in result["failures"]
    )


def test_component_pass_remains_nonpromoting_and_zero_credit(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: _pass_result())
    monkeypatch.setattr(gate.epistemic, "adjudicate", lambda row: _pass_result())

    result = gate.adjudicate({})
    assert result["pass"]
    assert result["candidate_pre_admission_pass"]
    assert result["positive_D_E_promotion_ready"] is False
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0
    assert result["jspace_runtime_credit_minted"] == 0
    assert result["hcu_runtime_credit_minted"] == 0
    assert result["entityos_runtime_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_invalid_component_result_fails_closed(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: None)
    result = gate.adjudicate({})
    assert not result["pass"]
    assert "GENERATION:RESULT_INVALID" in result["failures"]
