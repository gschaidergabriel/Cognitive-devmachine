#!/usr/bin/env python3
"""Abstract-state + token-scope successor promotion gate for Trigger-1.

v11 composes the exact producer-plan-bound v10 with two non-conflated blockers:
- actual-text abstraction/lexical-disjointness auditing, including lexical pole and generic
  compliance fences; and
- three-way intervention-scope adjudication.

A native abstract-state J-Space candidate requires v10 scientific evidence plus the text-level
abstraction audit and an independently causal native all-token carrier.  Strict replication
of the earlier PyTorch last-token witness is a *separate* claim and is never required merely
for native semantic causality.

This gate is non-minting adjudication only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from tools import trigger1_jspace_promotion_gate_v10 as v10
    from tools import trigger1_abstract_state_text_audit as text_audit
    from tools import trigger1_scope_equivalence_adjudicator as scope_gate
except ImportError:  # script execution from tools/
    import trigger1_jspace_promotion_gate_v10 as v10
    import trigger1_abstract_state_text_audit as text_audit
    import trigger1_scope_equivalence_adjudicator as scope_gate

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def _build_text_payload(candidate: dict[str, Any]) -> dict[str, Any]:
    att = candidate.get("abstract_state_attestation")
    if not isinstance(att, dict):
        return {"schema": text_audit.SCHEMA}
    evidence = candidate.get("preregistration_evidence")
    evidence = evidence if isinstance(evidence, dict) else {}
    case_plans = evidence.get("case_plans")
    case_plans = case_plans if isinstance(case_plans, dict) else {}
    return {
        "schema": text_audit.SCHEMA,
        "basis_design": att.get("basis_design"),
        "calibration_plan": case_plans.get("CALIBRATION"),
        "holdout_plan": case_plans.get("HOLDOUT"),
        "config": att.get("text_audit_config") or {},
    }


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    text = text_audit.audit(_build_text_payload(candidate))
    scope_payload = candidate.get("scope_equivalence_evidence")
    scope = scope_gate.adjudicate(scope_payload if isinstance(scope_payload, dict) else {})

    abstract_text_ok = text.get("pass") is True
    native_causal_ok = bool(
        scope.get("pass") is True
        and scope.get("native_all_token_causal_carrier_candidate") is True
    )
    v10_science = base.get("scientifically_independent_vector_candidate") is True
    v10_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    v10_modular = base.get("modular_hcu_jspace_control_candidate") is True
    base_full_native = base.get("full_native_jspace_vector_control_candidate") is True

    abstract_semantic = bool(v10_science and abstract_text_ok and native_causal_ok)
    owner = bool(v10_owner and abstract_text_ok and native_causal_ok)
    modular = bool(v10_modular and abstract_text_ok and native_causal_ok)
    full_native = bool(base_full_native and v10_science and v10_modular and abstract_text_ok and native_causal_ok)
    strict_replication = bool(
        abstract_semantic and scope.get("strict_last_token_native_replication_candidate") is True
    )

    failures = sorted(set(
        list(base.get("v10_failures", []))
        + [f"ABSTRACT_TEXT:{x}" for x in text.get("failures", [])]
        + [f"SCOPE:{x}" for x in scope.get("failures", [])]
        + ([] if native_causal_ok else ["SCOPE:NATIVE_ALL_TOKEN_CAUSAL_CARRIER_REQUIRED"])
    ))

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "abstract_state_text_audit_pass": abstract_text_ok,
        "abstract_state_text_audit_receipt_sha256": text.get("audit_receipt_sha256"),
        "abstract_state_text_audit_failures": list(text.get("failures", [])),
        "scope_equivalence_classification": scope.get("classification"),
        "native_all_token_causal_carrier_candidate": native_causal_ok,
        "pytorch_last_vs_all_scope_equivalence_pass": scope.get("pytorch_last_vs_all_scope_equivalence_pass") is True,
        "native_vs_pytorch_all_token_carrier_match_pass": scope.get("native_vs_pytorch_all_token_carrier_match_pass") is True,
        "strict_last_token_native_replication_candidate": strict_replication,
        "scientifically_independent_vector_candidate": abstract_semantic,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v11_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v11 requires exact producer-plan-bound v10 evidence, actual model-facing text to pass a lexical/"
            "compliance abstraction audit, and an independently causal native all-token carrier. "
            "Strict PyTorch-last-token/native equivalence is reported separately and is not inferred "
            "from native causality. This gate never mints canonical or runtime credit."
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
            "strict_last_token_native_replication_candidate": False,
            "canonical_credit_minted": False,
            "v11_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "modular_hcu_jspace_control_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "strict_last_token_native_replication_candidate": False,
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
    positives = [row for row in verdicts if row.get("owner_trigger1_goal_credit_candidate") is True]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "abstract_native_positive_candidate_files": len(positives),
        "owner_trigger1_goal_credit_candidate": bool(positives),
        "strict_last_token_native_replication_candidate": any(
            row.get("strict_last_token_native_replication_candidate") is True for row in verdicts
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
