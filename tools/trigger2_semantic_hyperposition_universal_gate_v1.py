#!/usr/bin/env python3
"""Fail-closed Trigger-2 universal semantic-Hyperposition corpus gate.

This is a source/data-design validator. It does not grant accepted-dataset, training,
J-Space, HCU or EntityOS runtime credit.

A Trigger-2 row passes only if semantic Hyperposition is part of the model-facing
input and supervised target, or the row carries an admissible explicitly resolved
singleton proof. Metadata-only mentions of Hyperposition do not pass.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

GATE_SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_UNIVERSAL_GATE/v1"
FRAME_SCHEMA = "SEMANTIC_HYPERPOSITION_FRAME/v1"
BRANCH_FIELDS = ("id", "v", "K", "E_plus", "E_minus", "F", "T", "A", "sigma")
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


def _branches(state: Any) -> list[dict[str, Any]] | None:
    if not isinstance(state, dict):
        return None
    branches = state.get("branches")
    return branches if isinstance(branches, list) else None


def _validate_branch(branch: Any, prefix: str, failures: list[str]) -> None:
    if not isinstance(branch, dict):
        failures.append(f"{prefix}:branch_not_object")
        return
    for field in BRANCH_FIELDS:
        if field not in branch:
            failures.append(f"{prefix}:missing_branch_field:{field}")
    if "sigma" in branch and branch["sigma"] not in EPISTEMIC_TYPES:
        failures.append(f"{prefix}:invalid_epistemic_type:{branch['sigma']!r}")
    for evidence_field in ("E_plus", "E_minus"):
        if evidence_field in branch and not isinstance(branch[evidence_field], list):
            failures.append(f"{prefix}:{evidence_field}_must_be_list")


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
    for key in ("H_after", "resolution", "falsifier"):
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

    for i, branch in enumerate(before):
        _validate_branch(branch, f"H_before[{i}]", failures)
    for i, branch in enumerate(after):
        _validate_branch(branch, f"H_after[{i}]", failures)

    before_ids = [b.get("id") for b in before if isinstance(b, dict)]
    after_ids = [b.get("id") for b in after if isinstance(b, dict)]
    if None in before_ids or None in after_ids:
        failures.append("branch_id_missing")
    if len(before_ids) != len(set(before_ids)):
        failures.append("duplicate_H_before_branch_id")
    if len(after_ids) != len(set(after_ids)):
        failures.append("duplicate_H_after_branch_id")

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

    projection = supervision.get("projection")
    if projection is not None:
        if not isinstance(projection, dict):
            failures.append("projection_not_object")
        elif projection.get("deletes_unselected_branches") is not False:
            failures.append("projection_may_delete_unselected_branches")

    # An unresolved state must remain representable after the operation.
    if status in {"UNRESOLVED", "REQUEST_DISCRIMINATOR"} and not after:
        failures.append("unresolved_state_has_no_H_after_branches")

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

    passed = sum(1 for r in results if r["pass"])
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
