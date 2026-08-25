#!/usr/bin/env python3
"""Deterministic Trigger-1 v7 semantic-factorial case/evidence producer.

This module is deliberately execution-free. It freezes an exact 3x3 requested-semantic
state x output-code design for CALIBRATION and HOLDOUT, expands each planned case into the
six required native-cvec controls, and can later bind observed per-control runtime receipt
digests into the exact evidence envelope consumed by
trigger1_semantic_factorial_evidence_gate_v1.

It must never synthesize runtime receipts and it refuses legacy AFFIRMATIVE-only 1x3 data.
Runtime rows must also echo the exact deterministic case identity; case_id alone is not a
sufficient binding between an observed receipt and its planned semantic-factorial cell.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import trigger1_semantic_factorial_evidence_gate_v1 as evidence_gate

PLAN_SCHEMA = "CLAY_TRIGGER1_V7_SEMANTIC_FACTORIAL_CASE_PLAN/v1"
BOUND_SPLIT_SCHEMA = "CLAY_TRIGGER1_V7_BOUND_SEMANTIC_FACTORIAL_SPLIT/v1"
TARGETS = evidence_gate.TARGETS
CODES = evidence_gate.CODES
CONTROLS = evidence_gate.REQUIRED_CONTROLS
SPLITS = ("CALIBRATION", "HOLDOUT")
CASE_IDENTITY_FIELDS = (
    "case_id",
    "seed",
    "prompt_sha256",
    "semantic_target",
    "output_code_identity",
    "split_family_id",
)


class EvidenceBuildError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return evidence_gate.canonical_sha(value)


def _prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _case_identity(row: dict[str, Any]) -> str:
    return canonical_sha({key: row.get(key) for key in CASE_IDENTITY_FIELDS})


def _mapping_for(target: str, target_code: str, variant: int) -> dict[str, str]:
    """Return code->semantic bijection with target fixed to target_code."""
    remaining_targets = [x for x in TARGETS if x != target]
    remaining_codes = [x for x in CODES if x != target_code]
    if variant % 2:
        remaining_targets.reverse()
    mapping = {target_code: target}
    mapping[remaining_codes[0]] = remaining_targets[0]
    mapping[remaining_codes[1]] = remaining_targets[1]
    return {code: mapping[code] for code in CODES}


def _prompt(split: str, ordinal: int, target: str, target_code: str, mapping: dict[str, str]) -> str:
    mapping_text = "; ".join(f"{code}={mapping[code]}" for code in CODES)
    if split == "CALIBRATION":
        stem = "Calibration decision card"
        verb = "Return only the code assigned to the requested state"
    else:
        stem = "Unseen evaluation decision card"
        verb = "Emit exactly the code corresponding to the requested state"
    return (
        f"/no_think\n{stem} {ordinal}. Temporary codebook: {mapping_text}. "
        f"Requested semantic state: {target}. {verb}."
    )


def build_plan(split: str) -> dict[str, Any]:
    split = str(split).strip().upper()
    if split not in SPLITS:
        raise EvidenceBuildError(f"SPLIT_INVALID:{split}")
    seed_base = 7100 if split == "CALIBRATION" else 8100
    family_id = canonical_sha({
        "schema": PLAN_SCHEMA,
        "split": split,
        "family_version": 1,
        "purpose": "semantic_target_x_output_code_factorial",
    })
    cases: list[dict[str, Any]] = []
    ordinal = 0
    for target_index, target in enumerate(TARGETS):
        for code_index, target_code in enumerate(CODES):
            ordinal += 1
            mapping = _mapping_for(target, target_code, target_index + code_index + (0 if split == "CALIBRATION" else 1))
            prompt = _prompt(split, ordinal, target, target_code, mapping)
            case = {
                "case_id": f"{split.lower()}-{target.lower()}-{target_code.lower()}-v1",
                "seed": seed_base + ordinal,
                "semantic_target": target,
                "output_code_identity": target_code,
                "codebook": mapping,
                "prompt": prompt,
                "prompt_sha256": _prompt_sha(prompt),
                "split_family_id": family_id,
            }
            case["case_identity_sha256"] = _case_identity(case)
            cases.append(case)
    plan_core = {
        "schema": PLAN_SCHEMA,
        "split": split,
        "split_family_id": family_id,
        "semantic_targets": list(TARGETS),
        "output_codes": list(CODES),
        "required_controls": list(CONTROLS),
        "case_identity_fields": list(CASE_IDENTITY_FIELDS),
        "case_count": len(cases),
        "cases": cases,
        "model_executed": False,
        "runtime_receipts_present": False,
    }
    return {**plan_core, "plan_sha256": canonical_sha(plan_core)}


def expand_runtime_cases(plan: dict[str, Any], candidate_key: str) -> list[dict[str, Any]]:
    _validate_plan(plan)
    if not isinstance(candidate_key, str) or not candidate_key.strip():
        raise EvidenceBuildError("CANDIDATE_KEY_REQUIRED")
    expanded: list[dict[str, Any]] = []
    for case in plan["cases"]:
        for control in CONTROLS:
            expanded.append({
                "case_id": case["case_id"],
                "case_identity_sha256": case["case_identity_sha256"],
                "seed": case["seed"],
                "semantic_target": case["semantic_target"],
                "target_label": case["output_code_identity"],
                "output_code_identity": case["output_code_identity"],
                "prompt": case["prompt"],
                "prompt_sha256": case["prompt_sha256"],
                "prompt_family": case["case_id"],
                "split_family_id": case["split_family_id"],
                "control": control,
                "candidate_key": candidate_key,
            })
    return expanded


def _validate_plan(plan: Any) -> None:
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise EvidenceBuildError("PLAN_SCHEMA_INVALID")
    split = plan.get("split")
    if split not in SPLITS:
        raise EvidenceBuildError("PLAN_SPLIT_INVALID")
    cases = plan.get("cases")
    if not isinstance(cases, list) or len(cases) != 9:
        raise EvidenceBuildError("PLAN_EXACTLY_NINE_CASES_REQUIRED")
    if plan.get("runtime_receipts_present") is not False:
        raise EvidenceBuildError("PLAN_MUST_NOT_PRETEND_RUNTIME_RECEIPTS")
    if plan.get("model_executed") is not False:
        raise EvidenceBuildError("PLAN_MUST_BE_EXECUTION_FREE")
    if plan.get("case_identity_fields") != list(CASE_IDENTITY_FIELDS):
        raise EvidenceBuildError("PLAN_CASE_IDENTITY_FIELDS_MISMATCH")
    observed = {(row.get("semantic_target"), row.get("output_code_identity")) for row in cases}
    expected = {(target, code) for target in TARGETS for code in CODES}
    if observed != expected:
        raise EvidenceBuildError("PLAN_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")
    family_ids = {row.get("split_family_id") for row in cases}
    if len(family_ids) != 1 or None in family_ids:
        raise EvidenceBuildError("PLAN_SINGLE_SPLIT_FAMILY_REQUIRED")
    case_ids = [row.get("case_id") for row in cases]
    if any(not isinstance(x, str) or not x for x in case_ids) or len(set(case_ids)) != len(case_ids):
        raise EvidenceBuildError("PLAN_UNIQUE_CASE_IDS_REQUIRED")
    prompt_hashes = [row.get("prompt_sha256") for row in cases]
    if any(not isinstance(x, str) or len(x) != 64 for x in prompt_hashes) or len(set(prompt_hashes)) != len(prompt_hashes):
        raise EvidenceBuildError("PLAN_UNIQUE_PROMPT_SHA256_REQUIRED")
    for row in cases:
        mapping = row.get("codebook")
        if not isinstance(mapping, dict) or set(mapping) != set(CODES) or set(mapping.values()) != set(TARGETS):
            raise EvidenceBuildError(f"PLAN_CODEBOOK_INVALID:{row.get('case_id')}")
        if mapping[row["output_code_identity"]] != row["semantic_target"]:
            raise EvidenceBuildError(f"PLAN_TARGET_CODEBOOK_MISMATCH:{row.get('case_id')}")
        if row.get("case_identity_sha256") != _case_identity(row):
            raise EvidenceBuildError(f"PLAN_CASE_IDENTITY_MISMATCH:{row.get('case_id')}")


def bind_runtime_receipts(plan: dict[str, Any], runtime_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bind observed per-control receipts only after exact planned-case identity replay."""
    _validate_plan(plan)
    if not isinstance(runtime_rows, list):
        raise EvidenceBuildError("RUNTIME_ROWS_LIST_REQUIRED")
    expected_by_case = {row["case_id"]: row for row in plan["cases"]}
    grouped: dict[str, dict[str, str]] = {case_id: {} for case_id in expected_by_case}
    for index, row in enumerate(runtime_rows):
        if not isinstance(row, dict):
            raise EvidenceBuildError(f"RUNTIME_ROW_{index}_OBJECT_REQUIRED")
        case_id = row.get("case_id")
        control = row.get("control")
        receipt = row.get("runtime_receipt_sha256")
        if case_id not in expected_by_case:
            raise EvidenceBuildError(f"RUNTIME_ROW_UNKNOWN_CASE:{case_id}")
        expected_case = expected_by_case[case_id]
        if row.get("case_identity_sha256") != expected_case["case_identity_sha256"]:
            raise EvidenceBuildError(f"RUNTIME_ROW_CASE_IDENTITY_MISMATCH:{case_id}")
        for field in CASE_IDENTITY_FIELDS:
            if row.get(field) != expected_case.get(field):
                raise EvidenceBuildError(f"RUNTIME_ROW_CASE_FIELD_MISMATCH:{case_id}:{field}")
        if control not in CONTROLS:
            raise EvidenceBuildError(f"RUNTIME_ROW_UNKNOWN_CONTROL:{control}")
        if not isinstance(receipt, str) or len(receipt) != 64:
            raise EvidenceBuildError(f"RUNTIME_ROW_RECEIPT_INVALID:{case_id}:{control}")
        try:
            int(receipt, 16)
        except ValueError as exc:
            raise EvidenceBuildError(f"RUNTIME_ROW_RECEIPT_INVALID:{case_id}:{control}") from exc
        if control in grouped[case_id]:
            raise EvidenceBuildError(f"RUNTIME_ROW_DUPLICATE_CONTROL:{case_id}:{control}")
        grouped[case_id][control] = receipt.lower()

    case_rows: list[dict[str, Any]] = []
    for case_id in sorted(expected_by_case):
        case = expected_by_case[case_id]
        receipts = grouped[case_id]
        missing = [control for control in CONTROLS if control not in receipts]
        if missing:
            raise EvidenceBuildError(f"RUNTIME_CONTROLS_MISSING:{case_id}:{','.join(missing)}")
        case_rows.append({
            "case_id": case_id,
            "seed": case["seed"],
            "prompt_sha256": case["prompt_sha256"],
            "semantic_target": case["semantic_target"],
            "output_code_identity": case["output_code_identity"],
            "split_family_id": case["split_family_id"],
            "control_runtime_receipts": {control: receipts[control] for control in CONTROLS},
        })

    counts = {target: {code: 0 for code in CODES} for target in TARGETS}
    for row in case_rows:
        counts[row["semantic_target"]][row["output_code_identity"]] += 1
    split_name = str(plan["split"])
    material = {
        "schema": evidence_gate.FACTORIAL_RECEIPT_SCHEMA,
        "split_name": split_name,
        "split_family_id": plan["split_family_id"],
        "semantic_targets": list(TARGETS),
        "output_codes": list(CODES),
        "required_controls": list(CONTROLS),
        "factorial_counts": counts,
        "case_rows": sorted(
            case_rows,
            key=lambda row: (
                row["semantic_target"], row["output_code_identity"], row["case_id"], row["seed"]
            ),
        ),
    }
    receipt = canonical_sha(material)
    split = {
        "schema": BOUND_SPLIT_SCHEMA,
        "family_id": plan["split_family_id"],
        "semantic_targets": list(TARGETS),
        "semantic_target_counterbalanced": True,
        "label_mapping_counterbalanced": True,
        "semantic_target_x_output_code_factorial": True,
        "semantic_target_x_output_code_counts": counts,
        "case_rows": case_rows,
        "semantic_factorial_receipt_sha256": receipt,
        "source_plan_sha256": plan["plan_sha256"],
        "runtime_case_identity_binding": True,
    }
    derived, failures = evidence_gate.derive_split_receipt(split, split_name)
    if failures or derived is None or derived["receipt_sha256"] != receipt:
        raise EvidenceBuildError("EVIDENCE_GATE_SELF_CHECK_FAILED:" + ",".join(failures))
    return split


