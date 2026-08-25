#!/usr/bin/env python3
"""Fail-closed Trigger-2 semantic-Hyperposition corpus gate v3.

V3 is a source/data-design acceptance gate. It incorporates the 2026-08-25
exact-current adversarial audit of reference-labeler v1 and therefore does not trust
caller/generator asserted update effects or discriminator winners as ground truth.

It enforces:
- branch-local semantic Hyperposition state;
- typed evidence identity, provenance ancestry, dependence group and epistemic type;
- immutable evidence-id identity across before/after state;
- explicit joint-state semantics with no implicit Cartesian completion;
- transition/evidence locality through declared affected branches;
- dependence-group-aware duplicate evidence accounting;
- derivation-receipt binding for state-changing labels;
- admissible discriminator evaluation for discriminator-based resolution;
- output selection != semantic collapse;
- explicit reopening policy for resolved state.

This tool cannot itself prove that an external evaluator receipt is truthful. It only
fails closed when the required deterministic derivation identity is absent or internally
inconsistent. It mints no canonical truth, real-effect, model, J-Space, HCU, EntityOS,
accepted-dataset or training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

GATE_SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_UNIVERSAL_GATE/v3"
FRAME_SCHEMA = "SEMANTIC_HYPERPOSITION_FRAME/v3"
BRANCH_FIELDS = ("id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma")
EVIDENCE_CORE_FIELDS = (
    "evidence_id",
    "provenance_ancestry_id",
    "independence_group",
    "epistemic_type",
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
    "SYNTHETIC_PROOF",
}
RESOLUTION_STATES = {"UNRESOLVED", "REQUEST_DISCRIMINATOR", "RESOLVED"}
JOINT_REPRESENTATIONS = {"WHOLE_WORLD_BRANCHES", "EXPLICIT_COMPATIBILITY_SETS"}
REOPEN_POLICIES = {"REOPEN_ON_PRECONDITION_INVALIDATION", "IMMUTABLE_SYNTHETIC_PROOF"}
DERIVATION_KINDS = {
    "EXECUTABLE_TASK_WORLD_RELATION",
    "VERIFIED_DISCRIMINATOR_OUTCOME",
    "IMMUTABLE_SYNTHETIC_PROOF",
}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _branches(state: Any) -> list[dict[str, Any]] | None:
    if not isinstance(state, dict):
        return None
    branches = state.get("branches")
    return branches if isinstance(branches, list) else None


def _evidence_lists(branch: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any]]]:
    for side in ("E_plus", "E_minus"):
        items = branch.get(side, [])
        if not isinstance(items, list):
            continue
        for item in items:
            if isinstance(item, dict):
                yield side, item


def _validate_evidence_item(item: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(item, dict):
        failures.append(f"{prefix}:evidence_item_not_object")
        return
    for field in EVIDENCE_CORE_FIELDS:
        if field not in item:
            failures.append(f"{prefix}:missing_evidence_field:{field}")
        elif not _nonempty_string(item[field]):
            failures.append(f"{prefix}:empty_evidence_field:{field}")
    if item.get("epistemic_type") not in EPISTEMIC_TYPES:
        failures.append(f"{prefix}:invalid_evidence_epistemic_type:{item.get('epistemic_type')!r}")
    relation = item.get("relation", item.get("applied_effect"))
    if not _nonempty_string(relation):
        failures.append(f"{prefix}:missing_relation_or_applied_effect")


def _validate_branch(branch: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(branch, dict):
        failures.append(f"{prefix}:branch_not_object")
        return
    for field in BRANCH_FIELDS:
        if field not in branch:
            failures.append(f"{prefix}:missing_branch_field:{field}")
    if "id" in branch and not _nonempty_string(branch.get("id")):
        failures.append(f"{prefix}:empty_branch_id")
    if branch.get("sigma") not in EPISTEMIC_TYPES:
        failures.append(f"{prefix}:invalid_epistemic_type:{branch.get('sigma')!r}")

    seen_ids: set[str] = set()
    for side in ("E_plus", "E_minus"):
        items = branch.get(side)
        if not isinstance(items, list):
            failures.append(f"{prefix}:{side}_must_be_list")
            continue
        for index, item in enumerate(items):
            item_prefix = f"{prefix}:{side}[{index}]"
            _validate_evidence_item(item, item_prefix, failures)
            if isinstance(item, dict) and _nonempty_string(item.get("evidence_id")):
                eid = item["evidence_id"]
                if eid in seen_ids:
                    failures.append(f"{prefix}:duplicate_evidence_id:{eid}")
                seen_ids.add(eid)


def _branch_map(branches: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for branch in branches:
        if isinstance(branch, dict) and _nonempty_string(branch.get("id")):
            result[branch["id"]] = branch
    return result


def _all_evidence(branches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        for _, item in _evidence_lists(branch):
            out.append(item)
    return out


def _identity_core(item: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return tuple(item.get(field) for field in EVIDENCE_CORE_FIELDS)  # type: ignore[return-value]


def _validate_evidence_identity_consistency(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    failures: list[str],
) -> None:
    by_id: dict[str, tuple[Any, Any, Any, Any]] = {}
    for item in _all_evidence(before) + _all_evidence(after):
        eid = item.get("evidence_id")
        if not _nonempty_string(eid):
            continue
        core = _identity_core(item)
        previous = by_id.get(eid)
        if previous is None:
            by_id[eid] = core
        elif previous != core:
            failures.append(f"evidence_id_identity_conflict:{eid}")


def _validate_joint_state(joint_state: Any, branch_ids: set[str], failures: list[str]) -> None:
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


def _validate_derivation_receipt(receipt: Any, failures: list[str]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        failures.append("missing_derivation_receipt")
        return {}
    if receipt.get("kind") not in DERIVATION_KINDS:
        failures.append("invalid_derivation_kind")
    for field in ("evaluator_id", "input_digest", "output_digest"):
        if not _nonempty_string(receipt.get(field)):
            failures.append(f"derivation_receipt_missing:{field}")
    if receipt.get("self_asserted_label") is not False:
        failures.append("derivation_receipt_allows_self_asserted_label")
    return receipt


def _new_evidence_items(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    before_ids = {
        item.get("evidence_id")
        for item in _all_evidence(before)
        if _nonempty_string(item.get("evidence_id"))
    }
    return [
        item
        for item in _all_evidence(after)
        if _nonempty_string(item.get("evidence_id")) and item.get("evidence_id") not in before_ids
    ]


def _validate_dependence_group_accounting(
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
    failures: list[str],
) -> None:
    prior_groups = {
        item.get("independence_group")
        for item in _all_evidence(before)
        if _nonempty_string(item.get("independence_group"))
    }
    for item in _new_evidence_items(before, after):
        group = item.get("independence_group")
        if group in prior_groups and item.get("independent_for_update") is not False:
            failures.append(
                f"same_independence_group_counted_independent:{item.get('evidence_id')}:{group}"
            )


def _validate_discriminator_evaluation(
    evaluation: Any,
    before_ids: set[str],
    resolution: dict[str, Any],
    failures: list[str],
) -> None:
    if not isinstance(evaluation, dict):
        failures.append("resolved_by_discriminator_without_evaluation")
        return
    if evaluation.get("admissible") is not True:
        failures.append("inadmissible_discriminator_cannot_resolve")
    if evaluation.get("self_asserted_winner") is not False:
        failures.append("discriminator_winner_may_be_self_asserted")
    if evaluation.get("separation_derived") is not True:
        failures.append("discriminator_separation_not_derived")
    if not _nonempty_string(evaluation.get("observed_outcome_id")):
        failures.append("discriminator_missing_observed_outcome_id")
    predictions = evaluation.get("branch_predictions")
    if not isinstance(predictions, dict):
        failures.append("discriminator_branch_predictions_not_object")
    else:
        missing = sorted(before_ids - set(predictions))
        if missing:
            failures.append("discriminator_missing_branch_predictions:" + ",".join(missing))
    winner = evaluation.get("winner_branch_id")
    if not _nonempty_string(winner) or winner not in before_ids:
        failures.append("discriminator_winner_not_live_branch")
    declared_winner = resolution.get("resolved_branch_id")
    if declared_winner is not None and winner != declared_winner:
        failures.append("resolution_winner_mismatch")


def audit_row(row: dict[str, Any], row_ref: str) -> dict[str, Any]:
    failures: list[str] = []
    frame = row.get("semantic_hyperposition")
    if not isinstance(frame, dict):
        return {"row_ref": row_ref, "pass": False, "failures": ["missing_semantic_hyperposition_frame"]}

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
    _validate_evidence_identity_consistency(before, after, failures)
    _validate_dependence_group_accounting(before, after, failures)

    operation = model_input.get("operation")
    if not isinstance(operation, dict):
        failures.append("operation_not_object")
        operation = {}
    if not _nonempty_string(operation.get("type")):
        failures.append("operation_missing_type")
    affected = operation.get("affected_branch_ids")
    if not isinstance(affected, list):
        failures.append("operation_affected_branch_ids_must_be_list")
        affected = []
    elif any(not _nonempty_string(value) for value in affected):
        failures.append("operation_has_invalid_affected_branch_id")
    unknown_affected = sorted(set(affected) - before_id_set)
    if unknown_affected:
        failures.append("operation_unknown_affected_branch_ids:" + ",".join(unknown_affected))

    before_map = _branch_map(before)
    after_map = _branch_map(after)
    affected_set = set(affected)
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

    state_changed = bool(affected_set) or before != after
    if state_changed or status == "RESOLVED":
        receipt = _validate_derivation_receipt(supervision.get("derivation_receipt"), failures)
        if status == "RESOLVED" and resolution.get("discriminator_id"):
            if receipt.get("kind") != "VERIFIED_DISCRIMINATOR_OUTCOME":
                failures.append("discriminator_resolution_requires_verified_discriminator_derivation")
        elif status == "RESOLVED" and receipt.get("kind") not in {
            "IMMUTABLE_SYNTHETIC_PROOF",
            "EXECUTABLE_TASK_WORLD_RELATION",
        }:
            failures.append("policy_resolution_requires_semantic_derivation")

    discriminator_id = resolution.get("discriminator_id")
    policy_id = resolution.get("deterministic_policy_id")
    if status == "RESOLVED" and not (discriminator_id or policy_id):
        failures.append("resolved_without_discriminator_or_policy")
    if status == "RESOLVED" and discriminator_id:
        _validate_discriminator_evaluation(
            supervision.get("discriminator_evaluation"),
            before_id_set,
            resolution,
            failures,
        )

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

    if len(before) > 1 and len(after) < len(before) and status != "RESOLVED":
        failures.append("branch_loss_without_resolution")

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

    if status in {"UNRESOLVED", "REQUEST_DISCRIMINATOR"} and not after:
        failures.append("unresolved_state_has_no_H_after_branches")

    new_after_ids = after_id_set - before_id_set
    if new_after_ids and operation.get("allows_counterhypothesis_birth") is not True:
        failures.append(
            "new_branch_without_declared_counterhypothesis_birth:" + ",".join(sorted(new_after_ids))
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
            results.append({"row_ref": ref, "pass": False, "failures": ["json_parse_error", row["__parse_error__"]]})
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
