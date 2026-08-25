#!/usr/bin/env python3
"""Fail-closed abstract-state deconfound and intervention-scope gate for Trigger-1.

This companion closes two scientific gaps that token-scope classification alone cannot:

1. A vector that separates semantic classes can still be explained by model-facing
   AFFIRMATIVE/NEGATIVE lexemes, close semantic synonyms, output-code identity, or generic
   instruction/compliance. Positive evidence therefore requires a calibration-only nuisance
   subspace, explicit residualization, frozen lexical-disjointness audits, and holdout
   nuisance controls that fail to reproduce target-selective effects.

2. The historical PyTorch witness modifies only the final prompt token, while native
   llama.cpp cvec acts across the native prompt-token scope. They are not treated as the
   same intervention. A native abstract-state candidate must stand on direct native
   ALL_PROMPT_TOKENS evidence. A separate optional bridge can establish bounded *causal
   effect equivalence* between scopes; it never establishes microscopic mechanistic identity.

This module is adjudication only. It runs no model, opens no holdout, and mints no
canonical semantics, J-Space runtime, HCU, EntityOS, training, BASE, or effect credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_DECONFOUND_SCOPE_GATE/v1"
REQUIRED_NUISANCE_AXES = {
    "CANONICAL_LABEL_LEXEME",
    "SEMANTIC_SYNONYM_LEXICON",
    "GENERIC_INSTRUCTION_COMPLIANCE",
    "OUTPUT_CODE_IDENTITY",
}
NATIVE_SCOPE = "ALL_PROMPT_TOKENS"
LEGACY_SCOPE = "LAST_TOKEN_ONLY"
MAX_POST_PROJECTION_ABS_NUISANCE_COSINE = 1e-3
MIN_RETAINED_SEMANTIC_NORM_FRACTION = 0.20
MAX_EQUIVALENCE_ROPE = 0.25
MAX_EQUIVALENCE_ALPHA = 0.05


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value == value and abs(float(value)) != float("inf")


def _deconfound(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    d = candidate.get("abstract_state_deconfound")
    if not isinstance(d, dict):
        return False, ["ABSTRACT_STATE_DECONFOUND_REQUIRED"]

    for key, failure in (
        ("basis_model_facing_canonical_labels_absent", "BASIS_CANONICAL_LABELS_MUST_BE_MODEL_FACING_ABSENT"),
        ("holdout_model_facing_canonical_labels_absent", "HOLDOUT_CANONICAL_LABELS_MUST_BE_MODEL_FACING_ABSENT"),
        ("basis_holdout_lexically_disjoint", "BASIS_HOLDOUT_LEXICAL_DISJOINTNESS_REQUIRED"),
        ("basis_holdout_scenario_disjoint", "BASIS_HOLDOUT_SCENARIO_DISJOINTNESS_REQUIRED"),
        ("semantic_synonym_lexicon_disjoint", "SEMANTIC_SYNONYM_LEXICON_DISJOINTNESS_REQUIRED"),
        ("semantic_target_evaluator_metadata_only", "SEMANTIC_TARGET_MUST_BE_EVALUATOR_METADATA_ONLY"),
        ("full_three_by_three_target_x_output_code", "FULL_THREE_BY_THREE_TARGET_X_OUTPUT_CODE_REQUIRED"),
        ("per_scenario_target_and_code_rotation", "PER_SCENARIO_TARGET_AND_CODE_ROTATION_REQUIRED"),
        ("nuisance_subspace_fit_on_calibration_only", "NUISANCE_SUBSPACE_MUST_BE_FIT_ON_CALIBRATION_ONLY"),
        ("semantic_basis_residualized_against_nuisance_subspace", "SEMANTIC_BASIS_NUISANCE_RESIDUALIZATION_REQUIRED"),
        ("residualization_frozen_before_holdout", "RESIDUALIZATION_MUST_BE_FROZEN_BEFORE_HOLDOUT"),
        ("holdout_nuisance_controls_fail_to_reproduce", "HOLDOUT_NUISANCE_CONTROLS_MUST_FAIL_TO_REPRODUCE"),
        ("holdout_target_selective_causal_matrix_pass", "HOLDOUT_TARGET_SELECTIVE_CAUSAL_MATRIX_REQUIRED"),
    ):
        if d.get(key) is not True:
            failures.append(failure)

    axes = d.get("nuisance_axes")
    if not isinstance(axes, list) or set(axes) != REQUIRED_NUISANCE_AXES:
        failures.append("EXACT_REQUIRED_NUISANCE_AXIS_SET_REQUIRED")

    for field, failure in (
        ("lexical_audit_receipt_sha256", "LEXICAL_AUDIT_RECEIPT_REQUIRED"),
        ("nuisance_subspace_receipt_sha256", "NUISANCE_SUBSPACE_RECEIPT_REQUIRED"),
        ("projected_basis_receipt_sha256", "PROJECTED_BASIS_RECEIPT_REQUIRED"),
        ("holdout_nuisance_control_receipt_sha256", "HOLDOUT_NUISANCE_CONTROL_RECEIPT_REQUIRED"),
        ("holdout_causal_matrix_receipt_sha256", "HOLDOUT_CAUSAL_MATRIX_RECEIPT_REQUIRED"),
    ):
        if not _sha256(d.get(field)):
            failures.append(failure)

    cosine = d.get("post_projection_max_abs_nuisance_cosine")
    if not _finite(cosine) or float(cosine) < 0 or float(cosine) > MAX_POST_PROJECTION_ABS_NUISANCE_COSINE:
        failures.append("POST_PROJECTION_NUISANCE_ORTHOGONALITY_REQUIRED")

    retained = d.get("retained_semantic_subspace_norm_fraction")
    if not _finite(retained) or not (MIN_RETAINED_SEMANTIC_NORM_FRACTION <= float(retained) <= 1.0):
        failures.append("SEMANTIC_RESIDUAL_MUST_RETAIN_NONTRIVIAL_NORM")

    if d.get("lexical_audit_frozen_before_holdout") is not True:
        failures.append("LEXICAL_AUDIT_MUST_BE_FROZEN_BEFORE_HOLDOUT")

    return not failures, sorted(set(failures))


def _native_direct(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    n = candidate.get("direct_native_scope_evidence")
    if not isinstance(n, dict):
        return False, ["DIRECT_NATIVE_SCOPE_EVIDENCE_REQUIRED"]

    if n.get("runtime_intervention_class") != "LOCAL_LLAMA_CPP_CVEC_APPLIED":
        failures.append("DIRECT_NATIVE_LLAMA_CPP_CVEC_CLASS_REQUIRED")
    if n.get("token_scope") != NATIVE_SCOPE:
        failures.append("DIRECT_NATIVE_ALL_PROMPT_TOKENS_SCOPE_REQUIRED")
    if n.get("legacy_last_token_witness_used_as_causal_identity_premise") is not False:
        failures.append("LEGACY_LAST_TOKEN_WITNESS_CANNOT_BE_NATIVE_CAUSAL_IDENTITY_PREMISE")

    for key, failure in (
        ("same_projected_basis_as_preregistered", "NATIVE_PROJECTED_BASIS_BINDING_REQUIRED"),
        ("calibration_only_operating_point", "NATIVE_OPERATING_POINT_MUST_BE_CALIBRATION_ONLY"),
        ("operating_point_frozen_before_holdout", "NATIVE_OPERATING_POINT_MUST_BE_FROZEN_BEFORE_HOLDOUT"),
        ("fresh_label_free_counterbalanced_holdout", "NATIVE_FRESH_LABEL_FREE_COUNTERBALANCED_HOLDOUT_REQUIRED"),
        ("matched_sign_null_orthogonal_permuted_nuisance_controls", "NATIVE_MATCHED_CONTROL_FAMILY_REQUIRED"),
        ("nonterminal_transport_observed", "NATIVE_NONTERMINAL_TRANSPORT_REQUIRED"),
        ("context_valid_dual_readout_agrees", "NATIVE_CONTEXT_VALID_DUAL_READOUT_REQUIRED"),
        ("class_selective_causal_matrix_pass", "NATIVE_CLASS_SELECTIVE_CAUSAL_MATRIX_REQUIRED"),
    ):
        if n.get(key) is not True:
            failures.append(failure)

    for field, failure in (
        ("runtime_receipt_sha256", "DIRECT_NATIVE_RUNTIME_RECEIPT_REQUIRED"),
        ("nonterminal_transport_receipt_sha256", "DIRECT_NATIVE_TRANSPORT_RECEIPT_REQUIRED"),
        ("dual_readout_receipt_sha256", "DIRECT_NATIVE_DUAL_READOUT_RECEIPT_REQUIRED"),
        ("causal_matrix_receipt_sha256", "DIRECT_NATIVE_CAUSAL_MATRIX_RECEIPT_REQUIRED"),
    ):
        if not _sha256(n.get(field)):
            failures.append(failure)

    return not failures, sorted(set(failures))


def _scope_bridge(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    """Optional bridge: causal effect equivalence only, never microscopic identity."""
    b = candidate.get("cross_scope_effect_bridge")
    if b is None:
        return False, ["CROSS_SCOPE_EFFECT_BRIDGE_NOT_PROVIDED"]
    if not isinstance(b, dict):
        return False, ["CROSS_SCOPE_EFFECT_BRIDGE_INVALID"]

    failures: list[str] = []
    if b.get("legacy_scope") != LEGACY_SCOPE:
        failures.append("BRIDGE_LEGACY_SCOPE_MUST_BE_LAST_TOKEN_ONLY")
    if b.get("native_scope") != NATIVE_SCOPE:
        failures.append("BRIDGE_NATIVE_SCOPE_MUST_BE_ALL_PROMPT_TOKENS")
    if b.get("comparison_claim") != "CAUSAL_EFFECT_EQUIVALENCE_NOT_MECHANISTIC_IDENTITY":
        failures.append("BRIDGE_CLAIM_MUST_BE_EFFECT_EQUIVALENCE_ONLY")

    for key, failure in (
        ("same_case_universe", "BRIDGE_SAME_CASE_UNIVERSE_REQUIRED"),
        ("same_layer", "BRIDGE_SAME_LAYER_REQUIRED"),
        ("same_projected_vector_identity", "BRIDGE_SAME_PROJECTED_VECTOR_REQUIRED"),
        ("same_control_family", "BRIDGE_SAME_CONTROL_FAMILY_REQUIRED"),
        ("equivalence_protocol_frozen_before_observation", "BRIDGE_PROTOCOL_MUST_BE_FROZEN_BEFORE_OBSERVATION"),
        ("paired_tost_pass", "BRIDGE_PAIRED_TOST_REQUIRED"),
        ("control_normalized_effect_sign_structure_agrees", "BRIDGE_CONTROL_NORMALIZED_SIGN_STRUCTURE_REQUIRED"),
    ):
        if b.get(key) is not True:
            failures.append(failure)

    if b.get("equivalence_test_kind") != "PAIRED_TOST_ON_CONTROL_NORMALIZED_EFFECT":
        failures.append("BRIDGE_PAIRED_TOST_METRIC_REQUIRED")

    alpha = b.get("alpha")
    if not _finite(alpha) or not (0 < float(alpha) <= MAX_EQUIVALENCE_ALPHA):
        failures.append("BRIDGE_ALPHA_TOO_WEAK_OR_INVALID")
    rope = b.get("equivalence_rope_abs_standardized_effect")
    if not _finite(rope) or not (0 < float(rope) <= MAX_EQUIVALENCE_ROPE):
        failures.append("BRIDGE_EQUIVALENCE_ROPE_TOO_WEAK_OR_INVALID")

    for field, failure in (
        ("equivalence_protocol_sha256", "BRIDGE_EQUIVALENCE_PROTOCOL_RECEIPT_REQUIRED"),
        ("paired_effect_receipt_sha256", "BRIDGE_PAIRED_EFFECT_RECEIPT_REQUIRED"),
    ):
        if not _sha256(b.get(field)):
            failures.append(failure)

    if b.get("strict_micro_mechanistic_identity_claimed") is True:
        failures.append("MICRO_MECHANISTIC_IDENTITY_CLAIM_FORBIDDEN_FROM_SCOPE_BRIDGE")

    return not failures, sorted(set(failures))


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    d_ok, d_fail = _deconfound(candidate)
    n_ok, n_fail = _native_direct(candidate)
    b_ok, b_fail = _scope_bridge(candidate)

    abstract_native = bool(d_ok and n_ok)
    return {
        "schema": SCHEMA,
        "abstract_state_deconfound_pass": d_ok,
        "direct_native_scope_evidence_pass": n_ok,
        "cross_scope_causal_effect_equivalence_candidate": bool(d_ok and n_ok and b_ok),
        "abstract_native_semantic_jspace_candidate": abstract_native,
        "strict_micro_mechanistic_identity_candidate": False,
        "deconfound_failures": d_fail,
        "direct_native_scope_failures": n_fail,
        "scope_bridge_failures": b_fail,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "A positive abstract_native_semantic_jspace_candidate requires direct native "
            "ALL_PROMPT_TOKENS causal evidence after calibration-only residualization against "
            "canonical-label, semantic-synonym, generic-compliance, and output-code nuisance "
            "axes, with lexically/scenario-disjoint counterbalanced holdout and nuisance controls. "
            "The historical LAST_TOKEN_ONLY witness is not a premise for native causality. "
            "The optional bridge can establish bounded causal-effect equivalence via preregistered "
            "paired TOST, never microscopic mechanistic identity. This adjudicator mints no credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": SCHEMA,
            "abstract_state_deconfound_pass": False,
            "direct_native_scope_evidence_pass": False,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "abstract_native_semantic_jspace_candidate": False,
            "strict_micro_mechanistic_identity_candidate": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "canonical_credit_minted": False,
        }
    if not isinstance(obj, dict):
        return {
            "schema": SCHEMA,
            "abstract_state_deconfound_pass": False,
            "direct_native_scope_evidence_pass": False,
            "cross_scope_causal_effect_equivalence_candidate": False,
            "abstract_native_semantic_jspace_candidate": False,
            "strict_micro_mechanistic_identity_candidate": False,
            "failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "canonical_credit_minted": False,
        }
    result = adjudicate(obj)
    result["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()
    print(json.dumps(adjudicate_file(Path(args.candidate)), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
