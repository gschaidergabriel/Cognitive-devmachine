from __future__ import annotations

from tools import trigger2_hyperposition_causal_label_chain_v1 as chain


def branch(bid: str, value: str):
    return {
        "schema": chain.lab.BRANCH_SCHEMA,
        "branch_id": bid,
        "v_semantic_value": value,
        "K_context_predicate": "ctx=episode",
        "E_plus": [],
        "E_minus": [],
        "F_falsifier": "formal_test_mismatch",
        "T_validity_scope": "episode",
        "A_origin_provenance": "synthetic:test",
        "sigma_epistemic_status": "HYPOTHESIS",
        "projection_visibility": "VISIBLE",
        "validity": "LIVE",
    }


def world(mode="EXACT_FOR_SCOPE", predictions=None):
    predictions = predictions or {"A": "red", "B": "blue", "C": "green"}
    return {
        "schema": chain.WORLD_SCHEMA,
        "world_id": "w1",
        "branches": [
            {"branch_id": bid, "semantic_value": f"ALT_{bid}", "predicted_outcomes": {"t1": outcome}}
            for bid, outcome in predictions.items()
        ],
        "tests": [{
            "test_id": "t1", "mode": mode, "admissible": True,
            "outcome_domain": ["red", "blue", "green"],
            "independence_group": "ig-test", "payload_key": "pk-test", "cost_units": 1,
        }],
    }


def event(outcome="red", *, event_id="e1", source="src1", group="ig1", payload="pk1"):
    return {
        "schema": chain.EVENT_SCHEMA,
        "event_id": event_id,
        "world_id": "w1",
        "test_id": "t1",
        "execution_status": "EXECUTED_SYNTHETIC",
        "observed_outcome": outcome,
        "causal_source_id": source,
        "independence_group": group,
        "payload_key": payload,
    }


def branches(ids=("A", "B", "C")):
    return [branch(bid, f"ALT_{bid}") for bid in ids]


def test_exact_full_coverage_derives_decisive_relations_and_resolution():
    c = chain.derive_label_chain(branches(), world(), event("red"))
    r = c["relation_derivation_receipt"]
    assert r["branch_relations"] == {"A": "SUPPORT", "B": "FALSIFY", "C": "FALSIFY"}
    assert r["decision_role"] == "DECISIVE_SUPPORT"
    assert r["all_other_branches_explicitly_falsified"] is True
    assert c["reference_target"]["resolution"]["status"] == "RESOLVED_WITHIN_TASK"
    assert c["reference_target"]["resolution"]["resolved_branch"] == "A"


def test_partial_unknown_prediction_cannot_be_decisive():
    w = world(predictions={"A": "red", "B": "blue", "C": chain.UNKNOWN_OUTCOME})
    c = chain.derive_label_chain(branches(), w, event("red"))
    r = c["relation_derivation_receipt"]
    assert r["decision_role"] == "NONDECISIVE"
    assert r["branch_relations"] == {"A": "SUPPORT", "B": "FALSIFY", "C": "NO_EFFECT"}
    assert r["all_other_branches_explicitly_falsified"] is False
    assert c["reference_target"]["resolution"]["status"] == "UNRESOLVED"


def test_nondecisive_signal_mismatch_is_counter_not_falsifier():
    c = chain.derive_label_chain(branches(), world(mode="NONDECISIVE_SIGNAL"), event("red"))
    r = c["relation_derivation_receipt"]
    assert r["branch_relations"] == {"A": "SUPPORT", "B": "COUNTER", "C": "COUNTER"}
    assert r["decision_role"] == "NONDECISIVE"
    assert c["reference_target"]["resolution"]["status"] == "UNRESOLVED"


def test_repackaging_same_dependence_payload_keeps_canonical_label_evidence_identity():
    r1 = chain.derive_relation_receipt(world(), event(source="wrapper-1", event_id="e1", group="same-g", payload="same-p"))
    r2 = chain.derive_relation_receipt(world(), event(source="wrapper-2", event_id="e2", group="same-g", payload="same-p"))
    assert r1["canonical_evidence_identity"] == r2["canonical_evidence_identity"]
    assert r1["semantic_receipt_sha256"] == r2["semantic_receipt_sha256"]


def test_observed_outcome_mutation_changes_relations_mechanically():
    red = chain.derive_relation_receipt(world(), event("red"))
    blue = chain.derive_relation_receipt(world(), event("blue"))
    assert red["branch_relations"] == {"A": "SUPPORT", "B": "FALSIFY", "C": "FALSIFY"}
    assert blue["branch_relations"] == {"A": "FALSIFY", "B": "SUPPORT", "C": "FALSIFY"}
    assert red["winner_branch_id"] == "A" and blue["winner_branch_id"] == "B"


def test_branch_order_permutation_is_semantically_equivariant():
    c1 = chain.derive_label_chain(branches(("A", "B", "C")), world(), event("green"))
    c2 = chain.derive_label_chain(branches(("C", "A", "B")), world(), event("green"))
    assert c1["relation_derivation_receipt"]["branch_relations"] == c2["relation_derivation_receipt"]["branch_relations"]
    assert c1["reference_target"]["resolution"]["resolved_branch"] == c2["reference_target"]["resolution"]["resolved_branch"] == "C"


def test_discriminator_pairs_are_derived_not_caller_claimed():
    rows = chain.discriminator_metadata(world())
    assert rows[0]["separates_branch_pairs"] == [["A", "B"], ["A", "C"], ["B", "C"]]
    ranked = chain.lab.U_d_test_order(branches(), rows)
    assert ranked[0]["pair_coverage"] == 3


def test_world_branch_semantic_mismatch_fails_closed():
    bad = branches()
    bad[0]["v_semantic_value"] = "WRONG"
    try:
        chain.derive_label_chain(bad, world(), event())
    except chain.DerivationError:
        pass
    else:
        raise AssertionError("expected semantic alignment failure")
