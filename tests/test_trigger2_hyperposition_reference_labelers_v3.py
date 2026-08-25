import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_hyperposition_reference_labelers_v3.py"
spec = importlib.util.spec_from_file_location("lab3", P)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def world(*, mismatch="FALSIFIES", merge="NONE", births=None):
    return {
        "schema": lab.WORLD_SCHEMA,
        "world_id": "w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"mode": "A", "scope": "test"},
        "tests": {
            "t_binary": {
                "allowed_outcomes": ["YES", "NO"],
                "mismatch_effect": mismatch,
                "risk_rank": 0,
                "cost_rank": 1,
                "coordination_rank": 0,
            },
            "t_same": {
                "allowed_outcomes": ["UP", "DOWN"],
                "mismatch_effect": "COUNTERS",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            },
        },
        "merge_policy": merge,
        "branch_birth_rules": births or [],
    }


def branch(bid, value, binary, *, k="ALWAYS", same="UP"):
    return {
        "branch_id": bid,
        "v": value,
        "K": k,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": "test"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"t_binary": binary, "t_same": same},
    }


def state(branches=None):
    if branches is None:
        branches = [branch("h_yes", "YES_HYP", "YES"), branch("h_no", "NO_HYP", "NO")]
    return {
        "schema": lab.STATE_SCHEMA,
        "query_id": "q1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": copy.deepcopy(branches),
    }


def event(eid="e1", outcome="YES", *, ancestry="a1", group="g1", payload="p1", test="t_binary", qualified=True, **extra):
    out = {
        "schema": lab.EVENT_SCHEMA,
        "event_id": eid,
        "correlation_ancestry_id": ancestry,
        "independence_group": group,
        "payload_key": payload,
        "provenance": "synthetic:test",
        "epistemic_type": "OBSERVED",
        "test_id": test,
        "observed_outcome": outcome,
        "independence_qualified": qualified,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }
    out.update(extra)
    return out


def test_relations_and_targets_are_derived_from_world_not_supplied():
    r = lab.derive_relations(world(), state(), event())
    assert r["pass"]
    assert r["target_branch_ids"] == ["h_no", "h_yes"]
    assert r["relations"] == {"h_yes": "SUPPORTS", "h_no": "FALSIFIES"}
    assert r["derivation_receipt"]["caller_relation_fields_accepted"] is False


def test_caller_asserted_relation_or_target_is_rejected():
    r = lab.derive_relations(world(), state(), event(relation="SUPPORTS", target_branch_ids=["h_no"]))
    assert not r["pass"]
    assert r["failure"].startswith("CALLER_ASSERTED_LABEL_FIELD_FORBIDDEN:")


def test_formal_outcome_flip_flips_derived_relations():
    yes = lab.derive_relations(world(), state(), event(outcome="YES"))
    no = lab.derive_relations(world(), state(), event(outcome="NO"))
    assert yes["relations"]["h_yes"] == "SUPPORTS"
    assert yes["relations"]["h_no"] == "FALSIFIES"
    assert no["relations"]["h_yes"] == "FALSIFIES"
    assert no["relations"]["h_no"] == "SUPPORTS"


def test_update_then_resolution_requires_supported_survivor_and_falsified_competitor():
    u = lab.u_state(world(), state(), event())
    assert u["pass"] and u["independent_evidence_credit"] is True
    after = u["state_after"]
    by_id = {b["branch_id"]: b for b in after["branches"]}
    assert by_id["h_yes"]["sigma"] == "SUPPORTED_UNRESOLVED"
    assert by_id["h_no"]["sigma"] == "FALSIFIED"
    d = lab.d_resolve(world(), after)
    assert d["pass"]
    assert d["resolution"]["status"] == "RESOLVED_WITHIN_SYNTHETIC_WORLD"
    assert d["resolution"]["resolved_branch"] == "h_yes"
    assert d["canonical_truth_minted"] is False


