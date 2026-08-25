from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as gate


def _load_current_pilot_helper():
    path = Path(__file__).resolve().with_name("test_trigger2_generation_bound_hyperposition_gate_v2.py")
    spec = importlib.util.spec_from_file_location("trigger2_generation_bound_test_helper_for_a02_v4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row_without_candidate_discriminator_receipt():
    helper = _load_current_pilot_helper()
    row = helper._row()
    row["discriminator_execution_receipts_evaluator_only"] = []
    return row


def test_v4_full_bounded_pilot_passes_only_with_derived_producer_receipt():
    row = _row_without_candidate_discriminator_receipt()
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["discriminator_producer_auth"]["producer_invoked"] is True
    assert result["epistemic_state_history_proof"]["pass"] is True
    assert result["positive_D_E_promotion_ready"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0


def test_v4_rejects_legacy_coherent_row_carried_executed_receipt():
    helper = _load_current_pilot_helper()
    row = helper._row()
    legacy = deepcopy(row["discriminator_execution_receipts_evaluator_only"][0])
    assert legacy["admissible"] is True
    assert legacy["executed"] is True
    assert isinstance(legacy["execution_receipt_id"], str) and legacy["execution_receipt_id"]
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any(
        "DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER" in failure
        for failure in result["failures"]
    )


def test_v4_accepts_exact_recomputed_candidate_receipt_but_mints_zero_credit():
    row = _row_without_candidate_discriminator_receipt()
    auth = gate.producer_auth.authenticate_after_generation(row)
    assert auth["pass"], auth
    row["discriminator_execution_receipts_evaluator_only"] = [
        deepcopy(auth["expected_discriminator_receipt"])
    ]
    result = gate.adjudicate(row)
    assert result["pass"], result
    assert result["canonical_dataset_admission"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
