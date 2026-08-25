#!/usr/bin/env python3
"""Abstract-state + native-token-scope successor promotion gate for Trigger-1.

v10 composes v9 and closes the two remaining shortcut classes explicitly:

1. semantic abstraction: the calibration basis must come from the source-validated
   instruction-free six-family challenge, and the fresh holdout must be lexically disjoint
   and target-blind (identical model-facing prompt bytes for all three cvec targets);
2. intervention scope: the primary promotion run must use the native llama.cpp cvec only
   after an unsteered prefix prefill, on exactly the final prompt-token decode.  BROADCAST
   is a separate operational intervention and is not silently equated with the prior
   last-token witness.

A positive v10 result is still a research promotion CANDIDATE.  This deterministic gate
never runs the model, authenticates external receipt bytes by itself, or mints canonical
semantics/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v9 as v9
import trigger1_abstract_state_challenge_v1 as abstract_challenge
import trigger1_native_cvec_scope_analyze_v1 as scope_analyzer

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v10"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v10"
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _recompute_embedded_analysis(value: dict[str, Any]) -> str:
    core = dict(value)
    core.pop("analysis_sha256", None)
    return scope_analyzer.canonical_sha(core)


def _abstract_design(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    challenge = candidate.get("abstract_state_challenge")
    verdict = abstract_challenge.validate(challenge)
    failures = [f"ABSTRACT_DESIGN:{item}" for item in verdict.get("failures", [])]
    required_true = (
        "calibration_instruction_free",
        "holdout_target_blind",
        "repeated_target_lexical_marker_absent",
        "cross_split_content_lexically_disjoint",
        "semantic_target_x_code_counterbalanced",
    )
    for key in required_true:
        if verdict.get(key) is not True:
            failures.append(f"ABSTRACT_DESIGN_REQUIRED:{key}")
    if not _sha256(verdict.get("challenge_sha256")):
        failures.append("ABSTRACT_DESIGN_CHALLENGE_SHA256_REQUIRED")
    return bool(verdict.get("pass") is True and not failures), sorted(set(failures)), verdict


def _localized_scope(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    evidence = candidate.get("native_token_scope_evidence")
    failures: list[str] = []
    if not isinstance(evidence, dict):
        return False, ["NATIVE_TOKEN_SCOPE_EVIDENCE_REQUIRED"], {}
    analysis = evidence.get("analysis")
    if not isinstance(analysis, dict):
        return False, ["NATIVE_TOKEN_SCOPE_ANALYSIS_REQUIRED"], {}
    if analysis.get("schema") != scope_analyzer.SCHEMA:
        failures.append("NATIVE_TOKEN_SCOPE_ANALYSIS_SCHEMA_INVALID")
    declared = analysis.get("analysis_sha256")
    recomputed = _recompute_embedded_analysis(analysis)
    if not _sha256(declared) or declared != recomputed:
        failures.append("NATIVE_TOKEN_SCOPE_ANALYSIS_SHA256_MISMATCH")
    if analysis.get("pass") is not True:
        failures.append("NATIVE_TOKEN_SCOPE_ANALYSIS_MUST_PASS")
    if analysis.get("localized_native_scope_pass") is not True:
        failures.append("LAST_TOKEN_NATIVE_SCOPE_MUST_BE_OBSERVED")
    if analysis.get("immediate_actuator_equivalence_pass") is not True:
        failures.append("LOCALIZED_AND_BROADCAST_IMMEDIATE_ACTUATOR_PARITY_REQUIRED")
    if analysis.get("broadcast_full_causal_identity_claimed") is not False:
        failures.append("BROADCAST_FULL_CAUSAL_IDENTITY_MUST_NOT_BE_ASSUMED")

    for key in (
        "scope_probe_runtime_receipt_sha256",
        "scope_probe_harness_sha256",
        "localized_executor_sha256",
    ):
        if not _sha256(evidence.get(key)):
            failures.append(f"NATIVE_SCOPE_{key.upper()}_REQUIRED")
    if evidence.get("native_api") != "llama_set_adapter_cvec":
        failures.append("NATIVE_SCOPE_API_MUST_BE_LLAMA_SET_ADAPTER_CVEC")
    if evidence.get("promotion_token_scope") != "LAST_TOKEN_DECODE_ONLY":
        failures.append("PROMOTION_TOKEN_SCOPE_MUST_BE_LAST_TOKEN_DECODE_ONLY")
    if evidence.get("prefix_prefill_without_cvec") is not True:
        failures.append("PREFIX_MUST_BE_PREFILLED_WITHOUT_CVEC")
    if evidence.get("final_token_native_cvec_applied") is not True:
        failures.append("FINAL_TOKEN_NATIVE_CVEC_MUST_BE_APPLIED")
    return not failures, sorted(set(failures)), analysis


def _abstract_runtime(
    candidate: dict[str, Any], design_verdict: dict[str, Any]
) -> tuple[bool, list[str], dict[str, Any]]:
    evidence = candidate.get("abstract_state_runtime_evidence")
    failures: list[str] = []
    if not isinstance(evidence, dict):
        return False, ["ABSTRACT_STATE_RUNTIME_EVIDENCE_REQUIRED"], {}

    if candidate.get("runtime_intervention_class") != NATIVE_CVEC_CLASS:
        failures.append("ABSTRACT_STATE_RUNTIME_MUST_USE_NATIVE_LLAMA_CPP_CVEC")
    if evidence.get("token_scope") != "LAST_TOKEN_DECODE_ONLY":
        failures.append("ABSTRACT_RUNTIME_TOKEN_SCOPE_MUST_BE_LAST_TOKEN_DECODE_ONLY")
    if evidence.get("challenge_sha256") != design_verdict.get("challenge_sha256"):
        failures.append("ABSTRACT_RUNTIME_CHALLENGE_SHA256_MISMATCH")
    if evidence.get("fresh_holdout_opened_under_admitted_coordination") is not True:
        failures.append("FRESH_HOLDOUT_REQUIRES_ADMITTED_COORDINATION")
    if evidence.get("holdout_target_blind_prompt_bytes_attested") is not True:
        failures.append("EXECUTED_HOLDOUT_TARGET_BLIND_BYTES_REQUIRED")
    if evidence.get("calibration_holdout_lexical_disjointness_attested") is not True:
        failures.append("EXECUTED_CROSS_SPLIT_LEXICAL_DISJOINTNESS_REQUIRED")
    if evidence.get("six_calibration_families_executed") is not True:
        failures.append("SIX_CALIBRATION_FAMILIES_MUST_EXECUTE")
    if evidence.get("six_fresh_holdout_families_executed") is not True:
        failures.append("SIX_FRESH_HOLDOUT_FAMILIES_MUST_EXECUTE")
    if evidence.get("semantic_target_x_output_code_counterbalanced") is not True:
        failures.append("EXECUTED_TARGET_X_CODE_COUNTERBALANCE_REQUIRED")
    if evidence.get("target_selective_causal_matrix_pass") is not True:
        failures.append("ABSTRACT_TARGET_SELECTIVE_CAUSAL_MATRIX_REQUIRED")
    if evidence.get("sign_null_orthogonal_permuted_controls_pass") is not True:
        failures.append("ABSTRACT_MATCHED_VECTOR_CONTROLS_REQUIRED")
    if evidence.get("generic_compliance_axis_fails_to_reproduce_target_matrix") is not True:
        failures.append("GENERIC_COMPLIANCE_COUNTERHYPOTHESIS_MUST_FAIL")
    if evidence.get("downstream_nonterminal_transport_pass") is not True:
        failures.append("ABSTRACT_DOWNSTREAM_NONTERMINAL_TRANSPORT_REQUIRED")
    if evidence.get("dual_behavioral_readout_pass") is not True:
        failures.append("ABSTRACT_DUAL_BEHAVIORAL_READOUT_REQUIRED")
    if evidence.get("representation_transport_behavioral_rank_agree") is not True:
        failures.append("ABSTRACT_REPRESENTATION_TRANSPORT_BEHAVIORAL_RANK_MUST_AGREE")

    for key in (
        "runtime_receipt_sha256",
        "target_selective_matrix_receipt_sha256",
        "generic_compliance_control_receipt_sha256",
        "downstream_transport_receipt_sha256",
        "dual_readout_receipt_sha256",
    ):
        if not _sha256(evidence.get(key)):
            failures.append(f"ABSTRACT_RUNTIME_{key.upper()}_REQUIRED")
    return not failures, sorted(set(failures)), evidence


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v9.adjudicate(candidate)
    design_ok, design_failures, design = _abstract_design(candidate)
    scope_ok, scope_failures, scope = _localized_scope(candidate)
    runtime_ok, runtime_failures, runtime = _abstract_runtime(candidate, design)

    base_scientific = base.get("scientifically_independent_vector_candidate") is True
    base_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    base_modular = base.get("modular_hcu_jspace_control_candidate") is True
    scientific = bool(base_scientific and design_ok and scope_ok and runtime_ok)
    owner = bool(base_owner and design_ok and scope_ok and runtime_ok)
    modular = bool(base_modular and design_ok and scope_ok and runtime_ok)
    abstract_semantic = bool(scientific and owner and modular)

    failures = sorted(
        set(list(base.get("v9_failures", [])) + design_failures + scope_failures + runtime_failures)
    )
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "abstract_state_challenge_design_pass": design_ok,
        "localized_native_token_scope_pass": scope_ok,
        "abstract_state_runtime_pass": runtime_ok,
        "abstract_state_challenge_sha256": design.get("challenge_sha256"),
        "native_scope_analysis_sha256": scope.get("analysis_sha256"),
        "abstract_state_runtime_receipt_sha256": runtime.get("runtime_receipt_sha256"),
        "broadcast_causal_equivalence_required_for_localized_promotion": False,
        "broadcast_full_causal_identity_claimed": False,
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "modular_hcu_jspace_control_candidate": modular,
        "abstract_semantic_jspace_control_candidate": abstract_semantic,
        "v10_failures": failures,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v10 requires the same v9 evidence universe plus a source-validated six-family instruction-free "
            "calibration challenge, lexically disjoint byte-identical target-blind holdout prompts, a directly "
            "observed native LAST_TOKEN_ONLY cvec decode after unsteered prefix prefill, and fresh runtime evidence "
            "that rejects generic-compliance and nuisance-vector explanations while preserving downstream/behavioral "
            "rank consistency. BROADCAST is not silently promoted as causally identical. A positive result is a "
            "research claim candidate only; this gate mints no canonical semantics or product/model/training credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_semantic_jspace_control_candidate": False,
            "canonical_credit_minted": False,
            "v10_failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "abstract_semantic_jspace_control_candidate": False,
            "canonical_credit_minted": False,
            "v10_failures": ["CANDIDATE_OBJECT_REQUIRED"],
        }
    result = adjudicate(candidate)
    result["candidate_path"] = str(path)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    positives = [row for row in verdicts if row.get("abstract_semantic_jspace_control_candidate") is True]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "abstract_semantic_positive_candidate_files": len(positives),
        "abstract_semantic_jspace_control_candidate": bool(positives),
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
