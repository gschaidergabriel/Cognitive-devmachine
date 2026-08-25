import copy

from tools.trigger2_hyperposition_reference_labelers_v1 import (
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


def observation(relation, targets, *, evidence_id="e1", ancestry="a1"):
    return {
        "evidence_id": evidence_id,
        "causal_ancestry_id": ancestry,
        "independence_group": "g1",
        "provenance": "synthetic-test",
        "relation": relation,
        "target_branch_ids": list(targets),
    }


def canonical(state):
    out = copy.deepcopy(state)
    out["branches"] = sorted(out.get("branches", []), key=lambda x: x["branch_id"])
    return out


def test_support_is_idempotent_by_causal_ancestry():
    state = {"branches": [branch("A"), branch("B")]}
    once = u_state(state, observation("SUPPORTS", ["A"]))
    twice = u_state(once, observation("SUPPORTS", ["A"], evidence_id="e2", ancestry="a1"))
    assert len(once["branches"][0]["E_plus"]) == 1
    assert len(twice["branches"][0]["E_plus"]) == 1


def test_counterevidence_weakens_but_does_not_falsify():
    state = {"branches": [branch("A")]}
    out = u_state(state, observation("COUNTERS", ["A"]))
    assert out["branches"][0]["sigma"] == "WEAKENED_UNRESOLVED"
    assert out["branches"][0]["F"] == []


def test_explicit_falsifier_falsifies_only_when_context_applies():
    state = {"branches": [branch("A", K="APPLIES"), branch("B", K="UNKNOWN")]}
    out = u_state(state, observation("FALSIFIES", ["A", "B"]))
    by_id = {b["branch_id"]: b for b in out["branches"]}
    assert by_id["A"]["sigma"] == "FALSIFIED"
    assert by_id["B"]["sigma"] == "LIVE_UNRESOLVED"
    assert len(by_id["B"]["pending_falsifiers"]) == 1


def test_context_filter_is_not_deletion():
    state = {"branches": [branch("A", K="DOES_NOT_APPLY"), branch("B")]}
    out = u_state(state, observation("IRRELEVANT", ["A"]))
    assert {b["branch_id"] for b in out["branches"]} == {"A", "B"}
    by_id = {b["branch_id"]: b for b in out["branches"]}
    assert by_id["A"]["projection_visibility"] == "FILTERED_CONTEXT"


def test_d_resolve_preserves_multiple_live_alternatives():
    state = {"branches": [branch("A"), branch("B")]}
    assert d_resolve(state) == {"resolution": "UNRESOLVED", "selected_branch_id": None}


def test_d_resolve_passes_only_unique_live_applicable_branch():
    state = {"branches": [branch("A"), branch("B", sigma="FALSIFIED")]}
    decision = d_resolve(state)
    assert decision == {"resolution": "PASS", "selected_branch_id": "A"}
    out = apply_resolution(state, decision)
    assert {b["branch_id"]: b["sigma"] for b in out["branches"]}["A"] == "RESOLVED_PASS"


def test_unknown_context_blocks_resolution():
    state = {"branches": [branch("A"), branch("B", K="UNKNOWN", sigma="WEAKENED_UNRESOLVED")]}
    assert d_resolve(state)["resolution"] == "UNRESOLVED"


def test_branch_permutation_does_not_change_update_semantics():
    state1 = {"branches": [branch("A"), branch("B")]}
    state2 = {"branches": [branch("B"), branch("A")]}
    obs = observation("SUPPORTS", ["A"])
    assert canonical(u_state(state1, obs)) == canonical(u_state(state2, obs))


def test_merge_requires_explicit_equivalence_and_matching_semantics():
    state = {"branches": [branch("A", v="same"), branch("B", v="same")]}
    no_cert = u_state(state, observation("IRRELEVANT", []))
    assert len(no_cert["branches"]) == 2
    obs = observation("IRRELEVANT", [])
    obs["equivalence_certificate"] = {
        "equivalent": True,
        "branch_ids": ["A", "B"],
        "certificate_id": "eq1",
    }
    merged = u_state(state, obs)
    assert len(merged["branches"]) == 1
    assert merged["branches"][0]["merged_from_branch_ids"] == ["A", "B"]


def test_test_order_prefers_actual_branch_separation_over_cheaper_nondiscriminator():
    state = {"branches": [branch("A"), branch("B"), branch("C")]}
    tests = [
        {
            "test_id": "cheap-no-separation",
            "outcomes": {"A": "x", "B": "x", "C": "x"},
            "risk_class": 0,
            "execution_cost_class": 0,
            "coordination_cost_class": 0,
        },
        {
            "test_id": "separating",
            "outcomes": {"A": "x", "B": "y", "C": "z"},
            "risk_class": 2,
            "execution_cost_class": 2,
            "coordination_cost_class": 2,
        },
    ]
    assert u_test_order(state, tests)[0] == "separating"


def test_test_order_is_probability_free_and_stable():
    state = {"branches": [branch("A"), branch("B")]}
    tests = [
        {"test_id": "b", "outcomes": {"A": "x", "B": "y"}},
        {"test_id": "a", "outcomes": {"A": "x", "B": "y"}},
    ]
    assert u_test_order(state, tests) == ["a", "b"]


def test_salience_ranks_attention_without_changing_truth_state():
    state = {"branches": [branch("A"), branch("B")]}
    before = copy.deepcopy(state)
    order = f_salience_order([
        {"item_id": "normal", "authority_boundary_risk": 0},
        {"item_id": "authority-risk", "authority_boundary_risk": 3},
    ])
    assert order == ["authority-risk", "normal"]
    assert state == before
    assert d_resolve(state)["resolution"] == "UNRESOLVED"
