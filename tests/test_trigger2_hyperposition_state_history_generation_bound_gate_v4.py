from __future__ import annotations

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as gate


def _pass_result(**extra):
    return {"pass": True, "failures": [], **extra}


def _fail_result(reason: str):
    return {"pass": False, "failures": [reason]}


def test_generation_failure_short_circuits_producer_and_epistemic(monkeypatch):
    calls = []

    def generation_fail(row):
        calls.append("generation")
        return _fail_result("BAD_GENERATION")

    def producer_must_not_run(row):
        calls.append("producer")
        raise AssertionError("producer auth must not run")

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic must not run")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_fail)
    monkeypatch.setattr(gate.producer_auth, "authenticate_after_generation", producer_must_not_run)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation"]
    assert "GENERATION:BAD_GENERATION" in result["failures"]


def test_producer_rejection_occurs_after_generation_and_short_circuits_epistemic(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return _pass_result()

    def producer_fail(row):
        calls.append("producer")
        return _fail_result("DISCRIMINATOR_PRODUCER_SOURCE_IDENTITY_MISMATCH")

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic must not run")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.producer_auth, "authenticate_after_generation", producer_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert not result["pass"]
    assert calls == ["generation", "producer"]
    assert (
        "DISCRIMINATOR_PRODUCER_AUTH:DISCRIMINATOR_PRODUCER_SOURCE_IDENTITY_MISMATCH"
        in result["failures"]
    )


def test_epistemic_runs_only_on_producer_sanitized_row(monkeypatch):
    calls = []
    sanitized = {"sanitized": True}

    def generation_pass(row):
        calls.append(("generation", row))
        return _pass_result()

    def producer_pass(row):
        calls.append(("producer", row))
        return _pass_result(sanitized_row_evaluator_only=sanitized)

    def epistemic_pass(row):
        calls.append(("epistemic", row))
        assert row is sanitized
        return _pass_result()

    original = {"candidate": True}
    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.producer_auth, "authenticate_after_generation", producer_pass)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_pass)

    result = gate.adjudicate(original)
    assert result["pass"], result
    assert [x[0] for x in calls] == ["generation", "producer", "epistemic"]


def test_component_pass_remains_nonpromoting_zero_credit(monkeypatch):
    monkeypatch.setattr(gate.generation, "adjudicate", lambda row: _pass_result())
    monkeypatch.setattr(
        gate.producer_auth,
        "authenticate_after_generation",
        lambda row: _pass_result(sanitized_row_evaluator_only={}),
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
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False
    assert result["second_semantic_authority_created"] is False