def test_soft_mismatch_counters_and_does_not_resolve():
    w = world(mismatch="COUNTERS")
    u = lab.u_state(w, state(), event())
    after = u["state_after"]
    by_id = {b["branch_id"]: b for b in after["branches"]}
    assert by_id["h_no"]["sigma"] == "WEAKENED_UNRESOLVED"
    d = lab.d_resolve(w, after)
    assert d["resolution"]["status"] == "UNRESOLVED"


def test_exact_event_replay_is_idempotent():
    w = world()
    first = lab.u_state(w, state(), event())
    second = lab.u_state(w, first["state_after"], event())
    assert second["pass"]
    assert second["exact_replay_idempotent"] is True
    assert second["independent_evidence_credit"] is False
    a = lab.canonical_semantic_state(first["state_after"])
    b = lab.canonical_semantic_state(second["state_after"])
    assert a["canonical_state_sha256"] == b["canonical_state_sha256"]


def test_same_correlation_ancestry_new_event_gets_no_independent_credit():
    w = world()
    first = lab.u_state(w, state(), event())
    second_event = event(eid="e2", ancestry="a1", group="g2", payload="p2")
    second = lab.u_state(w, first["state_after"], second_event)
    assert second["pass"]
    assert second["independent_evidence_credit"] is False
    assert "CORRELATION_ANCESTRY_REUSE" in second["nonindependence_reasons"]


def test_payload_repackaging_new_ancestry_and_group_gets_no_independent_credit():
    w = world()
    first = lab.u_state(w, state(), event())
    second_event = event(eid="e2", ancestry="a2", group="g2", payload="p1")
    second = lab.u_state(w, first["state_after"], second_event)
    assert second["pass"]
    assert second["independent_evidence_credit"] is False
    assert "PAYLOAD_REPACKAGING" in second["nonindependence_reasons"]


def test_context_predicate_derives_targets_and_projection_without_deletion():
    b1 = branch("ha", "A_ONLY", "YES", k={"all": [{"key": "mode", "op": "EQ", "value": "A"}]})
    b2 = branch("hb", "B_ONLY", "NO", k={"all": [{"key": "mode", "op": "EQ", "value": "B"}]})
    s = state([b1, b2])
    r = lab.derive_relations(world(), s, event())
    assert r["target_branch_ids"] == ["ha"]
    p = lab.project_state(world(), s)
    assert p["pass"] and p["branch_count_before"] == p["branch_count_after"] == 2
    assert p["branch_deletion_performed"] is False
    assert p["visible_branch_ids"] == ["ha"]
    assert p["projected_out_branch_ids"] == ["hb"]


def test_context_in_not_in_require_json_array_operands_and_fail_closed():
    malformed_values = ["A", {"A": True}, None, 7, True]
    for op in ("IN", "NOT_IN"):
        for value in malformed_values:
            bad = branch(
                "ha",
                "BAD_CONTEXT",
                "YES",
                k={"all": [{"key": "mode", "op": op, "value": value}]},
            )
            good = branch("hb", "CONTROL", "NO")
            r = lab.derive_relations(world(), state([bad, good]), event())
            assert r["pass"] is False
            assert r["failure"] == "BRANCH_K_INVALID"
            assert r["canonical_truth_minted"] is False
            assert r["training_credit_minted"] is False


def test_context_in_not_in_accept_explicit_json_array_operands():
    in_branch = branch(
        "hin",
        "IN_SCOPE",
        "YES",
        k={"all": [{"key": "mode", "op": "IN", "value": ["A", "B"]}]},
    )
    not_in_branch = branch(
        "hnot",
        "NOT_IN_SCOPE",
        "NO",
        k={"all": [{"key": "mode", "op": "NOT_IN", "value": ["B", "C"]}]},
    )
    s = state([in_branch, not_in_branch])
    r = lab.derive_relations(world(), s, event())
    assert r["pass"] is True
    assert r["target_branch_ids"] == ["hin", "hnot"]
    assert r["context_applicability"] == {"hin": True, "hnot": True}


