#!/usr/bin/env python3
"""Pure design primitives for the strict Qwen3-0.6B J-Space successor.

This module deliberately contains no model/runtime code. It defines the label-free
basis families, the semantic-target x output-code factorial split, nuisance separation,
residual-norm calibration math, and the cross-target specificity acceptance metric used
by the native llama.cpp cvec executor successor.

Scientific intent:
- model-facing semantic basis prompts contain no pole labels or close label words;
- semantic target and output code are independently counterbalanced;
- three target directions are evaluated as a shared J-Space family, not as one
  privileged AFFIRMATIVE axis;
- a matching semantic vector must beat both mismatched semantic vectors;
- a label-only nuisance vector must not reproduce the matching-vector effect;
- operating-point magnitude is expressed relative to the measured residual norm.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import math
import re
from typing import Any, Mapping, Sequence

SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_TARGET_X_CODE_DESIGN/v1"
SEMANTIC_TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
OUTPUT_CODES = ("A", "B", "C")
BASE_CONTROLS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)
EXTRA_CONTROLS = ("LABEL_ONLY_NUISANCE_VECTOR",)
ALL_CONTROLS = BASE_CONTROLS + EXTRA_CONTROLS

# Model-facing semantic basis prompts intentionally avoid the semantic class names,
# yes/no, and close decision-pole vocabulary. Each row is a different lexical/domain
# realization so a direction cannot be reconstructed from one repeated label token.
LABEL_FREE_BASIS_FAMILIES: dict[str, tuple[tuple[int, str, str], ...]] = {
    "AFFIRMATIVE": (
        (7101, "access", "/no_think\nThe indicator turns green and the turnstile unlocks. Internalize the resulting state."),
        (7102, "workflow", "/no_think\nThe queued process leaves the queue and begins running. Internalize the resulting state."),
        (7103, "motion", "/no_think\nThe motion takes effect and its prescribed action begins. Internalize the resulting state."),
    ),
    "NEGATIVE": (
        (7201, "access", "/no_think\nThe indicator turns red and the turnstile stays locked. Internalize the resulting state."),
        (7202, "workflow", "/no_think\nThe queued process is removed and does not begin running. Internalize the resulting state."),
        (7203, "motion", "/no_think\nThe motion is removed from effect and its prescribed action does not begin. Internalize the resulting state."),
    ),
    "NEUTRAL": (
        (7301, "access", "/no_think\nThe indicator stays amber and the turnstile awaits another reading. Internalize the resulting state."),
        (7302, "workflow", "/no_think\nThe queued process remains pending while another check is awaited. Internalize the resulting state."),
        (7303, "motion", "/no_think\nThe motion is held for later consideration and its action remains pending. Internalize the resulting state."),
    ),
}

# These are not semantic basis prompts. They form a deliberately explicit nuisance
# subspace/control so leakage from pole vocabulary can be measured/projected out.
LABEL_ONLY_NUISANCE_PROMPTS: tuple[tuple[int, str, str], ...] = (
    (7901, "AFFIRMATIVE", "/no_think\nAFFIRMATIVE yes approve accept allow endorse"),
    (7902, "NEGATIVE", "/no_think\nNEGATIVE no reject deny refuse oppose"),
    (7903, "NEUTRAL", "/no_think\nNEUTRAL abstain undecided neither"),
)

FORBIDDEN_BASIS_LEXEMES = {
    "affirmative", "negative", "neutral", "yes", "no", "approve", "approval",
    "accept", "acceptance", "allow", "permission", "endorse", "reject", "rejection",
    "deny", "denial", "refuse", "refusal", "oppose", "opposition", "abstain",
    "abstention", "undecided",
}

CALIBRATION_FAMILIES: tuple[dict[str, str], ...] = (
    {
        "family": "cal_gate",
        "AFFIRMATIVE": "green lamp and unlocked gate",
        "NEGATIVE": "red lamp and locked gate",
        "NEUTRAL": "amber lamp and waiting gate",
    },
    {
        "family": "cal_job",
        "AFFIRMATIVE": "job leaves queue and runs",
        "NEGATIVE": "job is removed before running",
        "NEUTRAL": "job stays queued for another check",
    },
    {
        "family": "cal_switch",
        "AFFIRMATIVE": "switch closes the circuit and current flows",
        "NEGATIVE": "switch opens the circuit and current stops",
        "NEUTRAL": "switch position is held pending another measurement",
    },
)

HOLDOUT_FAMILIES: tuple[dict[str, str], ...] = (
    {
        "family": "hold_route",
        "AFFIRMATIVE": "route becomes active and traffic enters it",
        "NEGATIVE": "route is withdrawn and traffic cannot enter it",
        "NEUTRAL": "route remains pending while traffic waits",
    },
    {
        "family": "hold_motion",
        "AFFIRMATIVE": "motion takes effect and the action starts",
        "NEGATIVE": "motion is removed from effect and the action stops",
        "NEUTRAL": "motion is held over and the action waits",
    },
    {
        "family": "hold_release",
        "AFFIRMATIVE": "release flag is set and the package moves onward",
        "NEGATIVE": "release flag is cleared and the package is held back",
        "NEUTRAL": "release flag remains pending while the package waits",
    },
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _words(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z]+", text.lower().replace("/no_think", "")))


def validate_label_free_basis() -> dict[str, Any]:
    failures: list[str] = []
    seen_prompts: set[str] = set()
    family_coverage: dict[str, set[str]] = {target: set() for target in SEMANTIC_TARGETS}
    for target in SEMANTIC_TARGETS:
        rows = LABEL_FREE_BASIS_FAMILIES.get(target, ())
        if len(rows) < 3:
            failures.append(f"BASIS_FAMILY_TOO_SMALL:{target}")
        for seed, family, prompt in rows:
            if prompt in seen_prompts:
                failures.append(f"DUPLICATE_BASIS_PROMPT:{seed}")
            seen_prompts.add(prompt)
            bad = sorted(_words(prompt) & FORBIDDEN_BASIS_LEXEMES)
            if bad:
                failures.append(f"FORBIDDEN_BASIS_LEXEME:{target}:{seed}:{','.join(bad)}")
            family_coverage[target].add(family)
    expected_families = family_coverage[SEMANTIC_TARGETS[0]]
    for target in SEMANTIC_TARGETS[1:]:
        if family_coverage[target] != expected_families:
            failures.append(f"BASIS_DOMAIN_COVERAGE_MISMATCH:{target}")
    return {
        "pass": not failures,
        "failures": failures,
        "prompt_count": len(seen_prompts),
        "domains": sorted(expected_families),
        "basis_family_sha256": canonical_sha(LABEL_FREE_BASIS_FAMILIES),
        "nuisance_family_sha256": canonical_sha(LABEL_ONLY_NUISANCE_PROMPTS),
    }


def _latin_mapping(rotation: int) -> dict[str, str]:
    return {
        code: SEMANTIC_TARGETS[(idx + rotation) % len(SEMANTIC_TARGETS)]
        for idx, code in enumerate(OUTPUT_CODES)
    }


def build_factorial_split(phase: str) -> list[dict[str, Any]]:
    if phase not in {"CALIBRATION", "FRESH_HOLDOUT"}:
        raise ValueError("UNKNOWN_PHASE")
    families = CALIBRATION_FAMILIES if phase == "CALIBRATION" else HOLDOUT_FAMILIES
    seed_base = 8100 if phase == "CALIBRATION" else 9100
    rows: list[dict[str, Any]] = []
    for family_index, family in enumerate(families):
        mapping = _latin_mapping(family_index)
        descriptions = {code: family[mapping[code]] for code in OUTPUT_CODES}
        for target_index, semantic_target in enumerate(SEMANTIC_TARGETS):
            target_code = next(code for code, semantic in mapping.items() if semantic == semantic_target)
            seed = seed_base + family_index * 10 + target_index + 1
            prompt = (
                "/no_think\n"
                f"Codebook: A = {descriptions['A']}; B = {descriptions['B']}; C = {descriptions['C']}. "
                f"Requested state: {family[semantic_target]}. Output only its code token."
            )
            rows.append({
                "seed": seed,
                "phase": phase,
                "lexical_family": family["family"],
                "semantic_target": semantic_target,
                "target_label": target_code,
                "mapping": mapping,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            })
    validate_factorial_split(rows, phase)
    return rows


def validate_factorial_split(rows: Sequence[Mapping[str, Any]], phase: str) -> dict[str, Any]:
    failures: list[str] = []
    if len(rows) != 9:
        failures.append(f"{phase}_CASE_COUNT_MUST_BE_9:{len(rows)}")
    target_counts = Counter(str(row.get("semantic_target")) for row in rows)
    if set(target_counts) != set(SEMANTIC_TARGETS) or any(target_counts[t] != 3 for t in SEMANTIC_TARGETS):
        failures.append(f"{phase}_SEMANTIC_TARGET_NOT_3X3_COUNTERBALANCED")
    pairs = Counter((str(row.get("semantic_target")), str(row.get("target_label"))) for row in rows)
    expected_pairs = {(target, code) for target in SEMANTIC_TARGETS for code in OUTPUT_CODES}
    if set(pairs) != expected_pairs or any(pairs[pair] != 1 for pair in expected_pairs):
        failures.append(f"{phase}_TARGET_X_CODE_NOT_FULL_FACTORIAL")
    lexical = Counter(str(row.get("lexical_family")) for row in rows)
    if len(lexical) != 3 or any(count != 3 for count in lexical.values()):
        failures.append(f"{phase}_LEXICAL_FAMILY_BALANCE_INVALID")
    if len({str(row.get("prompt_sha256")) for row in rows}) != len(rows):
        failures.append(f"{phase}_PROMPTS_NOT_UNIQUE")
    if failures:
        raise ValueError(";".join(failures))
    return {
        "pass": True,
        "semantic_targets": list(SEMANTIC_TARGETS),
        "target_codes": list(OUTPUT_CODES),
        "target_x_code_full_factorial": True,
        "semantic_target_counterbalanced": True,
        "label_mapping_counterbalanced": True,
        "lexical_families": sorted(lexical),
        "family_id": canonical_sha([
            {
                "seed": row["seed"],
                "lexical_family": row["lexical_family"],
                "semantic_target": row["semantic_target"],
                "target_label": row["target_label"],
                "prompt_sha256": row["prompt_sha256"],
            }
            for row in rows
        ]),
    }


def project_out_subspace(torch: Any, vector: Any, nuisance_vectors: Sequence[Any], eps: float = 1e-12):
    """Remove the component of vector lying in nuisance span using QR projection."""
    if not nuisance_vectors:
        return vector
    matrix = torch.stack([v.to(vector.device, dtype=vector.dtype) for v in nuisance_vectors], dim=1)
    q, _r = torch.linalg.qr(matrix, mode="reduced")
    projected = vector - q @ (q.transpose(0, 1) @ vector)
    norm = torch.linalg.vector_norm(projected)
    if not bool(torch.isfinite(norm)) or float(norm) <= eps:
        raise RuntimeError("NUISANCE_PROJECTION_DEGENERATE")
    return projected / norm


def centered_target_directions(
    torch: Any, class_means: Mapping[str, Any], nuisance_vectors: Sequence[Any] = ()
) -> dict[str, Any]:
    """Build three centered semantic directions and project out nuisance span."""
    missing = [target for target in SEMANTIC_TARGETS if target not in class_means]
    if missing:
        raise ValueError(f"MISSING_CLASS_MEANS:{','.join(missing)}")
    center = sum(
        (class_means[target] for target in SEMANTIC_TARGETS),
        torch.zeros_like(class_means[SEMANTIC_TARGETS[0]]),
    ) / 3.0
    result: dict[str, Any] = {}
    for target in SEMANTIC_TARGETS:
        raw = class_means[target] - center
        raw_norm = torch.linalg.vector_norm(raw)
        if not bool(torch.isfinite(raw_norm)) or float(raw_norm) <= 1e-12:
            raise RuntimeError(f"TARGET_DIRECTION_DEGENERATE:{target}")
        unit = raw / raw_norm
        if nuisance_vectors:
            unit = project_out_subspace(torch, unit, nuisance_vectors)
        result[target] = unit
    return result


def scale_to_residual_norm(vector: Any, residual_norm: float, fraction: float):
    """Scale a vector so ||delta|| = fraction * measured residual norm."""
    if not math.isfinite(float(residual_norm)) or float(residual_norm) <= 0:
        raise ValueError("RESIDUAL_NORM_MUST_BE_POSITIVE_FINITE")
    if not math.isfinite(float(fraction)) or float(fraction) <= 0:
        raise ValueError("RESIDUAL_FRACTION_MUST_BE_POSITIVE_FINITE")
    norm = vector.norm()
    if not bool(norm.isfinite()) or float(norm) <= 1e-12:
        raise ValueError("VECTOR_NORM_MUST_BE_POSITIVE_FINITE")
    return vector * (float(residual_norm) * float(fraction) / norm)


def metric_row_key(row: Mapping[str, Any]) -> tuple[int, str]:
    return int(row["seed"]), str(row["lexical_family"])


def cross_target_specificity_metrics(
    rows: Sequence[Mapping[str, Any]], nuisance_tolerance: float = 0.10
) -> dict[str, Any]:
    """Fail closed unless matching semantic vectors beat mismatched vectors per case."""
    by_case: dict[tuple[int, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_case[metric_row_key(row)].append(row)

    failures: list[str] = []
    per_target: dict[str, list[dict[str, float]]] = {target: [] for target in SEMANTIC_TARGETS}
    for case_key, case_rows in sorted(by_case.items()):
        requested = {str(r["semantic_target"]) for r in case_rows}
        if len(requested) != 1:
            failures.append(f"CASE_SEMANTIC_TARGET_AMBIGUOUS:{case_key}")
            continue
        target = next(iter(requested))
        regular: dict[str, float] = {}
        applied: dict[str, float] = {}
        for row in case_rows:
            control = str(row["control"])
            score = float(row["target_score"])
            applied_target = row.get("applied_semantic_target")
            if control == "+VECTOR" and applied_target in SEMANTIC_TARGETS:
                applied[str(applied_target)] = score
            elif control in ALL_CONTROLS:
                regular[control] = score
        needed_regular = {
            "BASELINE", "SIGN_FLIP", "NULL_VECTOR", "ORTHOGONAL_SAME_NORM",
            "PERMUTED_SAME_NORM", "LABEL_ONLY_NUISANCE_VECTOR",
        }
        if not needed_regular.issubset(regular) or set(applied) != set(SEMANTIC_TARGETS):
            failures.append(f"CASE_CONTROL_MATRIX_INCOMPLETE:{case_key}")
            continue
        match = applied[target]
        mismatched = [applied[t] for t in SEMANTIC_TARGETS if t != target]
        baseline = regular["BASELINE"]
        per_target[target].append({
            "match_vs_baseline": match - baseline,
            "match_vs_best_mismatch": match - max(mismatched),
            "baseline_vs_sign_flip": baseline - regular["SIGN_FLIP"],
            "match_vs_orthogonal": match - regular["ORTHOGONAL_SAME_NORM"],
            "match_vs_permuted": match - regular["PERMUTED_SAME_NORM"],
            "nuisance_abs_drift": abs(regular["LABEL_ONLY_NUISANCE_VECTOR"] - baseline),
            "null_abs_drift": abs(regular["NULL_VECTOR"] - baseline),
        })

    target_summary: dict[str, Any] = {}
    pass_targets = True
    for target in SEMANTIC_TARGETS:
        records = per_target[target]
        if len(records) != 3:
            failures.append(f"TARGET_CASE_COUNT_INVALID:{target}:{len(records)}")
            pass_targets = False
            continue
        minima = {
            "min_match_vs_baseline": min(r["match_vs_baseline"] for r in records),
            "min_match_vs_best_mismatch": min(r["match_vs_best_mismatch"] for r in records),
            "min_baseline_vs_sign_flip": min(r["baseline_vs_sign_flip"] for r in records),
            "min_match_vs_orthogonal": min(r["match_vs_orthogonal"] for r in records),
            "min_match_vs_permuted": min(r["match_vs_permuted"] for r in records),
            "max_nuisance_abs_drift": max(r["nuisance_abs_drift"] for r in records),
            "max_null_abs_drift": max(r["null_abs_drift"] for r in records),
        }
        target_pass = (
            minima["min_match_vs_baseline"] > 0
            and minima["min_match_vs_best_mismatch"] > 0
            and minima["min_baseline_vs_sign_flip"] > 0
            and minima["min_match_vs_orthogonal"] > 0
            and minima["min_match_vs_permuted"] > 0
            and minima["max_nuisance_abs_drift"] <= nuisance_tolerance
            and minima["max_null_abs_drift"] <= 1e-5
        )
        target_summary[target] = {**minima, "pass": target_pass}
        pass_targets = pass_targets and target_pass

    return {
        "schema": "CLAY_TRIGGER1_CROSS_TARGET_SPECIFICITY_METRIC/v1",
        "pass": not failures and pass_targets,
        "failures": failures,
        "semantic_target_interaction_test": True,
        "cross_target_vector_specificity_test": True,
        "targets": target_summary,
        "nuisance_tolerance": nuisance_tolerance,
        "generic_compliance_rejection_rule": (
            "matching target vector must beat both mismatched target vectors for every semantic target and lexical family"
        ),
    }


def protocol_manifest() -> dict[str, Any]:
    calibration = build_factorial_split("CALIBRATION")
    holdout = build_factorial_split("FRESH_HOLDOUT")
    return {
        "schema": SCHEMA,
        "semantic_targets": list(SEMANTIC_TARGETS),
        "output_codes": list(OUTPUT_CODES),
        "model_facing_basis_label_free": validate_label_free_basis()["pass"],
        "label_only_nuisance_control": True,
        "semantic_target_counterbalanced": True,
        "target_x_code_full_factorial": True,
        "cross_lexical_families": True,
        "cross_target_vector_specificity_test": True,
        "token_scope_required": "ALL_PROMPT_TOKENS_CVEC",
        "residual_norm_relative_operating_point_required": True,
        "operating_point_selected_on_calibration_only": True,
        "calibration_family_id": validate_factorial_split(calibration, "CALIBRATION")["family_id"],
        "holdout_family_id": validate_factorial_split(holdout, "FRESH_HOLDOUT")["family_id"],
        "basis_family_sha256": canonical_sha(LABEL_FREE_BASIS_FAMILIES),
        "nuisance_family_sha256": canonical_sha(LABEL_ONLY_NUISANCE_PROMPTS),
    }


if __name__ == "__main__":
    print(json.dumps(protocol_manifest(), sort_keys=True, ensure_ascii=False))
