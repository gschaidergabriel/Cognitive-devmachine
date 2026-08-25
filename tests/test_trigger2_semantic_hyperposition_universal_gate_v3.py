from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger2_semantic_hyperposition_universal_gate_v3.py"
SPEC = importlib.util.spec_from_file_location("trigger2_semantic_hyperposition_universal_gate_v3", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def evidence(
    eid: str,
    ancestry: str,
    group: str,
    relation: str,
    *,
    epistemic_type: str = "OBSERVED",
    independent_for_update: bool | None = None,
) -> dict:
    out = {
        "evidence_id": eid,
        "provenance_ancestry_id": ancestry,
        "independence_group": group,
        "epistemic_type": epistemic_type,
        "relation": relation,
    }
    if independent_for_update is not None:
        out["independent_for_update"] = independent_for_update
    return out


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
            "schema": "SEMANTIC_HYPERPOSITION_FRAME/v3",
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
                    "type": "NONDISCRIMINATING_OBSERVATION",
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


def add_valid_update_receipt(row: dict, *, kind: str = "EXECUTABLE_TASK_WORLD_RELATION") -> None:
    row["semantic_hyperposition"]["supervision"]["derivation_receipt"] = {
        "kind": kind,
        "evaluator_id": "synthetic-evaluator:v1",
        "input_digest": "sha256:input",
        "output_digest": "sha256:output",
        "self_asserted_label": False,
    }


def test_valid_noop_joint_state_row_passes() -> None:
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


def test_factorized_joint_state_rejects_unknown_member() -> None:
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


def test_rejects_evidence_id_replay_with_changed_ancestry() -> None:
    row = good_row()
    after = row["semantic_hyperposition"]["supervision"]["H_after"]["branches"][0]
    after["E_plus"][0]["provenance_ancestry_id"] = "src:forged"
    assert "evidence_id_identity_conflict:e0" in failures(row)


def test_unaffected_branch_must_remain_identical() -> None:
    row = good_row()
    row["semantic_hyperposition"]["supervision"]["H_after"]["branches"][1]["sigma"] = "OBSERVED"
    assert "unaffected_branch_mutated:b1" in failures(row)


def test_state_change_requires_non_self_asserted_derivation_receipt() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0"]
    frame["supervision"]["H_after"]["branches"][0]["sigma"] = "OBSERVED"
    frame["supervision"]["derivation_receipt"] = {
        "kind": "EXECUTABLE_TASK_WORLD_RELATION",
        "evaluator_id": "synthetic-evaluator:v1",
        "input_digest": "sha256:input",
        "output_digest": "sha256:output",
        "self_asserted_label": True,
    }
    assert "derivation_receipt_allows_self_asserted_label" in failures(row)


def test_same_dependence_group_cannot_be_counted_as_new_independent_evidence() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0"]
    frame["supervision"]["H_after"]["branches"][0]["E_plus"].append(
        evidence(
            "e1",
            "src:different-packaging",
            "ind:0",
            "SUPPORTS",
            independent_for_update=True,
        )
    )
    add_valid_update_receipt(row)
    assert any(
        failure.startswith("same_independence_group_counted_independent:e1:ind:0")
        for failure in failures(row)
    )


def test_same_dependence_group_marked_nonindependent_can_pass() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0"]
    frame["supervision"]["H_after"]["branches"][0]["E_plus"].append(
        evidence(
            "e1",
            "src:different-packaging",
            "ind:0",
            "SUPPORTS",
            independent_for_update=False,
        )
    )
    add_valid_update_receipt(row)
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]


def test_inadmissible_discriminator_cannot_resolve() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "discriminator_id": "disc:1",
        "resolved_branch_id": "b0",
        "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
        "precondition_ids": ["e0"],
    }
    frame["supervision"]["discriminator_evaluation"] = {
        "admissible": False,
        "self_asserted_winner": False,
        "separation_derived": True,
        "observed_outcome_id": "obs:disc:1",
        "branch_predictions": {"b0": "yes", "b1": "no"},
        "winner_branch_id": "b0",
    }
    add_valid_update_receipt(row, kind="VERIFIED_DISCRIMINATOR_OUTCOME")
    assert "inadmissible_discriminator_cannot_resolve" in failures(row)


def test_self_asserted_discriminator_winner_cannot_resolve() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "discriminator_id": "disc:1",
        "resolved_branch_id": "b0",
        "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
        "precondition_ids": ["e0"],
    }
    frame["supervision"]["discriminator_evaluation"] = {
        "admissible": True,
        "self_asserted_winner": True,
        "separation_derived": True,
        "observed_outcome_id": "obs:disc:1",
        "branch_predictions": {"b0": "yes", "b1": "no"},
        "winner_branch_id": "b0",
    }
    add_valid_update_receipt(row, kind="VERIFIED_DISCRIMINATOR_OUTCOME")
    assert "discriminator_winner_may_be_self_asserted" in failures(row)


def test_valid_discriminator_resolution_passes() -> None:
    row = good_row()
    frame = row["semantic_hyperposition"]
    frame["model_input"]["operation"]["affected_branch_ids"] = ["b0", "b1"]
    frame["supervision"]["resolution"] = {
        "status": "RESOLVED",
        "discriminator_id": "disc:1",
        "resolved_branch_id": "b0",
        "reopen_policy": "REOPEN_ON_PRECONDITION_INVALIDATION",
        "precondition_ids": ["e0"],
    }
    frame["supervision"]["discriminator_evaluation"] = {
        "admissible": True,
        "self_asserted_winner": False,
        "separation_derived": True,
        "observed_outcome_id": "obs:disc:1",
        "branch_predictions": {"b0": "yes", "b1": "no"},
        "winner_branch_id": "b0",
    }
    add_valid_update_receipt(row, kind="VERIFIED_DISCRIMINATOR_OUTCOME")
    result = GATE.audit_row(row, "test-row")
    assert result["pass"], result["failures"]


def test_output_selection_cannot_collapse_unresolved_state() -> None:
    row = good_row()
    row["semantic_hyperposition"]["supervision"]["output_projection"]["semantic_state_collapsed"] = True
    assert "output_selection_collapses_unresolved_semantic_state" in failures(row)


def test_new_branch_requires_declared_counterhypothesis_birth() -> None:
    row = good_row()
    row["semantic_hyperposition"]["supervision"]["H_after"]["branches"].append(branch("b2", "QUERY_UNKNOWN"))
    add_valid_update_receipt(row)
    assert any(
        failure.startswith("new_branch_without_declared_counterhypothesis_birth:b2")
        for failure in failures(row)
    )
