#!/usr/bin/env python3
"""Evidence-authenticity successor for the Trigger-1 J-Space promotion chain.

V7 composes the retained v6 second-order gate with the deterministic case-bound semantic
factorial evidence gate.  This closes a narrow composition gap: v6 can only contribute to
a semantic/full-native promotion candidate when the claimed calibration/holdout 3x3
semantic-target x output-code design is reconstructed from exact case rows, every row binds
the six required runtime-control receipt identities, and the interaction analysis binds the
exact holdout factorial receipt.

This module is adjudication only.  It never runs a model and never mints canonical semantics,
J-Space model-runtime, HCU, training, EntityOS, or whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v6 as v6
import trigger1_semantic_factorial_evidence_gate_v1 as factorial

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v7"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v7"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v6.adjudicate(candidate)
    factor = factorial.adjudicate(candidate)
    factor_ok = factor.get("evidence_bound_semantic_factorial_candidate") is True

    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and factor_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and factor_ok)
    full_native = bool(base.get("full_native_jspace_vector_control_candidate") is True and factor_ok)

    owner_failures = base.get("owner_target_failures")
    if not isinstance(owner_failures, list):
        owner_failures = []
    factor_failures = factor.get("failures")
    if not isinstance(factor_failures, list):
        factor_failures = ["SEMANTIC_FACTORIAL_EVIDENCE_GATE_INVALID_RESULT"]
    composed_failures = [f"SEMANTIC_FACTORIAL_EVIDENCE:{item}" for item in factor_failures]

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v6_scientific_candidate": bool(base.get("scientifically_independent_vector_candidate") is True),
        "v6_full_native_candidate": bool(base.get("full_native_jspace_vector_control_candidate") is True),
        "case_bound_semantic_factorial_evidence_pass": factor_ok,
        "semantic_factorial_calibration_receipt_sha256": factor.get("calibration_factorial_receipt_sha256"),
        "semantic_factorial_holdout_receipt_sha256": factor.get("holdout_factorial_receipt_sha256"),
        "semantic_interaction_binding_sha256": factor.get("semantic_interaction_binding_sha256"),
        "semantic_factorial_evidence_failures": factor_failures,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "full_native_jspace_vector_control_candidate": full_native,
        "owner_target_failures": sorted(set(owner_failures + composed_failures)),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v7 composes v6 with case-bound semantic-factorial authenticity. A v6 scientific/full-native candidate "
            "is blocked unless calibration and holdout factorial claims are reconstructed from exact case rows, every "
            "row binds all six required runtime-control receipt identities, and the semantic interaction analysis binds "
            "the exact holdout factorial receipt. PASS remains a research-candidate verdict only and mints no canonical "
            "semantics, J-Space model-runtime, HCU, training, EntityOS, or whole-product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "case_bound_semantic_factorial_evidence_pass": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "semantic_factorial_evidence_failures": [],
            "owner_target_failures": [],
            "evidence_boundary": "Invalid candidate files fail closed.",
        }
    if not isinstance(candidate, dict):
        candidate = {}
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "mechanism_runtime_vector_credit_candidate": any(
            item.get("mechanism_runtime_vector_credit_candidate") is True for item in verdicts
        ),
        "scientifically_independent_vector_candidate": any(
            item.get("scientifically_independent_vector_candidate") is True for item in verdicts
        ),
        "owner_trigger1_goal_credit_candidate": any(
            item.get("owner_trigger1_goal_credit_candidate") is True for item in verdicts
        ),
        "full_native_jspace_vector_control_candidate": any(
            item.get("full_native_jspace_vector_control_candidate") is True for item in verdicts
        ),
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
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
