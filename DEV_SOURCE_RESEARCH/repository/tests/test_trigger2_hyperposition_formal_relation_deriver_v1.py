#!/usr/bin/env python3
import importlib.util
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_hyperposition_formal_relation_deriver_v1.py"
s = importlib.util.spec_from_file_location("d", P)
d = importlib.util.module_from_spec(s)
assert s and s.loader
s.loader.exec_module(d)


def b(i):
    return {
        "schema": d.BRANCH_SCHEMA,
        "branch_id": f"b{i}",
        "v_semantic_value": f"ALT{i}",
        "K_context_predicate": "ctx",
        "E_plus": [],
        "E_minus": [],
        "F_falsifier": f"f{i}",
        "T_validity_scope": "episode",
        "A_origin_provenance": f"syn:b{i}",
        "sigma_epistemic_status": "HYPOTHESIS",
        "projection_visibility": "VISIBLE",
        "validity": "LIVE",
    }


branches = [b(0), b(1), b(2)]
world = {
    "schema": d.WORLD_SCHEMA,
    "world_id": "w1",
    "canonical_truth_allowed": False,
    "direct_effect_authority": False,
    "model_visible": False,
    "tests": [
        {
            "schema": d.TEST_SCHEMA,
            "test_id": "t_sep",
            "admissible": True,
            "observable": True,
            "deterministic_total": True,
            "independence_group": "ig-sep",
            "cost_units": 2,
            "predicted_outcome_by_branch": {"b0": "red", "b1": "blue", "b2": "green"},
        },
        {
            "schema": d.TEST_SCHEMA,
            "test_id": "t_weak",
            "admissible": True,
            "observable": True,
            "deterministic_total": True,
            "independence_group": "ig-weak",
            "cost_units": 0,
            "predicted_outcome_by_branch": {"b0": "x", "b1": "x", "b2": "y"},
        },
    ],
}

# A unique predicted outcome mechanically yields one support and two falsifications.
r = d.derive_outcome(branches, world, test_id="t_sep", observed_outcome="red", evidence_id="e1")
assert r["observation"]["branch_relations"] == {"b0": "SUPPORT", "b1": "FALSIFY", "b2": "FALSIFY"}
assert r["observation"]["evidence"]["decision_role"] == "DECISIVE_SUPPORT"
assert r["resolve_context"]["all_other_branches_explicitly_falsified"] is True
assert r["model_visible"] is False

# A non-unique match is nondiscriminating even though some other branch is falsified.
r2 = d.derive_outcome(branches, world, test_id="t_weak", observed_outcome="x", evidence_id="e2")
assert r2["observation"]["evidence"]["decision_role"] == "NONDECISIVE"
assert r2["resolve_context"]["all_other_branches_explicitly_falsified"] is False

# Pair separation is computed from predicted outcomes rather than caller-supplied counts.
m = d.derive_discriminator_metadata(branches, world)
by = {x["test_id"]: x for x in m}
assert len(by["t_sep"]["separates_branch_pairs"]) == 3
assert len(by["t_weak"]["separates_branch_pairs"]) == 2

# Mutation: changing the observed outcome changes the mechanically derived relations.
r3 = d.derive_outcome(branches, world, test_id="t_sep", observed_outcome="blue", evidence_id="e3")
assert r3["observation"]["branch_relations"]["b1"] == "SUPPORT"
assert r3["observation"]["branch_relations"]["b0"] == "FALSIFY"

# Mutation: changing a branch prediction changes the derived partition.
w2 = deepcopy(world)
w2["tests"][1]["predicted_outcome_by_branch"]["b1"] = "z"
m2 = d.derive_discriminator_metadata(branches, w2)
by2 = {x["test_id"]: x for x in m2}
assert len(by2["t_weak"]["separates_branch_pairs"]) == 3

print("PASS formal Hyperposition relation derivation: relations, decision roles, resolve context and pair separation are computed")
