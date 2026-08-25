#!/usr/bin/env python3
"""Fail-closed Trigger-2 semantic-Hyperposition corpus gate v4.

V4 is a strict successor layer over v3. It intentionally reuses v3's causal
state/derivation/discriminator checks and adds two boundaries that v1-v3 do not
prove by declaration alone:

1) the exact canonical Hyperposition model_input must occur in the actual model
   prompt bytes between explicit markers;
2) the exact canonical supervision object must occur in the parsed target bytes.

V4 also enforces dataset-level semantic-skeleton split isolation, branch-ID/order
counterfactual twins, and explicit artifact version/provenance status.

This remains SOURCE/DATA-DESIGN validation. It grants no accepted-dataset,
training, model, J-Space, HCU, EntityOS, canonical-truth, or effect credit.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from tools.trigger2_semantic_hyperposition_universal_gate_v3 import (
    FRAME_SCHEMA,
    audit_row as audit_row_v3,
)

GATE_SCHEMA = "CLAY_TRIGGER2_SEMANTIC_HYPERPOSITION_UNIVERSAL_GATE/v4"
INPUT_BEGIN = "<HYPERPOSITION_INPUT_V4>"
INPUT_END = "</HYPERPOSITION_INPUT_V4>"
ARTIFACT_STATUSES = {
    "CURRENT",
    "CURRENT_CANDIDATE",
    "BLOCKED",
    "RETROFIT_REQUIRED",
    "COMPONENT_ONLY",
    "QUARANTINE",
    "SUPERSEDED",
    "STALE_RECHECK",
}


def canon(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_target(row: dict[str, Any], failures: list[str]) -> dict[str, Any]:
    raw = row.get("target")
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        failures.append("target_not_json_object_or_string")
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        failures.append("target_string_not_json")
        return {}
    if not isinstance(parsed, dict):
        failures.append("target_json_not_object")
        return {}
    return parsed


def _v4_byte_and_version_failures(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    frame = row.get("semantic_hyperposition")
    if not isinstance(frame, dict):
        return ["v4_missing_semantic_hyperposition_frame"]

    model_input = frame.get("model_input")
    supervision = frame.get("supervision")
    if not isinstance(model_input, dict):
        failures.append("v4_missing_model_input")
        model_input = {}
    if not isinstance(supervision, dict):
        failures.append("v4_missing_supervision")
        supervision = {}

    prompt = row.get("prompt")
    canonical_input = canon(model_input)
    expected_block = INPUT_BEGIN + "\n" + canonical_input + "\n" + INPUT_END
    if not isinstance(prompt, str):
        failures.append("v4_prompt_not_string")
    elif expected_block not in prompt:
        failures.append("v4_canonical_model_input_not_embedded_in_prompt")

    target_obj = _parse_target(row, failures)
    if target_obj.get("semantic_hyperposition_supervision") != supervision:
        failures.append("v4_canonical_supervision_not_present_in_target")

    render_binding = row.get("render_binding")
    if not isinstance(render_binding, dict):
        failures.append("v4_missing_render_binding")
    else:
        expected_input_hash = sha256_text(canonical_input)
        expected_supervision_hash = sha256_text(canon(supervision))
        if render_binding.get("model_input_sha256") != expected_input_hash:
            failures.append("v4_model_input_hash_mismatch")
        if render_binding.get("supervision_sha256") != expected_supervision_hash:
            failures.append("v4_supervision_hash_mismatch")
        if render_binding.get("prompt_contains_canonical_input") is not True:
            failures.append("v4_prompt_binding_not_declared")
        if render_binding.get("target_contains_canonical_supervision") is not True:
            failures.append("v4_target_binding_not_declared")

    versioning = row.get("versioning")
    if not isinstance(versioning, dict):
        failures.append("v4_missing_versioning")
    else:
        for field in (
            "artifact_id",
            "version",
            "status",
            "predecessor",
            "successor",
            "revision_reason",
            "provenance_sources",
            "target_architecture",
        ):
            if field not in versioning:
                failures.append(f"v4_versioning_missing:{field}")
        if versioning.get("status") not in ARTIFACT_STATUSES:
            failures.append("v4_versioning_invalid_status")
        sources = versioning.get("provenance_sources")
        if not isinstance(sources, list) or not sources:
            failures.append("v4_versioning_provenance_sources_empty")

    for field in (
        "row_id",
        "split",
        "semantic_skeleton_id",
        "branch_permutation_group_id",
        "branch_permutation_id",
        "expected_semantic_outcome",
    ):
        if field not in row:
            failures.append(f"v4_missing_dataset_audit_field:{field}")

    # Fail closed if a trainable row does not bind the exact causal label derivation
    # identities expected by the current v3 causal gate lineage.
    if row.get("training_eligible") is True:
        binding = row.get("causal_label_binding")
        if not isinstance(binding, dict):
            failures.append("v4_trainable_row_missing_causal_label_binding")
        else:
            for field in (
                "task_world_evaluator_id",
                "task_world_evaluator_sha256",
                "reference_labeler_path",
                "reference_labeler_blob_sha",
                "derivation_receipt_id",
            ):
                value = binding.get(field)
                if not isinstance(value, str) or not value.strip():
                    failures.append(f"v4_causal_label_binding_missing:{field}")
            if binding.get("caller_asserted_branch_relations") is not False:
                failures.append("v4_causal_label_binding_allows_caller_asserted_branch_relations")
            if binding.get("caller_asserted_decision_roles") is not False:
                failures.append("v4_causal_label_binding_allows_caller_asserted_decision_roles")

    return failures


def audit_row_v4(row: dict[str, Any], row_ref: str) -> dict[str, Any]:
    base = audit_row_v3(row, row_ref)
    failures = list(base.get("failures", []))
    failures.extend(_v4_byte_and_version_failures(row))
    return {
        "row_ref": row_ref,
        "pass": not failures,
        "v3_pass": bool(base.get("pass")),
        "failures": failures,
    }


def _iter_jsonl(paths: Iterable[Path]) -> Iterable[tuple[str, dict[str, Any]]]:
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


def _dataset_failures(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    row_ids: set[str] = set()
    skeleton_splits: dict[str, set[str]] = collections.defaultdict(set)
    perm_groups: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)

    for row in rows:
        rid = row.get("row_id")
        if isinstance(rid, str):
            if rid in row_ids:
                failures.append(f"v4_duplicate_row_id:{rid}")
            row_ids.add(rid)
        skeleton = row.get("semantic_skeleton_id")
        split = row.get("split")
        if isinstance(skeleton, str) and isinstance(split, str):
            skeleton_splits[skeleton].add(split)
        group_id = row.get("branch_permutation_group_id")
        if isinstance(group_id, str):
            perm_groups[group_id].append(row)

    for skeleton, splits in sorted(skeleton_splits.items()):
        if len(splits) > 1:
            failures.append(f"v4_semantic_skeleton_cross_split_leak:{skeleton}:{sorted(splits)}")

    for group_id, group in sorted(perm_groups.items()):
        if len(group) < 2:
            failures.append(f"v4_branch_permutation_group_missing_twin:{group_id}")
            continue
        perm_ids = {row.get("branch_permutation_id") for row in group}
        if len(perm_ids) < 2:
            failures.append(f"v4_branch_permutation_group_not_permuted:{group_id}")
        outcomes = {canon(row.get("expected_semantic_outcome")) for row in group}
        if len(outcomes) != 1:
            failures.append(f"v4_branch_permutation_changes_semantic_outcome:{group_id}")
        splits = {row.get("split") for row in group}
        if len(splits) != 1:
            failures.append(f"v4_branch_permutation_group_cross_split:{group_id}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    parsed = list(_iter_jsonl(args.paths))
    results: list[dict[str, Any]] = []
    clean_rows: list[dict[str, Any]] = []
    for ref, row in parsed:
        if "__parse_error__" in row:
            results.append({"row_ref": ref, "pass": False, "v3_pass": False, "failures": ["json_parse_error", row["__parse_error__"]]})
        elif "__not_object__" in row:
            results.append({"row_ref": ref, "pass": False, "v3_pass": False, "failures": ["row_not_object"]})
        else:
            results.append(audit_row_v4(row, ref))
            clean_rows.append(row)

    dataset_failures = _dataset_failures(clean_rows)
    passed = sum(1 for result in results if result["pass"])
    failed = len(results) - passed
    report = {
        "schema": GATE_SCHEMA,
        "frame_schema": FRAME_SCHEMA,
        "rows": len(results),
        "passed": passed,
        "failed": failed,
        "dataset_failures": dataset_failures,
        "gate_pass": bool(results) and failed == 0 and not dataset_failures,
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
