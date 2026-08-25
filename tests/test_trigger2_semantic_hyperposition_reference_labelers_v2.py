#!/usr/bin/env python3
from copy import deepcopy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_reference_labelers_v2.py"
spec = importlib.util.spec_from_file_location("lab", P)
lab = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(lab)


def ev(eid, ancestry, group, payload, typ="OBSERVED"):
    return {
        "evidence_id": eid,
        "provenance_ancestry_id": ancestry,
        "independence_group": group,
        "payload_key": payload,
        "epistemic_type": typ,
    }


def branch(bid, value, status="HYPOTHESIS"):
    return {
        "branch_id": bid,
        "value": value,
        "context_predicate": "ALL",
        "evidence_for": [],
        "evidence_against": [],
        "falsifier": "disc:" + bid,
        "validity": "LIVE",
        "provenance": "SYNTHETIC",
        "epistemic_status": status,
        "visibility": "VISIBLE",
    }


state = {
    "schema": lab.STATE_SCHEMA,
    "query_id": "q1",
    "canonical_truth_allowed": False,
    "direct_effect_authority": False,
    "branches": [branch("b0", "A"), branch("b1", "B"), branch("b2", "C", "COUNTERHYPOTHESIS")],
}
obs = {
    "schema": lab.OBS_SCHEMA,
    "canonical_truth_allowed": False,
    "direct_effect_authority": False,
    "effect": "SUPPORT",
    "target_branch_ids": ["b0"],
    "evidence": ev("e1", "ancestry-a", "g1", "payload-x"),
}

# First evidence item is independent.
r1 = lab.U_update(state, obs)
assert r1["pass"] and r1["novel_independent_evidence"] is True
s1 = r1["state_after"]

# Repackaging the same underlying evidence under a DIFFERENT ancestry must not count twice.
obs2 = deepcopy(obs)
obs2["evidence"] = ev("e2", "ancestry-b", "g1", "payload-x")
r2 = lab.U_update(s1, obs2)
assert r2["pass"] and r2["novel_independent_evidence"] is False
assert len(r2["state_after"]["branches"][0]["evidence_for"]) == 1
assert r2["state_after"]["duplicate_evidence_receipts"]

# A genuinely new independence group is independent, but support cannot auto-resolve.
obs3 = deepcopy(obs)
obs3["evidence"] = ev("e3", "ancestry-c", "g2", "payload-x")
r3 = lab.U_update(r2["state_after"], obs3)
assert r3["novel_independent_evidence"] is True
assert r3["automatic_resolution_performed"] is False
assert lab.D_resolve(r3["state_after"])["resolution"]["status"] == "UNRESOLVED"

# Repeated independent but nondiscriminating support still cannot resolve.
s = r3["state_after"]
for i in range(3, 7):
    o = deepcopy(obs)
    o["evidence"] = ev(f"e{i+1}", f"a{i}", f"g{i}", f"p{i}")
    s = lab.U_update(s, o)["state_after"]
assert lab.D_resolve(s)["resolution"]["status"] == "UNRESOLVED"

# Only an adequate explicit discriminator can resolve this unresolved set.
disc = {
    "schema": lab.DISC_SCHEMA,
    "canonical_truth_allowed": False,
    "direct_effect_authority": False,
    "winner_branch_id": "b0",
    "separates_live_branch_ids": ["b0", "b1", "b2"],
    "evidence_qualified": True,
}
dr = lab.D_resolve(s, disc)
assert dr["resolution"]["resolved_branch"] == "b0"

# Projection hides but never deletes or resolves a branch.
proj = deepcopy(s)
proj["branches"][1]["visibility"] = "PROJECTED_OUT"
assert len(proj["branches"]) == 3
assert lab.D_resolve(proj)["resolution"]["status"] == "UNRESOLVED"

# U(d): a full three-way discriminator outranks a cheaper but nonseparating test.
tests = [
    {
        "schema": lab.DISC_SCHEMA,
        "discriminator_id": "cheap",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "admissible": True,
        "separates_pairs": [["b0", "b1"]],
        "risk_rank": 0,
        "cost_rank": 0,
        "coordination_rank": 0,
    },
    {
        "schema": lab.DISC_SCHEMA,
        "discriminator_id": "separating",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "admissible": True,
        "separates_pairs": [["b0", "b1"], ["b0", "b2"], ["b1", "b2"]],
        "risk_rank": 1,
        "cost_rank": 2,
        "coordination_rank": 2,
    },
]
ordr = lab.U_d_test_order(s, tests)
assert ordr["ordering"][0]["discriminator_id"] == "separating"
assert ordr["probability_output"] is False
assert ordr["expected_information_gain_output"] is False

# Salience is attention order only, never truth or resolution authority.
sal = lab.f_salience_rank([
    {"item_id": "loud", "actionability_rank": 0, "scope_rank": 0, "freshness_rank": 0},
    {"item_id": "quiet", "actionability_rank": 1, "scope_rank": 1, "freshness_rank": 1},
])
assert sal["truth_output"] is False
assert sal["resolution_authority_output"] is False

# GRF epistemic guard: hypotheses/unknown cannot self-promote to observed.
assert lab.epistemic_guard("HYPOTHESIS", "OBSERVED")["transition_allowed"] is False
assert lab.epistemic_guard("UNKNOWN", "OBSERVED")["transition_allowed"] is False

# Full h_i structure is mandatory at the labeler boundary.
bad = deepcopy(state)
del bad["branches"][0]["falsifier"]
assert lab.U_update(bad, obs)["pass"] is False

print("PASS v2 semantic-Hyperposition labelers: full h_i, evidence independence, anti-collapse, discriminator, salience, GRF typing")
