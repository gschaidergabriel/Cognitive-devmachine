from __future__ import annotations

import pytest

from tools.trigger2_cognitive_process_executable_transition_pilot_v2 import (
    DETERMINISTIC_OR_STORE_ONLY,
    OUTPUT_KEYS,
    TRAINABLE_PROCESS_IDS,
    make_row,
    rows,
    run,
    validate_row,
)


def by_pid(pid: str):
    return next(r for r in rows() if r["process_id_evaluator_only"] == pid)


def test_pilot_spans_all_trainable_processes_and_excludes_authority_processes():
    r = run()
    assert r["pass"] is True
    assert r["row_count"] == len(TRAINABLE_PROCESS_IDS) == 16
    assert r["all_trainable_processes_covered"] is True
    assert set(r["covered_process_ids"]).isdisjoint(DETERMINISTIC_OR_STORE_ONLY)
    assert r["accepted_dataset_tokens"] == 0
    assert r["training_credit"] == 0


def test_targets_are_instantiated_deltas_not_meta_rule_narration():
    for row in rows():
        target = row["supervision_target"]
        assert "rule" not in target
        assert "emit" not in target
        payload = target["candidate_payload"]
        assert OUTPUT_KEYS[row["process_id_evaluator_only"]].issubset(payload)


def test_oracle_packet_copies_bound_identity_instead_of_model_minting_it():
    for row in rows():
        w = row["model_visible"]["work_packet"]
        p = row["oracle_evaluator_only"]["result_packet"]
        assert p["causal_event_id"] == w["causal_event_id"]
        assert p["admission_id"] == w["admission_id"]
        assert p["generation"] == w["generation"]
        assert p["work_id"] == w["work_id"]
        assert p["process_id"] == w["process_id"]


def test_rule_only_substitution_fails_machine_adjudication():
    row = by_pid("ZECP06")
    row["supervision_target"]["candidate_payload"] = {"rule": "replan correctly"}
    with pytest.raises(ValueError, match="EXECUTABLE_OUTPUT_FIELDS_MISSING"):
        validate_row(row)


def test_model_cannot_self_mint_canonical_truth():
    row = by_pid("ZECP08")
    row["supervision_target"]["candidate_payload"]["canonical_truth"] = True
    with pytest.raises(ValueError, match="MODEL_AUTHORITY_SMUGGLING"):
        validate_row(row)


def test_non_effect_process_cannot_emit_effect_candidate():
    row = by_pid("ZECP08")
    row["supervision_target"]["effect_request_candidates"] = [{"tool": "x"}]
    with pytest.raises(ValueError, match="UNEXPECTED_EFFECT_CANDIDATE"):
        validate_row(row)


def test_effect_proposal_process_must_remain_candidate_only():
    row = by_pid("ZECP16")
    row["supervision_target"]["effect_request_candidates"] = []
    with pytest.raises(ValueError, match="ZECP16_EFFECT_CANDIDATE_REQUIRED"):
        validate_row(row)


def test_non_memory_process_cannot_emit_db_write_proposal():
    row = by_pid("ZECP07")
    row["supervision_target"]["db_write_proposals"] = [{"target": "canonical"}]
    with pytest.raises(ValueError, match="UNEXPECTED_DB_WRITE_PROPOSAL"):
        validate_row(row)


def test_jspace_pilot_is_measurement_unknown_not_positive_causal_label():
    row = by_pid("ZECP20")
    target = row["supervision_target"]
    assert target["result_class"] == "MEASUREMENT"
    assert target["candidate_payload"]["credit_scope"] == "NO_CAUSAL_JSPACE_CREDIT"
    assert "causal_effect" in target["unknowns"]
    target["candidate_payload"]["credit_scope"] = "CAUSAL_JSPACE_CREDIT"
    with pytest.raises(ValueError, match="ZECP20_CAUSAL_CREDIT_FORBIDDEN"):
        validate_row(row)


def test_semantic_target_tamper_breaks_stored_oracle_identity():
    row = by_pid("ZECP03")
    row["supervision_target"]["expected_state_after"]["resource_ceiling"] = "INVENTED"
    with pytest.raises(ValueError, match="ORACLE_RESULT_PACKET_MISMATCH"):
        validate_row(row)


def test_result_packet_digest_tamper_fails():
    row = by_pid("ZECP04")
    row["oracle_evaluator_only"]["result_packet"]["result_digest"] = "0" * 64
    with pytest.raises(ValueError, match="ORACLE_RESULT_PACKET_MISMATCH"):
        validate_row(row)


def test_claycode_semantic_identity_tamper_fails():
    row = by_pid("ZECP19")
    row["oracle_evaluator_only"]["claycode_roundtrip"]["clay_semantic_hash"] = "0" * 64
    with pytest.raises(ValueError, match="CLAYCODE_ORACLE_IDENTITY_MISMATCH"):
        validate_row(row)


def test_all_rows_remain_quarantined_not_training_admitted():
    for row in rows():
        assert row["training_eligible"] is False
        assert row["accepted_dataset_tokens"] == 0
        assert row["credit"]["training_row_admitted"] == 0
        assert row["credit"]["training"] == 0


def test_deterministic_boundary_process_cannot_be_smuggled_by_process_id_mutation():
    row = make_row("ZECP03", 1)
    row["process_id_evaluator_only"] = "ZECP17"
    with pytest.raises(ValueError, match="PROCESS_NOT_TRAINABLE_PILOT"):
        validate_row(row)
