import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_gate_v2.py"
spec = importlib.util.spec_from_file_location("gate", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
lab = gate.lab


ANTI = [
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
]


def branch(bid, value):
    return {
        "branch_id": bid,
        "value": value,
        "context_predicate": "ctx",
        "evidence_for": [],
        "evidence_against": [],
        "falsifier": "explicit_test",
        "validity": "LIVE",
        "provenance": "synthetic:test",
        "epistemic_status": "HYPOTHESIS",
        "projection_visibility": True,
    }


def state(order=("b0", "b1", "b2")):
    values = {"b0": "alpha", "b1": "beta", "b2": "gamma"}
    return {
        "schema": lab.STATE_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch(bid, values[bid]) for bid in order],
    }


def base_row():
    return {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": "TEST_SHP_V2",
        "provenance_ancestry_id": "test-shp-v2-family",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "HYPERPOSITION_PROTOCOL",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "prompt": "synthetic test prompt",
        "target": "synthetic test target",
    }


def permutation_case(pid):
    return {
        "group_id": "pg1",
        "permutation_id": pid,
        "semantic_equivalence_key": "same_latent_episode",
        "target_semantic_key": "remain_unresolved",
        "branch_order_is_nuisance": True,
    }


def projection(s):
    return {
        "operation": "NONDESTRUCTIVE_VIEW",
        "context": "ctx",
        "visible_branch_ids": [b["branch_id"] for b in s["branches"]],
        "deletes_hidden_branches": False,
    }


def obs():
    return {
        "schema": lab.OBS_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "effect": "SUPPORT",
        "target_branch_ids": ["b0"],
        "evidence": {
            "evidence_id": "e1",
            "provenance_ancestry_id": "a1",
            "independence_group": "g1",
            "epistemic_type": "OBSERVED",
        },
    }


def state_only_row(order=("b0", "b1", "b2"), pid="p0"):
    s = state(order)
    rr = lab.D_resolve(s)["resolution"]
    row = base_row()
    row["semantic_hyperposition"] = {
        "schema": gate.SHP_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "episode_kind": "STATE_ONLY",
        "query_id": "q-state",
        "state_before": s,
        "state_after": None,
        "reference_resolution": rr,
        "anti_collapse": ANTI,
        "projection": projection(s),
        "permutation_case": permutation_case(pid),
    }
    return row


def update_row():
    s = state()
    o = obs()
    ur = lab.U_update(s, o)
    after = ur["state_after"]
    rr = lab.D_resolve(after)["resolution"]
    row = base_row()
    row["semantic_hyperposition"] = {
        "schema": gate.SHP_SCHEMA,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "episode_kind": "UPDATE",
        "query_id": "q-update",
        "state_before": s,
        "observation": o,
        "state_after": after,
        "reference_update": ur["updates"],
        "reference_resolution": rr,
        "anti_collapse": ANTI,
        "projection": projection(s),
        "permutation_case": permutation_case("p-update"),
    }
    return row


def test_valid_state_only_passes():
    r = gate.adjudicate(state_only_row())
    assert r["semantic_hyperposition_pass"], r["failures"]


def test_valid_update_matches_reference_labelers():
    r = gate.adjudicate(update_row())
    assert r["semantic_hyperposition_pass"], r["failures"]


def test_tampered_update_fails_closed():
    row = update_row()
    row["semantic_hyperposition"]["state_after"]["branches"][0]["validity"] = "FALSIFIED"
    r = gate.adjudicate(row)
    assert not r["semantic_hyperposition_pass"]
    assert "STATE_AFTER_DOES_NOT_MATCH_REFERENCE_U_UPDATE" in r["failures"]


def test_projection_cannot_reference_unknown_branch():
    row = state_only_row()
    row["semantic_hyperposition"]["projection"]["visible_branch_ids"].append("ghost")
    r = gate.adjudicate(row)
    assert not r["semantic_hyperposition_pass"]
    assert "PROJECTION_REFERENCES_UNKNOWN_BRANCH" in r["failures"]


def test_branch_order_permutation_group_passes():
    a = state_only_row(("b0", "b1", "b2"), "p0")
    b = state_only_row(("b2", "b0", "b1"), "p1")
    r = gate.adjudicate_permutation_group([a, b])
    assert r["permutation_group_pass"], r["failures"]


def test_permutation_group_rejects_target_key_change():
    a = state_only_row(("b0", "b1", "b2"), "p0")
    b = state_only_row(("b2", "b0", "b1"), "p1")
    b["semantic_hyperposition"]["permutation_case"]["target_semantic_key"] = "different"
    r = gate.adjudicate_permutation_group([a, b])
    assert not r["permutation_group_pass"]
    assert "TARGET_SEMANTIC_KEY_MISMATCH" in r["failures"]


def test_missing_anti_collapse_rule_fails():
    row = state_only_row()
    row["semantic_hyperposition"]["anti_collapse"].remove("NO_RECURRENCE_AS_EVIDENCE")
    r = gate.adjudicate(row)
    assert not r["semantic_hyperposition_pass"]
    assert any(x.startswith("ANTI_COLLAPSE_MISSING:") for x in r["failures"])


def test_state_only_does_not_accept_fake_resolution():
    row = state_only_row()
    row["semantic_hyperposition"]["reference_resolution"] = {
        "status": "RESOLVED_WITHIN_SYNTHETIC_WORLD",
        "resolved_branch": "b0",
        "basis": "MAJORITY",
    }
    r = gate.adjudicate(row)
    assert not r["semantic_hyperposition_pass"]
    assert "REFERENCE_STATE_RESOLUTION_MISMATCH" in r["failures"]
