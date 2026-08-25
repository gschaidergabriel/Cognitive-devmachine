from __future__ import annotations

from copy import deepcopy

from tools import trigger2_discriminator_producer_auth_gate_v1 as gate


WORLD_SCHEMA = "XENO_HYPERPOSITION_FORMAL_TASK_WORLD/v1"
STATE_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_STATE/v3"
EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVENT/v3"


def _branch(branch_id: str, value: str, prediction: str):
    return {
        "branch_id": branch_id,
        "v": value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": "A02_TEST"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"db_probe": prediction},
    }


def _row():
    world = {
        "schema": WORLD_SCHEMA,
        "world_id": "t2gp:world:db-match:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": "synthetic_generation_provenance_pilot"},
        "tests": {
            "db_probe": {
                "allowed_outcomes": ["MATCH", "MISSING"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
        "event_dependence_registry": {
            "schema": "XENO_SYNTHETIC_EVENT_DEPENDENCE_REGISTRY/v1",
            "events": {},
        },
    }
    state = {
        "schema": STATE_SCHEMA,
        "query_id": "t2gp:query:db-match:v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            _branch("db-backed", "USE_PROVENANCE_BOUND_DATABASE_STATE", "MATCH"),
            _branch("guess", "RECONSTRUCT_DURABLE_STATE_FROM_MODEL_GUESS", "MISSING"),
        ],
    }
    event = {
        "schema": EVENT_SCHEMA,
        "event_id": "t2gp:event:db-match:v1",
        "correlation_ancestry_id": "t2gp:ancestry:db-match:v1",
        "independence_group": "t2gp:independence:db-match:v1",
        "payload_key": "t2gp:payload:db-match:v1",
        "provenance": "CLAY_TRIGGER2_TRUSTED_HYPERPOSITION_PILOT_GENERATOR/v1:T2_GP_PILOT_DB_MATCH_V1",
        "epistemic_type": "SYNTHETIC_PROOF",
        "test_id": "db_probe",
        "observed_outcome": "MATCH",
        "independence_qualified": False,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    return {
        "generation_case_id_evaluator_only": "T2_GP_PILOT_DB_MATCH_V1",
        "formal_task_world_evaluator_only": world,
        "hyperposition_state_before_evaluator_only": deepcopy(state),
        "hyperposition_genesis_state_evaluator_only": deepcopy(state),
        "synthetic_event_history_evaluator_only": [],
        "synthetic_test_event_evaluator_only": event,
        "discriminator_execution_receipts_evaluator_only": [],
    }


def _expected_receipt(row):
    first = gate.authenticate_after_generation(deepcopy(row))
    assert first["pass"], first
    return deepcopy(first["expected_discriminator_receipt"])


def test_a02_happy_path_derives_execution_from_repository_bound_producer():
    result = gate.authenticate_after_generation(_row())
    assert result["pass"], result
    assert result["repository_authority_resolved"] is True
    assert result["producer_invoked"] is True
    assert result["row_carried_admissible_is_authority"] is False
    assert result["row_carried_executed_is_authority"] is False
    receipt = result["expected_discriminator_receipt"]
    assert receipt["admissible"] is True
    assert receipt["executed"] is True
    assert receipt["execution_receipt_id"].startswith("t2disc:")
    assert receipt["producer_auth"]["producer_invocation_id"].startswith("t2disc-invoke:")
    assert result["accepted_dataset_tokens_minted"] == 0
    assert result["training_credit_minted"] == 0


def test_T2_SHPG_A02_FAKE_EXECUTED_rejected():
    row = _row()
    fake = _expected_receipt(row)
    fake["admissible"] = True
    fake["executed"] = True
    fake["execution_receipt_id"] = "forged:nonempty-but-not-producer-derived"
    row["discriminator_execution_receipts_evaluator_only"] = [fake]
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER" in result["failures"]


def test_T2_SHPG_A02_COHERENT_RECEIPT_REWRITE_rejected():
    row = _row()
    fake = _expected_receipt(row)
    fake["producer_auth"]["policy_id"] = "forged-policy"
    fake["producer_auth"]["producer_result_jcs_sha256"] = "f" * 64
    fake["execution_receipt_id"] = "t2disc:" + gate._jcs_sha256({
        "forged_producer_auth": fake["producer_auth"],
        "observed_outcome": fake["observed_outcome"],
        "separated_live_pairs": fake["separated_live_pairs"],
        "separates_all_live_pairs": fake["separates_all_live_pairs"],
    })
    row["discriminator_execution_receipts_evaluator_only"] = [fake]
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER" in result["failures"]


def test_T2_SHPG_A02_PRODUCER_PATH_OR_SHA_SWAP_rejected(monkeypatch):
    row = _row()
    original = gate._authority

    def mutated_authority():
        auth = deepcopy(original())
        auth["producer"]["source_sha256"] = "0" * 64
        return auth

    monkeypatch.setattr(gate, "_authority", mutated_authority)
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_PRODUCER_SOURCE_IDENTITY_MISMATCH" in result["failures"]


def test_T2_SHPG_A02_POLICY_SWAP_rejected(monkeypatch):
    row = _row()
    original = gate._authority

    def mutated_authority():
        auth = deepcopy(original())
        auth["allowed_cases"]["T2_GP_PILOT_DB_MATCH_V1"]["policy_id"] = "forged-policy"
        return auth

    monkeypatch.setattr(gate, "_authority", mutated_authority)
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_POLICY_AUTHORITY_MISMATCH" in result["failures"]


def test_T2_SHPG_A02_PRESTATE_REWRITE_rejected_against_original_receipt():
    row = _row()
    original_receipt = _expected_receipt(row)
    row["hyperposition_state_before_evaluator_only"]["branches"][0]["T"]["nonsemantic_note"] = "rewritten"
    row["hyperposition_genesis_state_evaluator_only"] = deepcopy(row["hyperposition_state_before_evaluator_only"])
    row["discriminator_execution_receipts_evaluator_only"] = [original_receipt]
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER" in result["failures"]


def test_T2_SHPG_A02_WORLD_SCOPED_EVENT_REWRITE_rejected():
    row = _row()
    row["formal_task_world_evaluator_only"]["world_id"] = "t2gp:world:other:v1"
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_POLICY_WORLD_ID_MISMATCH" in result["failures"]


def test_T2_SHPG_A02_COVERAGE_REWRITE_rejected():
    row = _row()
    fake = _expected_receipt(row)
    fake["separated_live_pairs"] = fake["separated_live_pairs"] + 1
    row["discriminator_execution_receipts_evaluator_only"] = [fake]
    result = gate.authenticate_after_generation(row)
    assert not result["pass"]
    assert "DISCRIMINATOR_RECEIPT_NOT_EXACTLY_RECOMPUTED_FROM_TRUSTED_PRODUCER" in result["failures"]
