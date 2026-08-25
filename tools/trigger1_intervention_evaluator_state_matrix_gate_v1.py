#!/usr/bin/env python3
"""Fail-closed intervention x evaluator-state specificity gate for Run 2.

This execution-free wrapper closes R2_B12: matched-only causal rows cannot
establish that S0/S1/S2 interventions selectively control distinct evaluator
states rather than acting as a generic confidence/separability direction.

The gate composes after the rank-complete cross-task v4 gate and requires a
complete intervention_state x evaluator_state x output_code x polarity x
family x replicate matrix. Model-facing case/prompt identity must be held fixed
while intervention_state changes. Diagonal effects must be positive and exceed
both NULL and every off-diagonal intervention by a preregistered margin.

This is a static evidence-policy gate. It cannot authenticate runtime evidence
and cannot mint canonical/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import collections
import math
import re
from typing import Any

from tools import trigger1_cross_task_abstract_control_gate_v4 as v4
from tools import trigger1_cross_task_abstract_control_gate_v2 as v2

SCHEMA = "CLAY_TRIGGER1_INTERVENTION_EVALUATOR_STATE_MATRIX_GATE/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_INTERVENTION_EVALUATOR_STATE_MATRIX_EVIDENCE/v1"
STATES = v2.STATES
CODES = v2.CODES
POLARITIES = v2.POLARITIES
MIN_REPLICATES = v2.MIN_CELL_REPLICATES
MIN_DIAGONAL_EFFECT = v2.MIN_EFFECT
MIN_SPECIFICITY_GAP = v2.MIN_EFFECT
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(float(x))


def _sha256(x: Any) -> bool:
    return isinstance(x, str) and bool(_SHA256_RE.fullmatch(x))


def _vector_registry(candidate: dict[str, Any], failures: list[str]) -> dict[str, str]:
    rows = candidate.get("intervention_vectors")
    if not isinstance(rows, list):
        failures.append("INTERVENTION_VECTOR_REGISTRY_REQUIRED")
        return {}
    out: dict[str, str] = {}
    for i, row in enumerate(rows):
        p = f"VECTOR_{i}"
        if not isinstance(row, dict):
            failures.append(p + "_OBJECT_REQUIRED")
            continue
        state = row.get("intervention_state_id")
        sha = row.get("vector_sha256")
        if state not in STATES:
            failures.append(p + "_STATE_INVALID")
            continue
        if not _sha256(sha):
            failures.append(p + "_SHA256_INVALID")
            continue
        if state in out:
            failures.append(p + "_DUPLICATE_STATE")
            continue
        out[state] = sha
    if set(out) != set(STATES):
        failures.append("INTERVENTION_VECTOR_REGISTRY_INCOMPLETE")
    if len(set(out.values())) != len(out):
        failures.append("DISTINCT_STATE_VECTOR_HASHES_REQUIRED")
    return out


def _matrix(candidate: dict[str, Any], failures: list[str], vectors: dict[str, str]) -> dict[str, Any]:
    rows = candidate.get("intervention_evaluator_rows")
    if not isinstance(rows, list) or not rows:
        failures.append("INTERVENTION_EVALUATOR_ROWS_REQUIRED")
        return {}

    groups: dict[tuple[str, str, str, str, str, str], dict[str, Any]] = {}
    family_grammars: dict[str, str] = {}
    prompt_identity: dict[tuple[str, str, str, str, str], tuple[str, str]] = {}
    replicate_ids: dict[tuple[str, str, str, str, str], set[str]] = collections.defaultdict(set)

    for i, row in enumerate(rows):
        p = f"MATRIX_{i}"
        if not isinstance(row, dict):
            failures.append(p + "_OBJECT_REQUIRED")
            continue
        fam = row.get("family_id")
        grammar = row.get("task_grammar_id")
        intervention = row.get("intervention_state_id")
        evaluator = row.get("evaluator_state_id")
        code = row.get("requested_code")
        polarity = row.get("probe_polarity")
        rep = row.get("replicate_id")
        case_id = row.get("case_id")
        prompt_sha = row.get("prompt_sha256")
        vector_sha = row.get("vector_sha256")
        intervention_margin = row.get("intervention_margin")
        null_margin = row.get("null_margin")

        if not all(isinstance(x, str) and x for x in (fam, grammar, rep, case_id)):
            failures.append(p + "_IDENTITY_INVALID")
            continue
        if intervention not in STATES or evaluator not in STATES:
            failures.append(p + "_STATE_INVALID")
            continue
        if code not in CODES or polarity not in POLARITIES:
            failures.append(p + "_CODE_OR_POLARITY_INVALID")
            continue
        if not _sha256(prompt_sha) or not _sha256(vector_sha):
            failures.append(p + "_HASH_INVALID")
            continue
        if vectors.get(intervention) != vector_sha:
            failures.append(p + "_VECTOR_REGISTRY_MISMATCH")
        if not _num(intervention_margin) or not _num(null_margin):
            failures.append(p + "_MARGIN_INVALID")
            continue

        prior_grammar = family_grammars.setdefault(fam, grammar)
        if prior_grammar != grammar:
            failures.append(p + "_FAMILY_GRAMMAR_DRIFT")

        prompt_key = (fam, evaluator, code, polarity, rep)
        identity = (case_id, prompt_sha)
        prior_prompt = prompt_identity.setdefault(prompt_key, identity)
        if prior_prompt != identity:
            failures.append(p + "_MODEL_FACING_CASE_DRIFT_ACROSS_INTERVENTIONS")

        key = (fam, intervention, evaluator, code, polarity, rep)
        if key in groups:
            failures.append(p + "_DUPLICATE_CELL")
            continue
        groups[key] = {
            "effect": float(intervention_margin) - float(null_margin),
            "intervention_margin": float(intervention_margin),
            "null_margin": float(null_margin),
            "case_id": case_id,
            "prompt_sha256": prompt_sha,
        }
        replicate_ids[(fam, intervention, evaluator, code, polarity)].add(rep)

    families = sorted(family_grammars)
    if len(families) < v2.MIN_HOLDOUT_FAMILIES:
        failures.append("MATRIX_HOLDOUT_FAMILIES_INSUFFICIENT")
    if len(set(family_grammars.values())) < v2.MIN_HOLDOUT_FAMILIES:
        failures.append("MATRIX_TASK_GRAMMARS_NOT_DISTINCT")

    expected_replicates: int | None = None
    for fam in families:
        for intervention in STATES:
            for evaluator in STATES:
                for code in CODES:
                    for polarity in POLARITIES:
                        reps = replicate_ids[(fam, intervention, evaluator, code, polarity)]
                        if len(reps) < MIN_REPLICATES:
                            failures.append(
                                f"MATRIX_REPLICATION_LOW:{fam}:{intervention}:{evaluator}:{code}:{polarity}"
                            )
                        if expected_replicates is None and reps:
                            expected_replicates = len(reps)
                        elif reps and expected_replicates is not None and len(reps) != expected_replicates:
                            failures.append("MATRIX_REPLICATION_IMBALANCE")
                        for rep in reps:
                            if (fam, intervention, evaluator, code, polarity, rep) not in groups:
                                failures.append("MATRIX_INTERNAL_CELL_MISSING")

    for prompt_key in sorted(prompt_identity):
        fam, evaluator, code, polarity, rep = prompt_key
        present = {
            intervention
            for intervention in STATES
            if (fam, intervention, evaluator, code, polarity, rep) in groups
        }
        if present != set(STATES):
            failures.append(
                "INTERVENTION_SET_INCOMPLETE:" + ":".join(prompt_key) + ":got=" + ",".join(sorted(present))
            )

    specificity_gaps: list[float] = []
    diagonal_effects: list[float] = []
    for prompt_key in sorted(prompt_identity):
        fam, evaluator, code, polarity, rep = prompt_key
        diag_key = (fam, evaluator, evaluator, code, polarity, rep)
        diag = groups.get(diag_key)
        if diag is None:
            failures.append("DIAGONAL_CELL_MISSING:" + ":".join(prompt_key))
            continue
        diag_effect = diag["effect"]
        diagonal_effects.append(diag_effect)
        if diag_effect <= MIN_DIAGONAL_EFFECT:
            failures.append("DIAGONAL_EFFECT_NOT_POSITIVE:" + ":".join(prompt_key))
        for alternative in STATES:
            if alternative == evaluator:
                continue
            off = groups.get((fam, alternative, evaluator, code, polarity, rep))
            if off is None:
                failures.append(
                    "OFF_DIAGONAL_CELL_MISSING:" + ":".join(prompt_key) + ":" + alternative
                )
                continue
            gap = diag_effect - off["effect"]
            specificity_gaps.append(gap)
            if gap <= MIN_SPECIFICITY_GAP:
                failures.append(
                    "DIAGONAL_NOT_ABOVE_OFF_DIAGONAL:"
                    + ":".join(prompt_key)
                    + f":alternative={alternative}:gap={gap:.12g}"
                )

    return {
        "families": len(families),
        "task_grammars": len(set(family_grammars.values())),
        "rows": len(groups),
        "prompt_strata": len(prompt_identity),
        "replicates_per_cell": expected_replicates,
        "matrix_factorial": "INTERVENTION_STATE_3_X_EVALUATOR_STATE_3_X_CODE_3_X_POLARITY_2_X_FAMILY_X_REPLICATE",
        "minimum_diagonal_effect": min(diagonal_effects) if diagonal_effects else None,
        "minimum_diagonal_offdiagonal_gap": min(specificity_gaps) if specificity_gaps else None,
    }


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("ATTESTATION_OBJECT_REQUIRED")
    if candidate.get("schema") != ATTESTATION_SCHEMA:
        failures.append("ATTESTATION_SCHEMA_MISMATCH")

    base_candidate = candidate.get("base_v4_attestation")
    if not isinstance(base_candidate, dict):
        failures.append("BASE_V4_ATTESTATION_REQUIRED")
        base = {"cross_task_abstract_native_control_pass": False, "failures": ["BASE_V4_ATTESTATION_REQUIRED"]}
    else:
        base = v4.adjudicate(base_candidate)
        if base.get("cross_task_abstract_native_control_pass") is not True:
            failures.append("BASE_V4_GATE_NOT_PASS")
            failures.extend("BASE_V4:" + str(x) for x in (base.get("failures") or []))

    vectors = _vector_registry(candidate, failures)
    matrix = _matrix(candidate, failures, vectors)
    passed = not failures

    return {
        "schema": SCHEMA,
        "intervention_evaluator_state_matrix_pass": passed,
        "failures": sorted(set(failures)),
        "matrix": matrix,
        "base_v4": base,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "authenticated_runtime_evidence": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_credit": False,
        "whole_entityos_hcu_credit": False,
        "training_credit": False,
        "claim_scope_if_pass": "STATIC_INTERVENTION_X_EVALUATOR_STATE_SPECIFICITY_POLICY_COMPONENT_ONLY",
        "evidence_boundary": (
            "PASS means a caller-supplied evidence object satisfies the full intervention-state x evaluator-state "
            "specificity matrix on top of strict v4. It does not authenticate Qwen runtime, prompt bytes, vector bytes, "
            "or receipt provenance; R2_B11 remains independently required."
        ),
    }
