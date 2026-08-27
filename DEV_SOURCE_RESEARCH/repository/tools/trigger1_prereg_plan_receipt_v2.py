#!/usr/bin/env python3
"""Successor Trigger-1 preregistration receipt with exact executable case-plan binding.

v1 binds the complete high-level preregistration plan and gate source. v2 additionally
requires the high-level plan to freeze the exact CALIBRATION and HOLDOUT semantic-factorial
producer plan hashes before runtime. This prevents a later evidence packet from selecting a
different case-to-scenario/lexical/codebook assignment while still citing the same generic
scientific preregistration.

This tool is execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_prereg_plan_receipt as v1

RECEIPT_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SCOPE_NORM_PREREG_RECEIPT/v2"
REQUIRED_SPLITS = ("CALIBRATION", "HOLDOUT")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def bind(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise ValueError("PREREGISTRATION_PLAN_OBJECT_REQUIRED")

    base = v1.bind(plan)
    failures = list(base.get("failures") or [])
    execution = plan.get("execution")
    if not isinstance(execution, dict):
        execution = {}

    declared = execution.get("factorial_case_plan_sha256")
    normalized: dict[str, str] = {}
    if not isinstance(declared, dict):
        failures.append("EXACT_FACTORIAL_CASE_PLAN_HASHES_REQUIRED")
    else:
        extra = set(declared) - set(REQUIRED_SPLITS)
        missing = set(REQUIRED_SPLITS) - set(declared)
        if extra:
            failures.append("UNKNOWN_FACTORIAL_CASE_PLAN_SPLIT:" + ",".join(sorted(extra)))
        if missing:
            failures.append("MISSING_FACTORIAL_CASE_PLAN_SPLIT:" + ",".join(sorted(missing)))
        for split in REQUIRED_SPLITS:
            value = declared.get(split)
            if not _sha256(value):
                failures.append(f"{split}_FACTORIAL_CASE_PLAN_SHA256_REQUIRED")
            else:
                normalized[split] = str(value)

    if len(normalized) == 2 and normalized["CALIBRATION"] == normalized["HOLDOUT"]:
        failures.append("CALIBRATION_HOLDOUT_FACTORIAL_CASE_PLANS_MUST_DIFFER")

    core = {
        "schema": RECEIPT_SCHEMA,
        "base_receipt_schema": base.get("schema"),
        "base_receipt_sha256": base.get("receipt_sha256"),
        "plan_sha256": base.get("plan_sha256"),
        "gate_source_sha256": base.get("gate_source_sha256"),
        "frozen_contract_sha256": base.get("frozen_contract_sha256"),
        "factorial_case_plan_sha256": normalized,
        "pass": bool(base.get("pass") is True and not failures),
        "failures": sorted(set(failures)),
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "whole_hcu_credit_minted": False,
        "whole_entityos_hcu_credit_minted": False,
        "training_credit_minted": False,
        "evidence_boundary": (
            "PASS binds the exact high-level preregistration plus exact calibration/holdout "
            "factorial case-plan identities before runtime. It does not execute a model or "
            "mint semantic, runtime, J-Space, HCU, EntityOS, training, BASE, or effect credit."
        ),
    }
    return {**core, "receipt_sha256": canonical_sha256(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        receipt = bind(plan)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "pass": False,
            "fail_closed": True,
            "error": str(exc),
            "runtime_credit_minted": False,
        }
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt.get("pass") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
