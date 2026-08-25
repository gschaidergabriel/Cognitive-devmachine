#!/usr/bin/env python3
"""Raw-causal-bound successor to Trigger-1 J-Space promotion gate v12.

v12 authenticates the exact target-blind/disjoint challenge bytes. v13 adds the matching
raw measurement requirement: held-out internal-state readout scores, native matched-control
causal rows and opaque-code logits must independently reconstruct the abstract-state claim.

Every inherited scientific/owner/modular promotion flag is explicitly masked by the full
v12 AND raw-evidence conjunction, preventing predecessor-positive flags from leaking through
a failed successor gate. Native ALL_PROMPT_TOKENS and historical LAST_TOKEN_ONLY evidence
remain distinct; microscopic mechanistic identity is never inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v12 as v12
import trigger1_abstract_raw_evidence_gate_v1 as raw_gate

SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v13"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v13"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v12.adjudicate(candidate)
    raw = raw_gate.adjudicate(candidate.get("abstract_state_raw_evidence"))
    v12_abstract = base.get("abstract_native_semantic_jspace_candidate") is True
    raw_ok = raw.get("raw_abstract_state_evidence_pass") is True
    abstract = bool(v12_abstract and raw_ok)

    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and abstract)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and abstract)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and abstract)
    cross_scope = bool(abstract and base.get("cross_scope_causal_effect_equivalence_candidate") is True)
    failures = sorted(set(list(base.get("v12_failures", [])) + list(raw.get("failures", []))))

    return {
        **base,
        "schema": SCHEMA,
        "v12_abstract_native_semantic_jspace_candidate": v12_abstract,
        "raw_abstract_state_evidence_pass": raw_ok,
        "raw_abstract_state_failures": list(raw.get("failures", [])),
        "raw_internal_readout_metrics": raw.get("readout"),
        "raw_native_causal_metrics": raw.get("native_causal"),
        "raw_opaque_code_metrics": raw.get("opaque_code"),
        "abstract_native_semantic_jspace_candidate": abstract,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "cross_scope_causal_effect_equivalence_candidate": cross_scope,
        "strict_micro_mechanistic_identity_candidate": False,
        "v13_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v13 requires the full v12 exact-challenge chain plus raw recomputation of balanced held-out internal "
            "state decoding, native target/null/shuffled/sign-flip causal effects, and opaque-code counterbalance. "
            "All inherited promotion flags are fail-closed behind that conjunction. Native BROADCAST evidence is "
            "not treated as causally identical to historical LAST_TOKEN_ONLY evidence. This adjudicator mints no "
            "canonical/model/HCU/EntityOS/training/effect credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "raw_abstract_state_evidence_pass": False,
            "canonical_credit_minted": False,
            "v13_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": SCHEMA,
            "abstract_native_semantic_jspace_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "raw_abstract_state_evidence_pass": False,
            "canonical_credit_minted": False,
            "v13_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    positive = [v for v in verdicts if v.get("owner_trigger1_goal_credit_candidate") is True]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "fully_raw_causal_positive_files": len(positive),
        "abstract_native_semantic_jspace_candidate": bool(positive),
        "owner_trigger1_goal_credit_candidate": bool(positive),
        "cross_scope_causal_effect_equivalence_candidate": any(v.get("cross_scope_causal_effect_equivalence_candidate") is True for v in positive),
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
