#!/usr/bin/env python3
"""Fail-closed abstraction/deconfounding gate for Trigger-1 J-Space promotion.

This gate closes three confounds that survive output-code counterbalancing:
1) direct semantic-pole lexical leakage or generic compliance carriers;
2) caller-asserted lexical-family metadata without content-derived disjointness; and
3) causal overclaim across the old last-token hook and native llama.cpp cvec broadcast.

The current producer's exact CALIBRATION/HOLDOUT source case plans are the evaluation
text authority. This gate recomputes lexical families from their raw prompt contents,
requires a separately frozen six-family native-Q8 basis prompt universe, and requires a
label-only nuisance intervention over the same case universe.

It is execution-free and non-minting. External runtime receipt authenticity and the
actual scientific measurements remain separate boundaries.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_SEMANTIC_ABSTRACTION_GATE/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_ABSTRACTION_ATTESTATION/v1"
LEXICAL_FAMILY_SCHEMA = "CLAY_TRIGGER1_CONTENT_LEXICAL_FAMILY/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
SPLITS = ("CALIBRATION", "HOLDOUT")
NUISANCE_CONTROL = "LABEL_ONLY_NUISANCE_VECTOR"

DIRECT_POLE_LEXEMES = frozenset({
    "affirmative", "negative", "neutral", "yes", "no", "agree", "agrees", "agreed",
    "agreement", "disagree", "disagrees", "disagreed", "disagreement", "approve",
    "approves", "approved", "approving", "approval", "reject", "rejects", "rejected",
    "rejecting", "rejection", "accept", "accepts", "accepted", "accepting", "acceptance",
    "decline", "declines", "declined", "declining", "refuse", "refuses", "refused",
    "refusing", "refusal", "grant", "grants", "granted", "granting", "allow", "allows",
    "allowed", "allowing", "deny", "denies", "denied", "denying", "denial", "support",
    "supports", "supported", "supporting", "oppose", "opposes", "opposed", "opposing",
    "opposition", "favor", "favors", "favored", "favoring", "favour", "favours",
    "favoured", "favouring", "endorse", "endorses", "endorsed", "endorsing",
    "endorsement", "permission", "permit", "permits", "permitted", "disallow",
    "disallows", "disallowed", "abstain", "abstains", "abstained", "abstention",
    "undecided", "noncommittal", "noncommittally", "select", "selects", "selected",
    "selecting", "selection", "proceed", "proceeds", "proceeded", "proceeding", "continue",
    "continues", "continued", "continuing", "stop", "stops", "stopped", "stopping",
    "defer", "defers", "deferred", "deferring", "deferment", "block", "blocks", "blocked",
    "blocking",
})

STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "into", "onto", "one", "that", "this", "its",
    "their", "they", "them", "then", "than", "while", "where", "when", "which", "who",
    "has", "have", "had", "was", "were", "are", "is", "be", "being", "been", "to", "of",
    "in", "on", "at", "by", "as", "or", "if", "but", "not", "yet", "now", "still",
    "a", "an", "do", "only", "internally", "represent", "representation", "state",
    "answer", "output", "emit", "code", "token", "class", "label", "model", "facing",
    "requested", "request", "case", "scenario", "semantic", "decision", "mapping", "means",
    "symbol", "match", "matching", "record", "recorded", "outcome", "following", "choose",
    "back", "toward", "upon", "beside", "near", "move", "moves", "moved", "moving",
    "return", "returns", "returned", "returning", "wait", "waits", "waited", "waiting",
    "stay", "stays", "stayed", "staying", "roll", "rolls", "rolled", "rolling", "show",
    "shows", "shown", "turn", "turns", "turned", "travel", "travels", "traveled",
    "travelling", "hold", "holds", "held", "remain", "remains", "rest", "rests",
})
TOKEN_RE = re.compile(r"[A-Za-z]+")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def prompt_sha(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def lexical_tokens(prompt: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_RE.findall(prompt)
        if len(token) >= 3 and token.lower() not in STOPWORDS
    }


def lexical_family_sha(tokens: set[str] | list[str]) -> str:
    return canonical_sha({"schema": LEXICAL_FAMILY_SCHEMA, "tokens": sorted(set(tokens))})


def _prompt_leaks(prompt: str) -> list[str]:
    words = {w.lower() for w in TOKEN_RE.findall(prompt)}
    return sorted(words & DIRECT_POLE_LEXEMES)


def _normalize_basis_row(raw: Any, index: int, failures: list[str]) -> dict[str, Any] | None:
    prefix = f"BASIS_ROW_{index}"
    if not isinstance(raw, dict):
        failures.append(f"{prefix}_OBJECT_REQUIRED")
        return None
    prompt = raw.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        failures.append(f"{prefix}_PROMPT_REQUIRED")
        return None
    target = str(raw.get("semantic_target") or "").strip().upper()
    family_id = raw.get("family_id")
    if target not in TARGETS:
        failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
    if not isinstance(family_id, str) or not family_id.strip():
        failures.append(f"{prefix}_FAMILY_ID_REQUIRED")
    actual_prompt_sha = prompt_sha(prompt)
    if raw.get("prompt_sha256") != actual_prompt_sha:
        failures.append(f"{prefix}_PROMPT_SHA256_MISMATCH")
    leaks = _prompt_leaks(prompt)
    if leaks:
        failures.append(f"{prefix}_DIRECT_POLE_LEXEME_LEAK:{','.join(leaks)}")
    tokens = lexical_tokens(prompt)
    actual_lexical = lexical_family_sha(tokens)
    if raw.get("lexical_content_sha256") != actual_lexical:
        failures.append(f"{prefix}_LEXICAL_CONTENT_SHA256_MISMATCH")
    return {
        "family_id": family_id.strip() if isinstance(family_id, str) else None,
        "semantic_target": target,
        "prompt_sha256": actual_prompt_sha,
        "lexical_content_sha256": actual_lexical,
        "tokens": tokens,
    }


def _audit_basis(raw_rows: Any, failures: list[str]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    if not isinstance(raw_rows, list) or len(raw_rows) != 18:
        failures.append("BASIS_EXACTLY_18_ROWS_REQUIRED")
        return [], {}
    rows = [r for i, raw in enumerate(raw_rows) if (r := _normalize_basis_row(raw, i, failures)) is not None]
    families: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        families.setdefault(str(row["family_id"]), []).append(row)
    if len(families) != 6:
        failures.append("BASIS_EXACTLY_SIX_FAMILIES_REQUIRED")
    for family, members in families.items():
        if len(members) != 3 or {m["semantic_target"] for m in members} != set(TARGETS):
            failures.append(f"BASIS_FAMILY_NOT_COMPLETE_TRIPLET:{family}")
    token_sets = {family: set().union(*(m["tokens"] for m in members)) for family, members in families.items()}
    names = sorted(token_sets)
    for i, left in enumerate(names):
        for right in names[i + 1:]:
            overlap = sorted(token_sets[left] & token_sets[right])
            if overlap:
                failures.append(f"BASIS_CROSS_FAMILY_CONTENT_OVERLAP:{left}:{right}:{','.join(overlap)}")
    return rows, token_sets


def _source_plan_cases(candidate: dict[str, Any], split: str, failures: list[str]) -> list[dict[str, Any]]:
    evidence = candidate.get("preregistration_evidence")
    plans = evidence.get("case_plans") if isinstance(evidence, dict) else None
    plan = plans.get(split) if isinstance(plans, dict) else None
    if not isinstance(plan, dict):
        failures.append(f"{split}_SOURCE_CASE_PLAN_REQUIRED_FOR_ABSTRACTION")
        return []
    cases = plan.get("cases")
    if not isinstance(cases, list) or len(cases) != 9:
        failures.append(f"{split}_SOURCE_CASE_PLAN_EXACTLY_NINE_CASES_REQUIRED")
        return []
    return cases


def _audit_eval_split(candidate: dict[str, Any], split: str, failures: list[str]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    cases = _source_plan_cases(candidate, split, failures)
    rows: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, raw in enumerate(cases):
        prefix = f"{split}_SOURCE_CASE_{index}"
        if not isinstance(raw, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        case_id = raw.get("case_id")
        prompt = raw.get("prompt")
        target = str(raw.get("semantic_target") or "").strip().upper()
        scenario_sha = raw.get("scenario_family_sha256")
        declared_lexical_sha = raw.get("lexical_family_sha256")
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
            continue
        if case_id in ids:
            failures.append(f"{prefix}_DUPLICATE_CASE_ID")
        ids.add(case_id)
        if not isinstance(prompt, str) or not prompt.strip():
            failures.append(f"{prefix}_PROMPT_REQUIRED")
            continue
        if raw.get("prompt_sha256") != prompt_sha(prompt):
            failures.append(f"{prefix}_PROMPT_SHA256_MISMATCH")
        if target not in TARGETS:
            failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
        if not _sha256(scenario_sha):
            failures.append(f"{prefix}_SCENARIO_FAMILY_SHA256_REQUIRED")
        if not _sha256(declared_lexical_sha):
            failures.append(f"{prefix}_LEXICAL_FAMILY_SHA256_REQUIRED")
        leaks = _prompt_leaks(prompt)
        if leaks:
            failures.append(f"{prefix}_DIRECT_POLE_LEXEME_LEAK:{','.join(leaks)}")
        rows.append({
            "split": split,
            "case_id": case_id,
            "semantic_target": target,
            "prompt_sha256": prompt_sha(prompt),
            "scenario_family_sha256": str(scenario_sha),
            "declared_lexical_family_sha256": str(declared_lexical_sha),
            "tokens": lexical_tokens(prompt),
        })

    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_scenario.setdefault(row["scenario_family_sha256"], []).append(row)
    if len(by_scenario) != 3:
        failures.append(f"{split}_EXACTLY_THREE_SCENARIO_FAMILIES_REQUIRED")
    token_sets: dict[str, set[str]] = {}
    for scenario_sha, members in by_scenario.items():
        if len(members) != 3 or {m["semantic_target"] for m in members} != set(TARGETS):
            failures.append(f"{split}_SCENARIO_NOT_COMPLETE_TARGET_TRIPLET:{scenario_sha}")
        union = set().union(*(m["tokens"] for m in members))
        derived = lexical_family_sha(union)
        token_sets[scenario_sha] = union
        if {m["declared_lexical_family_sha256"] for m in members} != {derived}:
            failures.append(f"{split}_LEXICAL_FAMILY_NOT_CONTENT_DERIVED:{scenario_sha}")
    return rows, token_sets


def _pairwise_disjoint(name_a: str, a: set[str], name_b: str, b: set[str], failures: list[str]) -> None:
    overlap = sorted(a & b)
    if overlap:
        failures.append(f"LEXICAL_SPLIT_OVERLAP:{name_a}:{name_b}:{','.join(overlap)}")


def _validate_nuisance(att: dict[str, Any], case_keys: set[tuple[str, str]], failures: list[str]) -> dict[str, Any] | None:
    nuisance = att.get("lexical_nuisance_control")
    if not isinstance(nuisance, dict):
        failures.append("LEXICAL_NUISANCE_CONTROL_REQUIRED")
        return None
    if nuisance.get("control_identity") != NUISANCE_CONTROL:
        failures.append("LEXICAL_NUISANCE_CONTROL_IDENTITY_MISMATCH")
    if nuisance.get("construction") != "DIRECT_POLE_LEXEMES_ONLY":
        failures.append("LEXICAL_NUISANCE_CONSTRUCTION_MUST_BE_DIRECT_POLE_LEXEMES_ONLY")
    if nuisance.get("excluded_from_semantic_basis") is not True:
        failures.append("LEXICAL_NUISANCE_MUST_BE_EXCLUDED_FROM_SEMANTIC_BASIS")

    receipts = nuisance.get("runtime_receipts")
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    if not isinstance(receipts, list):
        failures.append("LEXICAL_NUISANCE_RUNTIME_RECEIPTS_REQUIRED")
    else:
        for i, row in enumerate(receipts):
            prefix = f"LEXICAL_NUISANCE_RECEIPT_{i}"
            if not isinstance(row, dict):
                failures.append(f"{prefix}_OBJECT_REQUIRED")
                continue
            split = str(row.get("split") or "").strip().upper()
            case_id = row.get("case_id")
            digest = row.get("runtime_receipt_sha256")
            if split not in SPLITS or not isinstance(case_id, str) or not case_id:
                failures.append(f"{prefix}_CASE_IDENTITY_INVALID")
                continue
            key = (split, case_id)
            if not _sha256(digest):
                failures.append(f"{prefix}_RUNTIME_RECEIPT_SHA256_INVALID")
                continue
            if key in seen:
                failures.append(f"{prefix}_DUPLICATE_CASE")
                continue
            seen.add(key)
            normalized.append({"split": split, "case_id": case_id, "runtime_receipt_sha256": digest})
        if seen != case_keys:
            failures.append("LEXICAL_NUISANCE_RECEIPT_CASE_UNIVERSE_MISMATCH")

    analysis = nuisance.get("interaction_analysis")
    analysis_material = None
    if not isinstance(analysis, dict):
        failures.append("LEXICAL_NUISANCE_INTERACTION_ANALYSIS_REQUIRED")
    else:
        try:
            candidate_effect = float(analysis.get("candidate_semantic_interaction"))
            nuisance_effect = float(analysis.get("nuisance_semantic_interaction"))
            sign_flip_effect = float(analysis.get("sign_flip_semantic_interaction"))
            max_fraction = float(analysis.get("max_abs_nuisance_fraction"))
        except (TypeError, ValueError):
            failures.append("LEXICAL_NUISANCE_INTERACTION_NUMERICS_REQUIRED")
        else:
            if not all(math.isfinite(v) for v in (candidate_effect, nuisance_effect, sign_flip_effect, max_fraction)):
                failures.append("LEXICAL_NUISANCE_INTERACTION_NUMERICS_FINITE_REQUIRED")
            if candidate_effect <= 0:
                failures.append("CANDIDATE_SEMANTIC_INTERACTION_MUST_BE_POSITIVE")
            if sign_flip_effect >= 0:
                failures.append("SIGN_FLIP_SEMANTIC_INTERACTION_MUST_REVERSE")
            if not (0.0 <= max_fraction <= 0.5):
                failures.append("MAX_ABS_NUISANCE_FRACTION_MUST_BE_BETWEEN_ZERO_AND_HALF")
            if candidate_effect > 0 and abs(nuisance_effect) > max_fraction * candidate_effect:
                failures.append("LEXICAL_NUISANCE_REPRODUCES_TOO_MUCH_SEMANTIC_INTERACTION")
            for key in ("analysis_implementation_sha256", "analysis_result_receipt_sha256"):
                if not _sha256(analysis.get(key)):
                    failures.append(f"LEXICAL_NUISANCE_{key.upper()}_REQUIRED")
            analysis_material = {
                "candidate_semantic_interaction": candidate_effect,
                "nuisance_semantic_interaction": nuisance_effect,
                "sign_flip_semantic_interaction": sign_flip_effect,
                "max_abs_nuisance_fraction": max_fraction,
                "analysis_implementation_sha256": analysis.get("analysis_implementation_sha256"),
                "analysis_result_receipt_sha256": analysis.get("analysis_result_receipt_sha256"),
            }
            declared = analysis.get("analysis_binding_sha256")
            if not _sha256(declared) or declared != canonical_sha(analysis_material):
                failures.append("LEXICAL_NUISANCE_ANALYSIS_BINDING_SHA256_MISMATCH")
    return {"receipts": normalized, "analysis_material": analysis_material}


def _validate_native_semantics(att: dict[str, Any], failures: list[str]) -> dict[str, Any] | None:
    native = att.get("native_intervention_semantics")
    if not isinstance(native, dict):
        failures.append("NATIVE_INTERVENTION_SEMANTICS_REQUIRED")
        return None
    expected = {
        "basis_carrier": "QWEN3_0_6B_Q8_NATIVE_LAYER_INPUT_21",
        "actuation": "LLAMA_CPP_LLAMA_SET_ADAPTER_CVEC_LAYER20",
        "downstream_transport_endpoint": "QWEN3_0_6B_Q8_NATIVE_LAYER_INPUT_24",
        "promotion_evidence_path": "NATIVE_Q8_TO_NATIVE_CVEC_ONLY",
        "prior_last_token_witness_role": "DISCOVERY_ONLY",
    }
    for key, value in expected.items():
        if native.get(key) != value:
            failures.append(f"NATIVE_INTERVENTION_{key.upper()}_MISMATCH")
    if native.get("cross_method_causal_equivalence_claimed") is not False:
        failures.append("CROSS_METHOD_CAUSAL_EQUIVALENCE_MUST_NOT_BE_CLAIMED")
    if native.get("native_end_to_end_promotion_only") is not True:
        failures.append("NATIVE_END_TO_END_PROMOTION_ONLY_REQUIRED")
    for key in ("gguf_sha256", "llama_cpp_commit", "basis_packet_sha256", "downstream_transport_receipt_sha256"):
        if not _sha256(native.get(key)):
            failures.append(f"NATIVE_INTERVENTION_{key.upper()}_REQUIRED")
    return {key: native.get(key) for key in sorted(native)}


def adjudicate(candidate: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("CANDIDATE_OBJECT_REQUIRED")

    att = candidate.get("semantic_abstraction_attestation")
    if not isinstance(att, dict) or att.get("schema") != ATTESTATION_SCHEMA:
        failures.append("SEMANTIC_ABSTRACTION_ATTESTATION_REQUIRED")
        att = {}

    basis_rows, basis_families = _audit_basis(att.get("basis_rows"), failures)
    cal_rows, cal_families = _audit_eval_split(candidate, "CALIBRATION", failures)
    hold_rows, hold_families = _audit_eval_split(candidate, "HOLDOUT", failures)

    basis_tokens = set().union(*basis_families.values()) if basis_families else set()
    cal_tokens = set().union(*cal_families.values()) if cal_families else set()
    hold_tokens = set().union(*hold_families.values()) if hold_families else set()
    _pairwise_disjoint("BASIS", basis_tokens, "CALIBRATION", cal_tokens, failures)
    _pairwise_disjoint("BASIS", basis_tokens, "HOLDOUT", hold_tokens, failures)
    _pairwise_disjoint("CALIBRATION", cal_tokens, "HOLDOUT", hold_tokens, failures)

    basis_universe = canonical_sha([
        {
            "family_id": row["family_id"],
            "semantic_target": row["semantic_target"],
            "prompt_sha256": row["prompt_sha256"],
            "lexical_content_sha256": row["lexical_content_sha256"],
        }
        for row in sorted(basis_rows, key=lambda x: (str(x["family_id"]), x["semantic_target"]))
    ])
    derivation = candidate.get("vector_derivation")
    if not isinstance(derivation, dict):
        failures.append("VECTOR_DERIVATION_REQUIRED_FOR_ABSTRACTION_BINDING")
    elif derivation.get("label_free_basis_prompt_universe_sha256") != basis_universe:
        failures.append("VECTOR_DERIVATION_BASIS_PROMPT_UNIVERSE_MISMATCH")

    case_keys = {("CALIBRATION", r["case_id"]) for r in cal_rows} | {("HOLDOUT", r["case_id"]) for r in hold_rows}
    nuisance = _validate_nuisance(att, case_keys, failures)
    native = _validate_native_semantics(att, failures)

    audit_material = {
        "schema": ATTESTATION_SCHEMA,
        "basis_prompt_universe_sha256": basis_universe,
        "basis_content_tokens": sorted(basis_tokens),
        "calibration_content_tokens": sorted(cal_tokens),
        "holdout_content_tokens": sorted(hold_tokens),
        "case_keys": sorted([list(k) for k in case_keys]),
        "content_derived_calibration_lexical_families": sorted(cal_families),
        "content_derived_holdout_lexical_families": sorted(hold_families),
        "nuisance": nuisance,
        "native_intervention_semantics": native,
    }
    audit_sha = canonical_sha(audit_material)
    declared_audit = att.get("abstraction_audit_sha256")
    if not _sha256(declared_audit) or declared_audit != audit_sha:
        failures.append("SEMANTIC_ABSTRACTION_AUDIT_SHA256_MISMATCH")

    return {
        "schema": SCHEMA,
        "semantic_abstraction_candidate": not failures,
        "failures": sorted(set(failures)),
        "abstraction_audit_sha256": audit_sha,
        "basis_prompt_universe_sha256": basis_universe,
        "direct_pole_lexemes_forbidden_in_semantic_prompts": sorted(DIRECT_POLE_LEXEMES),
        "cross_split_content_overlap_required": 0,
        "content_derived_lexical_family_required": True,
        "lexical_nuisance_control_required": NUISANCE_CONTROL,
        "cross_method_causal_equivalence_required": False,
        "native_end_to_end_promotion_required": True,
        "canonical_credit_minted": False,
        "canonical_semantics_promotion": False,
        "jspace_model_runtime_credit": False,
        "whole_hcu_runtime_credit": False,
        "whole_entityos_hcu_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS means the candidate is structurally compatible with the hard abstraction test: the exact producer source-plan "
            "prompts and basis prompts are content-audited, direct pole lexemes are absent, declared lexical families are recomputed "
            "from prompt contents, basis/calibration/holdout content vocabularies are disjoint, a label-only nuisance control covers "
            "the same exact evaluation cases and fails to reproduce the candidate interaction within a preregistered bound, sign-flip "
            "reverses, and promotion relies only on the native Q8->native llama.cpp cvec path without asserting causal equivalence to "
            "the old last-token hook. External receipt authenticity and actual model measurements remain separate gates."
        ),
    }
