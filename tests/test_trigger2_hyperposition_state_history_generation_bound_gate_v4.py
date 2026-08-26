from __future__ import annotations

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as gate


def _pass_result():
    return {"pass": True, "failures": []}


def _fail_result(reason: str):
    return {"pass": False, "failures": [reason]}


def test_generation_failure_short_circuits_a02_and_epistemic(monkeypatch):
    calls = []

    def generation_fail(row):
        calls.append("generation")
        return _fail_result("BAD_GENERATION")

    def must_not_run(name):
        def inner(row):
            calls.append(name)
            raise AssertionError(name + " must be short-circuited")
        return inner

    monkeypatch.setattr(gate.generation, "adjudicate", generation_fail)
    monkeypatch.setattr(gate.a02, "adjudicate", must_not_run("a02"))
    monkeypatch.setattr(gate.epistemic, "adjudicate", must_not_run("epistemic"))

    result = gate.adjudicate({})
    assert result["pass"] is False
    assert calls == ["generation"]
    assert "GENERATION:BAD_GENERATION" in result["failures"]


def test_a02_failure_short_circuits_epistemic_state_update(monkeypatch):
    calls = []

    def generation_pass(row):
        calls.append("generation")
        return _pass_result()

    def a02_fail(row):
        calls.append("a02")
        return _fail_result("FAKE_EXECUTED")

    def epistemic_must_not_run(row):
        calls.append("epistemic")
        raise AssertionError("epistemic/state-history must be short-circuited")

    monkeypatch.setattr(gate.generation, "adjudicate", generation_pass)
    monkeypatch.setattr(gate.a02, "adjudicate", a02_fail)
    monkeypatch.setattr(gate.epistemic, "adjudicate", epistemic_must_not_run)

    result = gate.adjudicate({})
    assert result["pass"] is False
    assert calls == ["generation", "a02"]
    assert "A02:FAKE_EXECUTED" in result["failures"]


def test_full_component_pass_remains_nonpromoting_zero_credit(monkeypatch):
    calls = []

    def passed(name):
        def inner(row):
            calls.append(name)
            return _pass_result()
        return inner

    monkeypatch.setattr(gate.generation, "adjudicate", passed("generation"))
    monkeypatch.setattr(gate.a02, "adjudicate", passed("a02"))
    monkeypatch.setattr(gate.epistemic, "adjudicate", passed("epistemic"))
    monkeypatch.setattr(gate.tokenizer_abi, "adjudicate", passed("tokenizer_abi"))
    monkeypatch.setattr(gate.hyperposition_replay, "adjudicate", passed("hyperposition_replay"))

    result = gate.adjudicate({})
    assert result["pass"] is True
    assert calls == ["generation", "a02", "epistemic", "tokenizer_abi", "hyperposition_replay"]
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


def test_hyperposition_replay_failure_rejects_row(monkeypatch):
    def passed(name):
        def inner(row):
            return _pass_result()
        return inner

    def replay_fail(row):
        return {"pass": False, "failures": ["GENESIS_STATE_HISTORY_MISMATCH"]}

    monkeypatch.setattr(gate.generation, "adjudicate", passed("generation"))
    monkeypatch.setattr(gate.a02, "adjudicate", passed("a02"))
    monkeypatch.setattr(gate.epistemic, "adjudicate", passed("epistemic"))
    monkeypatch.setattr(gate.tokenizer_abi, "adjudicate", passed("tokenizer_abi"))
    monkeypatch.setattr(gate.hyperposition_replay, "adjudicate", replay_fail)

    result = gate.adjudicate({})
    assert result["pass"] is False
    assert any("HYPERPOSITION_REPLAY" in f for f in result["failures"])
    assert result["positive_D_E_promotion_ready"] is False
