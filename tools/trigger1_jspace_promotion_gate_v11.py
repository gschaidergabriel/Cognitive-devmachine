#!/usr/bin/env python3
"""Abstract-state/scope-safe successor promotion gate for Trigger-1 J-Space claims.

v11 composes the current v10 exact producer-plan/preregistration chain with the independent
abstract-state deconfound + intervention-scope companion.

The scientific upgrade is intentionally asymmetric:
- direct native ALL_PROMPT_TOKENS evidence can support an abstract native semantic J-Space
  *candidate* after lexical/compliance/output-code nuisance residualization and hard disjoint
  counterbalanced holdout;
- the historical LAST_TOKEN_ONLY witness is not needed as a causal-identity premise;
- an optional paired equivalence bridge may support cross-scope causal-effect equivalence,
  but never microscopic mechanistic identity.

This adjudicator is execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v10 as v10
import trigger1_jspace_abstract_deconfound_scope_gate as abstract_gate

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    hard = abstract_gate.adjudicate(candidate)

    base_scientific = base.get("scientifically_independent_vector_candidate") is True
    abstract_native = hard.get("abstract_native_semantic_jspace_candidate") is True
    scope_equiv = hard.get("cross_scope_causal_effect_equivalence_candidate") is True

    scientific = bool(base_scientific and abstract_native)
    failures = sorted(set(
        list(base.get("v10_failures", []))
        + list(hard.get("deconfound_failures", []))
        + list(hard.get("direct_native_scope_failures", []))
    ))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v10_scientifically_independent_vector_candidate": bool(base_scientific),
        "abstract_state_deconfound_pass": hard.get("abstract_state_deconfound_pass") is True,
        "direct_native_scope_evidence_pass": hard.get("direct_native_scope_evidence_pass") is True,
        "abstract_native_semantic_jspace_candidate": scientific,
        "cross_scope_causal_effect_equivalence_candidate": bool(scientific and scope_equiv),
        "strict_micro_mechanistic_identity_candidate": False,
        "v11_failures": failures,
        "v11_scope_bridge_failures": list(hard.get("scope_bridge_failures", [])),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v11 requires the complete v10 evidence/preregistration chain plus direct native "
            "ALL_PROMPT_TOKENS evidence after calibration-only residualization against explicit "
            "label, synonym, generic-compliance, and output-code nuisance axes, with frozen "
            "lexical/scenario-disjoint counterbalanced holdout and causal nuisance controls. "
            "The historical last-token witness is transfer evidence, not a premise for native "
            "causal identity. Optional paired TOST may establish bounded cross-scope causal-effect "
            "equivalence only. No microscopic mechanistic identity or canonical/runtime/product "
            "credit is minted by this adjudicator."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "strict_micro_mechanistic_identity_candidate": False,
            "canonical_credit_minted": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "strict_micro_mechanistic_identity_candidate": False,
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
        "abstract_native_semantic_jspace_candidate": any(
            x.get("abstract_native_semantic_jspace_candidate") is True for x in verdicts
        ),
        "cross_scope_causal_effect_equivalence_candidate": any(
            x.get("cross_scope_causal_effect_equivalence_candidate") is True for x in verdicts
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
