#!/usr/bin/env python3
"""Reconstructive lexical-audit successor for Trigger-1.

The v11 abstract deconfound gate correctly requires lexical disjointness, but its boolean
and receipt fields do not by themselves prove that the underlying model-facing texts are
actually disjoint. This companion recomputes that property from bound basis and exact
CALIBRATION/HOLDOUT case-plan prompts.

Only within-family common scaffold is removed before comparing discriminative vocabulary.
Canonical evaluator class names are forbidden everywhere. A/B/C output-code identities are
forbidden in BASIS derivation but allowed in CALIBRATION/HOLDOUT because the lower v10 chain
independently requires exact target x output-code counterbalancing.

This module is execution-free, fail-closed and non-minting.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_RECONSTRUCTIVE_LEXICAL_AUDIT_GATE/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
TARGET_SET = set(TARGETS)
CANONICAL_LABELS = tuple(x.lower() for x in TARGETS)
TOKEN_RE = re.compile(r"[a-z]+")

# Only grammar/protocol words belong here. Semantic polarity/status words deliberately do not.
GLOBAL_SCAFFOLD = {
    "a", "an", "the", "one", "is", "are", "was", "were", "be", "being", "been",
    "and", "or", "but", "not", "no", "to", "of", "for", "from", "in", "on", "at",
    "by", "with", "without", "it", "its", "this", "that", "these", "those", "as",
    "do", "does", "did", "only", "exactly", "internally", "represent", "return",
    "answer", "output", "emit", "code", "codes", "class", "label", "labels",
    "temporary", "card", "situation", "action", "actions",
}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def _tokens(prompt: str) -> set[str]:
    return {x for x in TOKEN_RE.findall(prompt.lower()) if x not in GLOBAL_SCAFFOLD}


def _prompt_leak(prompt: str, *, basis: bool) -> str | None:
    lower = prompt.lower()
    leaked = sorted(label for label in CANONICAL_LABELS if label in lower)
    if leaked:
        return "CANONICAL_SEMANTIC_LABEL:" + ",".join(leaked)
    if basis and re.search(r"(?<![A-Za-z])[ABC](?![A-Za-z])", prompt):
        return "BASIS_OUTPUT_CODE_IDENTITY"
    return None


def _families(
    rows: Any,
    *,
    family_field: str,
    target_field: str,
    scope: str,
    basis: bool,
) -> tuple[dict[str, set[str]], list[str]]:
    failures: list[str] = []
    if not isinstance(rows, list):
        return {}, [f"{scope}_ROWS_REQUIRED"]
    grouped: dict[str, dict[str, set[str]]] = {}
    for index, row in enumerate(rows):
        prefix = f"{scope}_ROW_{index}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        family = str(row.get(family_field) or "").strip()
        target = str(row.get(target_field) or "").strip().upper()
        prompt = row.get("prompt")
        if not family:
            failures.append(f"{prefix}_FAMILY_REQUIRED")
            continue
        if target not in TARGET_SET:
            failures.append(f"{prefix}_TARGET_INVALID")
            continue
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{prefix}_PROMPT_REQUIRED")
            continue
        leak = _prompt_leak(prompt, basis=basis)
        if leak:
            failures.append(f"{prefix}_MODEL_FACING_LEAK:{leak}")
        slot = grouped.setdefault(family, {})
        if target in slot:
            failures.append(f"{prefix}_DUPLICATE_TARGET")
            continue
        slot[target] = _tokens(prompt)

    discriminative: dict[str, set[str]] = {}
    for family, states in sorted(grouped.items()):
        if set(states) != TARGET_SET:
            failures.append(f"{scope}_FAMILY_MUST_CONTAIN_EXACT_TARGET_TRIAD:{family}")
            continue
        common = set.intersection(*(states[target] for target in TARGETS))
        discriminative[family] = set.union(*(states[target] - common for target in TARGETS))
        if not discriminative[family]:
            failures.append(f"{scope}_DISCRIMINATIVE_LEXICON_EMPTY:{family}")
    return discriminative, failures


def _within_overlap(families: dict[str, set[str]], scope: str) -> tuple[list[str], list[dict[str, Any]]]:
    failures: list[str] = []
    evidence: list[dict[str, Any]] = []
    names = sorted(families)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            overlap = sorted(families[left] & families[right])
            if overlap:
                failures.append(f"{scope}_DISCRIMINATIVE_LEXICAL_OVERLAP:{left}:{right}")
                evidence.append({"left": left, "right": right, "tokens": overlap})
    return failures, evidence


def _cross_overlap(
    left: dict[str, set[str]], right: dict[str, set[str]], label: str
) -> tuple[list[str], list[str]]:
    lu = set().union(*left.values()) if left else set()
    ru = set().union(*right.values()) if right else set()
    overlap = sorted(lu & ru)
    return ([] if not overlap else [f"{label}_DISCRIMINATIVE_LEXICON_MUST_BE_DISJOINT"], overlap)


def _case_rows(candidate: dict[str, Any], split: str) -> Any:
    evidence = candidate.get("preregistration_evidence")
    plans = evidence.get("case_plans") if isinstance(evidence, dict) else None
    plan = plans.get(split) if isinstance(plans, dict) else None
    return plan.get("cases") if isinstance(plan, dict) else None


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("CANDIDATE_OBJECT_REQUIRED")

    evidence = candidate.get("reconstructive_lexical_audit")
    basis_rows = evidence.get("basis_rows") if isinstance(evidence, dict) else None
    basis, f = _families(
        basis_rows,
        family_field="family_group_id",
        target_field="semantic_class",
        scope="BASIS",
        basis=True,
    )
    failures.extend(f)
    calibration, f = _families(
        _case_rows(candidate, "CALIBRATION"),
        family_field="scenario_family_sha256",
        target_field="semantic_target",
        scope="CALIBRATION",
        basis=False,
    )
    failures.extend(f)
    holdout, f = _families(
        _case_rows(candidate, "HOLDOUT"),
        family_field="scenario_family_sha256",
        target_field="semantic_target",
        scope="HOLDOUT",
        basis=False,
    )
    failures.extend(f)

    if len(basis) < 6:
        failures.append("AT_LEAST_SIX_BASIS_FAMILIES_REQUIRED")
    if len(calibration) < 3:
        failures.append("AT_LEAST_THREE_CALIBRATION_FAMILIES_REQUIRED")
    if len(holdout) < 3:
        failures.append("AT_LEAST_THREE_HOLDOUT_FAMILIES_REQUIRED")

    f, basis_overlap = _within_overlap(basis, "BASIS")
    failures.extend(f)
    f, calibration_overlap = _within_overlap(calibration, "CALIBRATION")
    failures.extend(f)
    f, holdout_overlap = _within_overlap(holdout, "HOLDOUT")
    failures.extend(f)

    cross: dict[str, list[str]] = {}
    for left, right, label in (
        (basis, calibration, "BASIS_CALIBRATION"),
        (basis, holdout, "BASIS_HOLDOUT"),
        (calibration, holdout, "CALIBRATION_HOLDOUT"),
    ):
        f, overlap = _cross_overlap(left, right, label)
        failures.extend(f)
        cross[label] = overlap

    # Bind the reconstruction to the v11 declared lexical audit rather than creating a
    # parallel authority. The v11 receipt remains required; this gate verifies the text.
    d = candidate.get("abstract_state_deconfound")
    if not isinstance(d, dict):
        failures.append("V11_ABSTRACT_STATE_DECONFOUND_REQUIRED")
        d = {}
    if d.get("basis_model_facing_canonical_labels_absent") is not True:
        failures.append("V11_BASIS_LABEL_FREE_DECLARATION_REQUIRED")
    if d.get("holdout_model_facing_canonical_labels_absent") is not True:
        failures.append("V11_HOLDOUT_LABEL_FREE_DECLARATION_REQUIRED")
    if d.get("basis_holdout_lexically_disjoint") is not True:
        failures.append("V11_BASIS_HOLDOUT_LEXICAL_DISJOINT_DECLARATION_REQUIRED")
    if d.get("semantic_synonym_lexicon_disjoint") is not True:
        failures.append("V11_SEMANTIC_SYNONYM_DISJOINT_DECLARATION_REQUIRED")
    if not _sha256(d.get("lexical_audit_receipt_sha256")):
        failures.append("V11_LEXICAL_AUDIT_RECEIPT_REQUIRED")

    material = {
        "schema": SCHEMA,
        "basis_family_count": len(basis),
        "calibration_family_count": len(calibration),
        "holdout_family_count": len(holdout),
        "basis_discriminative_tokens": {k: sorted(v) for k, v in sorted(basis.items())},
        "calibration_discriminative_tokens": {k: sorted(v) for k, v in sorted(calibration.items())},
        "holdout_discriminative_tokens": {k: sorted(v) for k, v in sorted(holdout.items())},
        "within_partition_overlaps": {
            "basis": basis_overlap,
            "calibration": calibration_overlap,
            "holdout": holdout_overlap,
        },
        "cross_partition_overlap_tokens": cross,
        "v11_declared_lexical_audit_receipt_sha256": d.get("lexical_audit_receipt_sha256"),
        "basis_output_codes_forbidden": True,
        "evaluation_output_codes_allowed_under_lower_factorial_gate": True,
    }
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "reconstructed_lexical_audit_receipt_sha256": canonical_sha(material),
        "reconstructed_material": material,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS recomputes model-facing label absence and strict discriminative lexical disjointness from the exact "
            "bound text universe; it verifies but does not replace the v11 nuisance/residualization evidence. "
            "It executes no model and mints no semantic/runtime/product credit."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    args = ap.parse_args()
    path = Path(args.candidate)
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        obj = {"_invalid": f"{type(exc).__name__}:{exc}"}
    print(json.dumps(adjudicate(obj), sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
