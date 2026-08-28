from __future__ import annotations

from tools import trigger2_hyperposition_causal_label_chain_v1 as chain
from tools import trigger2_hyperposition_derivation_bound_gate_v1 as gate


def branch(bid, value):
    return {
        "schema": chain.lab.BRANCH_SCHEMA,
        "branch_id": bid,
        "v_semantic_value": value,
        "K_context_predicate": "ctx",
        "E_plus": [],
        "E_minus": [],
        "F_falsifier": "mismatch",
        "T_validity_scope": "episode",
        "A_origin_provenance": "synthetic",
        "sigma_epistemic_status": "HYPOTHESIS",
        "projection_visibility": "VISIBLE",
        "validity": "LIVE",
    }


def row():
    world = {
        "schema": chain.WORLD_SCHEMA,
        "world_id": "w",
        "branches": [
            {"branch_id": "A", "semantic_value": "ALT_A", "predicted_outcomes": {"t": "x"}},
            {"branch_id": "B", "semantic_value": "ALT_B", "predicted_outcomes": {"t": "y"}},
        ],
        "tests": [{"test_id": "t", "mode": "EXACT_FOR_SCOPE", "admissible": True, "outcome_domain": ["x", "y"]}],
    }
    event = {
        "schema": chain.EVENT_SCHEMA,
        "event_id": "e",
        "world_id": "w",
        "test_id": "t",
        "execution_status": "EXECUTED_SYNTHETIC",
        "observed_outcome": "x",
        "causal_source_id": "src",
        "independence_group": "ig",
        "payload_key": "pk",
    }
    before = [branch("A", "ALT_A"), branch("B", "ALT_B")]
    target = chain.derive_label_chain(before, world, event)
    return {
        "schema": gate.ROW_SCHEMA,
        "training_eligible": False,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "model_visible_fields": ["prompt"],
        "prompt": "Choose next candidate state from the visible semantic episode.",
        "source_binding": gate.current_source_binding(),
        "formal_task_world_evaluator_only": world,
        "synthetic_test_event_evaluator_only": event,
        "hyperposition_state_before_evaluator_only": before,
        "causal_label_chain_target_evaluator_only": target,
    }


def test_exact_row_passes_only_pre_admission():
    out = gate.adjudicate(row())
    assert out["pass"] is True
    assert out["canonical_dataset_admission"] is False
    assert out["training_credit_minted"] == 0


def test_forged_hash_fails():
    r = row()
    r["source_binding"]["deriver_sha256"] = "0" * 64
    assert "SOURCE_BINDING_MISMATCH_ACTUAL_LOCAL_BYTES" in gate.adjudicate(r)["failures"]


def test_stale_target_after_observed_outcome_mutation_fails():
    r = row()
    r["synthetic_test_event_evaluator_only"]["observed_outcome"] = "y"
    assert "CLAIMED_TARGET_DOES_NOT_MATCH_RECOMPUTED_CAUSAL_CHAIN" in gate.adjudicate(r)["failures"]


def test_mutated_claimed_branch_relation_fails():
    r = row()
    r["causal_label_chain_target_evaluator_only"]["relation_derivation_receipt"]["branch_relations"]["A"] = "NO_EFFECT"
    assert "CLAIMED_TARGET_DOES_NOT_MATCH_RECOMPUTED_CAUSAL_CHAIN" in gate.adjudicate(r)["failures"]


def test_evaluator_metadata_cannot_be_model_visible():
    r = row()
    r["model_visible_fields"] = ["prompt", "formal_task_world_evaluator_only"]
    assert "ONLY_PROMPT_MAY_BE_MODEL_VISIBLE" in gate.adjudicate(r)["failures"]


def test_training_eligible_true_fails_closed():
    r = row()
    r["training_eligible"] = True
    assert "TRAINING_ELIGIBLE_MUST_REMAIN_FALSE_AT_PRE_ADMISSION_GATE" in gate.adjudicate(r)["failures"]
