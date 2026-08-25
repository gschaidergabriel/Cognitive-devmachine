from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

from tools import trigger2_hyperposition_state_history_generation_bound_gate_v4 as full_gate
from tools import trigger2_hyperposition_state_history_producer_bound_gate_v2 as gate
from tools import trigger2_trusted_discriminator_producer_v1 as producer


def _load_existing_fixture_module():
    path = Path(__file__).resolve().with_name("test_trigger2_generation_bound_hyperposition_gate_v2.py")
    spec = importlib.util.spec_from_file_location("trigger2_existing_generation_bound_fixture", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row():
    fixture = _load_existing_fixture_module()
    row = fixture._row()
    result = producer.produce(
        row["generation_case_id_evaluator_only"],
        row["formal_task_world_evaluator_only"],
        row["hyperposition_state_before_evaluator_only"],
        row["synthetic_test_event_evaluator_only"],
    )
    assert result["pass"], result
    row["discriminator_execution_receipts_evaluator_only"] = [deepcopy(result["receipt"])]
    return row


def test_T2_SHPG_A02_producer_bound_happy_path_is_candidate_only():
    result = gate.adjudicate(_row())
    assert result["pass"], result
    assert result["row_receipt_exact_match"] is True
    assert result["row_carried_admissible_authoritative"] is False
    assert result["row_carried_executed_authoritative"] is False
    assert result["row_carried_execution_receipt_id_authoritative"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0
    assert result["runtime_credit_minted"] == 0


def test_T2_SHPG_A02_fake_executed_receipt_id_rewrite_rejected():
    row = _row()
    row["discriminator_execution_receipts_evaluator_only"][0]["execution_receipt_id"] = "exec:forged-but-nonempty"
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert "ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_OUTPUT" in result["failures"]


def test_T2_SHPG_A02_coherent_receipt_rewrite_rejected_even_after_rehash():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["pre_state_sha256"] = "0" * 64
    core = deepcopy(receipt)
    core.pop("execution_receipt_id", None)
    receipt["execution_receipt_id"] = "t2disc:v2:" + producer._digest(core)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert "ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_OUTPUT" in result["failures"]


def test_T2_SHPG_A02_formal_discriminator_spec_rewrite_rejected_by_authority():
    row = _row()
    row["formal_task_world_evaluator_only"]["tests"]["db_probe"]["risk_rank"] = 9
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("DISCRIMINATOR_FORMAL_SPEC_DIGEST_MISMATCH" in x for x in result["failures"])


def test_T2_SHPG_A02_producer_source_sha_authority_rewrite_rejected(monkeypatch):
    row = _row()
    original = gate.producer._authority

    def forged_authority():
        authority = deepcopy(original())
        authority["producer"]["source_sha256"] = "0" * 64
        return authority

    monkeypatch.setattr(gate.producer, "_authority", forged_authority)
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert any("DISCRIMINATOR_PRODUCER_SOURCE_SHA_MISMATCH" in x for x in result["failures"])


def test_T2_SHPG_A02_nonempty_history_remains_fail_closed():
    row = _row()
    row["synthetic_event_history_evaluator_only"] = [deepcopy(row["synthetic_test_event_evaluator_only"])]
    result = gate.adjudicate(row)
    assert not result["pass"]
    assert "PRODUCER_BOUND_V2_ONLY_AUTHORIZES_EMPTY_HISTORY_PILOT" in result["failures"]


def test_T2_SHPG_A02_full_generation_epistemic_producer_chain_passes_source_candidate():
    result = full_gate.adjudicate(_row())
    assert result["pass"], result
    assert result["bounded_empty_history_synthetic_pilot_source_closure"] is True
    assert result["positive_D_E_promotion_ready"] is False
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0


def test_T2_SHPG_A02_full_chain_rejects_coherent_receipt_forgery():
    row = _row()
    receipt = row["discriminator_execution_receipts_evaluator_only"][0]
    receipt["live_branch_projection_sha256"] = "f" * 64
    core = deepcopy(receipt)
    core.pop("execution_receipt_id", None)
    receipt["execution_receipt_id"] = "t2disc:v2:" + producer._digest(core)
    result = full_gate.adjudicate(row)
    assert not result["pass"]
    assert any("ROW_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_OUTPUT" in x for x in result["failures"])
