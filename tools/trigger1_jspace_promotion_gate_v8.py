#!/usr/bin/env python3
"""Plan-bound successor promotion gate for Trigger-1 J-Space claims.

v8 composes the complete v7 scientific/evidence-bound chain with the exact
preregistration-to-runtime binding gate. A v7-positive candidate is still rejected if
its executed checkpoint/GGUF/runtime identity, metric, seeds, lexical families, scenario
families, or case universe drifted from the frozen Stage-1 preregistration.

This adjudicator is fail-closed and non-minting. It never runs a model and cannot mint
canonical semantics, J-Space model runtime, HCU, EntityOS, training, BASE, or effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v7 as v7
import trigger1_prereg_runtime_binding_gate as prereg_binding

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v8"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v8"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v7.adjudicate(candidate)
    bound = prereg_binding.validate(candidate)

    binding_ok = bound.get("pass") is True
    scientific = bool(
        base.get("scientifically_independent_vector_candidate") is True and binding_ok
    )
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and binding_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and binding_ok)
    full_native = bool(
        base.get("full_native_jspace_vector_control_candidate") is True and binding_ok
    )

    failures = sorted(
        set(list(base.get("v7_failures", [])) + list(bound.get("failures", [])))
    )

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "preregistration_runtime_binding_pass": binding_ok,
        "preregistration_runtime_binding_failures": list(bound.get("failures", [])),
        "bound_preregistration_plan_sha256": bound.get("bound_plan_sha256"),
        "bound_preregistration_receipt_sha256": bound.get(
            "bound_preregistration_receipt_sha256"
        ),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v8_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v8 composes the complete v7 scientific/evidence chain with exact frozen "
            "preregistration-to-runtime binding. Positive candidate status, including the strongest inherited "
            "full-native vector-control candidate, requires both the corresponding v7 evidence result and "
            "plan/runtime binding PASS; plan mutation, identity drift, metric drift, unplanned lexical/scenario "
            "families, seed drift, prompt reuse, or incomplete scenario target/code coverage fail closed. This is "
            "adjudication only and mints no canonical semantics, runtime, HCU, EntityOS, training, BASE, or effect credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "preregistration_runtime_binding_pass": False,
            "canonical_credit_minted": False,
            "v8_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "preregistration_runtime_binding_pass": False,
            "canonical_credit_minted": False,
            "v8_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "scientifically_independent_vector_candidate": any(
            row.get("scientifically_independent_vector_candidate") is True for row in verdicts
        ),
        "owner_trigger1_goal_credit_candidate": any(
            row.get("owner_trigger1_goal_credit_candidate") is True for row in verdicts
        ),
        "modular_hcu_jspace_control_candidate": any(
            row.get("modular_hcu_jspace_control_candidate") is True for row in verdicts
        ),
        "full_native_jspace_vector_control_candidate": any(
            row.get("full_native_jspace_vector_control_candidate") is True for row in verdicts
        ),
        "preregistration_runtime_binding_pass": any(
            row.get("preregistration_runtime_binding_pass") is True for row in verdicts
        ),
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = parser.parse_args()
    result = (
        adjudicate_file(Path(args.candidate))
        if args.candidate
        else scan_batch(Path(args.batch_dir))
    )
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
