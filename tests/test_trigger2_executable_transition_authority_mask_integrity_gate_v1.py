from __future__ import annotations

import copy

from tools import trigger2_executable_transition_authority_mask_integrity_gate_v1 as gate


def _baseline():
    rows = gate.rows()
    report = gate.audit_all()
    assert report["pass"], report
    assert len(rows) >= 14
    assert report["positive_rows_admitted"] == 0
    assert report["accepted_dataset_tokens_minted"] == 0
    assert report["training_credit_minted"] == 0
    return rows


def _refresh_digest(envelope):
    envelope["candidate_digest_evaluator_only"] = gate.dg(envelope["candidate"])


def test_baseline_exact_recomputation_passes():
    for envelope in _baseline():
        result = gate.adjudicate(envelope)
        assert result["pass"], result
        assert result["second_semantic_authority_created"] is False


def test_model_target_admission_id_injection_fails_closed():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["model_target"]["admission_id"] = "self-minted"
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert any("FORBIDDEN_AUTHORITY_IN_MODEL_TARGET" in x for x in result["failures"])


def test_nested_model_target_lease_id_injection_fails_closed():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["model_target"]["result_payload"]["lease_id"] = "self-elected"
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert any("FORBIDDEN_AUTHORITY_IN_MODEL_TARGET" in x for x in result["failures"])


def test_bound_oracle_admission_mutation_fails_recomputation():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["model_input"]["bound_oracle_envelope"]["admission_id"] = "forged-admission"
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_bound_oracle_generation_mutation_fails_recomputation():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["model_input"]["bound_oracle_envelope"]["generation"] += 1
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_unknown_collapse_fails_recomputation():
    envelope = next(copy.deepcopy(row) for row in _baseline() if row["candidate"]["model_target"]["unknowns"])
    envelope["candidate"]["model_target"]["unknowns"] = []
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_db_proposal_self_commit_fails_recomputation():
    envelope = next(copy.deepcopy(row) for row in _baseline() if row["candidate"]["model_target"]["db_write_proposals"])
    envelope["candidate"]["model_target"]["db_write_proposals"][0]["commit"] = True
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_effect_proposal_self_execution_fails_recomputation():
    envelope = next(copy.deepcopy(row) for row in _baseline() if row["candidate"]["model_target"]["effect_request_candidates"])
    envelope["candidate"]["model_target"]["effect_request_candidates"][0]["executed"] = True
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_state_before_mutation_fails_recomputation():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["model_input"]["state_before"]["forged"] = True
    _refresh_digest(envelope)
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DOES_NOT_MATCH_RETAINED_DONOR_RECOMPUTATION" in result["failures"]


def test_source_snapshot_mutation_fails_closed():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["source_snapshot_evaluator_only"]["files"]["cognitive_process_abi"]["sha256"] = "00" * 32
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "SOURCE_SNAPSHOT_MISMATCH" in result["failures"]


def test_candidate_digest_detects_transport_mutation():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["candidate"]["status"] = "MUTATED_IN_TRANSIT"
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "CANDIDATE_DIGEST_MISMATCH" in result["failures"]


def test_credit_fences_cannot_be_promoted():
    envelope = copy.deepcopy(_baseline()[0])
    envelope["training_eligible"] = True
    envelope["accepted_dataset_tokens_minted"] = 1
    envelope["training_credit_minted"] = 1
    result = gate.adjudicate(envelope)
    assert not result["pass"]
    assert "TRAINING_ELIGIBILITY_MUST_REMAIN_FALSE" in result["failures"]
    assert "ACCEPTED_DATASET_TOKENS_MUST_REMAIN_ZERO" in result["failures"]
    assert "TRAINING_CREDIT_MUST_REMAIN_ZERO" in result["failures"]
