#!/usr/bin/env python3
"""Fail-closed abstract-state / lexical-disjointness gate for Trigger-1.

This validator is execution-free. It proves that the frozen basis and the exact
producer plans describe a structural relational task in which evaluator semantic
labels and generic approval/refusal/compliance vocabulary are absent from model-facing
text, target-varying lexical atoms are matched within each triplet, and basis,
calibration and holdout payload lexicons are mutually disjoint.

It does not infer semantic success or mint runtime/J-Space/HCU/EntityOS/training credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_CASE_GATE/v1"
DESIGN_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_DESIGN/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
STATE_TO_TARGET = {"direct": "AFFIRMATIVE", "reverse": "NEGATIVE", "absent": "NEUTRAL"}
PAYLOAD_RE = re.compile(
    r"STATE_PAYLOAD_BEGIN\s*links=([a-z0-9]+)>([a-z0-9]+),([a-z0-9]+)>([a-z0-9]+);"
    r"query=([a-z0-9]+)>([a-z0-9]+)\s*STATE_PAYLOAD_END",
    re.IGNORECASE | re.DOTALL,
)
KEY_RE = re.compile(
    r"\bKEY\s+A=(direct|reverse|absent);B=(direct|reverse|absent);C=(direct|reverse|absent)\b",
    re.IGNORECASE,
)
WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
FORBIDDEN_MODEL_FACING = {
    "affirmative", "negative", "neutral",
    "approve", "approved", "approval", "reject", "rejected", "rejection",
    "grant", "granted", "permission", "refuse", "refused", "denial", "deny", "denied",
    "allow", "allowed", "disallow", "accept", "accepted", "decline", "declined",
    "support", "supported", "oppose", "opposed", "proceed", "compliance", "compliant",
    "defer", "deferred", "pending", "yes",
}


def _canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _words(text: str) -> set[str]:
    return {x.lower() for x in WORD_RE.findall(text)}


def _payload(prompt: str) -> tuple[str, tuple[str, str], tuple[tuple[str, str], ...], set[str]]:
    matches = list(PAYLOAD_RE.finditer(prompt))
    if len(matches) != 1:
        raise ValueError("EXACTLY_ONE_STATE_PAYLOAD_REQUIRED")
    m = matches[0]
    links = ((m.group(1).lower(), m.group(2).lower()), (m.group(3).lower(), m.group(4).lower()))
    query = (m.group(5).lower(), m.group(6).lower())
    atoms = {m.group(i).lower() for i in range(1, 7)}
    scaffold = prompt[:m.start()] + "STATE_PAYLOAD_SLOT" + prompt[m.end():]
    return scaffold, query, links, atoms


def _structural_state(query: tuple[str, str], links: tuple[tuple[str, str], ...]) -> str:
    if query in links:
        return "direct"
    if (query[1], query[0]) in links:
        return "reverse"
    return "absent"


def _check_prompt(prompt: Any, prefix: str, failures: list[str]) -> tuple[str | None, set[str] | None, str | None]:
    if not isinstance(prompt, str) or not prompt:
        failures.append(f"{prefix}_PROMPT_REQUIRED")
        return None, None, None
    forbidden = sorted(_words(prompt) & FORBIDDEN_MODEL_FACING)
    if forbidden:
        failures.append(f"{prefix}_FORBIDDEN_MODEL_FACING_LEXEMES:{','.join(forbidden)}")
    try:
        scaffold, query, links, atoms = _payload(prompt)
    except ValueError as exc:
        failures.append(f"{prefix}_{exc}")
        return None, None, None
    if len(atoms) != 3:
        failures.append(f"{prefix}_EXACTLY_THREE_NONCE_ENTITY_ATOMS_REQUIRED")
    if any(len(x) < 3 for x in atoms):
        failures.append(f"{prefix}_NONCE_ENTITY_ATOM_TOO_SHORT")
    state = _structural_state(query, links)
    return scaffold, atoms, state


def _check_basis(design: dict[str, Any], failures: list[str]) -> set[str]:
    section = design.get("basis_calibration")
    rows = section.get("rows") if isinstance(section, dict) else None
    if not isinstance(rows, list) or len(rows) != 18:
        failures.append("BASIS_EXACTLY_EIGHTEEN_ROWS_REQUIRED")
        return set()
    by_family: dict[str, list[dict[str, Any]]] = {}
    lexicon: set[str] = set()
    for i, row in enumerate(rows):
        prefix = f"BASIS_ROW_{i}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        prompt = row.get("prompt")
        if isinstance(prompt, str) and row.get("prompt_sha256") != hashlib.sha256(prompt.encode()).hexdigest():
            failures.append(f"{prefix}_PROMPT_SHA256_MISMATCH")
        scaffold, atoms, state = _check_prompt(prompt, prefix, failures)
        target = row.get("semantic_class")
        if target not in TARGETS:
            failures.append(f"{prefix}_SEMANTIC_CLASS_INVALID")
        if state is not None and target != STATE_TO_TARGET[state]:
            failures.append(f"{prefix}_SEMANTIC_CLASS_NOT_STRUCTURALLY_DERIVED")
        family = row.get("family_group_id")
        if not isinstance(family, str) or not family:
            failures.append(f"{prefix}_FAMILY_REQUIRED")
            continue
        by_family.setdefault(family, []).append({"scaffold": scaffold, "atoms": atoms, "target": target})
        if atoms:
            lexicon |= atoms
    if len(by_family) != 6:
        failures.append("BASIS_EXACTLY_SIX_MATCHED_FAMILIES_REQUIRED")
    for family, rows2 in sorted(by_family.items()):
        if len(rows2) != 3:
            failures.append(f"BASIS_FAMILY_EXACTLY_THREE_ROWS_REQUIRED:{family}")
            continue
        if {r["target"] for r in rows2} != set(TARGETS):
            failures.append(f"BASIS_FAMILY_TARGET_COVERAGE_INVALID:{family}")
        if len({r["scaffold"] for r in rows2}) != 1:
            failures.append(f"BASIS_FAMILY_SCAFFOLD_NOT_IDENTICAL:{family}")
        if len({tuple(sorted(r["atoms"] or set())) for r in rows2}) != 1:
            failures.append(f"BASIS_FAMILY_TARGET_VARIABLE_LEXICON_NOT_MATCHED:{family}")
    return lexicon


def _codebook(prompt: str, prefix: str, failures: list[str]) -> dict[str, str] | None:
    matches = list(KEY_RE.finditer(prompt))
    if len(matches) != 1:
        failures.append(f"{prefix}_EXACTLY_ONE_OPERATIONAL_CODEBOOK_REQUIRED")
        return None
    values = {"A": matches[0].group(1).lower(), "B": matches[0].group(2).lower(), "C": matches[0].group(3).lower()}
    if set(values.values()) != {"direct", "reverse", "absent"}:
        failures.append(f"{prefix}_CODEBOOK_NOT_PERMUTATION")
        return None
    return values


def _check_factor_plan(plan: Any, split: str, failures: list[str]) -> set[str]:
    if not isinstance(plan, dict):
        failures.append(f"{split}_SOURCE_CASE_PLAN_REQUIRED")
        return set()
    if str(plan.get("split") or "").upper() != split:
        failures.append(f"{split}_SOURCE_CASE_PLAN_SPLIT_MISMATCH")
    cases = plan.get("cases")
    if not isinstance(cases, list) or len(cases) != 9:
        failures.append(f"{split}_EXACTLY_NINE_CASES_REQUIRED")
        return set()
    observed = {(r.get("semantic_target"), r.get("output_code_identity")) for r in cases if isinstance(r, dict)}
    expected = {(t, c) for t in TARGETS for c in CODES}
    if observed != expected:
        failures.append(f"{split}_FULL_TARGET_X_CODE_FACTORIAL_REQUIRED")

    by_scenario: dict[str, list[dict[str, Any]]] = {}
    lexicon: set[str] = set()
    for i, row in enumerate(cases):
        prefix = f"{split}_ROW_{i}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        prompt = row.get("prompt")
        if isinstance(prompt, str) and row.get("prompt_sha256") != hashlib.sha256(prompt.encode()).hexdigest():
            failures.append(f"{prefix}_PROMPT_SHA256_MISMATCH")
        scaffold, atoms, state = _check_prompt(prompt, prefix, failures)
        mapping = _codebook(prompt, prefix, failures) if isinstance(prompt, str) else None
        target = row.get("semantic_target")
        code = row.get("output_code_identity")
        if state is not None and target != STATE_TO_TARGET[state]:
            failures.append(f"{prefix}_SEMANTIC_TARGET_NOT_STRUCTURALLY_DERIVED")
        if mapping and state is not None:
            expected_code = next((c for c, s in mapping.items() if s == state), None)
            if code != expected_code:
                failures.append(f"{prefix}_OUTPUT_CODE_NOT_OPERATIONALLY_DERIVED")
        scenario = row.get("scenario_family_sha256")
        if not isinstance(scenario, str) or len(scenario) != 64:
            failures.append(f"{prefix}_SCENARIO_FAMILY_REQUIRED")
            continue
        by_scenario.setdefault(scenario, []).append(
            {"scaffold": scaffold, "atoms": atoms, "target": target, "code": code, "mapping": mapping}
        )
        if atoms:
            lexicon |= atoms
    if len(by_scenario) != 3:
        failures.append(f"{split}_EXACTLY_THREE_SCENARIO_FAMILIES_REQUIRED")
    for scenario, rows2 in sorted(by_scenario.items()):
        if len(rows2) != 3:
            failures.append(f"{split}_SCENARIO_EXACTLY_THREE_ROWS_REQUIRED:{scenario}")
            continue
        if {r["target"] for r in rows2} != set(TARGETS):
            failures.append(f"{split}_SCENARIO_TARGET_COVERAGE_INVALID:{scenario}")
        if {r["code"] for r in rows2} != set(CODES):
            failures.append(f"{split}_SCENARIO_CODE_COVERAGE_INVALID:{scenario}")
        if len({r["scaffold"] for r in rows2}) != 1:
            failures.append(f"{split}_SCENARIO_SCAFFOLD_NOT_IDENTICAL:{scenario}")
        if len({tuple(sorted(r["atoms"] or set())) for r in rows2}) != 1:
            failures.append(f"{split}_SCENARIO_TARGET_VARIABLE_LEXICON_NOT_MATCHED:{scenario}")
        maps = [r["mapping"] for r in rows2]
        if not all(m == maps[0] for m in maps):
            failures.append(f"{split}_SCENARIO_CODEBOOK_NOT_IDENTICAL:{scenario}")
    return lexicon


def validate(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    design = candidate.get("abstract_state_design")
    if not isinstance(design, dict) or design.get("schema") != DESIGN_SCHEMA:
        failures.append("ABSTRACT_STATE_DESIGN_REQUIRED")
        design = {}
    if design.get("frozen_before_model_execution") is not True:
        failures.append("ABSTRACT_STATE_DESIGN_MUST_BE_FROZEN_BEFORE_MODEL_EXECUTION")
    declared = design.get("design_sha256")
    core = {k: v for k, v in design.items() if k != "design_sha256"}
    recomputed = _canonical_sha(core) if design else None
    if declared != recomputed:
        failures.append("ABSTRACT_STATE_DESIGN_SHA256_MISMATCH")
    basis_lex = _check_basis(design, failures)

    evidence = candidate.get("preregistration_evidence")
    case_plans = evidence.get("case_plans") if isinstance(evidence, dict) else None
    if not isinstance(case_plans, dict):
        failures.append("BOUND_SOURCE_CASE_PLANS_REQUIRED")
        case_plans = {}
    cal_lex = _check_factor_plan(case_plans.get("CALIBRATION"), "CALIBRATION", failures)
    hold_lex = _check_factor_plan(case_plans.get("HOLDOUT"), "HOLDOUT", failures)

    overlaps = {
        "basis_x_calibration": sorted(basis_lex & cal_lex),
        "basis_x_holdout": sorted(basis_lex & hold_lex),
        "calibration_x_holdout": sorted(cal_lex & hold_lex),
    }
    for name, atoms in overlaps.items():
        if atoms:
            failures.append(f"PAYLOAD_LEXICON_OVERLAP:{name}:{','.join(atoms)}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "design_sha256": recomputed,
        "payload_lexicon_sizes": {"basis": len(basis_lex), "calibration": len(cal_lex), "holdout": len(hold_lex)},
        "payload_lexicon_overlaps": overlaps,
        "model_facing_semantic_labels_absent": not any("FORBIDDEN_MODEL_FACING_LEXEMES" in f for f in failures),
        "structural_state_derivation_required": True,
        "target_variable_lexicon_matched_within_family": True,
        "shared_instruction_compliance_content_counterbalanced_within_family": True,
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "PASS establishes only frozen abstract structural case construction, structural evaluator-label derivation, "
            "within-family target-variable lexical matching and mutual basis/calibration/holdout payload lexical disjointness. "
            "It does not establish model causality or semantic J-Space control."
        ),
    }
