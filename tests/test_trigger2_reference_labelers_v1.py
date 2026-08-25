from copy import deepcopy

import pytest

from tools.trigger2_reference_labelers_v1 import (
    D_resolve,
    LabelerError,
    U_d_test_order,
    U_update,
    f_salience_rank,
)


def branch(branch_id: str, salience: float = 0.0):
    return {
        "branch_id": branch_id,
        "v_semantic_value": f"value-{branch_id}",
        "K_context_predicate": "ctx",
        "E_plus": [],
        "E_minus": [],
        "F_falsifier": "disc-x",
        "T_validity_scope": "synthetic",
        "A_origin_provenance": "unit-test",
        "sigma_epistemic_status": "HYPOTHESIS",
        "salience": salience,
    }


def observation(**relations):
    return {
        "evidence_id": "ev-1",
        "independence_group": "ig-1",
        "provenance": "synthetic-unit-test",
        "relation_by_branch": relations,
    }


def test_update_retains_all_branches_and_is_replay_safe():
    before = [branch("a"), branch("b")]
    obs = observation(a="SUPPORT", b="COUNTER")
    after = U_update(before, obs)
    replay = U_update(after, obs)

    assert [b["branch_id"] for b in after] == ["a", "b"]
    assert len(after[0]["E_plus"]) == 1
    assert len(after[1]["E_minus"]) == 1
    assert replay == after
    assert before[0]["E_plus"] == []


def test_falsify_marks_but_does_not_delete_branch():
    after = U_update(
        [branch("a"), branch("b")],
        observation(a="NONE", b="FALSIFY"),
    )
    assert len(after) == 2
    assert after[1]["sigma_epistemic_status"] == "FALSIFIED"
    assert after[1]["falsified_by"] == "ev-1"


def test_resolve_requires_unique_explicit_discriminator():
    branches = [branch("a", salience=100), branch("b", salience=1)]
    assert D_resolve(branches, None)["resolution_status"] == "UNRESOLVED"
    assert D_resolve(branches, {"a": "PASS", "b": "UNKNOWN"})["resolution_status"] == "UNRESOLVED"

    resolved = D_resolve(branches, {"a": "PASS", "b": "FAIL"})
    assert resolved == {
        "resolution_status": "RESOLVED_BY_DISCRIMINATOR",
        "resolved_branch_id": "a",
        "reason": "ONE_PASS_ALL_OTHERS_FAIL",
    }


def test_resolution_is_branch_permutation_invariant():
    branches = [branch("a"), branch("b"), branch("c")]
    outcomes = {"a": "FAIL", "b": "PASS", "c": "FAIL"}
    left = D_resolve(branches, outcomes)
    right = D_resolve(list(reversed(branches)), outcomes)
    assert left == right
    assert left["resolved_branch_id"] == "b"


def test_discriminator_order_prefers_coverage_then_independence_then_cost():
    candidates = [
        {
            "candidate_id": "cheap-one-pair",
            "distinguishes_pairs": [["a", "b"]],
            "independent_of_existing": True,
            "cost": 1,
        },
        {
            "candidate_id": "all-pairs-dependent",
            "distinguishes_pairs": [["a", "b"], ["a", "c"], ["b", "c"]],
            "independent_of_existing": False,
            "cost": 0.1,
        },
        {
            "candidate_id": "all-pairs-independent",
            "distinguishes_pairs": [["a", "b"], ["a", "c"], ["b", "c"]],
            "independent_of_existing": True,
            "cost": 2,
        },
    ]
    ranked = U_d_test_order(["a", "b", "c"], candidates)
    assert [row["candidate_id"] for row in ranked] == [
        "all-pairs-independent",
        "all-pairs-dependent",
        "cheap-one-pair",
    ]
    assert all(row["ordering_only"] for row in ranked)


def test_salience_rank_cannot_emit_truth_or_resolution():
    ranked = f_salience_rank([branch("a", 0.1), branch("b", 9.0)])
    assert [r["branch_id"] for r in ranked] == ["b", "a"]
    assert all(r["truth_semantics"] == "NONE" for r in ranked)
    assert all("resolved_branch_id" not in r for r in ranked)


def test_fail_closed_on_partial_relation_map():
    with pytest.raises(LabelerError):
        U_update(
            [branch("a"), branch("b")],
            {
                "evidence_id": "ev",
                "independence_group": "ig",
                "provenance": "test",
                "relation_by_branch": {"a": "SUPPORT"},
            },
        )
