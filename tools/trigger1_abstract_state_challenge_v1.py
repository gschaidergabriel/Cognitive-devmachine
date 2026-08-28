#!/usr/bin/env python3
"""Freeze and validate the hardest label-free Trigger-1 abstract-state challenge.

This module is execution-free.  It removes two shortcuts that weaker semantic tests can
leave open:

* calibration prompts are pure declarative state descriptions, not requests to comply;
* holdout prompts are target-blind: within each family the exact same prompt bytes are
  used for AFFIRMATIVE, NEGATIVE and NEUTRAL interventions.  The target exists only in
  evaluator metadata / the selected cvec.

Calibration uses six matched families so a class direction cannot be carried by one
repeated surface cue.  Holdout uses six new families with a disjoint content lexicon and
Latin-square code rotations repeated twice.  The validator derives lexical signatures
from the actual model-facing strings; caller-supplied lexical-family hashes are not
trusted as evidence.

No model is run and no canonical/J-Space/HCU/EntityOS/training credit is minted here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_CHALLENGE/v1"
VERDICT_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_CHALLENGE_GATE/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")

# Only grammatical/common scaffolding is removed.  Semantic content words are retained.
FUNCTION_WORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "else", "of", "to", "in",
    "on", "at", "by", "for", "from", "with", "without", "as", "is", "are", "was",
    "were", "be", "been", "being", "this", "that", "these", "those", "it", "its",
    "their", "into", "under", "over", "before", "after", "while", "until", "because",
    "when", "which", "one", "only", "exactly", "current", "three", "possible",
}

# Canonical evaluator labels and the most direct decision-label shortcuts are forbidden in
# calibration model-facing text.  The challenge does not pretend this list captures every
# synonym; repeated-target lexical-marker rejection + disjoint target-blind holdout are the
# stronger protections.
DIRECT_CALIBRATION_SHORTCUTS = {
    "affirmative", "negative", "neutral", "approve", "approved", "approval", "reject",
    "rejected", "rejection", "accept", "accepted", "decline", "declined", "grant",
    "granted", "deny", "denied", "allow", "allowed", "disallow", "support", "oppose",
    "defer", "deferred", "pending", "yes", "maybe",
}
CANONICAL_LABELS = {x.lower() for x in TARGETS}

CALIBRATION_FAMILIES: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "conveyor",
        {
            "AFFIRMATIVE": "Amber lamp glows; conveyor belt starts moving.",
            "NEGATIVE": "Crimson beacon flashes; conveyor belt stays motionless.",
            "NEUTRAL": "Indicator is dark; conveyor belt sensor reading is missing.",
        },
    ),
    (
        "vault",
        {
            "AFFIRMATIVE": "Latch releases; vault gate swings inward.",
            "NEGATIVE": "Deadbolt holds; vault gate cannot move.",
            "NEUTRAL": "Mechanism idles; vault gate credential is unsupplied.",
        },
    ),
    (
        "parcel",
        {
            "AFFIRMATIVE": "Parcel enters outbound lane.",
            "NEGATIVE": "Parcel returns to intake shelf.",
            "NEUTRAL": "Parcel waits inside buffer; scan is unfinished.",
        },
    ),
    (
        "reactor",
        {
            "AFFIRMATIVE": "Sequence energizes coils; reactor cycle begins.",
            "NEGATIVE": "Sequence aborts; reactor chamber is inert.",
            "NEUTRAL": "Sequence pauses; reactor temperature sample is unavailable.",
        },
    ),
    (
        "manuscript",
        {
            "AFFIRMATIVE": "Manuscript advances to typesetting.",
            "NEGATIVE": "Manuscript goes back to author desk.",
            "NEUTRAL": "Manuscript lingers under review; referee note is absent.",
        },
    ),
    (
        "transaction",
        {
            "AFFIRMATIVE": "Transaction commits; ledger changes persist.",
            "NEGATIVE": "Transaction reverts; ledger snapshot is unchanged.",
            "NEUTRAL": "Transaction hangs open; ledger prerequisite row is omitted.",
        },
    ),
)

HOLDOUT_FAMILIES: tuple[tuple[str, dict[str, str]], ...] = (
    (
        "drawbridge",
        {
            "AFFIRMATIVE": "Span rises and road traffic crosses canal.",
            "NEGATIVE": "Barriers lower and vehicles turn away.",
            "NEUTRAL": "Signals freeze while wind report is awaited.",
        },
    ),
    (
        "irrigation",
        {
            "AFFIRMATIVE": "Valves rotate; water floods orchard.",
            "NEGATIVE": "Supply pipe closes; soil receives nothing.",
            "NEUTRAL": "Controller preserves prior setting; moisture packet is delayed.",
        },
    ),
    (
        "clinic",
        {
            "AFFIRMATIVE": "Patient joins treatment queue.",
            "NEGATIVE": "Patient is sent outward to referral service.",
            "NEUTRAL": "Patient occupies triage station; lab panel is incomplete.",
        },
    ),
    (
        "drone",
        {
            "AFFIRMATIVE": "Rotors engage; craft leaves pad.",
            "NEGATIVE": "Motors disarm; craft settles onto cradle.",
            "NEUTRAL": "Craft hovers stationary; locator fix awaits acquisition.",
        },
    ),
    (
        "network",
        {
            "AFFIRMATIVE": "Router installs path; frames traverse uplink.",
            "NEGATIVE": "Router discards candidate; table keeps prior contents.",
            "NEUTRAL": "Router buffers proposal; neighbor advert is overdue.",
        },
    ),
    (
        "archive",
        {
            "AFFIRMATIVE": "Record writes permanently into index.",
            "NEGATIVE": "Record diverts and lands in discard bin.",
            "NEUTRAL": "Record sits within staging; checksum report is outstanding.",
        },
    ),
)

ROTATIONS = (
    {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
    {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
    {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_tokens(text: str) -> tuple[str, ...]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return tuple(sorted({w for w in words if len(w) > 1 and w not in FUNCTION_WORDS}))


def _holdout_prompt(branches: dict[str, str], target_to_code: dict[str, str]) -> str:
    by_code = {target_to_code[target]: branches[target] for target in TARGETS}
    lines = ["Three possible branch consequences are listed:"]
    lines.extend(f"{code}: {by_code[code]}" for code in CODES)
    lines.append("Return exactly one symbol matching the branch represented by the internal state; no requested branch is named in the text.")
    return "\n".join(lines)


def build_challenge() -> dict[str, Any]:
    calibration_rows: list[dict[str, Any]] = []
    for family_index, (family, surfaces) in enumerate(CALIBRATION_FAMILIES):
        family_sha = canonical_sha({"split": "CALIBRATION", "family": family, "version": 1})
        for target in TARGETS:
            surface = surfaces[target]
            calibration_rows.append(
                {
                    "split": "CALIBRATION",
                    "family_id": family,
                    "family_sha256": family_sha,
                    "semantic_target": target,
                    "prompt": surface,
                    "prompt_sha256": text_sha(surface),
                    "state_surface": surface,
                    "state_surface_sha256": text_sha(surface),
                    "state_content_tokens": list(content_tokens(surface)),
                    "model_facing_target_identity_exposed": False,
                    "instruction_free_state_capture": True,
                    "seed": 9100 + family_index,
                }
            )

    holdout_rows: list[dict[str, Any]] = []
    for family_index, (family, branches) in enumerate(HOLDOUT_FAMILIES):
        rotation = ROTATIONS[family_index % len(ROTATIONS)]
        prompt = _holdout_prompt(branches, rotation)
        family_sha = canonical_sha({"split": "HOLDOUT", "family": family, "version": 1})
        branch_sha = {target: text_sha(branches[target]) for target in TARGETS}
        branch_tokens = {target: list(content_tokens(branches[target])) for target in TARGETS}
        for target in TARGETS:
            holdout_rows.append(
                {
                    "split": "HOLDOUT",
                    "family_id": family,
                    "family_sha256": family_sha,
                    "semantic_target": target,
                    "output_code_identity": rotation[target],
                    "prompt": prompt,
                    "prompt_sha256": text_sha(prompt),
                    "branch_surfaces": dict(branches),
                    "branch_surface_sha256": branch_sha,
                    "branch_content_tokens": branch_tokens,
                    "model_facing_target_identity_exposed": False,
                    "target_blind_prompt": True,
                    "seed": 10100 + family_index,
                }
            )

    core = {
        "schema": SCHEMA,
        "challenge_version": 1,
        "calibration_rows": calibration_rows,
        "holdout_rows": holdout_rows,
        "required_calibration_families": 6,
        "required_holdout_families": 6,
        "required_targets": list(TARGETS),
        "required_codes": list(CODES),
        "canonical_credit_minted": False,
    }
    core["challenge_sha256"] = canonical_sha(core)
    return core


def validate(challenge: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(challenge, dict) or challenge.get("schema") != SCHEMA:
        challenge = {} if not isinstance(challenge, dict) else challenge
        failures.append("CHALLENGE_SCHEMA_INVALID")

    cal = challenge.get("calibration_rows")
    hold = challenge.get("holdout_rows")
    if not isinstance(cal, list) or len(cal) != 18:
        failures.append("EXACTLY_EIGHTEEN_CALIBRATION_ROWS_REQUIRED")
        cal = [] if not isinstance(cal, list) else cal
    if not isinstance(hold, list) or len(hold) != 18:
        failures.append("EXACTLY_EIGHTEEN_HOLDOUT_ROWS_REQUIRED")
        hold = [] if not isinstance(hold, list) else hold

    cal_by_family: dict[str, list[dict[str, Any]]] = {}
    hold_by_family: dict[str, list[dict[str, Any]]] = {}
    target_token_counts: dict[str, dict[str, int]] = {}
    cal_tokens: set[str] = set()
    hold_tokens: set[str] = set()

    for index, raw in enumerate(cal):
        prefix = f"CALIBRATION_ROW_{index}"
        if not isinstance(raw, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        target = str(raw.get("semantic_target") or "").upper()
        family = str(raw.get("family_id") or "")
        prompt = raw.get("prompt")
        surface = raw.get("state_surface")
        if target not in TARGETS:
            failures.append(f"{prefix}_TARGET_INVALID")
        if not family:
            failures.append(f"{prefix}_FAMILY_REQUIRED")
        if not isinstance(prompt, str) or not isinstance(surface, str) or prompt != surface:
            failures.append(f"{prefix}_CALIBRATION_MUST_BE_PURE_DECLARATIVE_STATE_SURFACE")
            continue
        if raw.get("instruction_free_state_capture") is not True:
            failures.append(f"{prefix}_INSTRUCTION_FREE_ATTESTATION_REQUIRED")
        if raw.get("model_facing_target_identity_exposed") is not False:
            failures.append(f"{prefix}_TARGET_IDENTITY_MUST_NOT_BE_EXPOSED")
        if text_sha(prompt) != raw.get("prompt_sha256") or text_sha(surface) != raw.get("state_surface_sha256"):
            failures.append(f"{prefix}_TEXT_HASH_MISMATCH")
        tokens = set(content_tokens(surface))
        if list(sorted(tokens)) != raw.get("state_content_tokens"):
            failures.append(f"{prefix}_DERIVED_TOKEN_SIGNATURE_MISMATCH")
        shortcuts = tokens & DIRECT_CALIBRATION_SHORTCUTS
        if shortcuts:
            failures.append(f"{prefix}_DIRECT_SEMANTIC_SHORTCUT:{','.join(sorted(shortcuts))}")
        if set(re.findall(r"[a-z0-9]+", prompt.lower())) & CANONICAL_LABELS:
            failures.append(f"{prefix}_CANONICAL_LABEL_PRESENT")
        for token in tokens:
            target_token_counts.setdefault(token, {name: 0 for name in TARGETS})
            if target in TARGETS:
                target_token_counts[token][target] += 1
        cal_tokens.update(tokens)
        cal_by_family.setdefault(family, []).append(raw)

    for token, counts in sorted(target_token_counts.items()):
        total = sum(counts.values())
        values = [counts[target] for target in TARGETS]
        # A content token may be family-shared (1,1,1) or unique to one row.  It may not
        # recur preferentially for one/two targets across families.
        if total > 1 and len(set(values)) != 1:
            failures.append(f"REPEATED_TARGET_ASSOCIATED_CALIBRATION_TOKEN:{token}:{values}")

    for family, rows in sorted(cal_by_family.items()):
        if len(rows) != 3 or {str(r.get("semantic_target")) for r in rows} != set(TARGETS):
            failures.append(f"CALIBRATION_FAMILY_NOT_COMPLETE:{family}")
    if len(cal_by_family) != 6:
        failures.append("EXACTLY_SIX_CALIBRATION_FAMILIES_REQUIRED")

    code_counts = {target: {code: 0 for code in CODES} for target in TARGETS}
    for index, raw in enumerate(hold):
        prefix = f"HOLDOUT_ROW_{index}"
        if not isinstance(raw, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        target = str(raw.get("semantic_target") or "").upper()
        code = str(raw.get("output_code_identity") or "").upper()
        family = str(raw.get("family_id") or "")
        prompt = raw.get("prompt")
        branches = raw.get("branch_surfaces")
        if target not in TARGETS or code not in CODES:
            failures.append(f"{prefix}_TARGET_OR_CODE_INVALID")
        else:
            code_counts[target][code] += 1
        if not family or not isinstance(prompt, str) or not isinstance(branches, dict):
            failures.append(f"{prefix}_FAMILY_PROMPT_BRANCHES_REQUIRED")
            continue
        if raw.get("target_blind_prompt") is not True or raw.get("model_facing_target_identity_exposed") is not False:
            failures.append(f"{prefix}_TARGET_BLIND_ATTESTATION_REQUIRED")
        if text_sha(prompt) != raw.get("prompt_sha256"):
            failures.append(f"{prefix}_PROMPT_HASH_MISMATCH")
        if set(re.findall(r"[a-z0-9]+", prompt.lower())) & CANONICAL_LABELS:
            failures.append(f"{prefix}_CANONICAL_LABEL_PRESENT")
        for branch_target in TARGETS:
            surface = branches.get(branch_target)
            if not isinstance(surface, str):
                failures.append(f"{prefix}_BRANCH_SURFACE_MISSING:{branch_target}")
                continue
            expected_sha = (raw.get("branch_surface_sha256") or {}).get(branch_target)
            expected_tokens = (raw.get("branch_content_tokens") or {}).get(branch_target)
            tokens = set(content_tokens(surface))
            if text_sha(surface) != expected_sha or list(sorted(tokens)) != expected_tokens:
                failures.append(f"{prefix}_BRANCH_DERIVATION_MISMATCH:{branch_target}")
            hold_tokens.update(tokens)
        hold_by_family.setdefault(family, []).append(raw)

    for family, rows in sorted(hold_by_family.items()):
        if len(rows) != 3 or {str(r.get("semantic_target")) for r in rows} != set(TARGETS):
            failures.append(f"HOLDOUT_FAMILY_NOT_COMPLETE:{family}")
            continue
        prompt_hashes = {r.get("prompt_sha256") for r in rows}
        prompt_texts = {r.get("prompt") for r in rows}
        if len(prompt_hashes) != 1 or len(prompt_texts) != 1:
            failures.append(f"HOLDOUT_TARGET_BLIND_PROMPT_BYTES_MUST_MATCH:{family}")
        if {str(r.get("output_code_identity")) for r in rows} != set(CODES):
            failures.append(f"HOLDOUT_FAMILY_MUST_ROTATE_ALL_CODES:{family}")
    if len(hold_by_family) != 6:
        failures.append("EXACTLY_SIX_HOLDOUT_FAMILIES_REQUIRED")

    if any(code_counts[target][code] != 2 for target in TARGETS for code in CODES):
        failures.append("HOLDOUT_TARGET_X_CODE_LATIN_SQUARE_MUST_BE_EXACTLY_BALANCED_TWICE")

    overlap = sorted(cal_tokens & hold_tokens)
    if overlap:
        failures.append("CALIBRATION_HOLDOUT_CONTENT_LEXICON_MUST_BE_DISJOINT:" + ",".join(overlap))

    cal_family_ids = set(cal_by_family)
    hold_family_ids = set(hold_by_family)
    if cal_family_ids & hold_family_ids:
        failures.append("CALIBRATION_HOLDOUT_FAMILY_IDS_MUST_BE_DISJOINT")

    declared_sha = challenge.get("challenge_sha256")
    core = dict(challenge)
    core.pop("challenge_sha256", None)
    recomputed_sha = canonical_sha(core) if challenge else None
    if declared_sha != recomputed_sha:
        failures.append("CHALLENGE_SHA256_MISMATCH")

    return {
        "schema": VERDICT_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "challenge_sha256": recomputed_sha,
        "calibration_family_count": len(cal_by_family),
        "holdout_family_count": len(hold_by_family),
        "calibration_instruction_free": bool(cal) and all(r.get("instruction_free_state_capture") is True for r in cal if isinstance(r, dict)),
        "holdout_target_blind": bool(hold) and all(r.get("target_blind_prompt") is True for r in hold if isinstance(r, dict)),
        "repeated_target_lexical_marker_absent": not any(f.startswith("REPEATED_TARGET_ASSOCIATED_CALIBRATION_TOKEN") for f in failures),
        "cross_split_content_lexically_disjoint": not overlap,
        "semantic_target_x_code_counterbalanced": not any("LATIN_SQUARE" in f for f in failures),
        "canonical_credit_minted": False,
        "jspace_model_runtime_credit": False,
        "training_credit": False,
        "evidence_boundary": (
            "PASS authenticates a source-level challenge design: six instruction-free declarative calibration families, "
            "no repeated target-associated calibration content token, six lexically disjoint target-blind holdout families, "
            "and exact semantic-target x output-code counterbalance. It is not model execution or semantic/J-Space credit."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-plan", type=Path)
    parser.add_argument("--validate", type=Path)
    args = parser.parse_args()
    challenge = json.loads(args.validate.read_text(encoding="utf-8")) if args.validate else build_challenge()
    verdict = validate(challenge)
    if args.write_plan:
        args.write_plan.parent.mkdir(parents=True, exist_ok=True)
        args.write_plan.write_text(json.dumps(challenge, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(verdict, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if verdict["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
