import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "tools" / "trigger2_semantic_hyperposition_gate_v3.py"
spec = importlib.util.spec_from_file_location("gate3", P)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
lab = gate.lab


def world():
    return {
        "schema": lab.WORLD_SCHEMA,
        "world_id": "gate-w1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"mode": "A"},
        "tests": {
            "probe": {
                "allowed_outcomes": ["YES", "NO"],
                "mismatch_effect": "FALSIFIES",
                "risk_rank": 0,
                "cost_rank": 0,
                "coordination_rank": 0,
            }
        },
        "merge_policy": "NONE",
        "branch_birth_rules": [],
    }


def branch(bid, value, prediction):
    return {
        "branch_id": bid,
        "v": value,
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": {"scope": "synthetic"},
        "A": {"origin": "gate-test"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"probe": prediction},
    }


def state(ids=("a", "b")):
    return {
        "schema": lab.STATE_SCHEMA,
        "query_id": "q-gate",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch(ids[0], "YES_BRANCH", "YES"), branch(ids[1], "NO_BRANCH", "NO")],
    }


def event(eid="e1"):
    return {
        "schema": lab.EVENT_SCHEMA,
        "event_id": eid,
        "correlation_ancestry_id": "anc-" + eid,
        "independence_group": "group-" + eid,
        "payload_key": "payload-" + eid,
        "provenance": "synthetic:gate-test",
        "epistemic_type": "OBSERVED",
        "test_id": "probe",
        "observed_outcome": "YES",
        "independence_qualified": True,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def make_row(ids=("a", "b"), pid="p0"):
    w = world()
    s = state(ids)
    e = event("e1")
    d = lab.derive_relations(w, s, e)
    u = lab.u_state(w, s, e)
    r = lab.d_resolve(w, u["state_after"])
    return {
        "schema": "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1",
        "evidence_class": "METHOD_ONLY",
        "reality_level": "R2",
        "family_id": "GATE3_F01",
        "provenance_ancestry_id": "gate3-family-v1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "fact_status": "NOT_APPLICABLE",
        "target_type": "HYPERPOSITION_TRANSITION",
        "split": "TRAIN",
        "split_unit": "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY",
        "selected_using_holdout": False,
        "prompt": "A formal synthetic probe returns YES. Update the unresolved alternatives without treating the task-local label as world truth.",
        "target": "Support the matching alternative, falsify only the formally incompatible alternative, preserve the branch structure, and keep canonical truth authority false.",
        "audit_metadata_model_visible": False,
        "training_admission_scope": "CANDIDATE_SOURCE_ONLY",
        "formal_hyperposition": {
            "schema": gate.EPISODE_SCHEMA,
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "world": w,
            "state_before": s,
            "event": e,
            "reference_binding": gate.reference_binding(w),
            "derived_target_branch_ids": d["target_branch_ids"],
            "derived_relations": d["relations"],
            "derivation_receipt": d["derivation_receipt"],
            "state_after": u["state_after"],
            "update_receipt": u["updates"],
            "independent_evidence_credit": u["independent_evidence_credit"],
            "nonindependence_reasons": u["nonindependence_reasons"],
            "born_branch_ids": u["born_branch_ids"],
            "task_resolution": r["resolution"],
            "model_visible_contains_reference_hashes": False,
            "model_visible_contains_branch_ids": False,
            "permutation_case": {
                "group_id": "pg1",
                "permutation_id": pid,
                "semantic_equivalence_key": "same-formal-world-event",
                "target_semantic_key": "yes-supported-no-falsified",
            },
        },
    }


def test_valid_derivation_bound_candidate_passes():
    r = gate.adjudicate(make_row())
    assert r["candidate_admission_pass"], r["failures"]
    assert r["training_credit_minted"] is False


def test_tampered_relation_label_fails():
    row = make_row()
    row["formal_hyperposition"]["derived_relations"]["a"] = "FALSIFIES"
    r = gate.adjudicate(row)
    assert not r["candidate_admission_pass"]
    assert "DERIVED_RELATIONS_MISMATCH" in r["failures"]


def test_tampered_state_after_fails():
    row = make_row()
    row["formal_hyperposition"]["state_after"]["branches"][0]["sigma"] = "FALSIFIED"
    r = gate.adjudicate(row)
    assert not r["candidate_admission_pass"]
    assert "STATE_AFTER_MISMATCH" in r["failures"]


def test_source_binding_mismatch_fails():
    row = make_row()
    row["formal_hyperposition"]["reference_binding"]["labeler_source_sha256"] = "0" * 64
    r = gate.adjudicate(row)
    assert not r["candidate_admission_pass"]
    assert "REFERENCE_SOURCE_OR_WORLD_BINDING_MISMATCH" in r["failures"]


def test_legacy_causal_hyperposition_field_is_rejected():
    row = make_row()
    row["hyperposition"] = {"resolution_status": "RESOLVED_BY_EVIDENCE"}
    r = gate.adjudicate(row)
    assert not r["candidate_admission_pass"]
    assert "LEGACY_CAUSAL_HYPERPOSITION_FIELD_FORBIDDEN_ON_FORMAL_SYNTHETIC_EPISODE" in r["failures"]


def test_audit_hashes_cannot_be_declared_model_visible():
    row = make_row()
    row["formal_hyperposition"]["model_visible_contains_reference_hashes"] = True
    r = gate.adjudicate(row)
    assert not r["candidate_admission_pass"]
    assert "REFERENCE_HASHES_MUST_NOT_BE_MODEL_VISIBLE" in r["failures"]


def test_branch_order_and_id_renaming_permutation_group_passes():
    a = make_row(("a", "b"), "p0")
    b = make_row(("renamed_yes", "renamed_no"), "p1")
    # Reverse row B's branch presentation while keeping its formal semantics unchanged.
    b["formal_hyperposition"]["state_before"]["branches"].reverse()
    # Recompute all exact reference labels after the presentation-only mutation.
    ep = b["formal_hyperposition"]
    d = lab.derive_relations(ep["world"], ep["state_before"], ep["event"])
    u = lab.u_state(ep["world"], ep["state_before"], ep["event"])
    r = lab.d_resolve(ep["world"], u["state_after"])
    ep["derived_target_branch_ids"] = d["target_branch_ids"]
    ep["derived_relations"] = d["relations"]
    ep["derivation_receipt"] = d["derivation_receipt"]
    ep["state_after"] = u["state_after"]
    ep["update_receipt"] = u["updates"]
    ep["independent_evidence_credit"] = u["independent_evidence_credit"]
    ep["nonindependence_reasons"] = u["nonindependence_reasons"]
    ep["born_branch_ids"] = u["born_branch_ids"]
    ep["task_resolution"] = r["resolution"]
    result = gate.adjudicate_permutation_group([a, b])
    assert result["permutation_group_pass"], result["failures"]


def test_permutation_group_rejects_semantic_target_change():
    a = make_row(("a", "b"), "p0")
    b = make_row(("renamed_yes", "renamed_no"), "p1")
    b["formal_hyperposition"]["permutation_case"]["target_semantic_key"] = "different"
    result = gate.adjudicate_permutation_group([a, b])
    assert not result["permutation_group_pass"]
    assert "TARGET_SEMANTIC_KEY_MISMATCH" in result["failures"]
