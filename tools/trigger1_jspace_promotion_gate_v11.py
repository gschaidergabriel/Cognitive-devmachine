#!/usr/bin/env python3
"""Abstract-state-bound successor promotion gate for Trigger-1 J-Space claims.

v11 composes the exact producer-plan-bound v10 chain with the hard abstract-state gate.
A v10-positive candidate is still rejected for scientific/owner/modular promotion unless
its embedded ``abstract_state_attestation`` independently survives:

* model-facing semantic-label / high-risk decision-word firewalling;
* exact state-varying semantic-payload isolation;
* pairwise lexical disjointness across basis/calibration/holdout;
* balanced held-out internal-state decoding;
* matched target/null/shuffled/sign-flip internal causal controls; and
* opaque output-code counterbalance from raw code logits.

Historical PyTorch last-token evidence is not silently equated with native llama.cpp cvec
broadcast. v11 can admit a native-broadcast-only abstract-state candidate while keeping
cross-intervention equivalence false unless a support-matched bridge is separately proven.

This source-only adjudicator mints no canonical/runtime/system/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_abstract_state_evidence_gate_v1 as abstract_gate
import trigger1_jspace_promotion_gate_v10 as v10

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    abstract = abstract_gate.adjudicate(candidate.get("abstract_state_attestation"))
    native_ok = abstract.get("native_broadcast_abstract_state_candidate") is True
    cross_ok = abstract.get("cross_intervention_equivalence_candidate") is True

    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and native_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and native_ok)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and native_ok)
    failures = sorted(set(list(base.get("v10_failures", [])) + list(abstract.get("native_scope_failures", []))))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "abstract_state_gate_pass": native_ok,
        "abstract_state_gate_failures": list(abstract.get("failures", [])),
        "abstract_state_native_scope_failures": list(abstract.get("native_scope_failures", [])),
        "native_broadcast_abstract_state_candidate": native_ok,
        "cross_intervention_equivalence_candidate": cross_ok,
        "abstract_state_claim_scope": abstract.get("claim_scope"),
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
            "v11 requires the complete v10 chain plus hard label-free/lexically-disjoint/counterbalanced "
            "abstract-state evidence under the pinned native llama.cpp cvec broadcast intervention. A native "
            "abstract-state candidate does not imply causal identity with the historical last-token witness; "
            "cross-intervention equivalence remains an independent stronger claim. PASS is adjudication only "
            "and mints no canonical semantics, J-Space runtime, HCU, EntityOS, training, BASE, or effect credit."
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
            "abstract_state_gate_pass": False,
            "canonical_credit_minted": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "abstract_state_gate_pass": False,
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
    positives = [v for v in verdicts if v.get("owner_trigger1_goal_credit_candidate") is True]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "native_abstract_state_positive_files": len(positives),
        "scientifically_independent_vector_candidate": bool(positives),
        "owner_trigger1_goal_credit_candidate": bool(positives),
        "cross_intervention_equivalence_candidate": any(v.get("cross_intervention_equivalence_candidate") is True for v in positives),
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
