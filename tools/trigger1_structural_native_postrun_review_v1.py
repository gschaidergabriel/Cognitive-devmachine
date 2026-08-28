#!/usr/bin/env python3
"""Deterministic post-run review for the frozen Trigger-1 structural native discriminator.

This reviewer does not execute a model, alter the frozen experiment, or mint semantic/J-Space
credit. It separates two claims that the frozen runtime result must not conflate:

1. strong class-selective structural native component evidence; and
2. stronger template-invariant abstract semantic evidence.

The frozen runtime may remain useful component evidence even when the stronger abstraction
claim is blocked. Current calibration/holdout lexical disjointness is therefore reviewed
separately from structural-template disjointness.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_NATIVE_POSTRUN_REVIEW/v1"
RUNTIME_SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_NATIVE_ABSTRACT_RUNTIME/v1"
CASESET_SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")

# The structural generator deliberately uses lowercase nonce/content atoms and uppercase
# syntax/code atoms. Erasing lowercase content exposes whether calibration and holdout still
# share the same formal template after lexical substitution.
LOWERCASE_CONTENT_ATOM_RE = re.compile(r"\b[a-z][a-z0-9_]*\b")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def structural_template(prompt: str) -> str:
    if not isinstance(prompt, str) or not prompt:
        raise ValueError("PROMPT_REQUIRED")
    return LOWERCASE_CONTENT_ATOM_RE.sub("<x>", prompt)


def _split_prompts(bundle: dict[str, Any], split: str) -> list[str]:
    node = bundle.get(split)
    if not isinstance(node, dict):
        raise ValueError(f"{split.upper()}_OBJECT_REQUIRED")
    cases = node.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError(f"{split.upper()}_CASES_REQUIRED")
    prompts: list[str] = []
    for i, row in enumerate(cases):
        if not isinstance(row, dict) or not isinstance(row.get("prompt"), str) or not row["prompt"]:
            raise ValueError(f"{split.upper()}_CASE_{i}_PROMPT_REQUIRED")
        prompts.append(row["prompt"])
    return prompts


def audit_templates(bundle: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(bundle, dict) or bundle.get("schema") != CASESET_SCHEMA:
        return {
            "template_disjoint": False,
            "overlap_count": 0,
            "overlap_examples": [],
            "failures": ["CASE_BUNDLE_SCHEMA_MISMATCH"],
        }
    try:
        cal = {structural_template(x) for x in _split_prompts(bundle, "calibration")}
        hold = {structural_template(x) for x in _split_prompts(bundle, "holdout")}
    except ValueError as exc:
        return {
            "template_disjoint": False,
            "overlap_count": 0,
            "overlap_examples": [],
            "failures": [str(exc)],
        }
    overlap = sorted(cal & hold)
    if overlap:
        failures.append("CALIBRATION_HOLDOUT_STRUCTURAL_TEMPLATE_OVERLAP")
    return {
        "template_disjoint": not overlap,
        "calibration_template_count": len(cal),
        "holdout_template_count": len(hold),
        "overlap_count": len(overlap),
        "overlap_examples": overlap[:6],
        "failures": failures,
    }


def audit_matrix(result: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(result, dict):
        return {
            "matrix_valid": False,
            "every_class_positive": False,
            "row_selective_every_class": False,
            "column_selective_every_class": False,
            "failures": ["RUNTIME_RESULT_OBJECT_REQUIRED"],
        }
    matrix = result.get("behavioral_causal_matrix")
    if not isinstance(matrix, dict):
        return {
            "matrix_valid": False,
            "every_class_positive": False,
            "row_selective_every_class": False,
            "column_selective_every_class": False,
            "failures": ["BEHAVIORAL_CAUSAL_MATRIX_REQUIRED"],
        }
    means = matrix.get("mean_delta_matrix_intervention_x_requested_target")
    if not isinstance(means, dict) or set(means) != set(CLASSES):
        failures.append("CAUSAL_MATRIX_INTERVENTION_UNIVERSE_MISMATCH")
        means = {}

    normalized: dict[str, dict[str, float]] = {}
    if not failures:
        for intervention in CLASSES:
            row = means.get(intervention)
            if not isinstance(row, dict) or set(row) != set(CLASSES):
                failures.append(f"CAUSAL_MATRIX_TARGET_UNIVERSE_MISMATCH:{intervention}")
                continue
            if not all(_finite_number(row.get(target)) for target in CLASSES):
                failures.append(f"CAUSAL_MATRIX_NONFINITE:{intervention}")
                continue
            normalized[intervention] = {target: float(row[target]) for target in CLASSES}

    matrix_valid = not failures and len(normalized) == len(CLASSES)
    every_positive = False
    row_selective = False
    column_selective = False
    diagonal: dict[str, float] = {}
    row_advantage: dict[str, float] = {}
    column_advantage: dict[str, float] = {}

    if matrix_valid:
        diagonal = {c: normalized[c][c] for c in CLASSES}
        every_positive = all(diagonal[c] > 0 for c in CLASSES)
        row_advantage = {
            c: diagonal[c] - max(normalized[c][other] for other in CLASSES if other != c)
            for c in CLASSES
        }
        column_advantage = {
            c: diagonal[c] - max(normalized[other][c] for other in CLASSES if other != c)
            for c in CLASSES
        }
        row_selective = all(row_advantage[c] > 0 for c in CLASSES)
        column_selective = all(column_advantage[c] > 0 for c in CLASSES)
        if not every_positive:
            failures.append("NOT_EVERY_CLASS_HAS_POSITIVE_MATCHED_CAUSAL_EFFECT")
        if not row_selective:
            failures.append("MATCHED_INTERVENTION_NOT_ROW_SELECTIVE_FOR_EVERY_CLASS")
        if not column_selective:
            failures.append("MATCHED_INTERVENTION_NOT_COLUMN_SELECTIVE_FOR_EVERY_CLASS")

    declared_each_positive = matrix.get("diagonal_each_positive")
    if matrix_valid and declared_each_positive is not None and declared_each_positive is not every_positive:
        failures.append("DECLARED_DIAGONAL_EACH_POSITIVE_MISMATCH")

    return {
        "matrix_valid": matrix_valid,
        "every_class_positive": every_positive,
        "row_selective_every_class": row_selective,
        "column_selective_every_class": column_selective,
        "diagonal_by_class": diagonal,
        "row_selectivity_advantage_by_class": row_advantage,
        "column_selectivity_advantage_by_class": column_advantage,
        "failures": sorted(set(failures)),
    }


def adjudicate(result: Any, bundle: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(result, dict) or result.get("schema") != RUNTIME_SCHEMA:
        failures.append("RUNTIME_RESULT_SCHEMA_MISMATCH")
        result = result if isinstance(result, dict) else {}
    if not isinstance(bundle, dict) or bundle.get("schema") != CASESET_SCHEMA:
        failures.append("CASE_BUNDLE_SCHEMA_MISMATCH")
        bundle = bundle if isinstance(bundle, dict) else {}

    runner_pass = (
        result.get("status") == "PASS_ABSTRACT_NATIVE_DISCRIMINATOR"
        and result.get("abstract_native_discriminator_pass") is True
    )
    if not runner_pass:
        failures.append("FROZEN_RUNTIME_PASS_REQUIRED")

    lexical = bundle.get("lexical_disjointness_audit") if isinstance(bundle, dict) else None
    lexical_disjoint = isinstance(lexical, dict) and lexical.get("basis_holdout_lexically_disjoint") is True
    if not lexical_disjoint:
        failures.append("CALIBRATION_HOLDOUT_LEXICAL_DISJOINTNESS_REQUIRED")

    matrix = audit_matrix(result)
    templates = audit_templates(bundle)
    failures.extend(matrix["failures"])

    per_class_selective = (
        matrix["matrix_valid"]
        and matrix["every_class_positive"]
        and matrix["row_selective_every_class"]
        and matrix["column_selective_every_class"]
    )
    strong_structural = bool(runner_pass and lexical_disjoint and per_class_selective)

    # Template overlap does not erase a valid structural component result. It only blocks
    # the stronger inference that the controlled state is invariant to the shared formal
    # grammar/template family used by calibration and holdout.
    template_invariant = bool(strong_structural and templates["template_disjoint"])
    if strong_structural and not templates["template_disjoint"]:
        failures.append("TEMPLATE_INVARIANT_ABSTRACTION_NOT_ESTABLISHED")

    return {
        "schema": SCHEMA,
        "frozen_runtime_pass_observed": runner_pass,
        "lexically_disjoint_calibration_holdout": lexical_disjoint,
        "per_class_causal_selectivity": matrix,
        "structural_template_audit": templates,
        "strong_structural_native_component_candidate": strong_structural,
        "template_invariant_abstract_semantic_candidate": template_invariant,
        "semantic_jspace_promotion_candidate": False,
        "canonical_semantics_promotion": False,
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": 0,
        "whole_hcu_credit": 0,
        "whole_entityos_hcu_credit": 0,
        "training_credit": 0,
        "frozen_scientific_design_modified": False,
        "new_model_intervention_executed": False,
        "failures": sorted(set(failures)),
        "evidence_boundary": (
            "This deterministic post-run review may classify an already-executed frozen result as strong "
            "class-selective structural native component evidence only when every class has a positive matched "
            "causal effect and matched interventions are row- and column-selective. Template reuse is reviewed "
            "separately: lexical disjointness alone does not establish template-invariant semantic abstraction. "
            "The reviewer executes no model, changes no preregistered experiment, and mints no semantic/J-Space/" 
            "HCU/EntityOS/training/canonical credit."
        ),
    }


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--result", type=Path, required=True)
    ap.add_argument("--case-bundle", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    try:
        review = adjudicate(_load(args.result), _load(args.case_bundle))
    except (OSError, json.JSONDecodeError) as exc:
        review = {
            "schema": SCHEMA,
            "strong_structural_native_component_candidate": False,
            "template_invariant_abstract_semantic_candidate": False,
            "semantic_jspace_promotion_candidate": False,
            "canonical_semantics_promotion": False,
            "canonical_credit_minted": False,
            "jspace_model_runtime_credit": 0,
            "new_model_intervention_executed": False,
            "failures": [f"INPUT_INVALID:{type(exc).__name__}"],
        }
    text = json.dumps(review, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
