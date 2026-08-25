#!/usr/bin/env python3
"""Evidence-bound successor promotion gate for Trigger-1 J-Space claims.

v7 composes the current promotion-v6 chain through the evidence-bound modularity-v2
companion with the semantic-factorial evidence gate. Upstream summary declarations cannot
produce a positive scientific/owner candidate unless modularity rows and calibration/
holdout semantic factorial evidence satisfy their respective reconstruction boundaries.

This adjudicator is fail-closed and non-minting. It never runs a model and cannot mint
canonical semantics, J-Space model runtime, HCU, EntityOS, training, BASE, or real-effect
credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_modularity_companion_v2 as modularity
import trigger1_semantic_factorial_evidence_gate_v1 as factorial

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v7"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v7"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = modularity.adjudicate(candidate)
    bound = factorial.adjudicate(candidate)

    factor_ok = bound.get("evidence_bound_semantic_factorial_candidate") is True
    base_scientific = base.get("scientifically_independent_vector_candidate") is True
    base_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    base_modular = base.get("modular_hcu_jspace_control_candidate") is True
    base_full_native = base.get("full_native_jspace_vector_control_candidate") is True

    scientific = bool(base_scientific and factor_ok)
    owner = bool(base_owner and factor_ok)
    modular = bool(base_modular and factor_ok)
    full_native = bool(base_full_native and base_modular and factor_ok)

    failures = sorted(set(
        list(base.get("v5_specificity_failures", []))
        + list(base.get("modularity_failures", []))
        + list(base.get("modularity_binding_failures", []))
        + list(bound.get("failures", []))
    ))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "evidence_bound_semantic_factorial_candidate": factor_ok,
        "semantic_factorial_failures": list(bound.get("failures", [])),
        "calibration_factorial_receipt_sha256": bound.get("calibration_factorial_receipt_sha256"),
        "holdout_factorial_receipt_sha256": bound.get("holdout_factorial_receipt_sha256"),
        "semantic_interaction_binding_sha256": bound.get("semantic_interaction_binding_sha256"),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v7_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v7 composes promotion-v6 through modularity-v2 and independent semantic-factorial case-row binding. "
            "A positive candidate must survive upstream scientific controls, reconstruct/digest-bind modularity family "
            "rows, and reconstruct the balanced semantic-target x output-code factorial from per-case six-control "
            "receipt digests with holdout interaction binding. The strongest inherited full-native vector-control "
            "candidate is additionally gated by both evidence-bound modularity and case-bound factorial evidence. "
            "External runtime receipt authenticity is still a separate boundary. This adjudicator mints no canonical "
            "semantics, runtime, HCU, EntityOS, training, BASE, or effect credit."
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
            "evidence_bound_semantic_factorial_candidate": False,
            "canonical_credit_minted": False,
            "v7_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "evidence_bound_semantic_factorial_candidate": False,
            "canonical_credit_minted": False,
            "v7_failures": ["CANDIDATE_OBJECT_REQUIRED"],
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
