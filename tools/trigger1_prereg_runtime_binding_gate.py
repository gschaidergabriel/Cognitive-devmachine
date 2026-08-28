#!/usr/bin/env python3
"""Verify that Trigger-1 runtime/case evidence implements the exact frozen preregistration.

This boundary composes the existing preregistration gate through the exact-plan receipt.
It does not adjudicate semantic success and does not mint runtime/J-Space/HCU/product
credit. It only rejects plan/runtime drift before post-runtime promotion gates are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import trigger1_prereg_plan_receipt as prereg_receipt

VERDICT_SCHEMA = "CLAY_TRIGGER1_PREREG_RUNTIME_BINDING_GATE/v1"
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
REQUIRED_TARGETS = {"AFFIRMATIVE", "NEGATIVE", "NEUTRAL"}
REQUIRED_CODES = {"A", "B", "C"}


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _as_set(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(item) for item in value}


def _runtime_identity(candidate: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    p = plan.get("identity")
    c = candidate.get("source_identity")
    if not isinstance(p, dict):
        return ["BOUND_PLAN_IDENTITY_REQUIRED"]
    if not isinstance(c, dict):
        return ["CANDIDATE_SOURCE_IDENTITY_REQUIRED"]

    for key in ("checkpoint_sha256", "tokenizer_sha256"):
        if c.get(key) != p.get(key):
            failures.append(f"RUNTIME_PLAN_IDENTITY_MISMATCH:{key}")

    if candidate.get("runtime_intervention_class") == NATIVE_CVEC_CLASS:
        for key in ("gguf_sha256", "native_harness_sha256"):
            if not _sha256(c.get(key)) or c.get(key) != p.get(key):
                failures.append(f"NATIVE_RUNTIME_PLAN_IDENTITY_MISMATCH:{key}")
        if not _git_sha(c.get("llama_cpp_commit")) or c.get("llama_cpp_commit") != p.get(
            "llama_cpp_commit"
        ):
            failures.append("NATIVE_RUNTIME_PLAN_IDENTITY_MISMATCH:llama_cpp_commit")
    return failures


def _measurement_binding(candidate: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    outcomes = plan.get("outcomes") if isinstance(plan.get("outcomes"), dict) else {}
    measurement = plan.get("measurement") if isinstance(plan.get("measurement"), dict) else {}
    holdout = candidate.get("holdout") if isinstance(candidate.get("holdout"), dict) else {}
    intervention = (
        candidate.get("intervention") if isinstance(candidate.get("intervention"), dict) else {}
    )

    if holdout.get("metric_definition_sha256") != outcomes.get("metric_definition_sha256"):
        failures.append("RUNTIME_METRIC_DEFINITION_DRIFT_FROM_PREREGISTRATION")
    if candidate.get("runtime_intervention_class") == NATIVE_CVEC_CLASS:
        if intervention.get("token_scope") != "ALL_PROMPT_TOKENS":
            failures.append("NATIVE_CVEC_RUNTIME_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
        scopes = _as_set(measurement.get("token_scope_conditions"))
        if "NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC" not in scopes:
            failures.append("BOUND_PLAN_DOES_NOT_AUTHORIZE_NATIVE_ALL_PROMPT_TOKEN_SCOPE")
    if intervention.get("residual_norm_ratio") is None:
        failures.append("RUNTIME_RESIDUAL_NORM_RATIO_REQUIRED")
    return failures


def _case_family_binding(candidate: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    """Bind executed case rows to planned lexical/scenario families and seeds."""
    failures: list[str] = []
    attestation = candidate.get("semantic_factorial_attestation")
    if not isinstance(attestation, dict):
        return ["SEMANTIC_FACTORIAL_ATTESTATION_REQUIRED_FOR_PLAN_BINDING"]
    rows = attestation.get("rows")
    if not isinstance(rows, list) or not rows:
        return ["SEMANTIC_FACTORIAL_CASE_ROWS_REQUIRED_FOR_PLAN_BINDING"]

    scenario = (
        plan.get("scenario_blocking") if isinstance(plan.get("scenario_blocking"), dict) else {}
    )
    calibration = (
        plan.get("calibration") if isinstance(plan.get("calibration"), dict) else {}
    )
    holdout = plan.get("holdout") if isinstance(plan.get("holdout"), dict) else {}

    planned = {
        "CALIBRATION": {
            "scenario": _as_set(scenario.get("calibration_scenario_family_sha256")),
            "lexical": _as_set(calibration.get("lexical_family_sha256")),
            "seeds": {str(x) for x in (calibration.get("seeds") or [])},
        },
        "HOLDOUT": {
            "scenario": _as_set(scenario.get("holdout_scenario_family_sha256")),
            "lexical": _as_set(holdout.get("lexical_family_sha256")),
            "seeds": {str(x) for x in (holdout.get("seeds") or [])},
        },
    }

    observed = {
        "CALIBRATION": {"scenario": set(), "lexical": set()},
        "HOLDOUT": {"scenario": set(), "lexical": set()},
    }
    scenario_targets: dict[tuple[str, str], set[str]] = {}
    scenario_codes: dict[tuple[str, str], set[str]] = {}
    prompt_hashes: set[str] = set()

    for index, row in enumerate(rows):
        prefix = f"BOUND_CASE_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        split = str(row.get("split") or "").strip().upper()
        if split not in planned:
            failures.append(f"{prefix}_SPLIT_INVALID")
            continue

        scenario_sha = row.get("scenario_family_sha256")
        lexical_sha = row.get("lexical_family_sha256")
        if not _sha256(scenario_sha) or scenario_sha not in planned[split]["scenario"]:
            failures.append(f"{prefix}_SCENARIO_FAMILY_NOT_IN_BOUND_PLAN")
        else:
            observed[split]["scenario"].add(str(scenario_sha))
        if not _sha256(lexical_sha) or lexical_sha not in planned[split]["lexical"]:
            failures.append(f"{prefix}_LEXICAL_FAMILY_NOT_IN_BOUND_PLAN")
        else:
            observed[split]["lexical"].add(str(lexical_sha))

        if str(row.get("seed")) not in planned[split]["seeds"]:
            failures.append(f"{prefix}_SEED_NOT_IN_BOUND_PLAN")

        prompt_sha = row.get("prompt_sha256")
        if not _sha256(prompt_sha):
            failures.append(f"{prefix}_PROMPT_SHA256_REQUIRED")
        elif prompt_sha in prompt_hashes:
            failures.append(f"{prefix}_PROMPT_SHA256_REUSED_ACROSS_CASE_UNIVERSE")
        else:
            prompt_hashes.add(str(prompt_sha))

        target = str(row.get("semantic_target") or "").strip().upper()
        code = str(row.get("output_code_identity") or "").strip().upper()
        if _sha256(scenario_sha) and target in REQUIRED_TARGETS:
            scenario_targets.setdefault((split, str(scenario_sha)), set()).add(target)
        if _sha256(scenario_sha) and code in REQUIRED_CODES:
            scenario_codes.setdefault((split, str(scenario_sha)), set()).add(code)

    for split in ("CALIBRATION", "HOLDOUT"):
        if observed[split]["scenario"] != planned[split]["scenario"]:
            failures.append(f"{split}_EXECUTED_SCENARIO_FAMILY_SET_MISMATCH")
        if observed[split]["lexical"] != planned[split]["lexical"]:
            failures.append(f"{split}_EXECUTED_LEXICAL_FAMILY_SET_MISMATCH")
        for scenario_sha in sorted(planned[split]["scenario"]):
            key = (split, scenario_sha)
            if scenario_targets.get(key, set()) != REQUIRED_TARGETS:
                failures.append(f"{split}_SCENARIO_MISSING_SEMANTIC_TARGETS:{scenario_sha}")
            if scenario_codes.get(key, set()) != REQUIRED_CODES:
                failures.append(f"{split}_SCENARIO_MISSING_OUTPUT_CODE_ROTATION:{scenario_sha}")
    return failures


def validate(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    evidence = candidate.get("preregistration_evidence")
    if not isinstance(evidence, dict):
        failures.append("PREREGISTRATION_EVIDENCE_REQUIRED")
        evidence = {}

    plan = evidence.get("plan")
    declared_receipt = evidence.get("receipt")
    if not isinstance(plan, dict):
        failures.append("BOUND_PREREGISTRATION_PLAN_REQUIRED")
        plan = {}
    if not isinstance(declared_receipt, dict):
        failures.append("BOUND_PREREGISTRATION_RECEIPT_REQUIRED")
        declared_receipt = {}

    try:
        recomputed_receipt = prereg_receipt.bind(plan)
    except Exception as exc:
        recomputed_receipt = {}
        failures.append(f"PREREGISTRATION_RECEIPT_RECOMPUTE_FAILED:{type(exc).__name__}")

    if declared_receipt != recomputed_receipt:
        failures.append("PREREGISTRATION_RECEIPT_MISMATCH")
    if recomputed_receipt.get("pass") is not True:
        failures.append("BOUND_PREREGISTRATION_MUST_PASS")
    if evidence.get("plan_sha256") != recomputed_receipt.get("plan_sha256"):
        failures.append("PREREGISTRATION_PLAN_SHA256_BINDING_MISMATCH")
    if evidence.get("receipt_sha256") != recomputed_receipt.get("receipt_sha256"):
        failures.append("PREREGISTRATION_RECEIPT_SHA256_BINDING_MISMATCH")

    failures.extend(_runtime_identity(candidate, plan))
    failures.extend(_measurement_binding(candidate, plan))
    failures.extend(_case_family_binding(candidate, plan))

    return {
        "schema": VERDICT_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "bound_plan_sha256": recomputed_receipt.get("plan_sha256"),
        "bound_preregistration_receipt_sha256": recomputed_receipt.get("receipt_sha256"),
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "whole_hcu_credit_minted": False,
        "whole_entityos_hcu_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "This gate verifies exact preregistration-to-runtime identity/family/measurement "
            "binding only. PASS is not semantic success, model runtime credit, J-Space credit, "
            "HCU credit, EntityOS credit, training credit, or canonical truth."
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
