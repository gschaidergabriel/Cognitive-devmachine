#!/usr/bin/env python3
"""Fail-closed preregistration gate for the next Trigger-1 J-Space discriminator.

This gate does not execute a model and mints no runtime/product credit. It validates that
an experiment plan closes the known semantic-label, lexical-axis, scenario-family,
output-realization/context-boundary, operating-point, intervention-scope, and
steering-coherence confounds before a fresh holdout is opened.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SCOPE_NORM_PREREG/v1"
VERDICT_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_SCOPE_NORM_PREREG_GATE/v1"

SEMANTIC_TARGETS = {"AFFIRMATIVE", "NEGATIVE", "NEUTRAL"}
OUTPUT_CODES = {"A", "B", "C"}
REQUIRED_CONTROLS = {
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
    "LABEL_ONLY_NUISANCE_VECTOR",
}
REQUIRED_SCOPE_CONDITIONS = {
    "PYTORCH_LAST_TOKEN_ONLY",
    "PYTORCH_ALL_PROMPT_TOKENS",
    "NATIVE_LLAMA_CPP_ALL_PROMPT_TOKENS_CVEC",
}


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _git_sha(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 40:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _norm_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(v).strip().upper() for v in values}


def _unique_sha_list(values: Any, minimum: int) -> bool:
    return (
        isinstance(values, list)
        and len(values) >= minimum
        and all(_sha256(v) for v in values)
        and len(set(values)) == len(values)
    )


def _identity(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    ident = plan.get("identity")
    if not isinstance(ident, dict):
        return ["IDENTITY_OBJECT_REQUIRED"]
    for key in ("checkpoint_sha256", "tokenizer_sha256", "gguf_sha256", "native_harness_sha256"):
        if not _sha256(ident.get(key)):
            failures.append(f"IDENTITY_SHA256_REQUIRED:{key}")
    if not _git_sha(ident.get("llama_cpp_commit")):
        failures.append("EXACT_LLAMA_CPP_COMMIT_REQUIRED")
    if not _nonempty(ident.get("model_id")):
        failures.append("MODEL_ID_REQUIRED")
    if not _nonempty(ident.get("model_revision")):
        failures.append("MODEL_REVISION_REQUIRED")
    return failures


def _basis(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    basis = plan.get("basis")
    if not isinstance(basis, dict):
        return ["BASIS_OBJECT_REQUIRED"]
    if basis.get("model_facing_explicit_semantic_labels") is not False:
        failures.append("MODEL_FACING_BASIS_MUST_BE_LABEL_FREE")
    if basis.get("uses_evaluation_output_codes") is not False:
        failures.append("BASIS_MUST_NOT_USE_EVALUATION_OUTPUT_CODES")
    if basis.get("uses_holdout_data") is not False:
        failures.append("BASIS_MUST_NOT_USE_HOLDOUT_DATA")
    if not _unique_sha_list(basis.get("lexical_family_sha256"), minimum=3):
        failures.append("AT_LEAST_THREE_DISTINCT_LEXICAL_BASIS_FAMILIES_REQUIRED")
    nuisance = basis.get("lexical_nuisance_control")
    if not isinstance(nuisance, dict):
        failures.append("LEXICAL_NUISANCE_CONTROL_REQUIRED")
    else:
        if nuisance.get("enabled") is not True:
            failures.append("LEXICAL_NUISANCE_CONTROL_MUST_BE_ENABLED")
        if nuisance.get("construction_independent_of_semantic_vector") is not True:
            failures.append("LEXICAL_NUISANCE_CONSTRUCTION_INDEPENDENCE_REQUIRED")
        if not _sha256(nuisance.get("definition_sha256")):
            failures.append("LEXICAL_NUISANCE_DEFINITION_SHA256_REQUIRED")
    return failures


def _factorial(split: Any, prefix: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(split, dict):
        return [f"{prefix}_OBJECT_REQUIRED"]
    if _norm_set(split.get("semantic_targets")) != SEMANTIC_TARGETS:
        failures.append(f"{prefix}_SEMANTIC_TARGET_SET_REQUIRED")
    if _norm_set(split.get("output_codes")) != OUTPUT_CODES:
        failures.append(f"{prefix}_OUTPUT_CODE_SET_REQUIRED")
    cells = split.get("target_x_code_cells")
    expected = {f"{t}:{c}" for t in SEMANTIC_TARGETS for c in OUTPUT_CODES}
    got: set[str] = set()
    if isinstance(cells, list):
        for row in cells:
            if not isinstance(row, dict):
                continue
            t = str(row.get("semantic_target", "")).strip().upper()
            c = str(row.get("output_code", "")).strip().upper()
            got.add(f"{t}:{c}")
    if got != expected:
        failures.append(f"{prefix}_FULL_TARGET_X_CODE_FACTORIAL_REQUIRED")
    if split.get("balanced_cell_counts") is not True:
        failures.append(f"{prefix}_BALANCED_CELL_COUNTS_REQUIRED")
    if not _unique_sha_list(split.get("lexical_family_sha256"), minimum=3):
        failures.append(f"{prefix}_AT_LEAST_THREE_DISTINCT_LEXICAL_FAMILIES_REQUIRED")
    if not isinstance(split.get("seeds"), list) or not split.get("seeds"):
        failures.append(f"{prefix}_FIXED_SEEDS_REQUIRED")
    return failures


def _split_independence(plan: dict[str, Any]) -> list[str]:
    failures = _factorial(plan.get("calibration"), "CALIBRATION")
    failures.extend(_factorial(plan.get("holdout"), "HOLDOUT"))
    cal = plan.get("calibration") if isinstance(plan.get("calibration"), dict) else {}
    hold = plan.get("holdout") if isinstance(plan.get("holdout"), dict) else {}
    cal_f = set(cal.get("lexical_family_sha256") or [])
    hold_f = set(hold.get("lexical_family_sha256") or [])
    if cal_f & hold_f:
        failures.append("CALIBRATION_HOLDOUT_LEXICAL_FAMILIES_MUST_BE_DISJOINT")
    cal_s = {str(x) for x in (cal.get("seeds") or [])}
    hold_s = {str(x) for x in (hold.get("seeds") or [])}
    if cal_s & hold_s:
        failures.append("CALIBRATION_HOLDOUT_SEEDS_MUST_BE_DISJOINT")
    if hold.get("sealed_until_operating_point_frozen") is not True:
        failures.append("HOLDOUT_MUST_REMAIN_SEALED_UNTIL_OPERATING_POINT_FROZEN")
    return failures


def _scenario_blocking(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    b = plan.get("scenario_blocking")
    if not isinstance(b, dict):
        return ["SCENARIO_BLOCKING_OBJECT_REQUIRED"]
    if b.get("unit") != "SCENARIO_FAMILY":
        failures.append("SCENARIO_FAMILY_MUST_BE_BLOCKING_UNIT")
    if b.get("every_family_contains_all_semantic_targets") is not True:
        failures.append("EVERY_SCENARIO_FAMILY_MUST_CONTAIN_ALL_SEMANTIC_TARGETS")
    if b.get("matched_content_skeleton_within_family") is not True:
        failures.append("MATCHED_CONTENT_SKELETON_WITHIN_SCENARIO_REQUIRED")
    if b.get("model_facing_target_identity_exposed") is not False:
        failures.append("SCENARIO_TARGET_IDENTITY_MUST_NOT_BE_MODEL_FACING")
    if b.get("within_family_centering") is not True:
        failures.append("WITHIN_FAMILY_CENTERING_REQUIRED")
    if b.get("equal_family_weighting") is not True:
        failures.append("EQUAL_SCENARIO_FAMILY_WEIGHTING_REQUIRED")
    if b.get("blocked_permutation_within_family") is not True:
        failures.append("BLOCKED_PERMUTATION_WITHIN_SCENARIO_REQUIRED")
    if b.get("output_code_rotation_independent_within_family") is not True:
        failures.append("INDEPENDENT_OUTPUT_CODE_ROTATION_WITHIN_SCENARIO_REQUIRED")
    for split in ("basis", "calibration", "holdout"):
        key = f"{split}_scenario_family_sha256"
        if not _unique_sha_list(b.get(key), minimum=3):
            failures.append(f"{split.upper()}_SCENARIO_FAMILIES_REQUIRED")
    sets = [set(b.get(f"{split}_scenario_family_sha256") or []) for split in ("basis", "calibration", "holdout")]
    if (sets[0] & sets[1]) or (sets[0] & sets[2]) or (sets[1] & sets[2]):
        failures.append("BASIS_CALIBRATION_HOLDOUT_SCENARIO_FAMILIES_MUST_BE_DISJOINT")
    if not _sha256(b.get("blocked_rank_and_permutation_rule_sha256")):
        failures.append("BLOCKED_RANK_AND_PERMUTATION_RULE_SHA256_REQUIRED")
    return failures


def _measurement(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    m = plan.get("measurement")
    if not isinstance(m, dict):
        return ["MEASUREMENT_OBJECT_REQUIRED"]
    if m.get("gain_selection_split") != "CALIBRATION_ONLY":
        failures.append("GAIN_SELECTION_MUST_BE_CALIBRATION_ONLY")
    if m.get("residual_norm_relative") is not True:
        failures.append("RESIDUAL_NORM_RELATIVE_INTERVENTION_REQUIRED")
    if not _nonempty(m.get("residual_norm_definition")):
        failures.append("RESIDUAL_NORM_DEFINITION_REQUIRED")
    grid = m.get("residual_norm_fraction_grid")
    if not isinstance(grid, list) or not grid or not all(isinstance(x, (int, float)) and 0 < float(x) for x in grid):
        failures.append("POSITIVE_RESIDUAL_NORM_FRACTION_GRID_REQUIRED")
    elif len(set(float(x) for x in grid)) != len(grid):
        failures.append("RESIDUAL_NORM_FRACTION_GRID_MUST_BE_UNIQUE")
    if not _sha256(m.get("operating_point_rule_sha256")):
        failures.append("OPERATING_POINT_RULE_SHA256_REQUIRED")
    if m.get("holdout_can_change_operating_point") is not False:
        failures.append("HOLDOUT_MUST_NOT_CHANGE_OPERATING_POINT")
    if _norm_set(m.get("token_scope_conditions")) != REQUIRED_SCOPE_CONDITIONS:
        failures.append("ALL_SCOPE_MATCH_CONDITIONS_REQUIRED")
    if not _nonempty(m.get("scope_divergence_classification_rule")):
        failures.append("SCOPE_DIVERGENCE_CLASSIFICATION_RULE_REQUIRED")
    return failures


def _controls(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    c = plan.get("controls")
    if not isinstance(c, dict):
        return ["CONTROLS_OBJECT_REQUIRED"]
    if _norm_set(c.get("names")) != REQUIRED_CONTROLS:
        failures.append("SEVEN_MATCHED_CONTROLS_REQUIRED")
    if c.get("same_norm_for_nonzero_geometric_controls") is not True:
        failures.append("MATCHED_NORM_GEOMETRIC_CONTROLS_REQUIRED")
    if c.get("same_cases_across_controls") is not True:
        failures.append("SAME_CASES_ACROSS_CONTROLS_REQUIRED")
    return failures


def _coherence(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    c = plan.get("coherence")
    if not isinstance(c, dict):
        return ["COHERENCE_OBJECT_REQUIRED"]
    if c.get("cross_family_cosine_required") is not True:
        failures.append("CROSS_FAMILY_COSINE_REQUIRED")
    if c.get("permutation_null_required") is not True:
        failures.append("COHERENCE_PERMUTATION_NULL_REQUIRED")
    if c.get("threshold_selected_on") != "CALIBRATION_ONLY":
        failures.append("COHERENCE_THRESHOLD_MUST_BE_CALIBRATION_ONLY")
    if c.get("per_family_directional_signs_preserved") is not True:
        failures.append("PER_FAMILY_DIRECTIONAL_SIGNS_REQUIRED")
    if not _sha256(c.get("coherence_rule_sha256")):
        failures.append("COHERENCE_RULE_SHA256_REQUIRED")
    return failures


def _output_realization(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    r = plan.get("output_realization")
    if not isinstance(r, dict):
        return ["OUTPUT_REALIZATION_OBJECT_REQUIRED"]
    if r.get("context_boundary_attestation_required") is not True:
        failures.append("CONTEXT_BOUNDARY_ATTESTATION_REQUIRED")
    if r.get("prompt_plus_completion_prefix_check") is not True:
        failures.append("PROMPT_PLUS_COMPLETION_PREFIX_CHECK_REQUIRED")
    fam = r.get("codebook_family_sha256")
    if not _unique_sha_list(fam, minimum=2):
        failures.append("AT_LEAST_TWO_DISTINCT_CODEBOOK_FAMILIES_REQUIRED")
    if r.get("codebook_family_counterbalance_required") is not True:
        failures.append("CODEBOOK_FAMILY_COUNTERBALANCE_REQUIRED")
    if r.get("generated_or_constrained_behavioral_agreement_required") is not True:
        failures.append("BEHAVIORAL_OUTPUT_AGREEMENT_REQUIRED")
    if r.get("realization_rule_frozen_before_holdout") is not True:
        failures.append("OUTPUT_REALIZATION_RULE_MUST_BE_FROZEN_BEFORE_HOLDOUT")
    if not _sha256(r.get("realization_metric_sha256")):
        failures.append("OUTPUT_REALIZATION_METRIC_SHA256_REQUIRED")
    return failures


def _outcomes(plan: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    o = plan.get("outcomes")
    if not isinstance(o, dict):
        return ["OUTCOMES_OBJECT_REQUIRED"]
    if o.get("primary_test") != "TREATMENT_X_SEMANTIC_TARGET_INTERACTION":
        failures.append("PRIMARY_TREATMENT_X_SEMANTIC_TARGET_INTERACTION_REQUIRED")
    if o.get("sign_flip_must_reverse_interaction") is not True:
        failures.append("SIGN_FLIP_REVERSAL_REQUIRED")
    if o.get("fresh_family_consistency_required") is not True:
        failures.append("FRESH_FAMILY_CONSISTENCY_REQUIRED")
    if not _nonempty(o.get("off_target_task_family")):
        failures.append("OFF_TARGET_TASK_FAMILY_REQUIRED")
    if not isinstance(o.get("off_target_drift_threshold"), (int, float)) or float(o.get("off_target_drift_threshold", -1)) < 0:
        failures.append("NONNEGATIVE_OFF_TARGET_DRIFT_THRESHOLD_REQUIRED")
    if not _sha256(o.get("metric_definition_sha256")):
        failures.append("PRIMARY_METRIC_DEFINITION_SHA256_REQUIRED")
    if not _nonempty(o.get("multiple_comparison_rule")):
        failures.append("MULTIPLE_COMPARISON_RULE_REQUIRED")
    return failures


def validate(plan: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if plan.get("schema") != SCHEMA:
        failures.append("SCHEMA_INVALID")
    failures.extend(_identity(plan))
    failures.extend(_basis(plan))
    failures.extend(_split_independence(plan))
    failures.extend(_scenario_blocking(plan))
    failures.extend(_measurement(plan))
    failures.extend(_controls(plan))
    failures.extend(_coherence(plan))
    failures.extend(_output_realization(plan))
    failures.extend(_outcomes(plan))
    execution = plan.get("execution")
    if not isinstance(execution, dict):
        failures.append("EXECUTION_OBJECT_REQUIRED")
    else:
        if execution.get("requires_canonical_atomic_lease") is not True:
            failures.append("CANONICAL_ATOMIC_LEASE_MUST_BE_REQUIRED_BEFORE_EXECUTION")
        if execution.get("mode") != "FREE_ONLY":
            failures.append("FREE_ONLY_EXECUTION_MODE_REQUIRED")
        if execution.get("preregistration_mints_runtime_credit") is not False:
            failures.append("PREREGISTRATION_MUST_NOT_MINT_RUNTIME_CREDIT")
    return {
        "schema": VERDICT_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "whole_hcu_credit_minted": False,
        "training_credit_minted": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    verdict = validate(plan)
    text = json.dumps(verdict, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if verdict["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
