#!/usr/bin/env python3
"""Bind Trigger-1 preregistration PASS to the exact frozen plan and gate source.

This is a receipt layer over trigger1_label_free_scope_norm_prereg_gate. It does not
weaken that gate and does not execute a model. Its only purpose is to make Stage-1
preregistration replayable and identity-bound so a later runtime cannot cite an
unrelated generic PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_label_free_scope_norm_prereg_gate as prereg

RECEIPT_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SCOPE_NORM_PREREG_RECEIPT/v1"


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


def _source_sha256() -> str:
    return hashlib.sha256(Path(prereg.__file__).read_bytes()).hexdigest()


def _frozen_contract(plan: dict[str, Any]) -> dict[str, Any]:
    scenario = plan.get("scenario_blocking")
    calibration = plan.get("calibration")
    holdout = plan.get("holdout")
    basis = plan.get("basis")
    measurement = plan.get("measurement")
    outcomes = plan.get("outcomes")
    identity = plan.get("identity")
    controls = plan.get("controls")
    output_realization = plan.get("output_realization")
    return {
        "identity": identity if isinstance(identity, dict) else None,
        "basis_lexical_family_sha256": (
            basis.get("lexical_family_sha256") if isinstance(basis, dict) else None
        ),
        "calibration": {
            "lexical_family_sha256": (
                calibration.get("lexical_family_sha256")
                if isinstance(calibration, dict)
                else None
            ),
            "seeds": calibration.get("seeds") if isinstance(calibration, dict) else None,
        },
        "holdout": {
            "lexical_family_sha256": (
                holdout.get("lexical_family_sha256")
                if isinstance(holdout, dict)
                else None
            ),
            "seeds": holdout.get("seeds") if isinstance(holdout, dict) else None,
            "sealed_until_operating_point_frozen": (
                holdout.get("sealed_until_operating_point_frozen")
                if isinstance(holdout, dict)
                else None
            ),
        },
        "scenario_families": {
            "basis": (
                scenario.get("basis_scenario_family_sha256")
                if isinstance(scenario, dict)
                else None
            ),
            "calibration": (
                scenario.get("calibration_scenario_family_sha256")
                if isinstance(scenario, dict)
                else None
            ),
            "holdout": (
                scenario.get("holdout_scenario_family_sha256")
                if isinstance(scenario, dict)
                else None
            ),
            "blocked_rank_and_permutation_rule_sha256": (
                scenario.get("blocked_rank_and_permutation_rule_sha256")
                if isinstance(scenario, dict)
                else None
            ),
        },
        "measurement": measurement if isinstance(measurement, dict) else None,
        "controls": controls if isinstance(controls, dict) else None,
        "output_realization": (
            output_realization if isinstance(output_realization, dict) else None
        ),
        "outcomes": outcomes if isinstance(outcomes, dict) else None,
    }


def bind(plan: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(plan, dict):
        raise ValueError("PREREGISTRATION_PLAN_OBJECT_REQUIRED")
    gate_verdict = prereg.validate(plan)
    if not isinstance(gate_verdict, dict):
        raise ValueError("PREREGISTRATION_GATE_VERDICT_OBJECT_REQUIRED")

    contract = _frozen_contract(plan)
    core = {
        "schema": RECEIPT_SCHEMA,
        "plan_schema": plan.get("schema"),
        "plan_sha256": canonical_sha256(plan),
        "gate_verdict_schema": gate_verdict.get("schema"),
        "gate_source_sha256": _source_sha256(),
        "pass": gate_verdict.get("pass") is True,
        "failures": list(gate_verdict.get("failures") or []),
        "frozen_contract": contract,
        "frozen_contract_sha256": canonical_sha256(contract),
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "whole_hcu_credit_minted": False,
        "training_credit_minted": False,
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
        return 2

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if receipt["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
