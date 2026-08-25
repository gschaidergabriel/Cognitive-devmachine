import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_reference_labelers_v1.py"
spec = importlib.util.spec_from_file_location("lab", P)
lab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lab)


def state():
    return {
        "schema": lab.STATE_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [
            {"branch_id": "b0", "validity": "LIVE", "evidence_for": [], "evidence_against": []},
            {"branch_id": "b1", "validity": "LIVE", "evidence_for": [], "evidence_against": []},
            {"branch_id": "b2", "validity": "LIVE", "evidence_for": [], "evidence_against": []},
        ],
    }


def obs(effect="SUPPORT", targets=None, eid="e1", ancestry="a1"):
    return {
        "schema": lab.OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "effect": effect,
        "target_branch_ids": targets or ["b0"],
        "evidence": {
            "evidence_id": eid,
            "provenance_ancestry_id": ancestry,
            "independence_group": "g1",
            "epistemic_type": "OBSERVED",
        },
    }


def disc(**kw):
    x = {
        "schema": lab.DISC_SCHEMA,
        "discriminator_id": "d1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "admissible": True,
        "winner_branch_id": "b0",
        "separates_live_branch_ids": ["b0", "b1", "b2"],
        "separates_pairs": [["b0", "b1"], ["b0", "b2"]],
        "cost_rank": 1,
    }
    x.update(kw)
    return x


def test_update_preserves_branch_set_and_does_not_resolve():
    r = lab.U_update(state(), obs())
    assert r["pass"]
    assert r["branch_count_before"] == r["branch_count_after"] == 3
    assert r["automatic_resolution_performed"] is False


def test_same_ancestry_is_nonindependent():
    r1 = lab.U_update(state(), obs(effect="PROVE"))
    s1 = r1["state_after"]
    r2 = lab.U_update(s1, obs(effect="PROVE", eid="e2", ancestry="a1"))
    assert r2["updates"][0]["independent_for_update"] is False
    assert r2["updates"][0]["validity_before"] == "PROVEN_WITHIN_SYNTHETIC_WORLD"


def test_falsify_marks_but_never_deletes():
    r = lab.U_update(state(), obs(effect="FALSIFY", targets=["b1"]))
    assert r["pass"]
    assert len(r["state_after"]["branches"]) == 3
    b1 = next(b for b in r["state_after"]["branches"] if b["branch_id"] == "b1")
    assert b1["validity"] == "FALSIFIED"


def test_no_discriminator_no_resolution():
    r = lab.D_resolve(state())
    assert r["pass"] and r["resolution"]["status"] == "UNRESOLVED"


def test_explicit_proof_resolves_without_deletion():
    s = lab.U_update(state(), obs(effect="PROVE", targets=["b0"]))["state_after"]
    r = lab.D_resolve(s)
    assert r["resolution"]["resolved_branch"] == "b0"
    assert r["retained_branch_ids"] == ["b0", "b1", "b2"]


def test_incomplete_discriminator_does_not_resolve():
    d = disc(separates_live_branch_ids=["b0", "b1"])
    r = lab.D_resolve(state(), d)
    assert r["pass"] and r["resolution"]["status"] == "UNRESOLVED"


def test_full_discriminator_resolves_task_locally():
    r = lab.D_resolve(state(), disc())
    assert r["pass"] and r["resolution"]["resolved_branch"] == "b0"
    assert r["canonical_truth_minted"] is False


def test_discriminator_order_is_ordinal_not_probability():
    ds = [
        disc(discriminator_id="cheap", separates_pairs=[["b0", "b1"]], cost_rank=0),
        disc(discriminator_id="wide", separates_pairs=[["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], cost_rank=5),
        disc(discriminator_id="bad", admissible=False, separates_pairs=[["b0", "b1"], ["b0", "b2"], ["b1", "b2"]], cost_rank=0),
    ]
    r = lab.U_d_test_order(state(), ds)
    assert [x["discriminator_id"] for x in r["ordering"]] == ["wide", "cheap", "bad"]
    assert r["probability_output"] is False and r["truth_output"] is False


def test_salience_never_outputs_truth_or_probability():
    r = lab.f_salience_rank([
        {"item_id": "x", "actionability_rank": 1, "scope_rank": 0, "freshness_rank": 0},
        {"item_id": "y", "actionability_rank": 0, "scope_rank": 9, "freshness_rank": 9},
    ])
    assert [x["item_id"] for x in r["ranking"]] == ["y", "x"]
    assert r["truth_output"] is False
    assert r["probability_output"] is False
    assert r["evidence_strength_output"] is False


def test_truth_authority_leak_fails_closed():
    s = state()
    s["canonical_truth_allowed"] = True
    assert lab.D_resolve(s)["pass"] is False
