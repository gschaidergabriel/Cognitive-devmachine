import copy

import pytest

from tools.trigger2_hyperposition_reference_labelers_v2 import (
    apply_resolution,
    d_resolve,
    f_salience_order,
    u_state,
    u_test_order,
)


def branch(branch_id, *, K="APPLIES", sigma="LIVE_UNRESOLVED", v=None, T="scope"):
    return {
        "branch_id": branch_id,
        "v": v or branch_id,
        "K": K,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": T,
        "A": {"src": branch_id},
        "sigma": sigma,
        "projection_visibility": "VISIBLE",
    }


def observation(relation, targets, *, event="e1", ancestry="a1", independent=True):
    return {
        "evidence_event_id": event,
        "correlation_ancestry_id": ancestry,
        "independence_group": "g1",
        "provenance": "synthetic-test",
        "relation": relation,
        "target_branch_ids": list(targets),
        "independence_qualified": independent,
    }


def canonical(state):
    out = copy.deepcopy(state)
    out["branches"] = sorted(out.get("branches", []), key=lambda x: x["branch_id"])
    return out


def test_exact_replay_idempotent():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"]))
    twice = u_state(once, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    assert len(twice["branches"][0]["E_plus"]) == 1
    assert not twice["branches"][0].get("correlated_observations")


def test_exact_event_id_cannot_change_relation():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    with pytest.raises(ValueError, match="conflicting relation"):
        u_state(once, observation("COUNTERS", ["A"], event="e1", ancestry="a1"))


def test_exact_event_id_cannot_change_correlation_ancestry():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    with pytest.raises(ValueError, match="conflicting correlation ancestry"):
        u_state(once, observation("SUPPORTS", ["A"], event="e1", ancestry="a2"))


def test_unknown_target_branch_fails_closed():
    state = {"branches": [branch("A"), branch("B")]}
    with pytest.raises(ValueError, match="unknown target branch"):
        u_state(state, observation("SUPPORTS", ["TYPO_BRANCH"]))


def test_duplicate_branch_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate branch_id"):
        d_resolve({"branches": [branch("A"), branch("A")]})


def test_distinct_event_same_ancestry_preserved_not_independent():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    twice = u_state(once, observation("SUPPORTS", ["A"], event="e2", ancestry="a1"))
    a = twice["branches"][0]
    assert len(a["E_plus"]) == 1
    assert len(a["correlated_observations"]) == 1
    assert a["correlated_observations"][0]["evidence_event_id"] == "e2"
    assert a["correlated_observations"][0]["independent_credit"] is False


def test_independent_event_preserved_with_credit():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    twice = u_state(once, observation("SUPPORTS", ["A"], event="e2", ancestry="a2", independent=True))
    a = twice["branches"][0]
    assert len(a["E_plus"]) == 2
    assert a["E_plus"][1]["independent_credit"] is True


def test_correlated_counterevent_remains_auditable_without_reweighting_state():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    twice = u_state(once, observation("COUNTERS", ["A"], event="e2", ancestry="a1"))
    a = twice["branches"][0]
    assert a["sigma"] == "SUPPORTED_UNRESOLVED"
    assert a["E_minus"] == []
    assert a["correlated_observations"][0]["relation"] == "COUNTERS"


def test_counterevidence_weakens_not_falsifies():
    out = u_state({"branches": [branch("A")]}, observation("COUNTERS", ["A"]))
    assert out["branches"][0]["sigma"] == "WEAKENED_UNRESOLVED"
    assert out["branches"][0]["F"] == []


def test_falsifier_only_when_context_applies():
    state = {"branches": [branch("A", K="APPLIES"), branch("B", K="UNKNOWN")]}
    out = u_state(state, observation("FALSIFIES", ["A", "B"]))
    by_id = {b["branch_id"]: b for b in out["branches"]}
    assert by_id["A"]["sigma"] == "FALSIFIED"
    assert by_id["B"]["sigma"] == "LIVE_UNRESOLVED"
    assert len(by_id["B"]["pending_falsifiers"]) == 1


def test_context_filter_not_deletion():
    state = {"branches": [branch("A", K="DOES_NOT_APPLY"), branch("B")]}
    out = u_state(state, observation("IRRELEVANT", ["A"]))
    assert {b["branch_id"] for b in out["branches"]} == {"A", "B"}
    by_id = {b["branch_id"]: b for b in out["branches"]}
    assert by_id["A"]["projection_visibility"] == "FILTERED_CONTEXT"


def test_multiple_live_unresolved():
    assert d_resolve({"branches": [branch("A"), branch("B")]}) == {
        "resolution": "UNRESOLVED",
        "selected_branch_id": None,
    }


def test_unique_applicable_survivor_passes():
    state = {"branches": [branch("A"), branch("B", sigma="FALSIFIED")]}
    decision = d_resolve(state)
    assert decision == {"resolution": "PASS", "selected_branch_id": "A"}
    out = apply_resolution(state, decision)
    assert {b["branch_id"]: b["sigma"] for b in out["branches"]}["A"] == "RESOLVED_PASS"


def test_apply_resolution_rejects_unknown_selected_branch():
    state = {"branches": [branch("A"), branch("B", sigma="FALSIFIED")]}
    with pytest.raises(ValueError, match="select exactly one existing branch"):
        apply_resolution(state, {"resolution": "PASS", "selected_branch_id": "TYPO_BRANCH"})


def test_unknown_context_blocks_resolution():
    state = {"branches": [branch("A"), branch("B", K="UNKNOWN", sigma="WEAKENED_UNRESOLVED")]}
    assert d_resolve(state)["resolution"] == "UNRESOLVED"


def test_correlated_majority_never_resolves():
    state = {"branches": [branch("A"), branch("B")]}
    state = u_state(state, observation("SUPPORTS", ["A"], event="e1", ancestry="a1"))
    for i in range(2, 8):
        state = u_state(state, observation("SUPPORTS", ["A"], event=f"e{i}", ancestry="a1"))
    assert d_resolve(state)["resolution"] == "UNRESOLVED"
    assert len(state["branches"][0]["correlated_observations"]) == 6


def test_branch_permutation_invariance():
    state1 = {"branches": [branch("A"), branch("B")]}
    state2 = {"branches": [branch("B"), branch("A")]}
    obs = observation("SUPPORTS", ["A"])
    assert canonical(u_state(state1, obs)) == canonical(u_state(state2, obs))


def test_explicit_equivalence_merge_only():
    state = {"branches": [branch("A", v="same"), branch("B", v="same")]}
    assert len(u_state(state, observation("IRRELEVANT", []))["branches"]) == 2
    obs = observation("IRRELEVANT", [])
    obs["equivalence_certificate"] = {
        "equivalent": True,
        "branch_ids": ["A", "B"],
        "certificate_id": "eq1",
    }
    assert len(u_state(state, obs)["branches"]) == 1


def test_merge_target_cannot_collide_with_surviving_branch():
    state = {
        "branches": [
            branch("A", v="same"),
            branch("B", v="same"),
            branch("C", v="different"),
        ]
    }
    obs = observation("IRRELEVANT", [])
    obs["equivalence_certificate"] = {
        "equivalent": True,
        "branch_ids": ["A", "B"],
        "merge_to_branch_id": "C",
        "certificate_id": "eq-collision",
    }
    with pytest.raises(ValueError, match="collides"):
        u_state(state, obs)


def test_test_order_prefers_separation():
    state = {"branches": [branch("A"), branch("B"), branch("C")]}
    tests = [
        {"test_id": "cheap", "outcomes": {"A": "x", "B": "x", "C": "x"}},
        {
            "test_id": "separating",
            "outcomes": {"A": "x", "B": "y", "C": "z"},
            "risk_class": 2,
            "execution_cost_class": 2,
        },
    ]
    assert u_test_order(state, tests)[0] == "separating"


def test_test_order_probability_free_stable():
    state = {"branches": [branch("A"), branch("B")]}
    tests = [
        {"test_id": "b", "outcomes": {"A": "x", "B": "y"}},
        {"test_id": "a", "outcomes": {"A": "x", "B": "y"}},
    ]
    assert u_test_order(state, tests) == ["a", "b"]


def test_salience_does_not_mutate_truth_state():
    state = {"branches": [branch("A"), branch("B")]}
    before = copy.deepcopy(state)
    order = f_salience_order([
        {"item_id": "normal", "authority_boundary_risk": 0},
        {"item_id": "authority-risk", "authority_boundary_risk": 3},
    ])
    assert order == ["authority-risk", "normal"]
    assert state == before
    assert d_resolve(state)["resolution"] == "UNRESOLVED"
