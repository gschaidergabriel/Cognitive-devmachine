#!/usr/bin/env python3
"""Hard semantic-abstraction successor for Trigger-1 J-Space claims.

v11 composes the current producer-plan-bound v10 scientific/preregistration/runtime
adjudicator with the content-derived semantic abstraction/deconfounding gate. It does
not attempt to prove the old last-token hook and native llama.cpp cvec broadcast are
causally identical; the former is discovery/provenance only and promotion is native
Q8 -> native cvec end-to-end only.

Execution-free, fail-closed and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v10 as v10
import trigger1_semantic_abstraction_gate_v1 as abstraction

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    hard = abstraction.adjudicate(candidate)
    hard_ok = hard.get("semantic_abstraction_candidate") is True

    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and hard_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and hard_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and hard_ok)
    failures = sorted(set(list(base.get("v10_failures", [])) + list(hard.get("failures", []))))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "semantic_abstraction_candidate": hard_ok,
        "semantic_abstraction_audit_sha256": hard.get("abstraction_audit_sha256"),
        "label_free_basis_prompt_universe_sha256": hard.get("basis_prompt_universe_sha256"),
        "semantic_abstraction_failures": list(hard.get("failures", [])),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "v11_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v11 requires the current v10 producer-plan/preregistration/runtime chain plus the hard semantic-abstraction gate. "
            "Positive candidate status requires content-derived lexical-family hashes, zero audited content-vocabulary overlap "
            "across basis/calibration/holdout, no direct semantic-pole lexemes in model-facing semantic prompts, a label-only "
            "nuisance control over the same exact evaluation case universe that cannot reproduce more than the preregistered "
            "fraction of the candidate semantic interaction, sign-flip reversal, and native Q8->native llama.cpp cvec-only "
            "promotion. Cross-method causal equivalence to the old last-token hook is explicitly neither required nor claimed. "
            "This is adjudication only and mints no canonical semantics/runtime/J-Space/HCU/EntityOS/training/BASE/effect credit."
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
            "semantic_abstraction_candidate": False,
            "canonical_credit_minted": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "semantic_abstraction_candidate": False,
            "canonical_credit_minted": False,
            "v11_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    positive = [
        row for row in verdicts
        if row.get("owner_trigger1_goal_credit_candidate") is True
        and row.get("modular_hcu_jspace_control_candidate") is True
        and row.get("semantic_abstraction_candidate") is True
    ]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "hard_abstraction_positive_candidate_files": len(positive),
        "owner_trigger1_goal_credit_candidate": bool(positive),
        "modular_hcu_jspace_control_candidate": bool(positive),
        "semantic_abstraction_candidate": bool(positive),
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
