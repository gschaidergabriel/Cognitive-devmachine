#!/usr/bin/env python3
"""Exact producer-plan-bound successor promotion gate for Trigger-1 J-Space claims.

v10 composes the current v7 scientific/evidence chain directly with preregistration-runtime
binding v2. This supersedes the v8/v9 prototype path whose preregistration side expected a
separate semantic_factorial_attestation shape that the current hardened factorial producer
does not emit. Binding v2 instead consumes the producer's actual case_rows plus
preregistration_case_rows and requires the exact source producer plans frozen before runtime.

A positive candidate therefore requires one shared case/control universe from the exact
frozen high-level preregistration through exact producer plans, runtime split evidence and
v7 scientific adjudication. The strongest full-native flag is recomputed at this successor
boundary rather than inherited through ``**base``: it can remain true only when the upstream
full-native candidate, v7 scientific/owner/modular evidence and exact v2 plan/runtime binding
all pass together. This tool is fail-closed, execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v7 as v7
import trigger1_prereg_runtime_binding_gate_v2 as prereg_binding_v2

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v10"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v10"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v7.adjudicate(candidate)
    bound = prereg_binding_v2.validate(candidate)
    binding_ok = bound.get("pass") is True

    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and binding_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and binding_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and binding_ok)
    full_native = bool(
        base.get("full_native_jspace_vector_control_candidate") is True
        and scientific
        and owner
        and modular
        and binding_ok
    )
    failures = sorted(set(list(base.get("v7_failures", [])) + list(bound.get("failures", []))))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "preregistration_runtime_binding_v2_pass": binding_ok,
        "preregistration_runtime_binding_v2_failures": list(bound.get("failures", [])),
        "bound_preregistration_plan_sha256": bound.get("bound_plan_sha256"),
        "bound_preregistration_receipt_sha256": bound.get("bound_preregistration_receipt_sha256"),
        "bound_factorial_case_plan_sha256": bound.get("bound_factorial_case_plan_sha256"),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v10_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v10 requires both the current v7 scientific/evidence chain and exact producer-plan-bound "
            "preregistration/runtime binding v2. The exact high-level preregistration, calibration/holdout "
            "producer plans, runtime source-plan hashes, producer preregistration_case_rows and the case_rows "
            "consumed by v7 must form one bound case/control universe. The strongest full-native candidate is "
            "recomputed here and cannot survive failure of scientific, owner, modular or exact binding evidence. "
            "PASS is adjudication only and mints no canonical semantics, runtime, J-Space, HCU, EntityOS, "
            "training, BASE, or effect credit."
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
            "preregistration_runtime_binding_v2_pass": False,
            "canonical_credit_minted": False,
            "v10_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "preregistration_runtime_binding_v2_pass": False,
            "canonical_credit_minted": False,
            "v10_failures": ["CANDIDATE_OBJECT_REQUIRED"],
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
        "preregistration_runtime_binding_v2_pass": any(
            row.get("preregistration_runtime_binding_v2_pass") is True for row in verdicts
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
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
