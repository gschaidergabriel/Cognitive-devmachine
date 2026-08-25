#!/usr/bin/env python3
"""Deterministic text-level audit for abstract Trigger-1 J-Space state evidence.

This module closes a gap left by hash-only lexical-family attestations.  It inspects the
actual model-facing basis/calibration/holdout text and fails closed when canonical class
labels, strong decision-pole proxy lexemes, generic-compliance markers, repeated
class-predictive unigrams, or excessive cross-split content overlap can explain the
purported semantic direction.

It executes no model and mints no runtime/J-Space/HCU/EntityOS/training/canonical credit.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_TEXT_AUDIT/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
TARGET_SET = set(TARGETS)

CANONICAL_LABELS = {"affirmative", "negative", "neutral"}
POLE_PROXY_LEXEMES = {
    # affirmative-like lexical shortcuts
    "yes", "agree", "agrees", "agreed", "agreement", "approve", "approves", "approved",
    "approval", "accept", "accepts", "accepted", "acceptance", "allow", "allows", "allowed",
    "endorse", "endorses", "endorsed", "endorsement", "support", "supports", "supported",
    "supporting", "grant", "grants", "granted", "proceed", "proceeds", "proceeding",
    "favorable", "favourable", "welcome", "select", "selected", "adopt", "adoption",
    # negative-like lexical shortcuts
    "no", "disagree", "disagrees", "disagreed", "disagreement", "reject", "rejects",
    "rejected", "rejection", "refuse", "refuses", "refused", "refusal", "deny", "denies",
    "denied", "denial", "oppose", "opposes", "opposed", "opposition", "decline", "declines",
    "declined", "disallow", "disallowed", "block", "blocked", "unfavorable", "unfavourable",
    # neutral-like lexical shortcuts
    "abstain", "abstains", "abstained", "abstention", "undecided", "defer", "defers",
    "deferred", "deferring", "unresolved", "neither", "pending", "withhold", "withholds",
    "withheld", "withholding", "postpone", "postpones", "postponed", "noncommittal",
}

COMPLIANCE_PROXY_LEXEMES = {
    "request", "requests", "requested", "permission", "permissions", "approve", "approval",
    "authorized", "authorize", "authorization", "comply", "compliance", "obey", "instruction",
    "instructions", "policy", "policies", "rule", "rules", "mandatory", "mandate", "required",
    "requirement", "requirements", "must", "should", "allowed", "disallowed",
}

# Boilerplate/instruction words are excluded from lexical-overlap and class-marker diagnostics.
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "from", "with", "without",
    "is", "are", "was", "were", "be", "being", "been", "it", "its", "this", "that", "these",
    "those", "one", "two", "three", "as", "at", "by", "into", "than", "then", "if", "when",
    "while", "not", "do", "does", "did", "only", "exactly", "internally", "represent", "return",
    "emit", "output", "answer", "code", "codes", "class", "label", "labels", "temporary",
    "decision", "card", "situation", "state", "target", "semantic", "model", "facing", "no_think",
}
TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class AuditError(ValueError):
    pass


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _tokens(text: str) -> list[str]:
    return [m.group(0).lower() for m in TOKEN_RE.finditer(text)]


def content_tokens(text: str) -> set[str]:
    return {
        tok for tok in _tokens(text)
        if tok not in STOPWORDS and len(tok) > 1 and not tok.isdigit()
    }


def _sha256(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX64_RE.fullmatch(value))


def _row_text(row: dict[str, Any]) -> str:
    text = row.get("prompt")
    if not isinstance(text, str) or not text.strip():
        raise AuditError("MODEL_FACING_PROMPT_REQUIRED")
    declared = row.get("prompt_sha256")
    if declared is not None and declared != prompt_sha(text):
        raise AuditError("PROMPT_SHA256_MISMATCH")
    return text


def _target(row: dict[str, Any]) -> str:
    target = str(row.get("semantic_target") or row.get("semantic_class") or "").strip().upper()
    if target not in TARGET_SET:
        raise AuditError(f"SEMANTIC_TARGET_INVALID:{target or 'MISSING'}")
    return target


def _family(row: dict[str, Any]) -> str:
    value = row.get("family_group_id") or row.get("scenario_family_sha256") or row.get("family_id")
    if not isinstance(value, str) or not value.strip():
        raise AuditError("FAMILY_ID_REQUIRED")
    return value.strip()


def _extract_plan_rows(plan: Any, split: str) -> list[dict[str, Any]]:
    if not isinstance(plan, dict):
        raise AuditError(f"{split}_PLAN_OBJECT_REQUIRED")
    cases = plan.get("cases")
    if not isinstance(cases, list) or len(cases) != 9:
        raise AuditError(f"{split}_EXACTLY_NINE_CASES_REQUIRED")
    rows: list[dict[str, Any]] = []
    seen_cells: set[tuple[str, str]] = set()
    by_family: dict[str, list[dict[str, Any]]] = {}
    for raw in cases:
        if not isinstance(raw, dict):
            raise AuditError(f"{split}_CASE_OBJECT_REQUIRED")
        text = _row_text(raw)
        target = _target(raw)
        code = str(raw.get("output_code_identity") or "").strip().upper()
        if code not in {"A", "B", "C"}:
            raise AuditError(f"{split}_OUTPUT_CODE_INVALID:{code or 'MISSING'}")
        cell = (target, code)
        if cell in seen_cells:
            raise AuditError(f"{split}_DUPLICATE_TARGET_CODE_CELL:{target}:{code}")
        seen_cells.add(cell)
        family = _family(raw)
        row = {**raw, "prompt": text, "semantic_target": target, "audit_family_id": family}
        rows.append(row)
        by_family.setdefault(family, []).append(row)
    expected = {(target, code) for target in TARGETS for code in ("A", "B", "C")}
    if seen_cells != expected:
        raise AuditError(f"{split}_FULL_THREE_BY_THREE_FACTORIAL_REQUIRED")
    if len(by_family) < 3:
        raise AuditError(f"{split}_AT_LEAST_THREE_SCENARIO_FAMILIES_REQUIRED")
    for family, fam_rows in by_family.items():
        if {_target(row) for row in fam_rows} != TARGET_SET:
            raise AuditError(f"{split}_FAMILY_MISSING_TARGETS:{family}")
        if {str(row.get("output_code_identity")).upper() for row in fam_rows} != {"A", "B", "C"}:
            raise AuditError(f"{split}_FAMILY_MISSING_CODE_ROTATION:{family}")
    return rows


def _extract_basis_rows(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        rows = value.get("rows")
    else:
        rows = value
    if not isinstance(rows, list) or len(rows) < 18:
        raise AuditError("BASIS_AT_LEAST_EIGHTEEN_ROWS_REQUIRED")
    by_family: dict[str, list[dict[str, Any]]] = {}
    out: list[dict[str, Any]] = []
    prompt_hashes: set[str] = set()
    for raw in rows:
        if not isinstance(raw, dict):
            raise AuditError("BASIS_ROW_OBJECT_REQUIRED")
        text = _row_text(raw)
        target = _target(raw)
        family = _family(raw)
        sha = prompt_sha(text)
        if sha in prompt_hashes:
            raise AuditError("BASIS_PROMPTS_MUST_BE_UNIQUE")
        prompt_hashes.add(sha)
        row = {**raw, "prompt": text, "semantic_target": target, "audit_family_id": family}
        out.append(row)
        by_family.setdefault(family, []).append(row)
    if len(by_family) < 6:
        raise AuditError("BASIS_AT_LEAST_SIX_MATCHED_FAMILIES_REQUIRED")
    for family, fam_rows in by_family.items():
        if len(fam_rows) != 3 or {_target(row) for row in fam_rows} != TARGET_SET:
            raise AuditError(f"BASIS_FAMILY_MUST_BE_EXACT_TRIAD:{family}")
    return out


def _forbidden_hits(rows: list[dict[str, Any]], *, include_compliance: bool) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    forbidden = set(CANONICAL_LABELS) | set(POLE_PROXY_LEXEMES)
    if include_compliance:
        forbidden |= set(COMPLIANCE_PROXY_LEXEMES)
    for row in rows:
        tokens = set(_tokens(row["prompt"]))
        overlap = sorted(tokens & forbidden)
        if overlap:
            hits.append({
                "family_id": row["audit_family_id"],
                "semantic_target": row["semantic_target"],
                "hits": overlap,
            })
    return hits


def _class_marker_recurrence(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    by_family: dict[str, dict[str, set[str]]] = {}
    for row in rows:
        by_family.setdefault(row["audit_family_id"], {})[row["semantic_target"]] = content_tokens(row["prompt"])
    recurrence: dict[str, dict[str, int]] = {target: {} for target in TARGETS}
    for target in TARGETS:
        for family, target_tokens in by_family.items():
            if target not in target_tokens:
                continue
            others = set().union(*(toks for cls, toks in target_tokens.items() if cls != target))
            unique = target_tokens[target] - others
            for tok in unique:
                recurrence[target][tok] = recurrence[target].get(tok, 0) + 1
    return recurrence


def _aggregate(rows: list[dict[str, Any]]) -> set[str]:
    return set().union(*(content_tokens(row["prompt"]) for row in rows)) if rows else set()


def _family_token_sets(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["audit_family_id"], []).append(row)
    return {family: _aggregate(fam_rows) for family, fam_rows in grouped.items()}


def _family_specific_token_sets(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Remove stage-wide structural boilerplate before lexical-family comparisons.

    Tokens recurring in at least half of the scenario families are treated as shared
    carrier/instruction skeleton.  Class-predictive recurrence is audited separately, so
    this cannot make a repeated semantic shortcut disappear from the dedicated marker gate.
    """
    families = _family_token_sets(rows)
    if not families:
        return {}
    counts: dict[str, int] = {}
    for tokens in families.values():
        for tok in tokens:
            counts[tok] = counts.get(tok, 0) + 1
    structural_cutoff = max(2, math.ceil(len(families) / 2))
    structural = {tok for tok, count in counts.items() if count >= structural_cutoff}
    return {family: tokens - structural for family, tokens in families.items()}


