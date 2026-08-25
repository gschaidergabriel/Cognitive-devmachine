#!/usr/bin/env python3
"""Fail-closed abstraction/deconfounding gate for Trigger-1 J-Space promotion.

This gate addresses three confounds that survive output-code counterbalancing:
1) direct semantic-pole lexical leakage,
2) calibration/holdout lexical overlap or caller-asserted lexical-family metadata,
3) causal overclaim across the old last-token hook and native llama.cpp cvec broadcast.

It is execution-free and non-minting. It only validates evidence structure and declared
runtime bindings; external receipt authenticity remains a separate boundary.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_SEMANTIC_ABSTRACTION_GATE/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_SEMANTIC_ABSTRACTION_ATTESTATION/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
SPLITS = ("CALIBRATION", "HOLDOUT")
NUISANCE_CONTROL = "LABEL_ONLY_NUISANCE_VECTOR"

# Deliberately broad direct-pole vocabulary. These words may be used only to build the
# nuisance control, never in basis/calibration/holdout model-facing semantic prompts.
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

# Function words and experiment boilerplate do not count toward lexical identity. The
# content-token audit is intentionally conservative: all remaining alphabetic tokens of
# length >= 3 participate in cross-split disjointness.
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


def lexical_digest(prompt: str) -> str:
    return canonical_sha(sorted(lexical_tokens(prompt)))


def _normalize_prompt_row(
    raw: Any, *, prefix: str, require_case: bool, failures: list[str]
) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        failures.append(f"{prefix}_OBJECT_REQUIRED")
        return None
    prompt = raw.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        failures.append(f"{prefix}_PROMPT_REQUIRED")
        return None
    actual_sha = prompt_sha(prompt)
    if raw.get("prompt_sha256") != actual_sha:
        failures.append(f"{prefix}_PROMPT_SHA256_MISMATCH")
    target = str(raw.get("semantic_target") or "").strip().upper()
    if target not in TARGETS:
        failures.append(f"{prefix}_SEMANTIC_TARGET_INVALID")
    family = raw.get("family_id")
    if not isinstance(family, str) or not family.strip():
        failures.append(f"{prefix}_FAMILY_ID_REQUIRED")
    case_id = raw.get("case_id")
    split = str(raw.get("split") or "").strip().upper() if require_case else "BASIS"
    if require_case:
        if not isinstance(case_id, str) or not case_id.strip():
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
        if split not in SPLITS:
            failures.append(f"{prefix}_SPLIT_INVALID")

    words = {w.lower() for w in TOKEN_RE.findall(prompt)}
    leaked = sorted(words & DIRECT_POLE_LEXEMES)
    if leaked:
        failures.append(f"{prefix}_DIRECT_POLE_LEXEME_LEAK:{','.join(leaked)}")
    if any(t.lower() in prompt.lower() for t in TARGETS):
        failures.append(f"{prefix}_CANONICAL_TARGET_LABEL_LEAK")

    tokens = sorted(lexical_tokens(prompt))
    declared_lexical = raw.get("lexical_content_sha256")
    actual_lexical = canonical_sha(tokens)
    if declared_lexical != actual_lexical:
        failures.append(f"{prefix}_LEXICAL_CONTENT_SHA256_MISMATCH")

    return {
        "case_id": case_id.strip() if isinstance(case_id, str) else None,
        "split": split,
        "family_id": family.strip() if isinstance(family, str) else None,
        "semantic_target": target,
        "prompt_sha256": actual_sha,
        "lexical_content_sha256": actual_lexical,
        "tokens": tokens,
    }


def _audit_basis(raw_rows: Any, failures: list[str]) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    if not isinstance(raw_rows, list) or len(raw_rows) != 18:
        failures.append("BASIS_EXACTLY_18_ROWS_REQUIRED")
        return [], {}
    rows: list[dict[str, Any]] = []
    for i, raw in enumerate(raw_rows):
        row = _normalize_prompt_row(raw, prefix=f"BASIS_ROW_{i}", require_case=False, failures=failures)
        if row is not None:
            rows.append(row)
    families: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        families.setdefault(str(row["family_id"]), []).append(row)
    if len(families) != 6:
        failures.append("BASIS_EXACTLY_SIX_FAMILIES_REQUIRED")
    for family, members in families.items():
        if len(members) != 3 or {m["semantic_target"] for m in members} != set(TARGETS):
            failures.append(f"BASIS_FAMILY_NOT_COMPLETE_TRIPLET:{family}")
    token_sets = {family: set().union(*(set(m["tokens"]) for m in members)) for family, members in families.items()}
    # Strong anti-shortcut requirement: scenario families may share function words only.
    fam_names = sorted(token_sets)
    for i, left in enumerate(fam_names):
        for right in fam_names[i + 1:]:
            overlap = sorted(token_sets[left] & token_sets[right])
            if overlap:
                failures.append(f"BASIS_CROSS_FAMILY_CONTENT_OVERLAP:{left}:{right}:{','.join(overlap)}")
    return rows, token_sets


def _audit_eval_rows(
    raw_rows: Any, *, split: str, failures: list[str]
) -> tuple[list[dict[str, Any]], dict[str, set[str]]]:
    if not isinstance(raw_rows, list) or len(raw_rows) != 9:
        failures.append(f"{split}_EXACTLY_NINE_ROWS_REQUIRED")
        return [], {}
    rows: list[dict[str, Any]] = []
    for i, raw in enumerate(raw_rows):
        row = _normalize_prompt_row(raw, prefix=f"{split}_ROW_{i}", require_case=True, failures=failures)
        if row is not None:
            if row["split"] != split:
                failures.append(f"{split}_ROW_{i}_SPLIT_MISMATCH")
            rows.append(row)
    if len({r["case_id"] for r in rows}) != len(rows):
        failures.append(f"{split}_CASE_IDS_MUST_BE_UNIQUE")
    cells = {(r["semantic_target"], str(r.get("case_id"))) for r in rows}
    if len(cells) != len(rows):
        failures.append(f"{split}_DUPLICATE_TARGET_CASE_CELL")
    families: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        families.setdefault(str(row["family_id"]), []).append(row)
    if len(families) < 3:
        failures.append(f"{split}_AT_LEAST_THREE_FAMILIES_REQUIRED")
    token_sets = {family: set().union(*(set(m["tokens"]) for m in members)) for family, members in families.items()}
    return rows, token_sets


def _pairwise_disjoint(name_a: str, a: set[str], name_b: str, b: set[str], failures: list[str]) -> None:
    overlap = sorted(a & b)
    if overlap:
        failures.append(f"LEXICAL_SPLIT_OVERLAP:{name_a}:{name_b}:{','.join(overlap)}")


def _validate_nuisance(att: dict[str, Any], joint_case_keys: set[tuple[str, str]], failures: list[str]) -> dict[str, Any] | None:
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
    if not isinstance(receipts, list):
        failures.append("LEXICAL_NUISANCE_RUNTIME_RECEIPTS_REQUIRED")
    else:
        seen: set[tuple[str, str]] = set()
        for i, row in enumerate(receipts):
            prefix = f"LEXICAL_NUISANCE_RECEIPT_{i}"
            if not isinstance(row, dict):
                failures.append(f"{prefix}_OBJECT_REQUIRED")
                continue
            split = str(row.get("split") or "").strip().upper()
            case_id = row.get("case_id")
            digest = row.get("runtime_receipt_sha256")
            key = (split, case_id) if isinstance(case_id, str) else (split, "")
            if split not in SPLITS or not isinstance(case_id, str) or not case_id:
                failures.append(f"{prefix}_CASE_IDENTITY_INVALID")
                continue
            if not _sha256(digest):
                failures.append(f"{prefix}_RUNTIME_RECEIPT_SHA256_INVALID")
                continue
            if key in seen:
                failures.append(f"{prefix}_DUPLICATE_CASE")
                continue
            seen.add(key)
            normalized.append({"split": split, "case_id": case_id, "runtime_receipt_sha256": digest})
        if seen != joint_case_keys:
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


def adjudicate(candidate: Any, joint_binding: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(candidate, dict):
        candidate = {}
        failures.append("CANDIDATE_OBJECT_REQUIRED")
    if not isinstance(joint_binding, dict) or joint_binding.get("pass") is not True:
        failures.append("VALID_V9_JOINT_CASE_BINDING_REQUIRED")
        joint_rows: list[dict[str, Any]] = []
    else:
        material = joint_binding.get("binding_material")
        joint_rows = material.get("rows", []) if isinstance(material, dict) else []
    joint_by_key = {
        (str(r.get("split")), str(r.get("case_id"))): r
        for r in joint_rows if isinstance(r, dict)
    }
    joint_case_keys = set(joint_by_key)

    att = candidate.get("semantic_abstraction_attestation")
    if not isinstance(att, dict) or att.get("schema") != ATTESTATION_SCHEMA:
        failures.append("SEMANTIC_ABSTRACTION_ATTESTATION_REQUIRED")
        att = {}

    basis_rows, basis_families = _audit_basis(att.get("basis_rows"), failures)
    cal_rows, cal_families = _audit_eval_rows(att.get("calibration_rows"), split="CALIBRATION", failures=failures)
    hold_rows, hold_families = _audit_eval_rows(att.get("holdout_rows"), split="HOLDOUT", failures=failures)

    # Bind raw model-facing text to the exact v9 case universe via case id + prompt digest + target metadata.
    eval_rows = cal_rows + hold_rows
    eval_keys = {(r["split"], str(r["case_id"])) for r in eval_rows}
    if eval_keys != joint_case_keys:
        failures.append("ABSTRACTION_EVAL_CASE_UNIVERSE_MUST_MATCH_V9")
    for row in eval_rows:
        key = (row["split"], str(row["case_id"]))
        joint = joint_by_key.get(key)
        if joint is None:
            continue
        if row["prompt_sha256"] != joint.get("prompt_sha256"):
            failures.append(f"ABSTRACTION_PROMPT_SHA_MISMATCH:{key[0]}:{key[1]}")
        if row["semantic_target"] != joint.get("semantic_target"):
            failures.append(f"ABSTRACTION_TARGET_METADATA_MISMATCH:{key[0]}:{key[1]}")

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

    nuisance = _validate_nuisance(att, joint_case_keys, failures)
    native = _validate_native_semantics(att, failures)

    audit_material = {
        "schema": ATTESTATION_SCHEMA,
        "basis_prompt_universe_sha256": basis_universe,
        "basis_content_tokens": sorted(basis_tokens),
        "calibration_content_tokens": sorted(cal_tokens),
        "holdout_content_tokens": sorted(hold_tokens),
        "joint_case_keys": sorted([list(k) for k in joint_case_keys]),
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
            "PASS means the candidate is structurally compatible with the hard abstraction test: raw basis/calibration/holdout "
            "prompts are digest-bound, direct pole lexemes are absent, content vocabulary is disjoint across basis/calibration/holdout, "
            "the exact v9 runtime case universe is text-bound, a label-only nuisance control covers every executed case and fails to "
            "reproduce the candidate interaction within the preregistered bound, and promotion relies only on the native Q8->native "
            "llama.cpp cvec path without asserting causal equivalence to the old last-token hook. External runtime receipt authenticity "
            "and the actual scientific measurements remain separate gates; this module itself mints no credit."
        ),
    }