def build_interaction_binding(
    holdout_factorial_receipt_sha256: str,
    metric_definition_sha256: str,
    analysis_implementation_sha256: str,
    analysis_result_receipt_sha256: str,
) -> dict[str, Any]:
    analysis = {
        "factorial_receipt_sha256": holdout_factorial_receipt_sha256,
        "metric_definition_sha256": metric_definition_sha256,
        "analysis_implementation_sha256": analysis_implementation_sha256,
        "analysis_result_receipt_sha256": analysis_result_receipt_sha256,
        "treatment_control_identities": list(CONTROLS),
    }
    material = {
        "schema": evidence_gate.INTERACTION_BINDING_SCHEMA,
        "holdout_factorial_receipt_sha256": holdout_factorial_receipt_sha256,
        "metric_definition_sha256": metric_definition_sha256.lower(),
        "analysis_implementation_sha256": analysis_implementation_sha256.lower(),
        "analysis_result_receipt_sha256": analysis_result_receipt_sha256.lower(),
        "treatment_control_identities": list(CONTROLS),
    }
    analysis["analysis_binding_sha256"] = canonical_sha(material)
    bound, failures = evidence_gate.derive_interaction_binding(analysis, holdout_factorial_receipt_sha256)
    if failures or bound is None:
        raise EvidenceBuildError("INTERACTION_BINDING_SELF_CHECK_FAILED:" + ",".join(failures))
    return analysis


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=SPLITS)
    ap.add_argument("--output")
    args = ap.parse_args()
    plans = [build_plan(args.split)] if args.split else [build_plan(split) for split in SPLITS]
    payload: Any = plans[0] if args.split else {
        "schema": "CLAY_TRIGGER1_V7_SEMANTIC_FACTORIAL_PLAN_SET/v1",
        "plans": plans,
        "model_executed": False,
        "runtime_credit": 0,
    }
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
