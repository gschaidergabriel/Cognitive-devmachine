from copy import deepcopy
import pytest

from tools.trigger2_semantic_hyperposition_reference_labelers_v2 import (
    D_resolve, LabelerError, U_d_test_order, U_update,
    derive_prediction, discriminator_pair_coverage, f_salience_rank,
)


def branch(bid, color, shape="round", salience=0.0):
    return {
        "branch_id": bid,
        "v_semantic_value": f"hypothesis-{bid}",
        "K_context_predicate": "ctx",
        "E_plus": [], "E_minus": [],
        "F_falsifier": "attribute mismatch",
        "T_validity_scope": "synthetic",
        "A_origin_provenance": "unit-test",
        "sigma_epistemic_status": "HYPOTHESIS",
        "task_world": {"schema": "SYNTHETIC_ATTRIBUTE_WORLD/v1", "attributes": {"color": color, "shape": shape}},
        "salience": salience,
    }


def disc(attribute):
    return {"discriminator_id": f"d-{attribute}", "kind": "ATTRIBUTE_READ", "attribute": attribute}


def obs(outcome="red", evidence_id="ev-1", group="ig-1", attribute="color"):
    return {
        "evidence_id": evidence_id,
        "discriminator": disc(attribute),
        "observed_outcome": outcome,
        "independence_group": group,
        "provenance": "synthetic-unit-test",
    }


def test_prediction_and_update_are_derived_not_caller_labeled():
    branches = [branch("a", "red"), branch("b", "blue")]
    assert derive_prediction(branches[0], disc("color")) == "red"
    after = U_update(branches, obs("red"))
    assert after[0]["E_plus"][0]["relation"] == "SUPPORT"
    assert after[1]["E_minus"][0]["relation"] == "FALSIFY"
    assert after[1]["sigma_epistemic_status"] == "FALSIFIED"
    assert len(after) == 2


def test_resolution_follows_derived_updates_and_is_permutation_invariant():
    branches = [branch("a", "red"), branch("b", "blue"), branch("c", "green")]
    left = D_resolve(U_update(branches, obs("green")))
    right = D_resolve(U_update(list(reversed(branches)), obs("green")))
    assert left == right
    assert left["resolved_branch_id"] == "c"


def test_all_falsified_is_contradiction_not_forced_choice():
    result = D_resolve(U_update([branch("a", "red"), branch("b", "blue")], obs("yellow")))
    assert result["resolution_status"] == "UNRESOLVED_CONTRADICTION"
    assert result["resolved_branch_id"] is None


def test_nondiscriminating_observation_retains_multiple_live_branches():
    branches = [branch("a", "red", shape="round"), branch("b", "blue", shape="round")]
    after = U_update(branches, obs("round", attribute="shape"))
    assert D_resolve(after)["resolution_status"] == "UNRESOLVED"
    assert all(b["sigma_epistemic_status"] == "SUPPORTED" for b in after)


def test_inadmissible_discriminator_fails_before_resolution():
    with pytest.raises(LabelerError):
        U_update([branch("a", "red"), branch("b", "blue")], obs("x", attribute="missing"))


def test_same_evidence_id_changed_identity_fails_closed():
    after = U_update([branch("a", "red"), branch("b", "blue")], obs("red"))
    with pytest.raises(LabelerError):
        U_update(after, obs("blue", evidence_id="ev-1"))


def test_same_independence_group_different_observation_fails_closed():
    after = U_update([branch("a", "red"), branch("b", "blue")], obs("red", evidence_id="ev-1", group="ig-x"))
    with pytest.raises(LabelerError):
        U_update(after, obs("blue", evidence_id="ev-2", group="ig-x"))


def test_exact_replay_is_idempotent():
    before = [branch("a", "red"), branch("b", "blue")]
    once = U_update(before, obs("red"))
    twice = U_update(once, obs("red"))
    assert twice == once


def test_pair_coverage_is_derived_not_caller_asserted():
    branches = [branch("a", "red", "round"), branch("b", "blue", "round"), branch("c", "green", "square")]
    assert discriminator_pair_coverage(branches, disc("color")) == 3
    assert discriminator_pair_coverage(branches, disc("shape")) == 2
    ranked = U_d_test_order(branches, [
        {"candidate_id": "shape", "discriminator": disc("shape"), "independent_of_existing": True, "cost": 0.1},
        {"candidate_id": "color", "discriminator": disc("color"), "independent_of_existing": False, "cost": 9.0},
    ])
    assert [x["candidate_id"] for x in ranked] == ["color", "shape"]
    assert all(x["coverage_derived"] for x in ranked)


def test_salience_cannot_resolve_or_emit_truth():
    ranked = f_salience_rank([branch("a", "red", salience=100), branch("b", "blue", salience=1)])
    assert [x["branch_id"] for x in ranked] == ["a", "b"]
    assert all(x["truth_semantics"] == "NONE" for x in ranked)
    assert all("resolved_branch_id" not in x for x in ranked)


def test_task_world_mutation_changes_derived_label_not_metadata():
    base = [branch("a", "red"), branch("b", "blue")]
    mutated = deepcopy(base)
    mutated[0]["task_world"]["attributes"]["color"] = "black"
    assert U_update(base, obs("red"))[0]["E_plus"][0]["relation"] == "SUPPORT"
    assert U_update(mutated, obs("red"))[0]["E_minus"][0]["relation"] == "FALSIFY"