def _stage_specific_tokens(rows: list[dict[str, Any]]) -> set[str]:
    families = _family_specific_token_sets(rows)
    return set().union(*families.values()) if families else set()


def _pairwise_family_overlap(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families = _family_specific_token_sets(rows)
    names = sorted(families)
    out: list[dict[str, Any]] = []
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            out.append({
                "left_family": left,
                "right_family": right,
                "content_jaccard": _jaccard(families[left], families[right]),
            })
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))


def audit(payload: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    diagnostics: dict[str, Any] = {}
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["SCHEMA_INVALID"],
            "runtime_credit_minted": False,
            "canonical_semantics_promotion": False,
        }

    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    max_cross_jaccard = float(config.get("max_cross_split_content_jaccard", 0.10))
    max_family_jaccard = float(config.get("max_within_stage_family_content_jaccard", 0.25))
    max_marker_families = int(config.get("max_recurring_class_marker_families", 1))
    include_compliance = config.get("ban_generic_compliance_markers", True) is True
    if not (0.0 <= max_cross_jaccard <= 1.0):
        failures.append("MAX_CROSS_SPLIT_JACCARD_OUT_OF_RANGE")
    if not (0.0 <= max_family_jaccard <= 1.0):
        failures.append("MAX_WITHIN_STAGE_FAMILY_JACCARD_OUT_OF_RANGE")
    if max_marker_families < 1:
        failures.append("MAX_RECURRING_CLASS_MARKER_FAMILIES_INVALID")

    try:
        basis = _extract_basis_rows(payload.get("basis_design"))
        calibration = _extract_plan_rows(payload.get("calibration_plan"), "CALIBRATION")
        holdout = _extract_plan_rows(payload.get("holdout_plan"), "HOLDOUT")
    except AuditError as exc:
        failures.append(str(exc))
        basis, calibration, holdout = [], [], []

    if basis and calibration and holdout:
        for name, rows in (("BASIS", basis), ("CALIBRATION", calibration), ("HOLDOUT", holdout)):
            hits = _forbidden_hits(rows, include_compliance=include_compliance)
            diagnostics[f"{name.lower()}_forbidden_hits"] = hits
            if hits:
                failures.append(f"{name}_MODEL_FACING_LEXICAL_SHORTCUT_PRESENT")

        for name, rows in (("BASIS", basis), ("CALIBRATION", calibration), ("HOLDOUT", holdout)):
            family_overlap = _pairwise_family_overlap(rows)
            diagnostics[f"{name.lower()}_family_pairwise_content_jaccard"] = family_overlap
            if any(row["content_jaccard"] > max_family_jaccard for row in family_overlap):
                failures.append(f"{name}_LEXICAL_FAMILIES_NOT_DISJOINT_ENOUGH")

        recurrence = _class_marker_recurrence(basis)
        diagnostics["basis_class_marker_recurrence"] = recurrence
        repeated = {
            target: sorted((tok, count) for tok, count in counts.items() if count > max_marker_families)
            for target, counts in recurrence.items()
        }
        repeated = {target: rows for target, rows in repeated.items() if rows}
        diagnostics["basis_repeated_class_markers"] = repeated
        if repeated:
            failures.append("BASIS_RECURRING_CLASS_PREDICTIVE_LEXEMES_PRESENT")

        sets = {
            "basis": _stage_specific_tokens(basis),
            "calibration": _stage_specific_tokens(calibration),
            "holdout": _stage_specific_tokens(holdout),
        }
        overlap = {
            "basis_calibration": _jaccard(sets["basis"], sets["calibration"]),
            "basis_holdout": _jaccard(sets["basis"], sets["holdout"]),
            "calibration_holdout": _jaccard(sets["calibration"], sets["holdout"]),
        }
        diagnostics["content_jaccard"] = overlap
        diagnostics["content_token_counts"] = {name: len(tokens) for name, tokens in sets.items()}
        for pair, value in overlap.items():
            if value > max_cross_jaccard:
                failures.append(f"CROSS_SPLIT_LEXICAL_OVERLAP_TOO_HIGH:{pair}:{value:.6f}")

        # Exact model-facing prompt reuse is always forbidden across evidence stages.
        stage_hashes = {
            "basis": {prompt_sha(row["prompt"]) for row in basis},
            "calibration": {prompt_sha(row["prompt"]) for row in calibration},
            "holdout": {prompt_sha(row["prompt"]) for row in holdout},
        }
        if stage_hashes["basis"] & stage_hashes["calibration"]:
            failures.append("BASIS_CALIBRATION_PROMPT_REUSE")
        if stage_hashes["basis"] & stage_hashes["holdout"]:
            failures.append("BASIS_HOLDOUT_PROMPT_REUSE")
        if stage_hashes["calibration"] & stage_hashes["holdout"]:
            failures.append("CALIBRATION_HOLDOUT_PROMPT_REUSE")

    material = {
        "schema": SCHEMA,
        "config": {
            "max_cross_split_content_jaccard": max_cross_jaccard,
            "max_within_stage_family_content_jaccard": max_family_jaccard,
            "max_recurring_class_marker_families": max_marker_families,
            "ban_generic_compliance_markers": include_compliance,
        },
        "diagnostics": diagnostics,
    }
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "diagnostics": diagnostics,
        "audit_receipt_sha256": canonical_sha(material),
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "Text-level leakage/overlap audit only. PASS demonstrates that the submitted model-facing "
            "basis/calibration/holdout texts satisfy the declared lexical-abstraction fences; it does "
            "not demonstrate causal steering or semantic truth."
        ),
    }
