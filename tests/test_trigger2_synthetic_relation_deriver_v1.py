from copy import deepcopy

import pytest

from tools.trigger2_synthetic_relation_deriver_v1 import (
    OBS_SCHEMA,
    WORLD_SCHEMA,
    DerivationError,
    derive,
)


def world(*, decisive=True, admissible=True):
    return {
        "schema": WORLD_SCHEMA,
        "world_id": "world:test",
        "measurements": {
            "m": {
                "admissible": admissible,
                "decisive": decisive,
                "outcome_domain": ["red", "green", "blue"],
            }
        },
    }


def branches(order=("a", "b", "c")):
    values = {"a": "red", "b": "green", "c": "blue"}
    return [
        {"branch_id": bid, "K": "APPLIES", "predictions": {"m": values[bid]}}
        for bid in order
    ]


def observation(outcome="red"):
    return {
        "schema": OBS_SCHEMA,
        "evidence_event_id": "event-1",
        "correlation_ancestry_id": "family-1",
        "independence_group": "group-1",
        "provenance": "synthetic:test",
        "measurement_id": "m",
        "observed_outcome": outcome,
        "independence_qualified": True,
    }


def test_decisive_measurement_derives_support_and_falsification():
    r = derive(world(), branches(), observation("red"))
    rels = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert rels == {"a": "SUPPORTS", "b": "FALSIFIES", "c": "FALSIFIES"}
    assert r["derived_target_branch_ids"] == ["a", "b", "c"]
    assert r["discriminator"]["full_pairwise_separation"] is True
    assert r["discriminator"]["derived_winner_branch_id"] == "a"


def test_nondecisive_mismatch_is_counterevidence_not_falsification():
    r = derive(world(decisive=False), branches(), observation("red"))
    rels = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert rels == {"a": "SUPPORTS", "b": "COUNTERS", "c": "COUNTERS"}
    assert r["discriminator"]["derived_winner_branch_id"] is None


def test_shared_predicted_outcome_prevents_unique_resolution():
    bs = branches()
    bs[1]["predictions"]["m"] = "red"
    r = derive(world(), bs, observation("red"))
    assert r["discriminator"]["full_pairwise_separation"] is False
    assert r["discriminator"]["matching_branch_ids"] == ["a", "b"]
    assert r["discriminator"]["derived_winner_branch_id"] is None


def test_branch_serialization_order_is_nuisance():
    a = derive(world(), branches(("a", "b", "c")), observation("red"))
    b = derive(world(), branches(("c", "a", "b")), observation("red"))
    assert a["branch_relations"] == b["branch_relations"]
    assert a["derived_target_branch_ids"] == b["derived_target_branch_ids"]
    assert a["discriminator"] == b["discriminator"]


def test_unknown_context_does_not_receive_asserted_relation():
    bs = branches()
    bs[2]["K"] = "UNKNOWN"
    r = derive(world(), bs, observation("red"))
    rels = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert rels["c"] == "UNKNOWN_RELATION"
    assert "c" not in r["derived_target_branch_ids"]


def test_caller_asserted_relation_and_winner_fail_closed():
    for field, value in (
        ("relation", "SUPPORTS"),
        ("effect", "PROVE"),
        ("target_branch_ids", ["a"]),
        ("winner_branch_id", "a"),
        ("evidence_qualified", True),
    ):
        o = observation()
        o[field] = value
        with pytest.raises(DerivationError):
            derive(world(), branches(), o)


def test_world_digest_binds_semantics():
    w1 = world(decisive=True)
    w2 = deepcopy(w1)
    w2["measurements"]["m"]["decisive"] = False
    a = derive(w1, branches(), observation())
    b = derive(w2, branches(), observation())
    assert a["world_digest_sha256"] != b["world_digest_sha256"]


def test_no_authority_or_credit_is_minted():
    r = derive(world(), branches(), observation())
    assert r["canonical_truth_minted"] is False
    assert r["direct_effect_authority_minted"] is False
    assert r["jspace_causal_credit_minted"] is False
    assert r["runtime_credit_minted"] is False
    assert r["training_credit_minted"] is False
