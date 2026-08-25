from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/trigger2_executable_transition_pilot_v2.py"


def _load():
    spec = importlib.util.spec_from_file_location("trigger2_executable_transition_pilot_v2_test", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _baseline(mod):
    rows = mod.rows()
    report = mod.audit(rows)
    assert report["pass"], report
    assert report["positive_rows_admitted"] == 0
    assert report["accepted_dataset_tokens_minted"] == 0
    assert report["training_credit_minted"] == 0
    return rows


def test_baseline_passes_and_preserves_full_v1_packet_scoring():
    mod = _load()
    rows = _baseline(mod)
    donor_rows = mod.donor.rows()
    assert len(rows) == len(donor_rows)
    assert len(rows) >= 14
    for successor, predecessor in zip(rows, donor_rows):
        assert mod.compose_full_packet(successor) == predecessor["target"]


def test_model_target_contains_no_deterministic_authority_envelope_keys():
    mod = _load()
    for row in _baseline(mod):
        assert mod._forbidden_path(row["expected_model_target"]) is None
        assert row["model_supervision_fields"] == ["expected_model_target"]
        assert row["evaluator_only_fields_are_loss_masked"] is True


def test_injected_admission_id_in_model_target_fails_closed_before_composition():
    mod = _load()
    row = _baseline(mod)[0]
    bad = copy.deepcopy(row["expected_model_target"])
    bad["admission_id"] = "model-self-minted-admission"
    with pytest.raises(ValueError, match="MODEL_TARGET_AUTHORITY_FIELD"):
        mod.compose_full_packet(row, bad)


def test_injected_lease_id_nested_in_model_target_fails_closed():
    mod = _load()
    row = _baseline(mod)[0]
    bad = copy.deepcopy(row["expected_model_target"])
    bad["result_payload"]["lease_id"] = "self-elected-coordinator"
    with pytest.raises(ValueError, match="MODEL_TARGET_AUTHORITY_FIELD"):
        mod.compose_full_packet(row, bad)


def test_mutated_oracle_admission_identity_breaks_expected_packet_digest():
    mod = _load()
    rows = _baseline(mod)
    bad_rows = copy.deepcopy(rows)
    bad_rows[0]["oracle_context_evaluator_only"]["admission_id"] = "stale-or-forged-admission"
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("FULL_PACKET_DIGEST_MISMATCH:") for x in report["failures"])


def test_unknown_collapse_fails_closed():
    mod = _load()
    rows = _baseline(mod)
    idx = next(i for i, row in enumerate(rows) if row["required_unknowns_evaluator_only"])
    bad_rows = copy.deepcopy(rows)
    bad_rows[idx]["expected_model_target"]["unknowns"] = []
    bad_rows[idx]["expected_model_target_digest_evaluator_only"] = mod.dg(bad_rows[idx]["expected_model_target"])
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("UNKNOWN_COLLAPSE:") for x in report["failures"])


def test_db_proposal_cannot_self_commit():
    mod = _load()
    rows = _baseline(mod)
    idx = next(i for i, row in enumerate(rows) if row["expected_model_target"]["db_write_proposals"])
    bad_rows = copy.deepcopy(rows)
    bad_rows[idx]["expected_model_target"]["db_write_proposals"][0]["commit"] = True
    bad_rows[idx]["expected_model_target_digest_evaluator_only"] = mod.dg(bad_rows[idx]["expected_model_target"])
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("DB_AUTHORITY_SELF_MINT:") for x in report["failures"])


def test_effect_proposal_cannot_self_execute():
    mod = _load()
    rows = _baseline(mod)
    idx = next(i for i, row in enumerate(rows) if row["expected_model_target"]["effect_request_candidates"])
    bad_rows = copy.deepcopy(rows)
    bad_rows[idx]["expected_model_target"]["effect_request_candidates"][0]["executed"] = True
    bad_rows[idx]["expected_model_target_digest_evaluator_only"] = mod.dg(bad_rows[idx]["expected_model_target"])
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("EFFECT_AUTHORITY_SELF_MINT:") for x in report["failures"])


def test_source_identity_mutation_fails_closed():
    mod = _load()
    rows = _baseline(mod)
    bad_rows = copy.deepcopy(rows)
    bad_rows[0]["source_bindings_evaluator_only"]["files"]["abi"]["sha256"] = "00" * 32
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("SOURCE_BINDING_MISMATCH:") for x in report["failures"])


def test_state_before_mutation_without_digest_update_fails_closed():
    mod = _load()
    rows = _baseline(mod)
    bad_rows = copy.deepcopy(rows)
    bad_rows[0]["state_before"]["forged"] = True
    report = mod.audit(bad_rows)
    assert not report["pass"]
    assert any(x.startswith("STATE_BEFORE_DIGEST_MISMATCH:") for x in report["failures"])


def test_split_and_credit_remain_explicitly_nonpromoting():
    mod = _load()
    for row in _baseline(mod):
        assert row["split_evaluator_only"] == "CANDIDATE_UNSPLIT"
        assert row["training_eligible"] is False
        assert row["accepted_dataset_tokens_minted"] == 0
        assert row["training_credit_minted"] == 0