def test_branch_birth_is_derived_from_formal_world_rule():
    template = branch("h_new", "NEW_HYP", "YES")
    births = [{
        "rule_id": "birth-yes",
        "test_id": "t_binary",
        "observed_outcome": "YES",
        "branch_template": template,
    }]
    w = world(births=births)
    u = lab.u_state(w, state(), event())
    assert u["pass"]
    assert u["born_branch_ids"] == ["h_new"]
    assert {b["branch_id"] for b in u["state_after"]["branches"]} == {"h_yes", "h_no", "h_new"}


def test_branch_birth_rejects_nonempty_untyped_initial_evidence():
    template = branch("h_new", "NEW_HYP", "YES")
    for field in ("E_plus", "E_minus", "F"):
        bad_template = copy.deepcopy(template)
        bad_template[field] = [{"garbage": "not a typed evidence record"}]
        births = [{
            "rule_id": "birth-bad",
            "test_id": "t_binary",
            "observed_outcome": "YES",
            "branch_template": bad_template,
        }]
        w = world(births=births)
        err = lab._validate_world(w)
        assert err == "WORLD_BRANCH_BIRTH_TEMPLATE_INVALID:BRANCH_BIRTH_EVIDENCE_MUST_BE_EMPTY:" + field, (field, err)


def test_branch_birth_accepts_exactly_empty_initial_evidence():
    template = branch("h_new", "NEW_HYP", "YES")
    births = [{
        "rule_id": "birth-ok",
        "test_id": "t_binary",
        "observed_outcome": "YES",
        "branch_template": template,
    }]
    w = world(births=births)
    assert lab._validate_world(w) is None


def test_exact_semantic_merge_uses_declared_policy_not_similarity():
    b1 = branch("a", "SAME", "YES")
    b2 = branch("b", "SAME", "YES")
    s = state([b1, b2])
    w = world(merge="EXACT_FORMAL_SEMANTIC_SIGNATURE")
    u = lab.u_state(w, s, event())
    assert u["pass"]
    assert len(u["state_after"]["branches"]) == 1
    assert u["state_after"]["branches"][0]["merged_from_branch_ids"] == ["a", "b"]


def test_discriminator_pair_separation_is_derived_from_predictions():
    r = lab.u_test_order(world(), state(), ["t_same", "t_binary"])
    assert r["pass"]
    assert [x["test_id"] for x in r["ordering"]] == ["t_binary", "t_same"]
    assert r["ordering"][0]["separated_live_pairs"] == 1
    assert r["ordering"][1]["separated_live_pairs"] == 0
    assert r["probability_output"] is False and r["truth_output"] is False


def test_permutation_and_branch_id_renaming_are_semantic_nuisances():
    s1 = state([
        branch("a", "YES_HYP", "YES"),
        branch("b", "NO_HYP", "NO"),
    ])
    s2 = state([
        branch("renamed_2", "NO_HYP", "NO"),
        branch("renamed_1", "YES_HYP", "YES"),
    ])
    r = lab.permutation_invariance_check(s1, s2)
    assert r["pass"] and r["invariant"] is True
    assert r["branch_order_and_ids_are_nuisance"] is True


def test_salience_is_never_truth_probability_evidence_or_resolution_authority():
    r = lab.f_salience_order([
        {"item_id": "x", "authority_boundary_risk_rank": 1, "expiry_rank": 0, "discriminator_relevance_rank": 0, "goal_relevance_rank": 0},
        {"item_id": "y", "authority_boundary_risk_rank": 0, "expiry_rank": 9, "discriminator_relevance_rank": 9, "goal_relevance_rank": 9},
    ])
    assert r["pass"]
    assert r["truth_output"] is False
    assert r["probability_output"] is False
    assert r["evidence_strength_output"] is False
    assert r["resolution_authority_output"] is False


def test_epistemic_unknown_cannot_self_promote_to_observed():
    r = lab.epistemic_guard("UNKNOWN", "OBSERVED", evidence_qualified_observation=False)
    assert r["pass"] and r["transition_allowed"] is False


def test_unknown_test_or_invalid_outcome_fails_closed():
    assert lab.derive_relations(world(), state(), event(test="missing"))["pass"] is False
    assert lab.derive_relations(world(), state(), event(outcome="MAYBE"))["pass"] is False
