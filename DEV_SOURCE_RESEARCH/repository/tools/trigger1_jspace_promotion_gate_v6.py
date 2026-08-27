#!/usr/bin/env python3
"""Second-order fail-closed gate for Trigger-1 semantic J-Space control.

V6 composes the existing v5 specificity gate. It adds the three evidence classes that
remain necessary before a strong "full vector control" research claim is even a candidate:

1. matched/blocked semantic-basis construction and an adequately powered simplex-rank decision;
2. independently measured downstream nonterminal semantic transport plus context-valid dual
   behavioral readout and a class-selective causal matrix; and
3. for the strongest native-carrier claim, independent Q8_0 target-carrier geometry evidence
   rather than treating a transferred full-precision actuator as proof of native geometry.

The gate is adjudication only. It never runs a model, opens holdout data, mints canonical
semantics, or grants EntityOS/HCU/J-Space/training/whole-product credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import trigger1_jspace_promotion_gate_v5 as v5

VERDICT_SCHEMA = "CLAY_TRIGGER1_JSPACE_PROMOTION_GATE/v6"
BATCH_SCHEMA = "CLAY_TRIGGER1_JSPACE_BATCH_PROMOTION_SCAN/v6"
NATIVE_CVEC_CLASS = "LOCAL_LLAMA_CPP_CVEC_APPLIED"
RANK_DECISIONS = {"ONE_DIMENSIONAL_SUPPORTED": 1, "TWO_DIMENSIONAL_REQUIRED": 2}
TERMINAL_ENDPOINT_MARKERS = ("lm_head", "output_head", "final_norm", "model.model.norm:output")


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _blocked_basis_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    basis = candidate.get("semantic_basis_design")
    if not isinstance(basis, dict):
        return False, ["SEMANTIC_BASIS_DESIGN_REQUIRED"]
    requirements = (
        ("matched_scenario_triplets", "MATCHED_SCENARIO_TRIPLETS_REQUIRED"),
        ("within_family_centered", "WITHIN_FAMILY_CENTERING_REQUIRED"),
        ("equal_family_weighting", "EQUAL_FAMILY_WEIGHTING_REQUIRED"),
        ("restricted_within_family_permutation", "WITHIN_FAMILY_PERMUTATION_NULL_REQUIRED"),
        ("basis_calibration_holdout_disjoint", "BASIS_CALIBRATION_HOLDOUT_DISJOINT_REQUIRED"),
    )
    for key, failure in requirements:
        if basis.get(key) is not True:
            failures.append(failure)
    if not _sha256(basis.get("blocked_basis_receipt_sha256")):
        failures.append("BLOCKED_BASIS_RECEIPT_REQUIRED")
    family_count = basis.get("matched_family_count")
    if not _positive_int(family_count) or int(family_count) < 3:
        failures.append("AT_LEAST_THREE_MATCHED_SCENARIO_FAMILIES_REQUIRED")
    return not failures, failures


def _rank_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], int | None]:
    failures: list[str] = []
    rank = candidate.get("semantic_simplex_rank")
    if not isinstance(rank, dict):
        return False, ["SEMANTIC_SIMPLEX_RANK_EVIDENCE_REQUIRED"], None
    decision = rank.get("decision")
    expected_rank = RANK_DECISIONS.get(decision)
    if expected_rank is None:
        failures.append("SEMANTIC_SIMPLEX_RANK_MUST_BE_RESOLVED_1D_OR_2D")
    if rank.get("design_adequately_powered") is not True:
        failures.append("SEMANTIC_SIMPLEX_RANK_DESIGN_MUST_BE_ADEQUATELY_POWERED")
    if not _sha256(rank.get("analysis_receipt_sha256")):
        failures.append("SEMANTIC_SIMPLEX_RANK_RECEIPT_REQUIRED")
    observed_rank = rank.get("representation_rank")
    if expected_rank is not None and observed_rank != expected_rank:
        failures.append("SEMANTIC_SIMPLEX_RANK_DECISION_MISMATCH")
    return not failures, failures, expected_rank


def _downstream_transport_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], int | None]:
    failures: list[str] = []
    transport = candidate.get("downstream_semantic_transport")
    if not isinstance(transport, dict):
        return False, ["DOWNSTREAM_SEMANTIC_TRANSPORT_REQUIRED"], None
    endpoint = transport.get("endpoint")
    if not _nonempty(endpoint):
        failures.append("DOWNSTREAM_NONTERMINAL_ENDPOINT_REQUIRED")
    else:
        normalized = str(endpoint).strip().lower().replace(" ", "")
        if any(marker in normalized for marker in TERMINAL_ENDPOINT_MARKERS):
            failures.append("DOWNSTREAM_ENDPOINT_MUST_BE_NONTERMINAL")
    for key, failure in (
        ("independent_of_intervention_vector", "DOWNSTREAM_ENDPOINT_MUST_BE_INDEPENDENT_OF_INTERVENTION_VECTOR"),
        ("independent_of_output_token_identities", "DOWNSTREAM_ENDPOINT_MUST_BE_INDEPENDENT_OF_OUTPUT_TOKENS"),
        ("target_specific_sign_sensitive_displacement", "TARGET_SPECIFIC_DOWNSTREAM_DISPLACEMENT_REQUIRED"),
        ("controls_fail_to_reproduce", "DOWNSTREAM_NUISANCE_CONTROLS_MUST_FAIL_TO_REPRODUCE"),
    ):
        if transport.get(key) is not True:
            failures.append(failure)
    if not _sha256(transport.get("transport_receipt_sha256")):
        failures.append("DOWNSTREAM_TRANSPORT_RECEIPT_REQUIRED")
    rank = transport.get("transport_rank")
    if rank not in (1, 2):
        failures.append("DOWNSTREAM_TRANSPORT_RANK_REQUIRED")
        rank = None
    return not failures, failures, rank


def _dual_readout_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    readout = candidate.get("context_valid_dual_readout")
    if not isinstance(readout, dict):
        return False, ["CONTEXT_VALID_DUAL_READOUT_REQUIRED"]
    if readout.get("exact_prompt_boundary_tokenization_attested") is not True:
        failures.append("EXACT_PROMPT_BOUNDARY_TOKENIZATION_ATTESTATION_REQUIRED")
    if not _sha256(readout.get("tokenizer_boundary_receipt_sha256")):
        failures.append("TOKENIZER_BOUNDARY_RECEIPT_REQUIRED")
    count = readout.get("context_valid_codebook_family_count")
    if not _positive_int(count) or int(count) < 2:
        failures.append("AT_LEAST_TWO_CONTEXT_VALID_CODEBOOK_FAMILIES_REQUIRED")
    if readout.get("semantic_target_x_code_identity_counterbalanced") is not True:
        failures.append("SEMANTIC_TARGET_X_CODE_IDENTITY_COUNTERBALANCE_REQUIRED")
    if not _sha256(readout.get("likelihood_margin_receipt_sha256")):
        failures.append("CONTEXT_VALID_LIKELIHOOD_MARGIN_RECEIPT_REQUIRED")
    if not _sha256(readout.get("emitted_decision_receipt_sha256")):
        failures.append("EMITTED_DECISION_RECEIPT_REQUIRED")
    if readout.get("dual_readout_agrees") is not True:
        failures.append("LIKELIHOOD_AND_EMITTED_DECISION_MUST_AGREE")
    return not failures, failures


def _causal_matrix_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], int | None]:
    failures: list[str] = []
    matrix = candidate.get("class_selective_causal_matrix")
    if not isinstance(matrix, dict):
        return False, ["CLASS_SELECTIVE_CAUSAL_MATRIX_REQUIRED"], None
    for key, failure in (
        ("diagonal_advantage", "CLASS_SELECTIVE_DIAGONAL_ADVANTAGE_REQUIRED"),
        ("sign_flip_reverses_selectivity", "SIGN_FLIP_MUST_REVERSE_CLASS_SELECTIVITY"),
        ("null_vector_baseline_like", "NULL_VECTOR_MUST_REMAIN_BASELINE_LIKE"),
        ("nuisance_controls_fail_to_reproduce", "CAUSAL_MATRIX_NUISANCE_CONTROLS_MUST_FAIL_TO_REPRODUCE"),
        ("equal_family_weighting", "CAUSAL_MATRIX_EQUAL_FAMILY_WEIGHTING_REQUIRED"),
    ):
        if matrix.get(key) is not True:
            failures.append(failure)
    if not _sha256(matrix.get("matrix_receipt_sha256")):
        failures.append("CAUSAL_MATRIX_RECEIPT_REQUIRED")
    rank = matrix.get("behavioral_rank")
    if rank not in (1, 2):
        failures.append("BEHAVIORAL_CAUSAL_RANK_REQUIRED")
        rank = None
    return not failures, failures, rank


def _carrier_geometry_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    carrier = candidate.get("native_carrier_geometry")
    if not isinstance(carrier, dict):
        return False, ["NATIVE_CARRIER_GEOMETRY_EVIDENCE_REQUIRED"]
    for key, failure in (
        ("target_runtime_basis_reconstructed_independently", "TARGET_RUNTIME_BASIS_MUST_BE_RECONSTRUCTED_INDEPENDENTLY"),
        ("imported_source_basis_excluded_from_parity_decision", "IMPORTED_SOURCE_BASIS_CANNOT_DEFINE_NATIVE_PARITY"),
        ("carrier_local_norm_calibration", "CARRIER_LOCAL_NORM_CALIBRATION_REQUIRED"),
        ("principal_angle_or_equivalent_subspace_test", "NATIVE_CARRIER_SUBSPACE_ALIGNMENT_TEST_REQUIRED"),
        ("leave_one_family_out_stability", "NATIVE_CARRIER_LOFO_STABILITY_REQUIRED"),
        ("permutation_null_passed", "NATIVE_CARRIER_PERMUTATION_NULL_REQUIRED"),
        ("within_carrier_causal_matrix_passed", "NATIVE_CARRIER_WITHIN_RUNTIME_CAUSAL_MATRIX_REQUIRED"),
    ):
        if carrier.get(key) is not True:
            failures.append(failure)
    if not _sha256(carrier.get("geometry_receipt_sha256")):
        failures.append("NATIVE_CARRIER_GEOMETRY_RECEIPT_REQUIRED")
    return not failures, failures


def _second_order_evidence(candidate: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    basis_ok, basis_failures = _blocked_basis_evidence(candidate)
    rank_ok, rank_failures, representation_rank = _rank_evidence(candidate)
    transport_ok, transport_failures, transport_rank = _downstream_transport_evidence(candidate)
    readout_ok, readout_failures = _dual_readout_evidence(candidate)
    matrix_ok, matrix_failures, behavioral_rank = _causal_matrix_evidence(candidate)

    failures = basis_failures + rank_failures + transport_failures + readout_failures + matrix_failures
    rank_compatible = (
        representation_rank is not None
        and transport_rank is not None
        and behavioral_rank is not None
        and representation_rank == transport_rank == behavioral_rank
    )
    if not rank_compatible:
        failures.append("REPRESENTATION_TRANSPORT_BEHAVIORAL_RANKS_MUST_AGREE")
    details = {
        "representation_rank": representation_rank,
        "downstream_transport_rank": transport_rank,
        "behavioral_causal_rank": behavioral_rank,
        "rank_compatible": rank_compatible,
    }
    return bool(basis_ok and rank_ok and transport_ok and readout_ok and matrix_ok and rank_compatible), sorted(set(failures)), details


def adjudicate(candidate: dict[str, Any]) -> dict[str, Any]:
    base = v5.adjudicate(candidate)
    second_ok, second_failures, rank_details = _second_order_evidence(candidate)
    carrier_ok, carrier_failures = _carrier_geometry_evidence(candidate)

    mechanism = base.get("mechanism_runtime_vector_credit_candidate") is True
    v5_scientific = base.get("scientifically_independent_vector_candidate") is True
    v5_owner = base.get("owner_trigger1_goal_credit_candidate") is True
    scientific = bool(mechanism and v5_scientific and second_ok)
    owner = bool(v5_owner and second_ok)
    native_runtime = candidate.get("runtime_intervention_class") == NATIVE_CVEC_CLASS
    full_native = bool(owner and native_runtime and carrier_ok)

    base_owner_failures = base.get("owner_target_failures")
    if not isinstance(base_owner_failures, list):
        base_owner_failures = []
    return {
        **base,
        "schema": VERDICT_SCHEMA,
        "v5_scientific_specificity_candidate": bool(v5_scientific),
        "v6_second_order_controls_pass": bool(second_ok),
        "v6_native_carrier_geometry_pass": bool(carrier_ok),
        "scientifically_independent_vector_candidate": scientific,
        "owner_trigger1_goal_credit_candidate": owner,
        "owner_trigger1_direct_free_api_model_credit_candidate": owner,
        "full_native_jspace_vector_control_candidate": full_native,
        "rank_consistency": rank_details,
        "v6_second_order_failures": second_failures,
        "v6_native_carrier_failures": carrier_failures,
        "owner_target_failures": sorted(set(base_owner_failures + second_failures)),
        "canonical_credit_minted": False,
        "whole_entityos_hcu_credit": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "v6 composes v5 and requires matched blocked semantic basis construction, a resolved adequately-powered "
            "1D/2D simplex decision, independent downstream nonterminal semantic transport, context-valid likelihood "
            "plus emitted-decision agreement, and a class-selective causal matrix with compatible rank. The strongest "
            "full_native_jspace_vector_control_candidate additionally requires independently reconstructed target-carrier "
            "geometry; successful transfer of an imported source vector is insufficient. All fields remain research "
            "candidates only and mint no canonical semantics, J-Space model-runtime, training, HCU, EntityOS or whole-product credit."
        ),
    }


def adjudicate_file(path: Path) -> dict[str, Any]:
    try:
        candidate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": [f"CANDIDATE_FILE_INVALID:{type(exc).__name__}"],
            "v6_second_order_failures": [],
            "v6_native_carrier_failures": [],
        }
    if not isinstance(candidate, dict):
        return {
            "schema": VERDICT_SCHEMA,
            "mechanism_runtime_vector_credit_candidate": False,
            "scientifically_independent_vector_candidate": False,
            "owner_trigger1_goal_credit_candidate": False,
            "owner_trigger1_direct_free_api_model_credit_candidate": False,
            "full_native_jspace_vector_control_candidate": False,
            "canonical_credit_minted": False,
            "whole_entityos_hcu_credit": False,
            "jspace_model_runtime_credit": False,
            "training_credit": False,
            "failures": ["CANDIDATE_OBJECT_REQUIRED"],
            "v6_second_order_failures": [],
            "v6_native_carrier_failures": [],
        }
    verdict = adjudicate(candidate)
    verdict["candidate_path"] = str(path)
    verdict["candidate_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return verdict


def scan_batch(batch_dir: Path) -> dict[str, Any]:
    paths = sorted(batch_dir.glob("**/trigger1_direct_steering_candidate.json"))
    verdicts = [adjudicate_file(path) for path in paths]
    return {
        "schema": BATCH_SCHEMA,
        "candidate_files_seen": len(paths),
        "mechanism_runtime_vector_credit_candidate": any(v.get("mechanism_runtime_vector_credit_candidate") is True for v in verdicts),
        "scientifically_independent_vector_candidate": any(v.get("scientifically_independent_vector_candidate") is True for v in verdicts),
        "owner_trigger1_goal_credit_candidate": any(v.get("owner_trigger1_goal_credit_candidate") is True for v in verdicts),
        "full_native_jspace_vector_control_candidate": any(v.get("full_native_jspace_vector_control_candidate") is True for v in verdicts),
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
