from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger2_semantic_hyperposition_universal_gate_v2.py"
SPEC = importlib.util.spec_from_file_location("trigger2_semantic_hyperposition_universal_gate_v2", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def evidence(eid: str, ancestry: str, group: str, relation: str) -> dict:
    return {
        "evidence_id": eid,
        "provenance_or_ancestry_id": ancestry,
        "independence_group": group,
        "relation": relation,
    }


def branch(
    bid: str,
    value: str,
    *,
    e_plus: list[dict] | None = None,
    e_minus: list[dict] | None = None,
) -> dict:
    return {
        "id": bid,
        "v": value,
        "K": "ctx:q",
        "E_plus": list(e_plus or []),
        "E_minus": list(e_minus or []),
        "F": "explicit_discriminator",
        "T": "episode",
        "A": "synthetic:test-family",
        "sigma": "HYPOTHESIS",
    }


def good_row() -> dict:
    b0 = branch(
        "b0",
        "QUERY_TRUE",
        e_plus=[evidence("e0", "src:0", "ind:0", "SUPPORTS")],
    )
    b1 = branch(
        "b1",
        "QUERY_FALSE",
        e_minus=[evidence("e0", "src:0", "ind:0", "CONTRADICTS")],
    )
    return {
        "semantic_hyperposition": {
            "schema": "SEMANTIC_HYPERPOSITION_FRAME/v2",
            "model_input_in_rendered_prompt": True,
            "supervision_in_target": True,
            "branch_order_semantically_irrelevant": True,
            "joint_state": {
                "representation": "WHOLE_WORLD_BRANCHES",
                "cartesian_completion_allowed": False,
            },
            "model_input": {
                "H_before": {"branches": [copy.deepcopy(b0), copy.deepcopy(b1)]},
                "operation": {
                    "type": "NONDISTRIMINATING_OBSERVATION",
                    "affected_branch_ids": [],
                    "allows_counterhypothesis_birth": False,
                },
            },
            "supervision": {
                "H_after": {"branches": [copy.deepcopy(b0), copy.deepcopy(b1)]},
                "resolution": {"status": "UNRESOLVED"},
                "falsifier": "run:explicit_discriminator",
                "output_projection": {
                    "deletes_unselected_branches": False,
                    "semantic_state_collapsed": False,
                },
            },
        }
    }


def failures(row: dict) -> list[str]:
    return GATE.audit_row(row, "test-row")["failures"]


def test_valid_joint_state_row_passes() -> None:
    result = GATE.audit_row(good_row(), "test-row")
    assert result["pass"], result["failures"]


def test_rejects_untyped_string_evidence() -> None:
    row = good_row()
    row["semantic_hyperposition"]["model_input"]["H_before"]["branches"][0]["E_plus"] = ["fact:x"]
    assert any("evidence_item_not_object" in failure for failure in failures(row))


def test_rejects_implicit_cartesian_completion() -> None:
    row = good_row()
    row["semantic_hyperposition"]["joint_state"]["cartesian_completion_allowed"] = True
    assert "implicit_cartesian_completion_not_forbidden" in failures(row)


def test_factorized_joint_state_requires_valid_compatibility_sets() -> None:
    row = good_row()
    row["semantic_hyperposition"]["joint_state"] = {
        "representation": "EXPLICIT_COMPATIBILITY_SETS",
        "cartesian_completion_allowed": False,
        "live_worlds": [
            {"world_id": "w0", "members": ["b0"]},
            {"world_id": "w1", "members": ["b-missing"]},
        ],
    }
    assert any("unknown_branch_members:b-missing" in failure for failure in failures(row))


def test_unaffected_branch_must_remain_semantically_identical() -> None:
    row = good_row()
    after_b1 = row["semantic_hyperposition"]["supervision"]["H_after"]["branches"][1]
    after_b1["sigma"] = "OBSERVED"
    assert "unaffected_branch_mutated:b1" in failures(row)


def test_declared_affected_branch_may_change() -> None:
    row = good_row()
    row["semantic_hyperposition"]["model_input"]["operation"]["affected_branch_ids"] = ["b1"]
    row["semantic_hyperposition"]["supervision"]["H_after"]["branches"][1]["sigma"] = "OBSERVED"
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]


def test_output_selection_cannot_collapse_unresolved_state() -> None:
    row = good_row()
    row["semantic_hyperposition"]["supervision"]["output_projection"]["semantic_state_collapsed"] = True
    assert "output_selection_collapses_unresolved_semantic_state" in failures(row)


def test_resolved_state_requires_reopen_policy() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "discriminator_id": "disc:1",
    }
    assert "resolved_without_valid_reopen_policy" in failures(row)


def test_reopenable_resolution_requires_preconditions() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "discriminator_id": "disc:1",
        "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
        "precondition_ids": [],
    }
    assert "reopenable_resolution_missing_precondition_ids" in failures(row)


def test_immutable_synthetic_resolution_can_pass() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "deterministic_policy_id": "synthetic-proof:v1",
        "reopen_policy": "IMMUTABLE_SYNTHETIC_PROOF",
    }
    frame["supervision"]["output_projection"]["semantic_state_collapsed"] = True
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]


def test_new_branch_requires_declared_counterhypothesis_birth() -> None:
    row = good_row()
    b2 = branch("b2", "QUERY_UNKNOWN")
    row["semantic_hyperposition"]["supervision"]["H_after"]["branches"].append(b2)
    assert any(
        failure.startswith("new_branch_without_declared_counterhypothesis_birth:b2")
        for failure in failures(row)
    )


def test_counterhypothesis_birth_can_be_declared() -> None:
    row = good_row()
    b2 = branch("b2", "QUERY_UNKNOWN")
    row["semantic_hyperposition"]["model_input"]["operation"]["allows_counterhypothesis_birth"] = True
    row["semantic_hyperposition"]["supervision"]["H_after"]["branches"].append(b2)
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]
