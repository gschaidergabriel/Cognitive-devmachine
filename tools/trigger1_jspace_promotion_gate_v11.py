#!/usr/bin/env python3
"""Abstract-state successor promotion gate for Trigger-1 J-Space claims.

v11 composes the exact producer-plan-bound v10 candidate with two new evidence receipts:

1. CLAY_TRIGGER1_ABSTRACT_STATE_DECONFOUND_RECEIPT/v1
   proves the frozen design is label/proxy-free, lexically and tokenizer-token disjoint
   across BASIS/CALIBRATION/HOLDOUT, and exactly counterbalanced within matched triplets.
2. CLAY_TRIGGER1_SCOPE_EQUIVALENCE_RECEIPT/v1
   separates PyTorch last-token, PyTorch all-prompt-token and native llama.cpp broadcast
   interventions rather than silently treating them as the same causal operation.

Two claim levels remain deliberately distinct:
* native_broadcast_abstract_state_candidate: abstract-state design + matched broadcast
  carrier replication; this says nothing about equivalence to the old last-token witness.
* abstract_state_cross_scope_replication_candidate: additionally survives the direct
  LAST_TOKEN vs ALL_PROMPT scope discriminator and is the only v11 status that licenses
  calling the two intervention families scope-invariant replicas.

This is an adjudicator, not a model executor.  It mints no canonical/runtime/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v10 as v10
import trigger1_abstract_state_deconfound_gate_v1 as deconfound
import trigger1_scope_equivalence_gate_v1 as scope_gate

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _receipt_valid(receipt: Any, schema: str) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != schema:
        return False
    claimed = receipt.get("receipt_sha256")
    if not isinstance(claimed, str):
        return False
    core = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
    return claimed == canonical_sha(core)


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    failures = list(base.get("v10_failures", []))

    deconf = candidate.get("abstract_state_deconfound_receipt")
    scope = candidate.get("intervention_scope_equivalence_receipt")

    deconf_valid = _receipt_valid(deconf, deconfound.RECEIPT_SCHEMA)
    scope_valid = _receipt_valid(scope, scope_gate.RECEIPT_SCHEMA)
    if not deconf_valid:
        failures.append("ABSTRACT_STATE_DECONFOUND_RECEIPT_INVALID_OR_UNBOUND")
    if not scope_valid:
        failures.append("INTERVENTION_SCOPE_EQUIVALENCE_RECEIPT_INVALID_OR_UNBOUND")

    deconf_pass = bool(deconf_valid and deconf.get("pass") is True)
    broadcast_pass = bool(scope_valid and scope.get("broadcast_scope_carrier_replication") is True)
    strict_scope_pass = bool(scope_valid and scope.get("strict_last_token_native_identity") is True and scope.get("pass") is True)
    v10_scientific = base.get("scientifically_independent_vector_candidate") is True

    if deconf_valid and not deconf_pass:
        failures.extend("DECONFOUND:" + str(x) for x in deconf.get("failures", []))
    if scope_valid and not broadcast_pass:
        failures.append("NATIVE_BROADCAST_CARRIER_REPLICATION_NOT_ESTABLISHED")
    if scope_valid and not strict_scope_pass:
        failures.append("LAST_TOKEN_TO_BROADCAST_SCOPE_INVARIANCE_NOT_ESTABLISHED")

    native_abstract = bool(v10_scientific and deconf_pass and broadcast_pass)
    cross_scope = bool(native_abstract and strict_scope_pass)

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "abstract_state_deconfound_pass": deconf_pass,
        "abstract_state_deconfound_receipt_sha256": deconf.get("receipt_sha256") if deconf_valid else None,
        "broadcast_scope_carrier_replication": broadcast_pass,
        "strict_last_token_native_identity": strict_scope_pass,
        "scope_equivalence_receipt_sha256": scope.get("receipt_sha256") if scope_valid else None,
        "native_broadcast_abstract_state_candidate": native_abstract,
        "abstract_state_cross_scope_replication_candidate": cross_scope,
        # The strongest visible semantic-J-Space label is intentionally tied to all blockers.
        "semantic_jspace_abstract_state_candidate": cross_scope,
        "v11_failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v11 can classify a source/runtime evidence packet as an abstract-state candidate only after the "
            "v10 scientific+prereg chain, hard lexical/token deconfounding, and scope-matched carrier evidence "
            "all agree. native_broadcast_abstract_state_candidate does not equate native broadcast with the old "
            "last-token witness. semantic_jspace_abstract_state_candidate additionally requires strict three-way "
            "scope invariance. No field in this adjudicator mints canonical truth or whole-system/model/training credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "semantic_jspace_abstract_state_candidate": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "canonical_credit_minted": False,
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "semantic_jspace_abstract_state_candidate": False,
            "v11_failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "canonical_credit_minted": False,
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
        "native_broadcast_abstract_state_candidate": any(v.get("native_broadcast_abstract_state_candidate") is True for v in verdicts),
        "abstract_state_cross_scope_replication_candidate": any(v.get("abstract_state_cross_scope_replication_candidate") is True for v in verdicts),
        "semantic_jspace_abstract_state_candidate": any(v.get("semantic_jspace_abstract_state_candidate") is True for v in verdicts),
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
