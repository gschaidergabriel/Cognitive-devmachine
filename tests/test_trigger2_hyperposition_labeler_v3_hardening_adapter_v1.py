from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "trigger2_hyperposition_labeler_v3_hardening_adapter_v1.py"
SPEC = importlib.util.spec_from_file_location("trigger2_hyperposition_labeler_v3_hardening_adapter_v1", PATH)
assert SPEC is not None and SPEC.loader is not None
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)
V3 = A.V3


def world() -> dict:
    return {
        "schema": V3.WORLD_SCHEMA,
        "world_id": "world:test",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "context": {"scope": "x"},
        "tests": {
            "disc:1": {
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


def branch(bid: str, outcome: str) -> dict:
    return {
        "branch_id": bid,
        "v": f"world:{bid}",
        "K": "ALWAYS",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "episode",
        "A": {"fixture": "adapter"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": True,
        "predictions": {"disc:1": outcome},
    }


def state() -> dict:
    return {
        "schema": V3.STATE_SCHEMA,
        "query_id": "q:1",
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "joint_state": {
            "representation": "WHOLE_WORLD_BRANCHES",
            "branch_semantics": "EACH_BRANCH_IS_COMPLETE_LIVE_WORLD_HYPOTHESIS",
            "cartesian_completion_allowed": False,
        },
        "branches": [branch("b0", "YES"), branch("b1", "NO")],
    }


def event(*, event_id: str = "ev:1", ancestry: str = "anc:1", group: str = "grp:1", outcome: str = "YES") -> dict:
    return {
        "schema": A.ADAPTER_EVENT_SCHEMA,
        "event_id": event_id,
        "correlation_ancestry_id": ancestry,
        "independence_group": group,
        "payload_key": "payload:" + event_id,
        "provenance": "synthetic:test",
        "epistemic_type": "OBSERVED",
        "test_id": "disc:1",
        "observed_outcome": outcome,
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
    }


def receipt(ev: dict, *, admissible: bool = True, executed: bool = True) -> dict:
    return {
        "schema": A.EXECUTION_RECEIPT_SCHEMA,
        "receipt_id": "receipt:" + ev["event_id"],
        "world_id": "world:test",
        "test_id": ev["test_id"],
        "event_id": ev["event_id"],
        "observed_outcome": ev["observed_outcome"],
        "source_digest": "sha256:fixture",
        "executed": executed,
        "admissible": admissible,
        "observable": True,
    }


def test_caller_independence_qualification_is_forbidden() -> None:
    ev = event()
    ev["independence_qualified"] = True
    out = A.u_state(world(), state(), ev)
    assert not out["pass"]
    assert out["failure"] == "CALLER_INDEPENDENCE_QUALIFICATION_FORBIDDEN"


def test_independence_is_derived_and_same_group_is_nonindependent() -> None:
    s = state()
    first = A.u_state(world(), s, event(event_id="ev:1", ancestry="anc:1", group="grp:1"))
    assert first["pass"]
    assert first["event_identity"]["derived_independence_qualified"] is True
    second_ev = event(event_id="ev:2", ancestry="anc:2", group="grp:1")
    second = A.u_state(world(), first["state_after"], second_ev)
    assert second["pass"]
    assert second["event_identity"]["derived_independence_qualified"] is False
    assert "INDEPENDENCE_GROUP_REUSE" in second["event_identity"]["derived_nonindependence_reasons"]


def test_exact_replay_is_idempotent_but_mutated_same_id_fails() -> None:
    ev = event()
    first = A.u_state(world(), state(), ev)
    assert first["pass"]
    replay = A.u_state(world(), first["state_after"], ev)
    assert replay["pass"]
    assert replay["event_identity"]["exact_replay"] is True

    mutated = event(outcome="NO")
    bad = A.u_state(world(), first["state_after"], mutated)
    assert not bad["pass"]
    assert bad["failure"] == "EVENT_ID_MUTATED_IMMUTABLE_PAYLOAD"


def test_resolution_requires_executed_admissible_receipt() -> None:
    ev = event()
    no_exec = A.update_and_resolve(world(), state(), ev, receipt(ev, executed=False))
    assert not no_exec["pass"]
    assert no_exec["failure"] == "SYNTHETIC_DISCRIMINATOR_NOT_EXECUTED"

    inadmissible = A.update_and_resolve(world(), state(), ev, receipt(ev, admissible=False))
    assert not inadmissible["pass"]
    assert inadmissible["failure"] == "SYNTHETIC_DISCRIMINATOR_NOT_ADMISSIBLE"


def test_valid_receipt_can_support_task_local_resolution_without_truth_credit() -> None:
    ev = event()
    out = A.update_and_resolve(world(), state(), ev, receipt(ev))
    assert out["pass"], out
    assert out["resolution"]["status"] == "RESOLVED"
    assert out["resolution_provenance"]["execution_receipt_id"] == "receipt:ev:1"
    assert out["canonical_truth_minted"] is False
    assert out["direct_effect_authority_minted"] is False
    assert out["training_credit_minted"] is False


def test_joint_state_cartesian_completion_fails_closed() -> None:
    s = state()
    s["joint_state"]["cartesian_completion_allowed"] = True
    out = A.u_state(world(), s, event())
    assert not out["pass"]
    assert out["failure"] == "IMPLICIT_CARTESIAN_COMPLETION_FORBIDDEN"


def test_factorized_joint_state_is_not_silently_admitted() -> None:
    s = state()
    s["joint_state"]["representation"] = "EXPLICIT_COMPATIBILITY_SETS"
    out = A.u_state(world(), s, event())
    assert not out["pass"]
    assert out["failure"] == "JOINT_STATE_REQUIRES_WHOLE_WORLD_BRANCHES"
