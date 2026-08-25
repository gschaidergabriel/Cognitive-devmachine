#!/usr/bin/env python3
"""Trigger-1 v12: v11 abstract-state gate plus reconstructive lexical audit.

v11 establishes the correct scientific contract: nuisance residualization, direct native
ALL_PROMPT_TOKENS evidence, and no causal-identity dependence on the historical last-token
witness. v12 adds one fail-closed authenticity requirement: lexical-disjointness declarations
must be reconstructed from the exact model-facing basis/calibration/holdout text universe.

Execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v11 as v11
import trigger1_reconstructive_lexical_audit_gate_v1 as lexical

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v12"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v12"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v11.adjudicate(candidate)
    audit = lexical.adjudicate(candidate)
    base_candidate = base.get("abstract_native_semantic_jspace_candidate") is True
    audit_ok = audit.get("pass") is True
    scientific = bool(base_candidate and audit_ok)
    failures = sorted(set(list(base.get("v11_failures", [])) + list(audit.get("failures", []))))
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v11_abstract_native_semantic_jspace_candidate": base_candidate,
        "reconstructive_lexical_audit_pass": audit_ok,
        "reconstructed_lexical_audit_receipt_sha256": audit.get("reconstructed_lexical_audit_receipt_sha256"),
        "abstract_native_semantic_jspace_candidate": scientific,
        "cross_scope_causal_effect_equivalence_candidate": bool(
            scientific and base.get("cross_scope_causal_effect_equivalence_candidate") is True
        ),
        "strict_micro_mechanistic_identity_candidate": False,
        "native_last_token_causal_identity_required": False,
        "v12_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v12 requires all v11 nuisance-residualized direct-native evidence and additionally reconstructs strict "
            "model-facing lexical disjointness from exact bound basis/calibration/holdout prompts. The native cvec "
            "claim stands at ALL_PROMPT_TOKENS scope; last-token equivalence is not a premise. A positive result is "
            "still a research candidate and mints no canonical semantics or runtime/product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "reconstructive_lexical_audit_pass": False,
            "canonical_credit_minted": False,
            "v12_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "reconstructive_lexical_audit_pass": False,
            "canonical_credit_minted": False,
            "v12_failures": ["CANDIDATE_OBJECT_REQUIRED"],
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
        "abstract_native_semantic_jspace_candidate": any(
            x.get("abstract_native_semantic_jspace_candidate") is True for x in verdicts
        ),
        "reconstructive_lexical_audit_pass": any(
            x.get("reconstructive_lexical_audit_pass") is True for x in verdicts
        ),
        "strict_micro_mechanistic_identity_candidate": False,
        "canonical_credit_minted": False,
        "verdicts": verdicts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--candidate")
    group.add_argument("--batch-dir")
    args = ap.parse_args()
    out = adjudicate_file(Path(args.candidate)) if args.candidate else scan_batch(Path(args.batch_dir))
    print(json.dumps(out, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
