#!/usr/bin/env python3
"""Evidence-reconstructing successor to Trigger-1 J-Space promotion v12.

v13 preserves v12 unchanged and adds one requirement: the claimed abstract internal state
must be reconstructible from an independent downstream hidden-state probe on the same exact
counterbalanced challenge, with baseline plus all three semantic commands competing on every
heldout case. This prevents boolean dual-readout / causal-matrix attestations or generic
compliance from producing a scientific candidate by declaration alone.

This adjudicator is fail-closed, execution-free and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v12 as v12
import trigger1_internal_state_specificity_gate_v2 as internal_gate

SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v13"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v13"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v12.adjudicate(candidate)
    internal = internal_gate.adjudicate(candidate)
    challenge_binding = bool(
        base.get("abstract_state_challenge_sha256")
        and internal.get("abstract_state_challenge_sha256") == base.get("abstract_state_challenge_sha256")
    )
    failures = list(base.get("v12_failures", [])) + [f"INTERNAL:{x}" for x in internal.get("failures", [])]
    if not challenge_binding:
        failures.append("V12_INTERNAL_STATE_CHALLENGE_BINDING_FAILED")
    internal_ok = internal.get("internal_state_specificity_candidate") is True
    scientific = bool(base.get("abstract_native_semantic_jspace_candidate") is True and internal_ok and challenge_binding)
    return {
        **base,
        "schema": SCHEMA,
        "v12_abstract_native_semantic_jspace_candidate": base.get("abstract_native_semantic_jspace_candidate") is True,
        "internal_state_specificity_candidate": internal_ok,
        "same_case_generic_compliance_rejected": internal.get("generic_compliance_rejected_by_same_case_competition") is True,
        "internal_state_analysis_sha256": internal.get("internal_state_analysis_sha256"),
        "v12_internal_state_challenge_binding_pass": challenge_binding,
        "abstract_native_semantic_jspace_candidate": scientific,
        "strict_micro_mechanistic_identity_candidate": False,
        "v13_failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v13 requires all v12 byte-derived label-free/lexically-disjoint/counterbalanced native evidence plus reconstruction of target-specific downstream hidden-state and behavioral effects from the same challenge using an independent calibration-only probe and same-case competition of all three nuisance-residualized commands. The historical last-token witness remains non-identical; v11/v12 scope law is preserved. External runtime receipt authenticity and canonical review remain separate, and no credit is minted here."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"schema": SCHEMA, "abstract_native_semantic_jspace_candidate": False, "v13_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"], "canonical_credit_minted": False}
    if not isinstance(candidate, dict):
        return {"schema": SCHEMA, "abstract_native_semantic_jspace_candidate": False, "v13_failures": ["CANDIDATE_OBJECT_REQUIRED"], "canonical_credit_minted": False}
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
        "abstract_native_semantic_jspace_candidate": any(x.get("abstract_native_semantic_jspace_candidate") is True for x in verdicts),
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
