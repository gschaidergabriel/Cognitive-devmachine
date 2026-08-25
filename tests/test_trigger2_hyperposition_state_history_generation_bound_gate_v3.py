from __future__ import annotations

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v3 as gate


def _generation_pass():
    return {
        "schema": gate.generation.SCHEMA,
        "pass": True,
        "generation_provenance_pass": True,
        "failures": [],
    }


def _pass_result():
    return {"pass": True, "failures": []}


def _fail_result(reason: str):
    return {"pass": False, "failures": [reason]}


def test_generation_failure_short_circuits_producer_epistemic_and_state_update_path(monkeypatch):
    calls = []

    def generation_fail(row):
        calls.append("generation")
        return _fail_result("BAD_GENERATION")

    def producer_must_not_run(row, upstream):
        calls.append("producer")
        raise AssertionError("producer path must be short-circuited")

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic/state-history path must be short-circuited")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_fail)
    monkeypatch.setattr(gate.producer_auth, "authenticate_and_sanitize", producer_must_not_run)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation"]
    assert "GENERATION:BAD_GENERATION" in result["failures"]


def test_producer_auth_failure_short_circuits_epistemic_and_state_update_path(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return _generation_pass()

    def producer_fail(row, upstream):
        calls.append("producer")
        return _fail_result("ROW_CARRIED_RECEIPT_FORGED"), None

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic/state-history path must be short-circuited")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.producer_auth, "authenticate_and_sanitize", producer_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation", "producer"]
    assert (
        "DISCRIMINATOR_PRODUCER_AUTH:ROW_CARRIED_RECEIPT_FORGED"
        in result["failures"]
    )


def test_epistemic_rejection_occurs_only_after_generation_and_producer_auth_pass(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return _generation_pass()

    def producer_pass(row, upstream):
        calls.append("producer")
        return _pass_result(), {"sanitized": True}

    def epistemic_fail(row):
        calls.append("epistemic")
        assert row == {"sanitized": True}
        return _fail_result("EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e1:HYPOTHESIS")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.producer_auth, "authenticate_and_sanitize", producer_pass)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_fail)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation", "producer", "epistemic"]
    assert (
        "EPISTEMIC_STATE_HISTORY:EPISTEMIC_TYPE_NOT_EVIDENCE_ADMISSIBLE:e1:HYPOTHESIS"
        in result["failures"]
    )


def test_component_pass_remains_nonpromoting_and_zero_credit(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: _generation_pass())
    monkeypatch.setattr(
        gate.producer_auth,
        "authenticate_and_sanitize",
        lambda row, upstream: (_pass_result(), {"sanitized": True}),
    )
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
    assert result["base_credit_minted"] == 0
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False
    assert result["row_carried_admissible_or_executed_is_authority"] is False


def test_invalid_component_result_fails_closed(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: None)
    result = gate.adjudicate({})
    assert not result["pass"]
    assert "GENERATION:RESULT_INVALID" in result["failures"]
