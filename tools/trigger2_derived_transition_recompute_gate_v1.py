#!/usr/bin/env python3
"""Recompute gate for Trigger-2 derived semantic-Hyperposition transitions v1.

This gate is deliberately narrow and compositional. It does NOT replace the current
universal corpus gate v4, which owns prompt/target byte binding, version/provenance,
semantic-skeleton split isolation and branch-permutation dataset checks.

For a D/E synthetic discriminator transition, this gate re-runs
trigger2_synthetic_relation_deriver_v1 on the declared H_before + observation and
requires every supervised causal object to equal the deterministic recomputation.
It also requires whole-world Hyperposition semantics with Cartesian completion disabled.

Both gates must pass before this lane can be considered for a future trainable pilot.
No accepted-dataset/training/model/J-Space/HCU/EntityOS/canonical-truth/effect credit is
minted by this source or by source-test existence.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

GATE_SCHEMA = "CLAY_TRIGGER2_DERIVED_TRANSITION_RECOMPUTE_GATE/v1"
DERIVER_PATH = Path(__file__).with_name("trigger2_synthetic_relation_deriver_v1.py")


def _load_deriver():
    spec = importlib.util.spec_from_file_location("trigger2_synthetic_relation_deriver_v1_recompute", DERIVER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load trigger2_synthetic_relation_deriver_v1")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


DERIVER = _load_deriver()


def _validate_joint_state(joint: Any, failures: list[str]) -> None:
    if not isinstance(joint, dict):
        failures.append("missing_joint_state")
        return
    if joint.get("representation") != "WHOLE_WORLD_BRANCHES":
        failures.append("derived_transition_v1_requires_whole_world_branches")
    if joint.get("branch_semantics") != "EACH_BRANCH_IS_COMPLETE_LIVE_WORLD_HYPOTHESIS":
        failures.append("whole_world_branch_semantics_not_explicit")
    if joint.get("cartesian_completion_allowed") is not False:
        failures.append("implicit_cartesian_completion_not_forbidden")


def audit_row(row: dict[str, Any], row_ref: str) -> dict[str, Any]:
    failures: list[str] = []
    transition = row.get("derived_transition")
    if not isinstance(transition, dict):
        return {"row_ref": row_ref, "pass": False, "failures": ["missing_derived_transition"]}

    _validate_joint_state(transition.get("joint_state"), failures)

    for key in (
        "H_before",
        "observation",
        "H_after",
        "relations",
        "resolution",
        "discriminator_evaluation",
        "derivation_receipt",
    ):
        if key not in transition:
            failures.append(f"missing_transition_field:{key}")

    if transition.get("caller_asserted_relation_allowed") is not False:
        failures.append("caller_asserted_relation_must_be_false")
    if transition.get("caller_asserted_winner_allowed") is not False:
        failures.append("caller_asserted_winner_must_be_false")
    if transition.get("branch_birth_allowed") is not False:
        failures.append("branch_birth_not_admitted_in_v1")

    derived: dict[str, Any] | None = None
    try:
        derived = DERIVER.derive(transition.get("H_before"), transition.get("observation"))
    except Exception as exc:
        failures.append(f"deriver_rejected_input:{type(exc).__name__}:{exc}")

    if derived is not None:
        pairs = (
            ("H_after", "state_after"),
            ("relations", "relations"),
            ("resolution", "resolution"),
            ("discriminator_evaluation", "discriminator_evaluation"),
            ("derivation_receipt", "derivation_receipt"),
        )
        for supervised_key, derived_key in pairs:
            if transition.get(supervised_key) != derived.get(derived_key):
                failures.append(f"recomputation_mismatch:{supervised_key}")

    resolution = transition.get("resolution")
    policy = transition.get("resolution_policy")
    if isinstance(resolution, dict) and resolution.get("status") == "RESOLVED":
        if not isinstance(policy, dict):
            failures.append("resolved_without_resolution_policy")
        else:
            if policy.get("reopen_policy") != "REOPEN_ON_PRECONDITION_INVALIDATION":
                failures.append("derived_resolution_requires_reopen_on_precondition_invalidation")
            ids = policy.get("precondition_ids")
            observation = transition.get("observation")
            event_id = observation.get("evidence_event_id") if isinstance(observation, dict) else None
            if not isinstance(ids, list) or not ids or event_id not in ids:
                failures.append("resolution_policy_missing_current_event_precondition")

    return {"row_ref": row_ref, "pass": not failures, "failures": failures}


def iter_jsonl(paths: Iterable[Path]) -> Iterable[tuple[str, dict[str, Any]]]:
    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            for line_no, raw in enumerate(fh, 1):
                if not raw.strip():
                    continue
                ref = f"{path}:{line_no}"
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    yield ref, {"__parse_error__": str(exc)}
                    continue
                if not isinstance(obj, dict):
                    yield ref, {"__not_object__": True}
                    continue
                yield ref, obj


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
        "deriver_schema": DERIVER.SCHEMA,
        "rows": len(results),
        "passed": passed,
        "failed": failed,
        "gate_pass": bool(results) and failed == 0,
        "composition_requirement": "MUST_ALSO_PASS_CURRENT_UNIVERSAL_CORPUS_GATE_V4_OR_SUCCESSOR",
        "credit_boundary": "SOURCE_DATA_DESIGN_RECOMPUTATION_COMPONENT_ONLY",
        "results": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0 if report["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
