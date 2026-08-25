from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "tools" / "trigger2_hyperposition_state_history_proof_gate_v2.py"

spec = importlib.util.spec_from_file_location("trigger2_hp_state_history_v2", GATE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def _row(history_type="SYNTHETIC_PROOF", current_type="SYNTHETIC_PROOF"):
    return {
        "synthetic_event_history_evaluator_only": [
            {"event_id": "history-1", "epistemic_type": history_type}
        ],
        "synthetic_test_event_evaluator_only": {
            "event_id": "current-1",
            "epistemic_type": current_type,
        },
    }


def _base_result(history_independent=True, current_independent=True):
    return {
        "pass": True,
        "failures": [],
        "replay_steps": [
            {
                "event_id": "history-1",
                "derived_independence_qualified": history_independent,
            }
        ],
        "base_derivation_gate_v2_result": {
            "independence_derivation": {
                "registry_event_id": "current-1",
                "derived_independence_qualified": current_independent,
            }
        },
        "recomputed_target": {"task_resolution": {"status": "UNRESOLVED"}},
    }


def test_synthetic_proof_may_receive_independent_credit():
    failures = mod.epistemic_credit_failures(_row(), _base_result())
    assert failures == []


def test_observed_may_receive_independent_credit_after_base_v1_receipt_gate():
    failures = mod.epistemic_credit_failures(
        _row(history_type="OBSERVED", current_type="OBSERVED"),
        _base_result(),
    )
    assert failures == []


def test_hypothesis_cannot_receive_independent_credit():
    failures = mod.epistemic_credit_failures(
        _row(history_type="HYPOTHESIS"),
        _base_result(),
    )
    assert any(
        f == "NON_EVIDENTIAL_EPISTEMIC_EVENT_CANNOT_RECEIVE_INDEPENDENT_CREDIT:history-1:HYPOTHESIS"
        for f in failures
    )


def test_unknown_current_event_cannot_receive_independent_credit():
    failures = mod.epistemic_credit_failures(
        _row(current_type="UNKNOWN"),
        _base_result(),
    )
    assert any(
        f == "NON_EVIDENTIAL_EPISTEMIC_EVENT_CANNOT_RECEIVE_INDEPENDENT_CREDIT:current-1:UNKNOWN"
        for f in failures
    )


def test_non_evidential_event_with_no_independent_credit_is_retained():
    failures = mod.epistemic_credit_failures(
        _row(history_type="PREDICTION", current_type="CONTRADICTION"),
        _base_result(history_independent=False, current_independent=False),
    )
    assert failures == []


def test_missing_derived_independence_fails_closed():
    base_result = _base_result()
    base_result["replay_steps"] = []
    failures = mod.epistemic_credit_failures(_row(), base_result)
    assert "DERIVED_INDEPENDENCE_MISSING_FOR_EVENT:history-1" in failures


def test_wrapper_propagates_base_v1_failure(monkeypatch):
    monkeypatch.setattr(
        mod.base,
        "adjudicate",
        lambda row: {"pass": False, "failures": ["EVENT_DIGEST_REGISTRY_MISMATCH:e1"]},
    )
    result = mod.adjudicate(_row())
    assert result["pass"] is False
    assert "BASE_V1:EVENT_DIGEST_REGISTRY_MISMATCH:e1" in result["failures"]
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0


def test_wrapper_blocks_independent_unknown_even_when_base_v1_passes(monkeypatch):
    monkeypatch.setattr(mod.base, "adjudicate", lambda row: _base_result())
    result = mod.adjudicate(_row(current_type="UNKNOWN"))
    assert result["pass"] is False
    assert any("NON_EVIDENTIAL_EPISTEMIC_EVENT" in f for f in result["failures"])
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_wrapper_keeps_generation_and_seed_rebind_credit_explicitly_open(monkeypatch):
    monkeypatch.setattr(mod.base, "adjudicate", lambda row: _base_result())
    result = mod.adjudicate(_row())
    assert result["pass"] is True
    assert result["generation_provenance_receipt_closed"] is False
    assert result["native_seed_rebound_to_this_gate"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
