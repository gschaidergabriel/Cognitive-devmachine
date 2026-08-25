import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_formal_world_relation_deriver_v1.py"
spec = importlib.util.spec_from_file_location("der", P)
der = importlib.util.module_from_spec(spec)
spec.loader.exec_module(der)


def world(admissible=True):
    return {
        "schema": der.WORLD_SCHEMA,
        "world_id": "w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": {
            "b0": {"claims": {"shape": "round", "temp": "hot"}, "falsifier_atoms": ["shape"]},
            "b1": {"claims": {"shape": "square", "temp": "hot"}, "falsifier_atoms": ["shape"]},
            "b2": {"claims": {"shape": "triangle", "temp": "cold"}, "falsifier_atoms": ["shape"]},
        },
        "tests": {
            "shape_probe": {
                "admissible": admissible,
                "predicted_outcomes": {"b0": "R", "b1": "S", "b2": "T"},
            },
            "weak_probe": {
                "admissible": True,
                "predicted_outcomes": {"b0": "X", "b1": "X", "b2": "Y"},
            },
        },
    }


def state(order=("b0", "b1", "b2")):
    return {
        "branches": [
            {
                "branch_id": bid,
                "K": "APPLIES",
                "sigma": "LIVE_UNRESOLVED",
                "E_plus": [],
                "E_minus": [],
                "F": [],
            }
            for bid in order
        ]
    }


def obs(**kw):
    x = {
        "schema": der.OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "evidence_event_id": "e1",
        "correlation_ancestry_id": "a1",
        "independence_group": "g1",
        "provenance": "synthetic:test",
        "atoms": {"shape": "round"},
    }
    x.update(kw)
    return x


def test_relation_is_derived_from_atoms_not_asserted():
    r = der.derive_observation(world(), state(), obs())
    got = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert got == {"b0": "SUPPORTS", "b1": "FALSIFIES", "b2": "FALSIFIES"}
    roles = {x["branch_id"]: x["decision_role"] for x in r["branch_relations"]}
    assert roles["b0"] == "DECISIVE_SUPPORT"
    assert r["surviving_live_branch_ids"] == ["b0"]
    assert der.verify_receipt(r)


def test_nonfalsifier_contradiction_is_counter_not_falsify():
    r = der.derive_observation(world(), state(), obs(atoms={"temp": "cold"}))
    got = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert got["b0"] == "COUNTERS"
    assert got["b1"] == "COUNTERS"
    assert got["b2"] == "SUPPORTS"
    assert r["surviving_live_branch_ids"] == ["b0", "b1", "b2"]


def test_shared_dependence_group_cannot_mint_independence():
    s = state()
    s["branches"][0]["E_plus"] = [{
        "evidence_event_id": "old",
        "correlation_ancestry_id": "different-ancestry",
        "independence_group": "g1",
    }]
    r = der.derive_observation(world(), s, obs(correlation_ancestry_id="new-ancestry"))
    assert r["event_identity"]["independence_qualified"] is False
    assert r["event_identity"]["reason"] == "CORRELATED_OR_SHARED_DEPENDENCE_GROUP"


def test_same_event_different_digest_fails_closed():
    o = obs()
    first = der.derive_observation(world(), state(), o)
    registry = {o["evidence_event_id"]: first["event_identity"]["event_digest"]}
    mutated = obs(atoms={"shape": "square"})
    with pytest.raises(der.DerivationError, match="different immutable digest"):
        der.derive_observation(world(), state(), mutated, event_registry=registry)


def test_exact_replay_is_idempotent_nonindependent():
    o = obs()
    first = der.derive_observation(world(), state(), o)
    registry = {o["evidence_event_id"]: first["event_identity"]["event_digest"]}
    replay = der.derive_observation(world(), state(), o, event_registry=registry)
    assert replay["event_identity"]["exact_replay"] is True
    assert replay["event_identity"]["independence_qualified"] is False


def test_discriminator_partition_and_unique_resolution_are_computed():
    t = {
        "schema": der.TEST_OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "test_id": "shape_probe",
        "observed_outcome": "S",
    }
    r = der.derive_discriminator(world(), state(), t)
    assert r["matching_live_branch_ids"] == ["b1"]
    assert r["adequate_unique_resolution"] is True
    got = {x["branch_id"]: x["relation"] for x in r["branch_relations"]}
    assert got == {"b0": "FALSIFIES", "b1": "SUPPORTS", "b2": "FALSIFIES"}
    assert der.verify_receipt(r)


def test_inadmissible_test_never_yields_adequate_resolution():
    t = {
        "schema": der.TEST_OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "test_id": "shape_probe",
        "observed_outcome": "R",
    }
    r = der.derive_discriminator(world(admissible=False), state(), t)
    assert r["matching_live_branch_ids"] == ["b0"]
    assert r["adequate_unique_resolution"] is False


def test_partial_discriminator_partition_is_not_unique():
    t = {
        "schema": der.TEST_OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "test_id": "weak_probe",
        "observed_outcome": "X",
    }
    r = der.derive_discriminator(world(), state(), t)
    assert r["matching_live_branch_ids"] == ["b0", "b1"]
    assert r["adequate_unique_resolution"] is False


def test_branch_serialization_order_does_not_change_semantic_derivation():
    a = der.derive_observation(world(), state(("b0", "b1", "b2")), obs())
    b = der.derive_observation(world(), state(("b2", "b0", "b1")), obs())
    norm = lambda r: sorted((x["branch_id"], x["relation"], x["decision_role"]) for x in r["branch_relations"])
    assert norm(a) == norm(b)
    assert a["surviving_live_branch_ids"] == b["surviving_live_branch_ids"] == ["b0"]
