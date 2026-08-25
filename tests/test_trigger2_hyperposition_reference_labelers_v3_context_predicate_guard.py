from __future__ import annotations

from tools import trigger2_hyperposition_reference_labelers_v3 as lab


def _pred(op: str, value):
    return {"all": [{"key": "mode", "op": op, "value": value}]}


def test_in_and_not_in_require_explicit_json_array_operands():
    assert lab._validate_context_predicate(_pred("IN", ["A", "B"])) is True
    assert lab._validate_context_predicate(_pred("NOT_IN", ["A", "B"])) is True

    malformed = [
        "A",
        {"A": True},
        7,
        True,
        None,
    ]
    for value in malformed:
        assert lab._validate_context_predicate(_pred("IN", value)) is False
        assert lab._validate_context_predicate(_pred("NOT_IN", value)) is False


def test_public_derivation_rejects_malformed_membership_structurally_not_by_membership_exception():
    world = {
        "schema": lab.WORLD_SCHEMA,
        "world_id": "predicate-guard-world",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"mode": "A"},
        "tests": {
            "t": {
                "allowed_outcomes": ["YES", "NO"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
    }
    branches = []
    for branch_id, predicted in (("h_yes", "YES"), ("h_no", "NO")):
        branches.append({
            "branch_id": branch_id,
            "v": branch_id,
            "K": _pred("IN", "A"),
            "E_plus": [],
            "E_minus": [],
            "F": [],
            "T": {"scope": "synthetic"},
            "A": {"origin": "predicate-guard-test"},
            "sigma": "LIVE_UNRESOLVED",
            "projection_visibility": True,
            "predictions": {"t": predicted},
        })
    state = {
        "schema": lab.STATE_SCHEMA,
        "query_id": "q-predicate-guard",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": branches,
    }
    event = {
        "schema": lab.EVENT_SCHEMA,
        "event_id": "e-predicate-guard",
        "correlation_ancestry_id": "a-predicate-guard",
        "independence_group": "g-predicate-guard",
        "payload_key": "p-predicate-guard",
        "provenance": "synthetic:predicate-guard-test",
        "epistemic_type": "SYNTHETIC_PROOF",
        "test_id": "t",
        "observed_outcome": "YES",
        "independence_qualified": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }

    result = lab.derive_relations(world, state, event)
    assert result["pass"] is False
    assert result["failure"] == "BRANCH_K_INVALID"
    assert result["training_credit_minted"] is False
    assert result["canonical_truth_minted"] is False
    assert result["direct_effect_authority_minted"] is False


def test_nonmembership_predicates_retain_scalar_operand_semantics():
    assert lab._validate_context_predicate(_pred("EQ", "A")) is True
    assert lab._validate_context_predicate(_pred("NEQ", "A")) is True
