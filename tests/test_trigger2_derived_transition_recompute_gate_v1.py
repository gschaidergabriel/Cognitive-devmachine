from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DERIVER_PATH = ROOT / "tools" / "trigger2_synthetic_relation_deriver_v1.py"
GATE_PATH = ROOT / "tools" / "trigger2_derived_transition_recompute_gate_v1.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DERIVER = load(DERIVER_PATH, "trigger2_synthetic_relation_deriver_v1_test")
GATE = load(GATE_PATH, "trigger2_derived_transition_recompute_gate_v1_test")


def branch(bid: str, prediction: str) -> dict:
    return {
        "branch_id": bid,
        "v": f"world:{bid}",
        "K": "APPLIES",
        "E_plus": [],
        "E_minus": [],
        "F": [],
        "T": "episode",
        "A": {"fixture": "recompute"},
        "sigma": "LIVE_UNRESOLVED",
        "projection_visibility": "VISIBLE",
        "predictions": {"disc:1": prediction},
    }


def state() -> dict:
    return {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "branches": [branch("b0", "YES"), branch("b1", "NO")],
        "discriminator_catalog": {
            "disc:1": {
                "test_id": "disc:1",
                "admissible": True,
                "exact_outcome_discriminator": True,
            }
        },
    }


def observation() -> dict:
    return {
        "evidence_event_id": "ev:1",
        "correlation_ancestry_id": "anc:1",
        "independence_group": "grp:1",
        "provenance": {"fixture": "recompute"},
        "test_id": "disc:1",
        "observed_outcome": "YES",
    }


def good_row() -> dict:
    before = state()
    obs = observation()
    derived = DERIVER.derive(before, obs)
    return {
        "derived_transition": {
            "joint_state": {
                "representation": "WHOLE_WORLD_BRANCHES",
                "branch_semantics": "EACH_BRANCH_IS_COMPLETE_LIVE_WORLD_HYPOTHESIS",
                "cartesian_completion_allowed": False,
            },
            "H_before": before,
            "observation": obs,
            "H_after": derived["state_after"],
            "relations": derived["relations"],
            "resolution": derived["resolution"],
            "discriminator_evaluation": derived["discriminator_evaluation"],
            "derivation_receipt": derived["derivation_receipt"],
            "resolution_policy": {
                "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
                "precondition_ids": ["ev:1"],
            },
            "caller_asserted_relation_allowed": False,
            "caller_asserted_winner_allowed": False,
            "branch_birth_allowed": False,
        }
    }


def failures(row: dict) -> list[str]:
    return GATE.audit_row(row, "test-row")["failures"]


def test_exact_recomputed_transition_passes() -> None:
    result = GATE.audit_row(good_row(), "test-row")
    assert result["pass"], result["failures"]


def test_tampered_relation_target_fails() -> None:
    row = good_row()
    row["derived_transition"]["relations"]["b1"] = "COUNTERS"
    assert "recomputation_mismatch:relations" in failures(row)


def test_tampered_state_after_fails() -> None:
    row = good_row()
    row["derived_transition"]["H_after"]["branches"][1]["sigma"] = "WEAKENED_UNRESOLVED"
    assert "recomputation_mismatch:H_after" in failures(row)


def test_tampered_resolution_winner_fails() -> None:
    row = good_row()
    row["derived_transition"]["resolution"]["resolved_branch_id"] = "b1"
    assert "recomputation_mismatch:resolution" in failures(row)


def test_tampered_discriminator_receipt_fails() -> None:
    row = good_row()
    row["derived_transition"]["discriminator_evaluation"]["self_asserted_winner"] = True
    assert "recomputation_mismatch:discriminator_evaluation" in failures(row)


def test_tampered_derivation_receipt_fails() -> None:
    row = good_row()
    row["derived_transition"]["derivation_receipt"]["self_asserted_label"] = True
    assert "recomputation_mismatch:derivation_receipt" in failures(row)


def test_cartesian_completion_is_forbidden() -> None:
    row = good_row()
    row["derived_transition"]["joint_state"]["cartesian_completion_allowed"] = True
    assert "implicit_cartesian_completion_not_forbidden" in failures(row)


def test_factorized_joint_state_not_silently_admitted() -> None:
    row = good_row()
    row["derived_transition"]["joint_state"]["representation"] = "EXPLICIT_COMPATIBILITY_SETS"
    assert "derived_transition_v1_requires_whole_world_branches" in failures(row)


def test_resolution_policy_must_bind_current_event() -> None:
    row = good_row()
    row["derived_transition"]["resolution_policy"]["precondition_ids"] = ["ev:other"]
    assert "resolution_policy_missing_current_event_precondition" in failures(row)


def test_caller_assertion_flags_fail_closed() -> None:
    row = good_row()
    row["derived_transition"]["caller_asserted_relation_allowed"] = True
    row["derived_transition"]["caller_asserted_winner_allowed"] = True
    fs = failures(row)
    assert "caller_asserted_relation_must_be_false" in fs
    assert "caller_asserted_winner_must_be_false" in fs


def test_branch_birth_flag_fails_closed() -> None:
    row = good_row()
    row["derived_transition"]["branch_birth_allowed"] = True
    assert "branch_birth_not_admitted_in_v1" in failures(row)


def test_branch_order_permutation_preserves_semantic_winner_after_recompute() -> None:
    row = good_row()
    before = copy.deepcopy(row["derived_transition"]["H_before"])
    before["branches"] = list(reversed(before["branches"]))
    derived = DERIVER.derive(before, row["derived_transition"]["observation"])
    row["derived_transition"]["H_before"] = before
    row["derived_transition"]["H_after"] = derived["state_after"]
    row["derived_transition"]["relations"] = derived["relations"]
    row["derived_transition"]["resolution"] = derived["resolution"]
    row["derived_transition"]["discriminator_evaluation"] = derived["discriminator_evaluation"]
    row["derived_transition"]["derivation_receipt"] = derived["derivation_receipt"]
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]
    assert row["derived_transition"]["resolution"]["resolved_branch_id"] == "b0"
