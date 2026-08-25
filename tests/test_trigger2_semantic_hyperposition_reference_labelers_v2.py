from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_reference_labelers_v2.py"
spec = importlib.util.spec_from_file_location("lab2", P)
assert spec is not None and spec.loader is not None
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def evidence(eid="e1", event="c1", ancestry="a1", group="g1"):
    return {
        "evidence_id": eid,
        "causal_event_id": event,
        "provenance_or_ancestry_id": ancestry,
        "independence_group": group,
        "provenance": "synthetic:test",
        "epistemic_type": "OBSERVED",
    }


def branch(bid, value, K="APPLIES"):
    return {
        "id": bid,
        "v": value,
        "K": K,
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "episode",
        "A": "synthetic:test",
        "sigma": "LIVE_UNRESOLVED",
    }


def state():
    return {
        "schema": lab.STATE_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "joint_state": {
            "representation": "WHOLE_WORLD_BRANCHES",
            "cartesian_completion_allowed": False,
        },
        "branches": [branch("b0", "red"), branch("b1", "blue"), branch("b2", "green")],
    }


def disc(**kw):
    d = {
        "schema": lab.DISC_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "admissible": True,
        "discriminator_id": "d1",
        "prediction_derivation_id": "world:eq-color:v1",
        "predictions_derived_from_synthetic_task_world": True,
        "exhaustive_deterministic_partition": True,
        "branch_predictions": {"b0": "R", "b1": "B", "b2": "G"},
        "risk_class": 0,
        "execution_cost_class": 1,
        "coordination_cost_class": 0,
    }
    d.update(kw)
    return d


def obs(result="R", ev=None, d=None, **extra):
    o = {
        "schema": lab.OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "observed_result": result,
        "evidence": ev or evidence(),
        "discriminator": d or disc(),
    }
    o.update(extra)
    return o


def test_derives_relations_no_effect_input():
    r = lab.U_update(state(), obs())
    assert r["pass"]
    assert {x["branch_id"]: x["derived_relation"] for x in r["derived_relations"]} == {
        "b0": "SUPPORTS",
        "b1": "FALSIFIES",
        "b2": "FALSIFIES",
    }
    assert r["state_after"]["branches"][0]["sigma"] == "SUPPORTED_UNRESOLVED"
    assert r["state_after"]["branches"][1]["sigma"] == "FALSIFIED"
    assert not r["automatic_resolution_performed"]


def test_rejects_forged_effect_and_winner():
    assert lab.U_update(state(), obs(effect="PROVE"))["pass"] is False
    assert lab.D_resolve(state(), obs(winner_branch_id="b0"))["pass"] is False


def test_inadmissible_discriminator_fails_closed():
    assert lab.U_update(state(), obs(d=disc(admissible=False)))["pass"] is False
    assert lab.D_resolve(state(), obs(d=disc(admissible=False)))["pass"] is False


def test_unique_resolution_is_derived_not_asserted():
    r = lab.D_resolve(state(), obs(result="B"))
    assert r["pass"] and r["resolution"]["resolved_branch"] == "b1"
    assert r["retained_branch_ids"] == ["b0", "b1", "b2"]
    assert r["canonical_truth_minted"] is False


def test_nonunique_prediction_partition_remains_unresolved():
    d = disc(branch_predictions={"b0": "X", "b1": "X", "b2": "Y"})
    r = lab.D_resolve(state(), obs(result="X", d=d))
    assert r["pass"] and r["resolution"]["status"] == "UNRESOLVED"
    assert r["resolution"]["matching_live_branch_ids"] == ["b0", "b1"]


def test_nonexhaustive_discriminator_cannot_resolve_or_falsify():
    d = disc(exhaustive_deterministic_partition=False)
    r = lab.D_resolve(state(), obs(result="R", d=d))
    assert r["resolution"]["status"] == "UNRESOLVED"
    u = lab.U_update(state(), obs(result="R", d=d))
    sig = {b["id"]: b["sigma"] for b in u["state_after"]["branches"]}
    assert sig["b0"] == "SUPPORTED_UNRESOLVED"
    assert sig["b1"] == "WEAKENED_UNRESOLVED"


def test_same_independence_group_is_nonindependent_even_with_new_ancestry():
    r1 = lab.U_update(state(), obs())
    r2 = lab.U_update(
        r1["state_after"],
        obs(ev=evidence(eid="e2", event="c2", ancestry="a2", group="g1")),
    )
    assert r2["pass"] and r2["evidence_independent_for_update"] is False


def test_evidence_replay_identity_conflict_fails():
    r1 = lab.U_update(state(), obs())
    bad = evidence(eid="e1", event="c1", ancestry="DIFFERENT", group="g1")
    r2 = lab.U_update(r1["state_after"], obs(ev=bad))
    assert r2["pass"] is False
    assert r2["failure"].startswith("EVIDENCE_IDENTITY_REPLAY_CONFLICT")


def test_exact_replay_is_idempotent():
    r1 = lab.U_update(state(), obs())
    s = r1["state_after"]
    counts1 = [len(b["E_plus"]) + len(b["E_minus"]) + len(b["F"]) for b in s["branches"]]
    r2 = lab.U_update(s, obs())
    assert r2["pass"] and r2["replay_detected"]
    counts2 = [
        len(b["E_plus"]) + len(b["E_minus"]) + len(b["F"])
        for b in r2["state_after"]["branches"]
    ]
    assert counts2 == counts1


def test_context_unknown_does_not_falsify():
    s = state()
    s["branches"][2]["K"] = "UNKNOWN"
    r = lab.U_update(s, obs(result="R"))
    rel = {x["branch_id"]: x["derived_relation"] for x in r["derived_relations"]}
    assert rel["b2"] == "UNKNOWN_RELATION"
    assert r["state_after"]["branches"][2]["sigma"] == "LIVE_UNRESOLVED"


def test_branch_permutation_invariance():
    a = lab.D_resolve(state(), obs(result="G"))
    s = state()
    s["branches"] = list(reversed(s["branches"]))
    b = lab.D_resolve(s, obs(result="G"))
    assert a["resolution"]["resolved_branch"] == b["resolution"]["resolved_branch"] == "b2"


def test_discriminator_order_uses_derived_partition():
    dwide = disc(discriminator_id="wide")
    dnarrow = disc(
        discriminator_id="narrow",
        branch_predictions={"b0": "X", "b1": "X", "b2": "Y"},
        execution_cost_class=0,
    )
    r = lab.U_d_test_order(state(), [dnarrow, dwide])
    assert r["pass"]
    assert [x["discriminator_id"] for x in r["ordering"]] == ["wide", "narrow"]
    assert r["probability_output"] is False and r["truth_output"] is False


def test_truth_and_effect_authority_fail_closed():
    s = state()
    s["canonical_truth_allowed"] = True
    assert lab.U_update(s, obs())["pass"] is False
    d = disc()
    d["direct_effect_authority"] = True
    assert lab.D_resolve(state(), obs(d=d))["pass"] is False
