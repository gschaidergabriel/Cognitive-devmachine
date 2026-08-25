#!/usr/bin/env python3
"""Abstract-state + one-token native-scope successor promotion gate for Trigger-1.

v11 composes current v10 exact producer-plan/runtime binding with two harder causal
requirements:
  * the exact bound case plans must pass the abstract structural, label-free,
    target-lexicon-matched and basis/calibration/holdout lexically-disjoint gate; and
  * native cvec runtime rows must prove cvec was inactive for prompt prefill and active
    only for a one-token decode of the original final prompt token.

This successor explicitly does NOT rehabilitate the older multi-token-prefill cvec run
as equivalent to the PyTorch hidden[:, -1, :] witness. Instead the native Q8 lane must
stand on its own position-scoped causal evidence.

Adjudication is non-minting and cannot promote canonical semantics by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v10 as v10
import trigger1_abstract_state_case_gate_v1 as abstract_gate
import trigger1_native_single_token_scope_gate_v1 as scope_gate

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v11"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v11"


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v10.adjudicate(candidate)
    abstract = abstract_gate.validate(candidate)
    scope = scope_gate.validate(candidate)

    hardening_ok = abstract.get("pass") is True and scope.get("pass") is True
    scientific = bool(base.get("scientifically_independent_vector_candidate") is True and hardening_ok)
    owner = bool(base.get("owner_trigger1_goal_credit_candidate") is True and scientific)
    modular = bool(base.get("modular_hcu_jspace_control_candidate") is True and scientific)
    full_native = bool(
        base.get("full_native_jspace_vector_control_candidate") is True
        and scientific
        and modular
        and scope.get("native_single_token_position_scope_candidate") is True
    )

    failures = sorted(set(
        list(base.get("v10_failures", []))
        + [f"ABSTRACT:{x}" for x in abstract.get("failures", [])]
        + [f"NATIVE_SCOPE:{x}" for x in scope.get("failures", [])]
    ))
    if base.get("full_native_jspace_vector_control_candidate") is True and not full_native:
        failures.append("FULL_NATIVE_REVOKED_BY_V11_HARDENING")

    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "abstract_state_case_gate_pass": abstract.get("pass") is True,
        "abstract_state_case_gate_failures": list(abstract.get("failures", [])),
        "abstract_state_design_sha256": abstract.get("design_sha256"),
        "payload_lexicon_sizes": abstract.get("payload_lexicon_sizes"),
        "payload_lexicon_overlaps": abstract.get("payload_lexicon_overlaps"),
        "native_single_token_scope_gate_pass": scope.get("pass") is True,
        "native_single_token_scope_gate_failures": list(scope.get("failures", [])),
        "legacy_multitoken_prefill_cvec_causally_identical_to_last_token_witness": False,
        "cross_runtime_numeric_identity_claimed": False,
        "cross_runtime_mechanistic_identity_claimed": False,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "full_native_jspace_vector_control_candidate": full_native,
        "v11_failures": sorted(set(failures)),
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "whole_entityos_hcu_credit": False,
        "whole_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v11 requires v10 exact producer-plan/runtime binding plus structurally derived abstract "
            "label-free state cases with matched target-variable lexicon, mutually disjoint basis/calibration/"
            "holdout payload lexicons, and native cvec runtime evidence whose active decode contains exactly "
            "the original last prompt token after unsteered prefill. The older multi-token-prefill cvec "
            "intervention remains non-identical to the PyTorch last-token witness. PASS is adjudication only "
            "and mints no canonical semantics, runtime, J-Space, HCU, EntityOS, training, BASE or effect credit."
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
            "abstract_state_case_gate_pass": False,
            "native_single_token_scope_gate_pass": False,
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
            "abstract_state_case_gate_pass": False,
            "native_single_token_scope_gate_pass": False,
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
        "abstract_state_case_gate_pass": any(row.get("abstract_state_case_gate_pass") is True for row in verdicts),
        "native_single_token_scope_gate_pass": any(
            row.get("native_single_token_scope_gate_pass") is True for row in verdicts
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
