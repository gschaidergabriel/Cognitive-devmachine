#!/usr/bin/env python3
"""Evidence-bound semantic-factorial authenticity gate for Trigger-1.

This deterministic gate does not run a model and never mints canonical credit. It
reconstructs the semantic-target x output-code factorial from digest-bound case rows
and binds the holdout interaction analysis to that exact case universe. Candidate
summary booleans are treated as claims to verify, not as evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

OUTPUT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_FACTORIAL_EVIDENCE_GATE/v1"
FACTORIAL_RECEIPT_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_FACTORIAL_RECEIPT/v1"
INTERACTION_BINDING_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_INTERACTION_BINDING/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
REQUIRED_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalize_row(row: Any, index: int, split_name: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    prefix = f"{split_name}_CASE_{index}"
    if not isinstance(row, dict):
        return None, [f"{prefix}_OBJECT_REQUIRED"]

    case_id = row.get("case_id")
    seed = row.get("seed")
    prompt_sha = row.get("prompt_sha256")
    target = str(row.get("semantic_target") or "").strip().upper()
    code = str(row.get("output_code_identity") or "").strip().upper()
    family = row.get("split_family_id")
    receipts = row.get("control_runtime_receipts")

    if not _nonempty(case_id):
        failures.append(f"{prefix}_CASE_ID_REQUIRED")
    if not isinstance(seed, int) or isinstance(seed, bool):
        failures.append(f"{prefix}_INTEGER_SEED_REQUIRED")
    if not _sha256(prompt_sha):
        failures.append(f"{prefix}_PROMPT_SHA256_REQUIRED")
    if target not in TARGETS:
        failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
    if code not in CODES:
        failures.append(f"{prefix}_OUTPUT_CODE_INVALID")
    if not _nonempty(family):
        failures.append(f"{prefix}_SPLIT_FAMILY_ID_REQUIRED")

    normalized_receipts: dict[str, str] = {}
    if not isinstance(receipts, dict):
        failures.append(f"{prefix}_CONTROL_RECEIPTS_OBJECT_REQUIRED")
    else:
        observed = set(receipts)
        required = set(REQUIRED_CONTROLS)
        if observed != required:
            failures.append(f"{prefix}_CONTROL_RECEIPT_SET_MUST_MATCH_REQUIRED_CONTROLS")
        for control in REQUIRED_CONTROLS:
            receipt = receipts.get(control)
            if not _sha256(receipt):
                failures.append(f"{prefix}_CONTROL_RUNTIME_RECEIPT_REQUIRED:{control}")
            else:
                normalized_receipts[control] = str(receipt).lower()

    if failures:
        return None, failures
    return {
        "case_id": str(case_id).strip(),
        "seed": int(seed),
        "prompt_sha256": str(prompt_sha).lower(),
        "semantic_target": target,
        "output_code_identity": code,
        "split_family_id": str(family).strip(),
        "control_runtime_receipts": normalized_receipts,
    }, []


def derive_split_receipt(split: Any, split_name: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(split, dict):
        return None, [f"{split_name}_OBJECT_REQUIRED"]
    rows = split.get("case_rows")
    if not isinstance(rows, list) or len(rows) < 9:
        return None, [f"{split_name}_AT_LEAST_NINE_CASE_ROWS_REQUIRED"]

    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        normalized, row_failures = _normalize_row(row, index, split_name)
        failures.extend(row_failures)
        if normalized is not None:
            normalized_rows.append(normalized)
    if failures:
        return None, failures

    case_ids = [row["case_id"] for row in normalized_rows]
    if len(set(case_ids)) != len(case_ids):
        failures.append(f"{split_name}_DUPLICATE_CASE_ID")

    family_ids = sorted({row["split_family_id"] for row in normalized_rows})
    if len(family_ids) != 1:
        failures.append(f"{split_name}_EXACTLY_ONE_SPLIT_FAMILY_ID_REQUIRED")

    counts = {target: {code: 0 for code in CODES} for target in TARGETS}
    for row in normalized_rows:
        counts[row["semantic_target"]][row["output_code_identity"]] += 1
    flat_counts = [counts[target][code] for target in TARGETS for code in CODES]
    if any(count <= 0 for count in flat_counts):
        failures.append(f"{split_name}_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")
    if flat_counts and len(set(flat_counts)) != 1:
        failures.append(f"{split_name}_FACTORIAL_CELL_COUNTS_MUST_BE_EXACTLY_BALANCED")

    declared_targets = split.get("semantic_targets")
    if not isinstance(declared_targets, list) or {str(x).strip().upper() for x in declared_targets} != set(TARGETS):
        failures.append(f"{split_name}_DECLARED_SEMANTIC_TARGET_SET_MISMATCH")
    if split.get("semantic_target_counterbalanced") is not True:
        failures.append(f"{split_name}_DECLARED_SEMANTIC_COUNTERBALANCE_MUST_BE_TRUE")
    if split.get("label_mapping_counterbalanced") is not True:
        failures.append(f"{split_name}_DECLARED_OUTPUT_CODE_COUNTERBALANCE_MUST_BE_TRUE")

    declared_counts = split.get("semantic_target_x_output_code_counts")
    if declared_counts is not None and declared_counts != counts:
        failures.append(f"{split_name}_DECLARED_FACTORIAL_COUNTS_DISAGREE_WITH_CASE_ROWS")

    if failures:
        return None, failures

    ordered_rows = sorted(
        normalized_rows,
        key=lambda row: (
            row["semantic_target"],
            row["output_code_identity"],
            row["case_id"],
            row["seed"],
        ),
    )
    material = {
        "schema": FACTORIAL_RECEIPT_SCHEMA,
        "split_name": split_name,
        "split_family_id": family_ids[0],
        "semantic_targets": list(TARGETS),
        "output_codes": list(CODES),
        "required_controls": list(REQUIRED_CONTROLS),
        "factorial_counts": counts,
        "case_rows": ordered_rows,
    }
    receipt = canonical_sha(material)
    declared_receipt = split.get("semantic_factorial_receipt_sha256")
    if not _sha256(declared_receipt):
        failures.append(f"{split_name}_SEMANTIC_FACTORIAL_RECEIPT_REQUIRED")
    elif str(declared_receipt).lower() != receipt:
        failures.append(f"{split_name}_SEMANTIC_FACTORIAL_RECEIPT_MISMATCH")
    if failures:
        return None, failures
    return {
        "receipt_sha256": receipt,
        "material": material,
        "case_count": len(ordered_rows),
        "runtime_observation_count_bound": len(ordered_rows) * len(REQUIRED_CONTROLS),
    }, []


def derive_interaction_binding(analysis: Any, holdout_receipt: str) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    if not isinstance(analysis, dict):
        return None, ["HOLDOUT_SEMANTIC_INTERACTION_ANALYSIS_OBJECT_REQUIRED"]

    if analysis.get("factorial_receipt_sha256") != holdout_receipt:
        failures.append("INTERACTION_MUST_BIND_EXACT_HOLDOUT_FACTORIAL_RECEIPT")
    for key in ("metric_definition_sha256", "analysis_implementation_sha256", "analysis_result_receipt_sha256"):
        if not _sha256(analysis.get(key)):
            failures.append(f"INTERACTION_{key.upper()}_REQUIRED")

    identities = analysis.get("treatment_control_identities")
    if not isinstance(identities, list) or set(map(str, identities)) != set(REQUIRED_CONTROLS):
        failures.append("INTERACTION_TREATMENT_CONTROL_IDENTITIES_MUST_MATCH_REQUIRED_CONTROLS")

    if failures:
        return None, failures
    material = {
        "schema": INTERACTION_BINDING_SCHEMA,
        "holdout_factorial_receipt_sha256": holdout_receipt,
        "metric_definition_sha256": str(analysis["metric_definition_sha256"]).lower(),
        "analysis_implementation_sha256": str(analysis["analysis_implementation_sha256"]).lower(),
        "analysis_result_receipt_sha256": str(analysis["analysis_result_receipt_sha256"]).lower(),
        "treatment_control_identities": list(REQUIRED_CONTROLS),
    }
    binding = canonical_sha(material)
    declared = analysis.get("analysis_binding_sha256")
    if not _sha256(declared):
        failures.append("INTERACTION_ANALYSIS_BINDING_SHA256_REQUIRED")
    elif str(declared).lower() != binding:
        failures.append("INTERACTION_ANALYSIS_BINDING_SHA256_MISMATCH")
    if failures:
        return None, failures
    return {"binding_sha256": binding, "material": material}, []


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        failures.append("CANDIDATE_OBJECT_REQUIRED")
        candidate = {}

    calibration_receipt, calibration_failures = derive_split_receipt(candidate.get("calibration"), "CALIBRATION")
    holdout_receipt, holdout_failures = derive_split_receipt(candidate.get("holdout"), "HOLDOUT")
    failures.extend(calibration_failures)
    failures.extend(holdout_failures)

    if calibration_receipt and holdout_receipt:
        cal_family = calibration_receipt["material"]["split_family_id"]
        hold_family = holdout_receipt["material"]["split_family_id"]
        if cal_family == hold_family:
            failures.append("CALIBRATION_AND_HOLDOUT_SPLIT_FAMILIES_MUST_DIFFER")

    interaction = None
    if holdout_receipt:
        interaction, interaction_failures = derive_interaction_binding(
            candidate.get("semantic_interaction_analysis"), holdout_receipt["receipt_sha256"]
        )
        failures.extend(interaction_failures)
    else:
        failures.append("INTERACTION_BINDING_BLOCKED_WITHOUT_VALID_HOLDOUT_FACTORIAL")

    pass_candidate = not failures
    return {
        "schema": OUTPUT_SCHEMA,
        "evidence_bound_semantic_factorial_candidate": pass_candidate,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "full_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "calibration_factorial_receipt_sha256": calibration_receipt["receipt_sha256"] if calibration_receipt else None,
        "holdout_factorial_receipt_sha256": holdout_receipt["receipt_sha256"] if holdout_receipt else None,
        "semantic_interaction_binding_sha256": interaction["binding_sha256"] if interaction else None,
        "failures": sorted(set(failures)),
        "evidence_boundary": (
            "PASS authenticates the executed-design envelope represented by case-row and control-receipt digests: "
            "a complete exactly balanced 3x3 semantic-target x output-code factorial and an interaction-analysis "
            "receipt bound to the exact holdout case universe. It does not validate the scientific interaction result, "
            "run a model, or mint J-Space/HCU/training/canonical-semantics/whole-product credit."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        candidate = {"_invalid_candidate": f"{type(exc).__name__}"}
    result = adjudicate(candidate)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["evidence_bound_semantic_factorial_candidate"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
