#!/usr/bin/env python3
"""Exact executable-case-plan successor for Trigger-1 preregistration/runtime binding.

v2 closes the remaining assignment self-attestation gap. It requires:
- the v2 preregistration receipt to freeze exact CALIBRATION/HOLDOUT producer-plan hashes;
- the exact source producer plan objects to be carried with the candidate and hash-replayed;
- each bound runtime split to cite the frozen source-plan hash;
- producer preregistration_case_rows to match the exact source case-plan identities;
- the scientific case_rows consumed by the v7 evidence gate to match those same case rows
  and runtime receipt sets; and
- executed scenario/lexical/codebook family sets, seeds, prompts and metric/runtime identity
  to match the frozen high-level preregistration.

The gate is adjudication only. It never runs a model or mints semantic/runtime/J-Space/HCU/
EntityOS/training/BASE/effect credit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import trigger1_prereg_plan_receipt_v2 as receipt_v2
import trigger1_prereg_runtime_binding_gate as binding_v1
import trigger1_v7_factorial_case_evidence as producer

VERDICT_SCHEMA = "CLAY_TRIGGER1_PREREG_RUNTIME_BINDING_GATE/v2"
REQUIRED_SPLITS = ("CALIBRATION", "HOLDOUT")
PLAN_CASE_FIELDS = (
    "case_id",
    "seed",
    "prompt_sha256",
    "semantic_target",
    "output_code_identity",
    "split_family_id",
    "scenario_family_sha256",
    "lexical_family_sha256",
    "codebook_family_sha256",
    "case_identity_sha256",
)
EVIDENCE_LINK_FIELDS = (
    "case_id",
    "seed",
    "prompt_sha256",
    "semantic_target",
    "output_code_identity",
    "split_family_id",
    "control_runtime_receipts",
)


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(value) for value in values}


def _recompute_source_plan(source_plan: Any, split: str) -> tuple[str | None, list[str]]:
    failures: list[str] = []
    if not isinstance(source_plan, dict):
        return None, [f"{split}_SOURCE_CASE_PLAN_OBJECT_REQUIRED"]
    try:
        producer._validate_plan(source_plan)
    except Exception as exc:
        failures.append(f"{split}_SOURCE_CASE_PLAN_INVALID:{type(exc).__name__}:{exc}")
        return None, failures
    if source_plan.get("split") != split:
        failures.append(f"{split}_SOURCE_CASE_PLAN_SPLIT_MISMATCH")
    declared = source_plan.get("plan_sha256")
    core = {key: value for key, value in source_plan.items() if key != "plan_sha256"}
    recomputed = producer.canonical_sha(core)
    if declared != recomputed:
        failures.append(f"{split}_SOURCE_CASE_PLAN_SHA256_RECOMPUTE_MISMATCH")
    return recomputed, failures


def _expected_high_level_sets(plan: dict[str, Any], split: str) -> dict[str, set[str]]:
    split_obj = plan.get(split.lower()) if isinstance(plan.get(split.lower()), dict) else {}
    scenario = plan.get("scenario_blocking") if isinstance(plan.get("scenario_blocking"), dict) else {}
    output = plan.get("output_realization") if isinstance(plan.get("output_realization"), dict) else {}
    scenario_key = f"{split.lower()}_scenario_family_sha256"
    return {
        "scenario": _set(scenario.get(scenario_key)),
        "lexical": _set(split_obj.get("lexical_family_sha256")),
        "seed": {str(x) for x in (split_obj.get("seeds") or [])},
        "codebook": _set(output.get("codebook_family_sha256")),
    }


def _split_case_binding(
    candidate: dict[str, Any],
    high_level_plan: dict[str, Any],
    source_plan: dict[str, Any],
    source_plan_sha: str,
    split: str,
    global_prompt_hashes: set[str],
) -> list[str]:
    failures: list[str] = []
    split_obj = candidate.get(split.lower())
    if not isinstance(split_obj, dict):
        return [f"{split}_BOUND_RUNTIME_SPLIT_OBJECT_REQUIRED"]
    if split_obj.get("source_plan_sha256") != source_plan_sha:
        failures.append(f"{split}_BOUND_SPLIT_SOURCE_PLAN_SHA256_MISMATCH")

    prereg_rows = split_obj.get("preregistration_case_rows")
    evidence_rows = split_obj.get("case_rows")
    if not isinstance(prereg_rows, list):
        failures.append(f"{split}_PREREGISTRATION_CASE_ROWS_REQUIRED")
        prereg_rows = []
    if not isinstance(evidence_rows, list):
        failures.append(f"{split}_EVIDENCE_CASE_ROWS_REQUIRED")
        evidence_rows = []

    source_cases = source_plan.get("cases") if isinstance(source_plan.get("cases"), list) else []
    if len(prereg_rows) != len(source_cases):
        failures.append(f"{split}_PREREGISTRATION_CASE_COUNT_MUST_MATCH_SOURCE_PLAN")
    if len(evidence_rows) != len(source_cases):
        failures.append(f"{split}_EVIDENCE_CASE_COUNT_MUST_MATCH_SOURCE_PLAN")

    source_by_id = {
        row.get("case_id"): row for row in source_cases if isinstance(row, dict) and row.get("case_id")
    }
    prereg_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(prereg_rows):
        prefix = f"{split}_PREREG_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        case_id = row.get("case_id")
        if case_id in prereg_by_id:
            failures.append(f"{prefix}_DUPLICATE_CASE_ID")
            continue
        if case_id not in source_by_id:
            failures.append(f"{prefix}_CASE_NOT_IN_SOURCE_PLAN")
            continue
        prereg_by_id[str(case_id)] = row
        source_case = source_by_id[case_id]
        for field in PLAN_CASE_FIELDS:
            if row.get(field) != source_case.get(field):
                failures.append(f"{prefix}_SOURCE_PLAN_FIELD_MISMATCH:{field}")
        prompt_sha = row.get("prompt_sha256")
        if not _sha256(prompt_sha):
            failures.append(f"{prefix}_PROMPT_SHA256_REQUIRED")
        elif str(prompt_sha) in global_prompt_hashes:
            failures.append(f"{prefix}_PROMPT_SHA256_REUSED_ACROSS_SPLITS")
        else:
            global_prompt_hashes.add(str(prompt_sha))

    evidence_by_id: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(evidence_rows):
        prefix = f"{split}_EVIDENCE_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        case_id = row.get("case_id")
        if case_id in evidence_by_id:
            failures.append(f"{prefix}_DUPLICATE_CASE_ID")
            continue
        evidence_by_id[str(case_id)] = row
        prereg_row = prereg_by_id.get(str(case_id))
        if prereg_row is None:
            failures.append(f"{prefix}_NO_MATCHING_PREREGISTRATION_CASE_ROW")
            continue
        for field in EVIDENCE_LINK_FIELDS:
            if row.get(field) != prereg_row.get(field):
                failures.append(f"{prefix}_PREREGISTRATION_FIELD_MISMATCH:{field}")

    if set(source_by_id) != set(prereg_by_id):
        failures.append(f"{split}_PREREGISTRATION_CASE_UNIVERSE_MISMATCH")
    if set(source_by_id) != set(evidence_by_id):
        failures.append(f"{split}_EVIDENCE_CASE_UNIVERSE_MISMATCH")

    expected = _expected_high_level_sets(high_level_plan, split)
    observed = {
        "scenario": {str(row.get("scenario_family_sha256")) for row in prereg_rows if isinstance(row, dict)},
        "lexical": {str(row.get("lexical_family_sha256")) for row in prereg_rows if isinstance(row, dict)},
        "seed": {str(row.get("seed")) for row in prereg_rows if isinstance(row, dict)},
        "codebook": {str(row.get("codebook_family_sha256")) for row in prereg_rows if isinstance(row, dict)},
    }
    for name in ("scenario", "lexical", "seed", "codebook"):
        if observed[name] != expected[name]:
            failures.append(f"{split}_EXECUTED_{name.upper()}_SET_MISMATCH_WITH_HIGH_LEVEL_PREREG")

    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in prereg_rows:
        if isinstance(row, dict) and _sha256(row.get("scenario_family_sha256")):
            by_scenario.setdefault(str(row["scenario_family_sha256"]), []).append(row)
    for scenario_sha in sorted(expected["scenario"]):
        rows = by_scenario.get(scenario_sha, [])
        if {str(row.get("semantic_target")) for row in rows} != set(producer.TARGETS):
            failures.append(f"{split}_SCENARIO_MISSING_SEMANTIC_TARGETS:{scenario_sha}")
        if {str(row.get("output_code_identity")) for row in rows} != set(producer.CODES):
            failures.append(f"{split}_SCENARIO_MISSING_OUTPUT_CODE_ROTATION:{scenario_sha}")
        if len({str(row.get("lexical_family_sha256")) for row in rows}) != 1:
            failures.append(f"{split}_SCENARIO_LEXICAL_FAMILY_NOT_MATCHED:{scenario_sha}")

    return failures


def validate(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    evidence = candidate.get("preregistration_evidence")
    if not isinstance(evidence, dict):
        failures.append("PREREGISTRATION_EVIDENCE_REQUIRED")
        evidence = {}

    high_level_plan = evidence.get("plan")
    declared_receipt = evidence.get("receipt")
    case_plans = evidence.get("case_plans")
    if not isinstance(high_level_plan, dict):
        failures.append("BOUND_HIGH_LEVEL_PREREGISTRATION_PLAN_REQUIRED")
        high_level_plan = {}
    if not isinstance(declared_receipt, dict):
        failures.append("BOUND_PREREGISTRATION_RECEIPT_V2_REQUIRED")
        declared_receipt = {}
    if not isinstance(case_plans, dict):
        failures.append("BOUND_SOURCE_CASE_PLANS_REQUIRED")
        case_plans = {}

    try:
        recomputed_receipt = receipt_v2.bind(high_level_plan)
    except Exception as exc:
        recomputed_receipt = {}
        failures.append(f"PREREGISTRATION_RECEIPT_V2_RECOMPUTE_FAILED:{type(exc).__name__}")

    if declared_receipt != recomputed_receipt:
        failures.append("PREREGISTRATION_RECEIPT_V2_MISMATCH")
    if recomputed_receipt.get("pass") is not True:
        failures.append("BOUND_PREREGISTRATION_RECEIPT_V2_MUST_PASS")
    if evidence.get("plan_sha256") != recomputed_receipt.get("plan_sha256"):
        failures.append("PREREGISTRATION_PLAN_SHA256_BINDING_MISMATCH")
    if evidence.get("receipt_sha256") != recomputed_receipt.get("receipt_sha256"):
        failures.append("PREREGISTRATION_RECEIPT_V2_SHA256_BINDING_MISMATCH")

    failures.extend(binding_v1._runtime_identity(candidate, high_level_plan))
    failures.extend(binding_v1._measurement_binding(candidate, high_level_plan))

    frozen_case_hashes = recomputed_receipt.get("factorial_case_plan_sha256")
    if not isinstance(frozen_case_hashes, dict):
        frozen_case_hashes = {}
    global_prompt_hashes: set[str] = set()
    observed_case_hashes: dict[str, str] = {}
    for split in REQUIRED_SPLITS:
        source_plan = case_plans.get(split)
        recomputed_plan_sha, plan_failures = _recompute_source_plan(source_plan, split)
        failures.extend(plan_failures)
        if recomputed_plan_sha is None:
            continue
        observed_case_hashes[split] = recomputed_plan_sha
        if frozen_case_hashes.get(split) != recomputed_plan_sha:
            failures.append(f"{split}_SOURCE_CASE_PLAN_NOT_FROZEN_BY_PREREGISTRATION")
        failures.extend(
            _split_case_binding(
                candidate,
                high_level_plan,
                source_plan,
                recomputed_plan_sha,
                split,
                global_prompt_hashes,
            )
        )

    return {
        "schema": VERDICT_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "bound_plan_sha256": recomputed_receipt.get("plan_sha256"),
        "bound_preregistration_receipt_sha256": recomputed_receipt.get("receipt_sha256"),
        "bound_factorial_case_plan_sha256": observed_case_hashes,
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "whole_hcu_credit_minted": False,
        "whole_entityos_hcu_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "v2 verifies exact high-level preregistration, exact source factorial case-plan "
            "objects, runtime split source-plan identity, case/evidence row linkage and high-level "
            "scenario/lexical/codebook/seed/metric/runtime identity. PASS is not semantic success "
            "and mints no runtime, J-Space, HCU, EntityOS, training, BASE, or effect credit."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    verdict = validate(candidate)
    text = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if verdict["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
