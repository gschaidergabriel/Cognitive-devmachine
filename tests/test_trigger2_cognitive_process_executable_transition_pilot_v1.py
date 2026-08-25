from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger2_cognitive_process_executable_transition_pilot_v1.py"
spec = importlib.util.spec_from_file_location("trigger2_exec_transition_v1", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def _rows_by_id():
    return {row["process_id_evaluator_only"]: row for row in mod.build_pilot_rows()}


def test_pilot_spans_exact_current_trainable_processes_and_admits_nothing():
    rows = mod.build_pilot_rows()
    assert len(rows) == 16
    assert {row["process_id_evaluator_only"] for row in rows} == mod.EXPECTED_TRAINABLE_PROCESS_IDS
    assert all(row["accepted_for_training"] is False for row in rows)
    assert all(row["accepted_dataset_tokens"] == 0 for row in rows)
    s = mod.summary(rows)
    assert s["status"] == "PASS_SOURCE_ONLY_QUARANTINED_PILOT"
    assert s["accepted_positive_rows"] == 0
    assert s["accepted_dataset_tokens"] == 0
    assert s["training_credit"] == 0


def test_targets_are_concrete_transitions_not_rule_narration():
    for row in mod.build_pilot_rows():
        target = row["target"]
        assert "rule" not in target
        assert "emit" not in target
        assert set(target) == {"schema", "result_payload", "result_packet", "state_after"}
        process = mod._process_map()[row["process_id_evaluator_only"]]
        assert set(target["result_payload"]) == set(process["outputs"])
        verdict = mod.adjudicate(row, copy.deepcopy(target))
        assert verdict["pass"], verdict


def test_deterministic_and_store_authority_processes_are_not_model_targets():
    rows = mod.build_pilot_rows()
    ids = {row["process_id_evaluator_only"] for row in rows}
    assert {"ZECP01", "ZECP02", "ZECP11", "ZECP17"}.isdisjoint(ids)


def test_wrong_oracle_bound_identity_fails_closed():
    row = _rows_by_id()["ZECP08"]
    candidate = copy.deepcopy(row["target"])
    candidate["result_packet"]["admission_id"] = "adm-model-minted"
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "BOUND_IDENTITY_NOT_COPIED:admission_id" in verdict["failures"]


def test_model_cannot_mint_authority_key():
    row = _rows_by_id()["ZECP15"]
    candidate = copy.deepcopy(row["target"])
    candidate["result_payload"]["canonical_truth_authority"] = "MODEL"
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert any(f.startswith("MODEL_TARGET_AUTHORITY_SMUGGLING:") for f in verdict["failures"])


def test_effect_proposal_cannot_become_effect_receipt_or_executed_effect():
    row = _rows_by_id()["ZECP16"]
    candidate = copy.deepcopy(row["target"])
    candidate["result_packet"]["result_class"] = "EFFECT_RECEIPT"
    candidate["state_after"]["effect_execution_status"] = "EXECUTED"
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "MODEL_TARGET_RESULT_CLASS_FORBIDDEN" in verdict["failures"]
    assert "EFFECT_CANDIDATE_CANNOT_IMPLY_EXECUTION" in verdict["failures"]


def test_majority_does_not_resolve_hyperposition():
    row = _rows_by_id()["ZECP07"]
    candidate = copy.deepcopy(row["target"])
    candidate["result_payload"]["uncertainty_readout"]["resolved"] = True
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "MAJORITY_CANNOT_RESOLVE_HYPERPOSITION" in verdict["failures"]


def test_jspace_unknown_and_zero_credit_are_load_bearing():
    row = _rows_by_id()["ZECP20"]
    candidate = copy.deepcopy(row["target"])
    candidate["result_payload"]["credit_scope"]["causal"] = 1
    candidate["result_packet"]["unknowns"] = []
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "JSPACE_SOURCE_PILOT_CANNOT_MINT_CAUSAL_CREDIT" in verdict["failures"]
    assert "JSPACE_CAUSALITY_UNKNOWN_MUST_BE_PRESERVED" in verdict["failures"]


def test_state_after_exact_semantics_fail_on_stale_epoch_relabel():
    row = _rows_by_id()["ZECP09"]
    candidate = copy.deepcopy(row["target"])
    candidate["state_after"]["source_workspace_epoch"] = 41
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "STATE_AFTER_SEMANTIC_MISMATCH" in verdict["failures"]


def test_claycode_roundtrip_identity_is_recorded_for_each_target():
    for row in mod.build_pilot_rows():
        ev = row["evaluator_only"]
        assert len(ev["claycode_packet_digest"]) == 64
        assert len(ev["claycode_source_sha256"]) == 64
        assert len(ev["claycode_semantic_hash"]) == 64
        assert len(ev["claycode_grammar_sha256"]) == 64
        assert mod.adjudicate(row, copy.deepcopy(row["target"]))["pass"]


def test_meta_rule_equivalent_without_concrete_transition_fails():
    row = _rows_by_id()["ZECP03"]
    candidate = {
        "schema": mod.TARGET_SCHEMA,
        "rule": "retrieve exact durable facts and preserve UNKNOWN",
        "emit": ["working_state_candidate", "missing_state_questions"],
    }
    verdict = mod.adjudicate(row, candidate)
    assert not verdict["pass"]
    assert "RESULT_PACKET_REQUIRED" in verdict["failures"]
    assert "RESULT_PAYLOAD_REQUIRED" in verdict["failures"]
    assert "STATE_AFTER_REQUIRED" in verdict["failures"]
