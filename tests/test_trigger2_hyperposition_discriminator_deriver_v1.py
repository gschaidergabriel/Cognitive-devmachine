from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "trigger2_hyperposition_discriminator_deriver_v1.py"
spec = importlib.util.spec_from_file_location("trigger2_hp_deriver", PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def _spec(predictions=None):
    return {
        "schema": mod.SPEC_SCHEMA,
        "test_id": "disc-1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "semantics": "EXACT_CATEGORICAL_MUTUALLY_EXCLUSIVE_EXHAUSTIVE",
        "live_branch_ids": ["b0", "b1", "b2"],
        "outcome_domain": ["RED", "BLUE", "GREEN"],
        "predicted_outcome_by_branch": predictions or {"b0": "RED", "b1": "BLUE", "b2": "GREEN"},
    }


def _obs(outcome="RED"):
    return {
        "schema": mod.OBS_SCHEMA,
        "test_id": "disc-1",
        "observed_outcome": outcome,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def test_unique_exact_outcome_derives_relations_and_resolution():
    result = mod.derive(_spec(), _obs("RED"))
    assert result["pass"] is True
    assert result["branch_relations"] == {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}
    assert result["decision_role_by_branch"] == {
        "b0": "DECISIVE_SUPPORT",
        "b1": "DECISIVE_CONTRADICTION",
        "b2": "DECISIVE_CONTRADICTION",
    }
    assert result["all_other_branches_explicitly_falsified"] is True
    assert result["resolution"]["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD"
    assert result["resolution"]["resolved_branch"] == "b0"
    assert result["derivation_receipt"]["training_credit_minted"] is False


def test_same_predicted_outcome_keeps_multiple_matching_branches_unresolved():
    s = _spec({"b0": "RED", "b1": "RED", "b2": "GREEN"})
    result = mod.derive(s, _obs("RED"))
    assert result["matching_branch_ids"] == ["b0", "b1"]
    assert result["branch_relations"]["b2"] == "FALSIFY"
    assert result["all_other_branches_explicitly_falsified"] is False
    assert result["resolution"]["status"] == "UNRESOLVED"


def test_unknown_prediction_is_not_silently_falsified():
    s = _spec({"b0": "RED", "b1": mod.UNKNOWN_PREDICTION, "b2": "GREEN"})
    result = mod.derive(s, _obs("RED"))
    assert result["branch_relations"]["b1"] == "NO_EFFECT"
    assert result["unknown_prediction_branch_ids"] == ["b1"]
    assert result["resolution"]["status"] == "UNRESOLVED"


def test_pair_separation_is_computed_from_predictions():
    s = _spec({"b0": "RED", "b1": "RED", "b2": "GREEN"})
    result = mod.derive(s, _obs("RED"))
    assert result["separates_branch_pairs"] == [["b0", "b2"], ["b1", "b2"]]


def test_caller_supplied_relation_metadata_fails_closed():
    s = _spec()
    s["branch_relations"] = {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}
    try:
        mod.derive(s, _obs())
    except mod.DerivationError as exc:
        assert str(exc) == "DERIVED_FIELDS_MUST_NOT_BE_CALLER_SUPPLIED"
    else:
        raise AssertionError("expected fail-closed rejection")


def test_observation_cannot_supply_resolved_branch():
    o = _obs()
    o["resolved_branch"] = "b0"
    try:
        mod.derive(_spec(), o)
    except mod.DerivationError as exc:
        assert str(exc) == "DERIVED_FIELDS_MUST_NOT_BE_OBSERVATION_SUPPLIED"
    else:
        raise AssertionError("expected fail-closed rejection")


def test_branch_order_permutation_is_semantically_equivariant():
    base = mod.derive(_spec(), _obs("RED"))
    s = _spec()
    s["live_branch_ids"] = ["b2", "b0", "b1"]
    s["predicted_outcome_by_branch"] = {"b2": "GREEN", "b0": "RED", "b1": "BLUE"}
    perm = mod.derive(s, _obs("RED"))
    assert base["branch_relations"] == perm["branch_relations"]
    assert base["decision_role_by_branch"] == perm["decision_role_by_branch"]
    assert base["resolution"] == perm["resolution"]
    assert base["separates_branch_pairs"] == perm["separates_branch_pairs"]


def test_receipt_changes_when_observed_outcome_changes():
    a = mod.derive(_spec(), _obs("RED"))
    b = mod.derive(_spec(), _obs("BLUE"))
    assert a["derivation_receipt"]["receipt_id"] != b["derivation_receipt"]["receipt_id"]
    assert a["derivation_receipt"]["observation_sha256"] != b["derivation_receipt"]["observation_sha256"]


def test_legacy_compatibility_does_not_fake_shared_decisive_role():
    legacy = mod.to_legacy_v1_inputs(
        _spec(),
        _obs("RED"),
        {"evidence_id": "e1", "provenance_ancestry_id": "synthetic:f1", "independence_group": "ig1"},
    )
    assert legacy["observation"]["evidence"]["decision_role"] == "NONDECISIVE"
    assert legacy["observation"]["branch_relations"] == {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}
    assert legacy["resolve_context"]["all_other_branches_explicitly_falsified"] is True
    assert legacy["training_credit_minted"] is False


def test_mutating_prediction_changes_derived_receipt():
    s1 = _spec()
    s2 = deepcopy(s1)
    s2["predicted_outcome_by_branch"]["b2"] = "BLUE"
    r1 = mod.derive(s1, _obs("RED"))
    r2 = mod.derive(s2, _obs("RED"))
    assert r1["derivation_receipt"]["spec_sha256"] != r2["derivation_receipt"]["spec_sha256"]
    assert r1["derivation_receipt"]["receipt_id"] != r2["derivation_receipt"]["receipt_id"]
