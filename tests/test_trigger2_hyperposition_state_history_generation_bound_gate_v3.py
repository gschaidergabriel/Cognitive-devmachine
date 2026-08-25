from __future__ import annotations

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v3 as gate


def _minimal_row(epistemic_type: str):
    return {
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": {
            "event_id": "e-current",
            "epistemic_type": epistemic_type,
        },
    }


def test_generation_failure_short_circuits_before_epistemic_guard(monkeypatch):
    calls = []

    def generation_fail(row):
        calls.append("generation")
        return {"pass": False, "failures": ["SOURCE_ROOT_INVALID"]}

    def epistemic_should_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic guard must not run after generation failure")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_should_not_run)

    result = gate.adjudicate(_minimal_row("HYPOTHESIS"))
    assert not result["pass"]
    assert calls == ["generation"]
    assert "GENERATION:SOURCE_ROOT_INVALID" in result["failures"]
    assert result["epistemic_preupdate_state_history_proof"] is None


def test_nonobservational_event_is_blocked_by_guard_before_state_history(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: {"pass": True, "failures": []})

    result = gate.adjudicate(_minimal_row("HYPOTHESIS"))
    assert not result["pass"]
    epi = result["epistemic_preupdate_state_history_proof"]
    assert epi["underlying_gate_called"] is False
    assert any(
        x == "EPISTEMIC:EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-current:HYPOTHESIS"
        for x in result["failures"]
    )
    assert result["direct_state_history_bypass_allowed"] is False


def test_proof_order_is_generation_then_epistemic_guard(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return {"pass": True, "failures": []}

    def epistemic_pass(row):
        calls.append("epistemic")
        return {"pass": True, "failures": [], "underlying_gate_called": True}

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_pass)

    result = gate.adjudicate(_minimal_row("OBSERVED"))
    assert result["pass"], result
    assert calls == ["generation", "epistemic"]
    assert result["proof_order"] == [
        "GENERATION_PROVENANCE",
        "EPISTEMIC_PREUPDATE_GUARD",
        "STATE_HISTORY_PROOF_VIA_GUARD",
    ]
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0


def test_epistemic_guard_failure_cannot_false_pass_even_after_generation_pass(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: {"pass": True, "failures": []})
    monkeypatch.setattr(
        gate.epistemic,
        "adjudicate",
        lambda row: {
            "pass": False,
            "failures": ["EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-current:UNKNOWN"],
            "underlying_gate_called": False,
        },
    )
    result = gate.adjudicate(_minimal_row("UNKNOWN"))
    assert not result["pass"]
    assert "EPISTEMIC:EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e-current:UNKNOWN" in result["failures"]
    assert result["candidate_pre_admission_pass"] is False
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False
