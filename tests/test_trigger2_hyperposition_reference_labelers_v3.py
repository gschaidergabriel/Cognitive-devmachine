from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_hyperposition_reference_labelers_v3.py"
spec = importlib.util.spec_from_file_location("lab3", P)
lab = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(lab)


def branch(bid, value, K="APPLIES"):
    return {
        "branch_id": bid,
        "v": value,
        "K": K,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "synthetic_episode",
        "A": {"origin": "pytest"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": "VISIBLE",
    }


def state(order=("b0", "b1", "b2")):
    values = {"b0": "QUERY_TRUE", "b1": "QUERY_FALSE", "b2": "QUERY_UNKNOWN"}
    return {
        "schema": lab.STATE_SCHEMA,
        "query_id": "q1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch(bid, values[bid]) for bid in order],
    }


def test(outcomes=None, tid="d1", **kw):
    x = {
        "schema": lab.TEST_SCHEMA,
        "test_id": tid,
        "outcomes": outcomes or {"b0": "YES", "b1": "NO", "b2": "MAYBE"},
        "risk_class": 0,
        "execution_cost_class": 1,
        "coordination_cost_class": 0,
    }
    x.update(kw)
    return x


def event(eid="e1", ancestry="a1", group="g1", payload="p1", outcome="YES", independent=True, **kw):
    x = {
        "schema": lab.EVENT_SCHEMA,
        "evidence_event_id": eid,
        "correlation_ancestry_id": ancestry,
        "independence_group": group,
        "payload_key": payload,
        "provenance": {"source": "synthetic_pytest"},
        "observed_outcome": outcome,
        "independence_qualified": independent,
        "discriminator": test(),
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    x.update(kw)
    return x


def test_relation_labels_are_derived_not_caller_asserted():
    e = event()
    e["relation"] = "FALSIFIES"
    e["target_branch_ids"] = ["b1"]
    derived = lab.derive_relations(state(), e)
    assert derived == {"b0": "SUPPORTS", "b1": "FALSIFIES", "b2": "FALSIFIES"}


def test_independent_event_can_resolve_only_after_mechanical_update():
    u = lab.u_state(state(), event())
    assert u["identity_status"] == "NOVEL_INDEPENDENT_EVENT"
    assert u["independent_evidence_credit"] is True
    assert u["derived_relations"]["b0"] == "SUPPORTS"
    after = u["state_after"]
    assert next(b for b in after["branches"] if b["branch_id"] == "b1")["sigma"] == "FALSIFIED"
    assert next(b for b in after["branches"] if b["branch_id"] == "b2")["sigma"] == "FALSIFIED"
    r = lab.d_resolve(after)
    assert r["resolution"] == "PASS" and r["selected_branch_id"] == "b0"
    resolved = lab.apply_resolution(after)
    assert next(b for b in resolved["branches"] if b["branch_id"] == "b0")["sigma"] == "RESOLVED_PASS"


def test_exact_event_replay_is_idempotent():
    first = lab.u_state(state(), event())
    replay = lab.u_state(first["state_after"], event())
    assert replay["identity_status"] == "EXACT_EVENT_REPLAY"
    assert replay["independent_evidence_credit"] is False
    assert replay["state_changed"] is False
    assert replay["state_after"] == first["state_after"]


def test_distinct_same_ancestry_event_is_preserved_without_independent_credit():
    first = lab.u_state(state(), event())
    second_event = event(eid="e2", ancestry="a1", group="g2", payload="p2")
    second = lab.u_state(first["state_after"], second_event)
    assert second["identity_status"] == "CORRELATED_ANCESTRY_EVENT"
    assert second["independent_evidence_credit"] is False
    assert len(second["state_after"]["correlated_observations"]) == 1
    b0_before = next(b for b in first["state_after"]["branches"] if b["branch_id"] == "b0")
    b0_after = next(b for b in second["state_after"]["branches"] if b["branch_id"] == "b0")
    assert b0_after == b0_before


def test_same_payload_independence_key_under_new_ancestry_is_repackaging_not_new_evidence():
    first = lab.u_state(state(), event())
    repack = event(eid="e2", ancestry="a2", group="g1", payload="p1")
    second = lab.u_state(first["state_after"], repack)
    assert second["identity_status"] == "REPACKAGED_PAYLOAD_EVENT"
    assert second["independent_evidence_credit"] is False


def test_novel_but_unqualified_event_does_not_update_branches():
    u = lab.u_state(state(), event(independent=False))
    assert u["identity_status"] == "NOVEL_BUT_NOT_INDEPENDENCE_QUALIFIED"
    assert u["independent_evidence_credit"] is False
    assert all(b["sigma"] == "LIVE_UNRESOLVED" for b in u["state_after"]["branches"])


def test_nonindependent_event_cannot_mutate_branch_topology():
    first = lab.u_state(state(), event())
    e = event(eid="e2", ancestry="a1", group="g2", payload="p2")
    e["new_branch_payload"] = branch("b3", "NEW_ALT")
    e["branch_birth_certificate"] = {
        "certificate_id": "birth1",
        "basis_event_id": "e2",
        "observed_outcome": "YES",
    }
    try:
        lab.u_state(first["state_after"], e)
    except lab.LabelerError as exc:
        assert "NONINDEPENDENT_EVENT_CANNOT_MUTATE_BRANCH_TOPOLOGY" in str(exc)
        return
    raise AssertionError("correlated evidence must not mutate branch topology")


def test_branch_birth_requires_certificate_and_preserves_hyperposition():
    e = event()
    e["new_branch_payload"] = branch("b3", "NEW_ALT")
    e["branch_birth_certificate"] = {
        "certificate_id": "birth1",
        "basis_event_id": "e1",
        "observed_outcome": "YES",
    }
    u = lab.u_state(state(), e)
    assert len(u["state_after"]["branches"]) == 4
    newborn = next(b for b in u["state_after"]["branches"] if b["branch_id"] == "b3")
    assert newborn["A"]["birth_certificate_id"] == "birth1"


def test_equivalence_merge_requires_v_k_t_identity_and_never_single_branch_collapse():
    s = state()
    b0 = next(b for b in s["branches"] if b["branch_id"] == "b0")
    b1 = next(b for b in s["branches"] if b["branch_id"] == "b1")
    b1["v"], b1["K"], b1["T"] = b0["v"], b0["K"], b0["T"]
    e = event()
    e["equivalence_certificate"] = {
        "certificate_id": "merge1",
        "equivalent": True,
        "branch_ids": ["b0", "b1"],
        "merge_to_branch_id": "b01",
    }
    u = lab.u_state(s, e)
    assert {b["branch_id"] for b in u["state_after"]["branches"]} == {"b01", "b2"}


def test_test_separation_is_derived_from_outcomes_not_caller_pairs():
    t = test()
    t["separates_pairs"] = []
    derived = lab.derive_test_separation(state(), t)
    assert derived["separated_pair_count"] == 3
    assert sorted(derived["separates_pairs"]) == [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]]


def test_test_order_is_ordinal_and_prefers_actual_separation():
    wide = test(tid="wide")
    narrow = test(outcomes={"b0": "YES", "b1": "NO", "b2": "NO"}, tid="narrow", execution_cost_class=0)
    ordered = lab.u_test_order(state(), [narrow, wide])
    assert ordered[0]["test_id"] == "wide"
    assert all(x["probability_output"] is False and x["truth_output"] is False for x in ordered)


def test_salience_is_not_truth_probability_or_evidence_strength():
    ranked = lab.f_salience_order([
        {"item_id": "a", "authority_boundary_risk": 1, "expiry_or_time_urgency": 0, "live_discriminator_relevance": 0, "current_goal_relevance": 0, "novel_independent_evidence": False},
        {"item_id": "b", "authority_boundary_risk": 0, "expiry_or_time_urgency": 9, "live_discriminator_relevance": 9, "current_goal_relevance": 9, "novel_independent_evidence": True},
    ])
    assert ranked[0]["item_id"] == "a"
    assert all(x["probability_output"] is False and x["truth_output"] is False and x["evidence_strength_output"] is False for x in ranked)


def test_branch_permutation_preserves_canonical_semantics():
    e = event()
    a = lab.u_state(state(("b0", "b1", "b2")), e)["state_after"]
    b = lab.u_state(state(("b2", "b0", "b1")), e)["state_after"]
    assert lab.canonical_semantics(a) == lab.canonical_semantics(b)


def test_truth_authority_leaks_fail_closed():
    s = state()
    s["canonical_truth_allowed"] = True
    try:
        lab.d_resolve(s)
    except lab.LabelerError:
        return
    raise AssertionError("canonical truth authority must fail closed")
