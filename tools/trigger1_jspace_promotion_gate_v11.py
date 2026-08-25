#!/usr/bin/env python3
"""Trigger-1 v11: v10 promotion evidence plus reconstructed lexical independence.

v11 does not require native llama.cpp cvec to be causally identical to an earlier
last-token PyTorch witness.  Native ALL_PROMPT_TOKENS evidence stands on its own carrier
scope.  Promotion additionally requires lexical_independence_gate_v1 to reconstruct the
actual model-facing basis/calibration/holdout vocabulary and reject lexical shortcuts and
generic-compliance-compatible designs.

Fail-closed, execution-free, non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v10 as v10
import trigger1_lexical_independence_gate_v1 as lexical

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    lex = lexical.validate(candidate)
    lexical_ok = lex.get("pass") is True
    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and lexical_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and lexical_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and lexical_ok)
    failures = sorted(set(list(base.get("v10_failures", [])) + list(lex.get("failures", []))))
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "reconstructed_lexical_independence_pass": lexical_ok,
        "reconstructed_lexical_independence_receipt_sha256": lex.get("lexical_independence_receipt_sha256"),
        "reconstructed_lexical_independence_failures": list(lex.get("failures", [])),
        "generic_compliance_counterhypothesis_rejected_by_design_candidate": lex.get(
            "generic_compliance_counterhypothesis_rejected_by_design_candidate"
        ) is True,
        "native_last_token_causal_identity_required": False,
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
            "v11 requires the complete v10 scientific/provenance chain plus reconstruction of label-freeness and "
            "discriminative lexical disjointness from actual model-facing prompts. Native cvec is evaluated at its "
            "true ALL_PROMPT_TOKENS scope and is never promoted by claiming equivalence to a last-token witness. "
            "A positive verdict remains a review candidate only and mints no canonical semantics or product credit."
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
            "reconstructed_lexical_independence_pass": False,
            "canonical_credit_minted": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "reconstructed_lexical_independence_pass": False,
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
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "scientifically_independent_vector_candidate": any(v.get("scientifically_independent_vector_candidate") is True for v in verdicts),
        "owner_trigger1_goal_credit_candidate": any(v.get("owner_trigger1_goal_credit_candidate") is True for v in verdicts),
        "modular_hcu_jspace_control_candidate": any(v.get("modular_hcu_jspace_control_candidate") is True for v in verdicts),
        "reconstructed_lexical_independence_pass": any(v.get("reconstructed_lexical_independence_pass") is True for v in verdicts),
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = ap.parse_args()
    result = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
