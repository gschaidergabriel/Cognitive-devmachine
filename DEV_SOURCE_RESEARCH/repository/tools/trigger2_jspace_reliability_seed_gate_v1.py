#!/usr/bin/env python3
"""Fail-closed source gate for Trigger-2 J-Space reliability candidate seed v1.

This validator checks only the newly introduced METHOD_ONLY / SYNTHETIC_HARD_NEGATIVE
candidate family. It does not admit canonical dataset rows and cannot mint model,
J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_JSPACE_RELIABILITY_SEED_GATE/v1"
ROW_SCHEMA = "ENTITYOS_HCU_TRAININGTRACE_CANDIDATE/v1"
HP_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION/v1"
EXPECTED_FAMILIES = {
    "JSR_GLOBAL_VECTOR_SINGLE_CONTEXT_F01",
    "JSR_CROSS_MODEL_TRANSFER_F02",
    "JSR_TARGET_SUCCESS_OFFTARGET_FAIL_F03",
    "JSR_POSTHOC_HOLDOUT_SELECTION_F04",
    "JSR_VECTOR_COMPOSITION_UNRESOLVED_F05",
    "JSR_STEERING_BRANCH_COLLAPSE_F06",
    "JSR_COORDINATE_MOVEMENT_BEHAVIOR_F07",
    "JSR_PROMPT_PRESENCE_REENTRY_F08",
}
EXPECTED_UNRESOLVED = {
    "JSR_VECTOR_COMPOSITION_UNRESOLVED_F05",
    "JSR_STEERING_BRANCH_COLLAPSE_F06",
}
REQUIRED_ANTI_COLLAPSE = {
    "NO_MAJORITY_AS_TRUTH",
    "NO_SALIENCE_AS_PROBABILITY",
    "NO_RECURRENCE_AS_EVIDENCE",
    "NO_SILENT_BRANCH_DROP",
    "PROJECTION_IS_NOT_DELETION",
}
REQUIRED_BRANCH_FIELDS = {
    "branch_id",
    "value",
    "context_predicate",
    "evidence_for",
    "evidence_against",
    "falsifier",
    "validity",
    "provenance",
    "epistemic_status",
}
FORBIDDEN_POSITIVE_CONTROL_FIELDS = {
    "steering_vector",
    "positive_jspace_target",
    "positive_hidden_state_target",
    "canonical_semantic_vector",
    "verified_control_layer",
}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {lineno}: invalid JSON: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"line {lineno}: row must be object")
        rows.append(row)
    return rows


def adjudicate(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rr = list(rows)
    failures: list[str] = []
    family_counts: dict[str, int] = {}

    if len(rr) != 8:
        failures.append(f"ROW_COUNT_EXPECTED_8_GOT_{len(rr)}")

    for idx, row in enumerate(rr):
        pfx = f"ROW_{idx}"
        family = row.get("family_id")
        if not _nonempty(family):
            failures.append(f"{pfx}:FAMILY_ID_REQUIRED")
            family = f"<missing-{idx}>"
        family_counts[family] = family_counts.get(family, 0) + 1

        if row.get("schema") != ROW_SCHEMA:
            failures.append(f"{pfx}:ROW_SCHEMA_MISMATCH")
        if row.get("evidence_class") not in {"METHOD_ONLY", "SYNTHETIC_HARD_NEGATIVE"}:
            failures.append(f"{pfx}:EVIDENCE_CLASS_NOT_SOURCE_CANDIDATE")
        if row.get("canonical_truth_allowed") is not False:
            failures.append(f"{pfx}:CANONICAL_TRUTH_MUST_BE_FALSE")
        if row.get("direct_effect_authority") is not False:
            failures.append(f"{pfx}:DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
        if row.get("training_eligible") is not False:
            failures.append(f"{pfx}:TRAINING_ELIGIBLE_MUST_BE_FALSE")
        if row.get("positive_jspace_label") is not False:
            failures.append(f"{pfx}:POSITIVE_JSPACE_LABEL_MUST_BE_FALSE")
        if row.get("split") != "TRAIN":
            failures.append(f"{pfx}:SEED_SPLIT_MUST_BE_TRAIN")
        if row.get("split_unit") != "CAUSAL_FAMILY_AND_PROVENANCE_ANCESTRY":
            failures.append(f"{pfx}:SPLIT_UNIT_MISMATCH")
        if row.get("selected_using_holdout") is not False:
            failures.append(f"{pfx}:HOLDOUT_SELECTION_MUST_BE_FALSE")
        if not _nonempty(row.get("provenance_ancestry_id")):
            failures.append(f"{pfx}:PROVENANCE_ANCESTRY_REQUIRED")
        if not _nonempty(row.get("prompt")) or not _nonempty(row.get("target")):
            failures.append(f"{pfx}:PROMPT_TARGET_REQUIRED")
        if not isinstance(row.get("external_method_sources"), list) or not row.get("external_method_sources"):
            failures.append(f"{pfx}:EXTERNAL_METHOD_SOURCE_REQUIRED")
        leaked = FORBIDDEN_POSITIVE_CONTROL_FIELDS & set(row)
        if leaked:
            failures.append(f"{pfx}:FORBIDDEN_POSITIVE_CONTROL_FIELDS:{','.join(sorted(leaked))}")

        hp = row.get("semantic_hyperposition")
        if not isinstance(hp, dict):
            failures.append(f"{pfx}:SEMANTIC_HYPERPOSITION_REQUIRED")
            continue
        if hp.get("schema") != HP_SCHEMA:
            failures.append(f"{pfx}:HP_SCHEMA_MISMATCH")
        if hp.get("canonical_truth_allowed") is not False:
            failures.append(f"{pfx}:HP_CANONICAL_TRUTH_MUST_BE_FALSE")
        anti = hp.get("anti_collapse")
        if not isinstance(anti, list) or not REQUIRED_ANTI_COLLAPSE.issubset(set(anti)):
            failures.append(f"{pfx}:ANTI_COLLAPSE_INCOMPLETE")
        projection = hp.get("projection")
        if not isinstance(projection, dict) or projection.get("operation") != "NONDESTRUCTIVE_VIEW":
            failures.append(f"{pfx}:PROJECTION_MUST_BE_NONDESTRUCTIVE")
        branches = hp.get("branches")
        if not isinstance(branches, list) or len(branches) < 2:
            failures.append(f"{pfx}:AT_LEAST_TWO_BRANCHES_REQUIRED")
            branches = []
        seen_ids: set[str] = set()
        for bidx, branch in enumerate(branches):
            if not isinstance(branch, dict):
                failures.append(f"{pfx}:BRANCH_{bidx}_OBJECT_REQUIRED")
                continue
            missing = REQUIRED_BRANCH_FIELDS - set(branch)
            if missing:
                failures.append(f"{pfx}:BRANCH_{bidx}_MISSING:{','.join(sorted(missing))}")
            bid = branch.get("branch_id")
            if not _nonempty(bid):
                failures.append(f"{pfx}:BRANCH_{bidx}_ID_REQUIRED")
            elif bid in seen_ids:
                failures.append(f"{pfx}:DUPLICATE_BRANCH_ID:{bid}")
            else:
                seen_ids.add(bid)
            if not isinstance(branch.get("evidence_for"), list) or not isinstance(branch.get("evidence_against"), list):
                failures.append(f"{pfx}:BRANCH_{bidx}_EVIDENCE_LISTS_REQUIRED")

        resolution = hp.get("task_resolution")
        if not isinstance(resolution, dict):
            failures.append(f"{pfx}:TASK_RESOLUTION_REQUIRED")
        else:
            status = resolution.get("status")
            resolved = resolution.get("resolved_branch")
            if family in EXPECTED_UNRESOLVED:
                if status != "UNRESOLVED" or resolved is not None:
                    failures.append(f"{pfx}:EXPECTED_UNRESOLVED")
                if not _nonempty(hp.get("requested_discriminator")):
                    failures.append(f"{pfx}:UNRESOLVED_REQUIRES_DISCRIMINATOR")
            else:
                if status != "RESOLVED_WITHIN_SYNTHETIC_WORLD":
                    failures.append(f"{pfx}:EXPECTED_SYNTHETIC_RESOLUTION")
                if resolved not in seen_ids:
                    failures.append(f"{pfx}:RESOLVED_BRANCH_NOT_IN_SET")

    if set(family_counts) != EXPECTED_FAMILIES:
        failures.append("EXPECTED_FAMILY_SET_MISMATCH")
    duplicates = sorted(k for k, v in family_counts.items() if v != 1)
    if duplicates:
        failures.append("FAMILY_COUNT_NOT_ONE:" + ",".join(duplicates))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "rows": len(rr),
        "families": len(family_counts),
        "failures": failures,
        "training_admission_performed": False,
        "accepted_dataset_tokens_minted": 0,
        "positive_jspace_labels_minted": 0,
        "training_credit_minted": False,
        "evidence_boundary": "Static source-candidate validation only.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    result = adjudicate(load_jsonl(args.path))
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
