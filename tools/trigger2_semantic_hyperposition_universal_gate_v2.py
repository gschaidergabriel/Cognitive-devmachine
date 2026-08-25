#!/usr/bin/env python3
"""Fail-closed Trigger-2 universal semantic-Hyperposition corpus gate v2.

V2 extends the v1 source/data-design gate with:
- typed evidence identity / ancestry / independence-group requirements;
- explicit joint-state semantics with no implicit Cartesian completion;
- evidence-locality transition checks through declared affected branches;
- output-selection vs semantic-resolution separation;
- reopening policy for resolved states.

This validator does not grant accepted-dataset, training, J-Space, HCU, EntityOS,
canonical-truth or real-effect credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

GATE_SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_UNIVERSAL_GATE/v2"
FRAME_SCHEMA = "SEMANTIC_HYPERPOSITION_FRAME/v2"
BRANCH_FIELDS = ("id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma")
EVIDENCE_FIELDS = (
    "evidence_id",
    "provenance_or_ancestry_id",
    "independence_group",
    "relation",
)
EPISTEMIC_TYPES = {
    "OBSERVED",
    "UNKNOWN",
    "HYPOTHESIS",
    "PREDICTION",
    "MEASUREMENT_ERROR",
    "COUNTERHYPOTHESIS",
    "CONTRADICTION",
    "FALSIFIER",
    "CANDIDATE",
}
RESOLUTION_STATES = {"UNRESOLVED", "REQUEST_DISCRIMINATOR", "RESOLVED"}
JOINT_REPRESENTATIONS = {"WHOLE_WORLD_BRANCHES", "EXPLICIT_COMPATIBILITY_SETS"}
REOPEN_POLICIES = {"REOPEN_ON_PRECONDITION_INVALIDATION", "IMMUTABLE_SYNTHETIC_PROOF"}


def _branches(state: Any) -> list[dict[str, Any]] | None:
    if not isinstance(state, dict):
        return None
    branches = state.get("branches")
    return branches if isinstance(branches, list) else None


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_evidence_item(item: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(item, dict):
        failures.append(f"{prefix}:evidence_item_not_object")
        return
    for field in EVIDENCE_FIELDS:
        if field not in item:
            failures.append(f"{prefix}:missing_evidence_field:{field}")
        elif not _nonempty_string(item[field]):
            failures.append(f"{prefix}:empty_evidence_field:{field}")


def _validate_branch(branch: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(branch, dict):
        failures.append(f"{prefix}:branch_not_object")
        return

    for field in BRANCH_FIELDS:
        if field not in branch:
            failures.append(f"{prefix}:missing_branch_field:{field}")

    branch_id = branch.get("id")
    if "id" in branch and not _nonempty_string(branch_id):
        failures.append(f"{prefix}:empty_branch_id")

    if "sigma" in branch and branch["sigma"] not in EPISTEMIC_TYPES:
        failures.append(f"{prefix}:invalid_epistemic_type:{branch['sigma']!r}")

    seen_evidence_ids: set[str] = set()
    for evidence_field in ("E_plus", "E_minus"):
        evidence_items = branch.get(evidence_field)
        if evidence_items is None:
            continue
        if not isinstance(evidence_items, list):
            failures.append(f"{prefix}:{evidence_field}_must_be_list")
            continue
        for index, item in enumerate(evidence_items):
            item_prefix = f"{prefix}:{evidence_field}[{index}]"
            _validate_evidence_item(item, item_prefix, failures)
            if isinstance(item, dict) and _nonempty_string(item.get("evidence_id")):
                evidence_id = item["evidence_id"]
                if evidence_id in seen_evidence_ids:
                    failures.append(f"{prefix}:duplicate_evidence_id:{evidence_id}")
                seen_evidence_ids.add(evidence_id)


def _validate_joint_state(
    joint_state: Any,
    branch_ids: set[str],
    failures: list[str],
) -> None:
    if not isinstance(joint_state, dict):
        failures.append("joint_state_not_object")
        return

    representation = joint_state.get("representation")
    if representation not in JOINT_REPRESENTATIONS:
        failures.append("invalid_joint_state_representation")

    if joint_state.get("cartesian_completion_allowed") is not False:
        failures.append("implicit_cartesian_completion_not_forbidden")

    if representation != "EXPLICIT_COMPATIBILITY_SETS":
        return

    live_worlds = joint_state.get("live_worlds")
    if not isinstance(live_worlds, list) or not live_worlds:
        failures.append("compatibility_sets_missing_live_worlds")
        return

    seen_world_ids: set[str] = set()
    seen_member_sets: set[tuple[str, ...]] = set()
    for index, world in enumerate(live_worlds):
        prefix = f"joint_state.live_worlds[{index}]"
        if not isinstance(world, dict):
            failures.append(f"{prefix}:world_not_object")
            continue
        world_id = world.get("world_id")
        members = world.get("members")
        if not _nonempty_string(world_id):
            failures.append(f"{prefix}:missing_world_id")
        elif world_id in seen_world_ids:
            failures.append(f"{prefix}:duplicate_world_id:{world_id}")
        else:
            seen_world_ids.add(world_id)
        if not isinstance(members, list) or not members:
            failures.append(f"{prefix}:members_must_be_nonempty_list")
            continue
        if any(not _nonempty_string(member) for member in members):
            failures.append(f"{prefix}:invalid_member_id")
            continue
        if len(members) != len(set(members)):
            failures.append(f"{prefix}:duplicate_member_id")
        unknown = sorted(set(members) - branch_ids)
        if unknown:
            failures.append(f"{prefix}:unknown_branch_members:{','.join(unknown)}")
        member_key = tuple(sorted(members))
        if member_key in seen_member_sets:
            failures.append(f"{prefix}:duplicate_compatibility_set")
        seen_member_sets.add(member_key)


def _branch_map(branches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for branch in branches:
        if isinstance(branch, dict) and _nonempty_string(branch.get("id")):
            result[branch["id"]] = branch
    return result


def audit_row(row: dict[str, Any], row_ref: str) -> dict[str, Any]:
    failures: list[str] = []
    frame = row.get("semantic_hyperposition")
    if not isinstance(frame, dict):
        return {
            "row_ref": row_ref,
            "pass": False,
            "failures": ["missing_semantic_hyperposition_frame"],
        }

    if frame.get("schema") != FRAME_SCHEMA:
        failures.append("wrong_or_missing_frame_schema")
    if frame.get("model_input_in_rendered_prompt") is not True:
        failures.append("frame_input_not_proven_model_visible")
    if frame.get("supervision_in_target") is not True:
        failures.append("frame_output_not_proven_supervised")
    if frame.get("branch_order_semantically_irrelevant") is not True:
        failures.append("branch_order_invariance_not_declared")

    model_input = frame.get("model_input")
    supervision = frame.get("supervision")
    if not isinstance(model_input, dict):
        failures.append("missing_model_input")
        model_input = {}
    if not isinstance(supervision, dict):
        failures.append("missing_supervision")
        supervision = {}

    for key in ("H_before", "operation"):
        if key not in model_input:
            failures.append(f"missing_model_input:{key}")
    for key in ("H_after", "resolution", "falsifier", "output_projection"):
        if key not in supervision:
            failures.append(f"missing_supervision:{key}")

    before = _branches(model_input.get("H_before"))
    after = _branches(supervision.get("H_after"))
    if before is None:
        failures.append("H_before_missing_branches")
        before = []
    if after is None:
        failures.append("H_after_missing_branches")
        after = []

    for index, branch in enumerate(before):
        _validate_branch(branch, f"H_before[{index}]", failures)
    for index, branch in enumerate(after):
        _validate_branch(branch, f"H_after[{index}]", failures)

    before_ids = [branch.get("id") for branch in before if isinstance(branch, dict)]
    after_ids = [branch.get("id") for branch in after if isinstance(branch, dict)]
    if None in before_ids or None in after_ids:
        failures.append("branch_id_missing")
    if len(before_ids) != len(set(before_ids)):
        failures.append("duplicate_H_before_branch_id")
    if len(after_ids) != len(set(after_ids)):
        failures.append("duplicate_H_after_branch_id")

    before_id_set = {value for value in before_ids if _nonempty_string(value)}
    after_id_set = {value for value in after_ids if _nonempty_string(value)}
    _validate_joint_state(frame.get("joint_state"), before_id_set, failures)

    operation = model_input.get("operation")
    if not isinstance(operation, dict):
        failures.append("operation_not_object")
        operation = {}
    if not _nonempty_string(operation.get("type")):
        failures.append("operation_missing_type")
    affected_branch_ids = operation.get("affected_branch_ids")
    if not isinstance(affected_branch_ids, list):
        failures.append("operation_affected_branch_ids_must_be_list")
        affected_branch_ids = []
    elif any(not _nonempty_string(value) for value in affected_branch_ids):
        failures.append("operation_has_invalid_affected_branch_id")
    unknown_affected = sorted(set(affected_branch_ids) - before_id_set)
    if unknown_affected:
        failures.append(f"operation_unknown_affected_branch_ids:{','.join(unknown_affected)}")

    # Evidence locality / transition locality: any branch not declared affected must
    # be byte-semantically unchanged when it survives into H_after.
    before_map = _branch_map(before)
    after_map = _branch_map(after)
    affected_set = set(affected_branch_ids)
    for branch_id in sorted((before_id_set & after_id_set) - affected_set):
        if before_map[branch_id] != after_map[branch_id]:
            failures.append(f"unaffected_branch_mutated:{branch_id}")

    resolution = supervision.get("resolution")
    if not isinstance(resolution, dict):
        failures.append("resolution_not_object")
        resolution = {}
    status = resolution.get("status")
    if status not in RESOLUTION_STATES:
        failures.append("invalid_resolution_status")

    discriminator_id = resolution.get("discriminator_id")
    policy_id = resolution.get("deterministic_policy_id")
    if status == "RESOLVED" and not (discriminator_id or policy_id):
        failures.append("resolved_without_discriminator_or_policy")

    if status == "RESOLVED":
        reopen_policy = resolution.get("reopen_policy")
        if reopen_policy not in REOPEN_POLICIES:
            failures.append("resolved_without_valid_reopen_policy")
        if reopen_policy == "REOPEN_ON_PRECONDITION_INVALIDATION":
            precondition_ids = resolution.get("precondition_ids")
            if not isinstance(precondition_ids, list) or not precondition_ids:
                failures.append("reopenable_resolution_missing_precondition_ids")
            elif any(not _nonempty_string(value) for value in precondition_ids):
                failures.append("reopenable_resolution_has_invalid_precondition_id")

    # Loss of branches is a semantic collapse unless the row proves a valid resolution.
    if len(before) > 1 and len(after) < len(before) and status != "RESOLVED":
        failures.append("branch_loss_without_resolution")

    # A singleton input is legal only when the row explains why the state is already resolved.
    if len(before) == 1:
        singleton = frame.get("resolved_singleton")
        if not isinstance(singleton, dict):
            failures.append("singleton_without_resolved_singleton_proof")
        elif not (singleton.get("discriminator_id") or singleton.get("deterministic_policy_id")):
            failures.append("singleton_proof_missing_discriminator_or_policy")

    output_projection = supervision.get("output_projection")
    if not isinstance(output_projection, dict):
        failures.append("output_projection_not_object")
        output_projection = {}
    if output_projection.get("deletes_unselected_branches") is not False:
        failures.append("output_projection_may_delete_unselected_branches")
    collapsed = output_projection.get("semantic_state_collapsed")
    if not isinstance(collapsed, bool):
        failures.append("output_projection_missing_semantic_state_collapsed_bool")
    elif status in {"UNRESOLVED", "REQUEST_DISCRIMINATOR"} and collapsed:
        failures.append("output_selection_collapses_unresolved_semantic_state")

    # Unresolved states must remain representable after the operation.
    if status in {"UNRESOLVED", "REQUEST_DISCRIMINATOR"} and not after:
        failures.append("unresolved_state_has_no_H_after_branches")

    # An unresolved transition cannot invent brand-new branch identities unless the
    # operation explicitly declares that it may birth counterhypotheses.
    new_after_ids = after_id_set - before_id_set
    if new_after_ids and operation.get("allows_counterhypothesis_birth") is not True:
        failures.append(
            "new_branch_without_declared_counterhypothesis_birth:"
            + ",".join(sorted(new_after_ids))
        )

    return {"row_ref": row_ref, "pass": not failures, "failures": failures}


def iter_jsonl(paths: Iterable[Path]) -> Iterable[tuple[str, dict[str, Any]]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, 1):
                if not raw.strip():
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    yield f"{path}:{line_no}", {"__parse_error__": str(exc)}
                    continue
                if not isinstance(obj, dict):
                    yield f"{path}:{line_no}", {"__not_object__": True}
                    continue
                yield f"{path}:{line_no}", obj


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    for ref, row in iter_jsonl(args.paths):
        if "__parse_error__" in row:
            results.append(
                {
                    "row_ref": ref,
                    "pass": False,
                    "failures": ["json_parse_error", row["__parse_error__"]],
                }
            )
        elif "__not_object__" in row:
            results.append({"row_ref": ref, "pass": False, "failures": ["row_not_object"]})
        else:
            results.append(audit_row(row, ref))

    passed = sum(1 for result in results if result["pass"])
    failed = len(results) - passed
    report = {
        "schema": GATE_SCHEMA,
        "frame_schema": FRAME_SCHEMA,
        "rows": len(results),
        "passed": passed,
        "failed": failed,
        "compliance": (passed / len(results)) if results else 0.0,
        "gate_pass": bool(results) and failed == 0,
        "credit_boundary": "SOURCE_DATA_DESIGN_GATE_ONLY",
        "results": results,
    }

    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
