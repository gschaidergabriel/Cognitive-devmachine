#!/usr/bin/env python3
"""Frozen label-free abstract-state protocol for Trigger-1 J-Space promotion.

This module defines the harder discriminator required before any "semantic J-Space" or
"abstract state control" claim can be promoted. Model-facing text never contains the
canonical evaluator labels or ordinary yes/no/approval/compliance vocabulary. The latent
classes live only in evaluator metadata and are instantiated as three abstract relations
between a finite record and a test:

* metadata AFFIRMATIVE: the test repeats the recorded exclusive binding;
* metadata NEGATIVE: the test assigns a different value to the same bound item;
* metadata NEUTRAL: the test concerns an item that is absent from the record.

The words above are source comments/metadata, never model-facing prompts. Each prompt uses
nonce lexicons. BASIS, CALIBRATION and HOLDOUT use pairwise-disjoint payload lexicons;
calibration/holdout infer arbitrary A/B/C output mappings only from in-context examples,
with a full 3x3 semantic-target x output-code factorial in each split.

The module is deterministic and execution-free. It does not run a model, open a holdout,
or mint runtime/J-Space/HCU/EntityOS/training/canonical-semantics credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from tools import trigger1_v7_factorial_case_evidence as producer

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_PROTOCOL/v1"
ATTESTATION_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_PROTOCOL_ATTESTATION/v1"
BASIS_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_BASIS_DESIGN/v1"
CLASSES = tuple(producer.TARGETS)
CODES = tuple(producer.CODES)

FORBIDDEN_MODEL_TOKENS = {
    "affirmative", "negative", "neutral",
    "yes", "no", "true", "false", "unknown", "undetermined",
    "agree", "agreement", "disagree", "disagreement",
    "approve", "approved", "approval", "reject", "rejected", "rejection",
    "accept", "accepted", "decline", "declined",
    "allow", "allowed", "deny", "denied", "permit", "permission",
    "support", "supported", "supporting", "oppose", "opposed", "opposing",
    "proceed", "proceeding", "grant", "granted", "granting", "refuse", "refused", "refusing",
    "comply", "compliance", "favorable", "unfavorable",
    "decision", "decide", "entailed", "contradicted", "correct", "incorrect",
}

SCAFFOLD_TOKENS = {
    "a", "an", "the", "each", "one", "exactly", "has", "with", "and", "only",
    "record", "records", "test", "tests", "example", "examples", "case", "code",
    "return", "write", "keep", "at", "marker", "rule", "item", "items", "uses",
    "then", "now", "final", "line", "relation", "inside", "in", "representation",
    "output", "three", "shown", "before", "after", "from", "same", "format",
}

_TOKEN_RE = re.compile(r"[A-Za-z]+")

PHASE_FAMILIES: dict[str, tuple[dict[str, Any], ...]] = {
    "BASIS": (
        {"family": "b_prism", "field": "sigil", "verb": "bears", "words": ("pravo", "selin", "kemba", "rutik")},
        {"family": "b_lantern", "field": "glyph", "verb": "holds", "words": ("dovar", "mecil", "purna", "wexin")},
        {"family": "b_tablet", "field": "rune", "verb": "carries", "words": ("gafor", "tulen", "nirek", "bavos")},
        {"family": "b_spindle", "field": "crest", "verb": "wears", "words": ("humer", "qalin", "zebro", "fadin")},
        {"family": "b_casket", "field": "seal", "verb": "keeps", "words": ("jovar", "lucin", "mepad", "suren")},
        {"family": "b_orbit", "field": "tag", "verb": "shows", "words": ("varet", "cunin", "pelig", "xomar")},
    ),
    "CALIBRATION": (
        {"family": "c_vessel", "field": "badge", "verb": "stores", "words": ("alvek", "bruni", "cetor", "dimas")},
        {"family": "c_harbor", "field": "stamp", "verb": "displays", "words": ("efran", "golik", "havid", "junes")},
        {"family": "c_meadow", "field": "token", "verb": "contains", "words": ("krova", "lumet", "nasis", "poder")},
    ),
    "HOLDOUT": (
        {"family": "h_orchard", "field": "emblem", "verb": "owns", "words": ("qeris", "rovan", "satek", "tubin")},
        {"family": "h_forge", "field": "insignia", "verb": "retains", "words": ("uvex", "woran", "yadil", "zumer")},
        {"family": "h_tower", "field": "device", "verb": "lists", "words": ("bekar", "corun", "femil", "gutes")},
    ),
}

CODE_ROTATIONS: tuple[dict[str, str], ...] = (
    {CLASSES[0]: "A", CLASSES[1]: "B", CLASSES[2]: "C"},
    {CLASSES[0]: "B", CLASSES[1]: "C", CLASSES[2]: "A"},
    {CLASSES[0]: "C", CLASSES[1]: "A", CLASSES[2]: "B"},
)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _visible_text(prompt: str) -> str:
    return prompt.replace("/no_think", " ")


def tokens(prompt: str) -> set[str]:
    return {x.lower() for x in _TOKEN_RE.findall(_visible_text(prompt))}


def forbidden_hits(prompt: str) -> list[str]:
    return sorted(tokens(prompt) & FORBIDDEN_MODEL_TOKENS)


def payload_lexicon(prompts: list[str]) -> set[str]:
    out: set[str] = set()
    for prompt in prompts:
        out |= tokens(prompt)
    return out - SCAFFOLD_TOKENS - {"a", "b", "c"}


def _relation_lines(family: dict[str, Any], semantic: str, offset: int = 0) -> tuple[str, str]:
    words = family["words"]
    subject = words[offset % len(words)]
    unseen = words[(offset + 1) % len(words)]
    value = words[(offset + 2) % len(words)]
    alternate = words[(offset + 3) % len(words)]
    verb = family["verb"]
    if semantic == CLASSES[0]:
        test_subject, test_value = subject, value
    elif semantic == CLASSES[1]:
        test_subject, test_value = subject, alternate
    elif semantic == CLASSES[2]:
        test_subject, test_value = unseen, value
    else:
        raise ValueError(f"SEMANTIC_INVALID:{semantic}")
    return f"Record: {subject} {verb} {value}.", f"Test: {test_subject} {verb} {test_value}."


def _rule_line(family: dict[str, Any]) -> str:
    return f"Rule: each item has exactly one {family['field']}."


def basis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_index, family in enumerate(PHASE_FAMILIES["BASIS"]):
        for semantic_index, semantic in enumerate(CLASSES):
            record, test = _relation_lines(family, semantic, offset=family_index)
            prompt = (
                "/no_think\n"
                f"{_rule_line(family)} {record} {test} "
                "Keep the relation inside the representation at the final marker. Marker."
            )
            rows.append({
                "row_id": f"{family['family']}:{semantic_index}",
                "family_group_id": family["family"],
                "semantic_class": semantic,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            })
    return rows


def _demo_lines(family: dict[str, Any], mapping: dict[str, str], scenario_index: int) -> list[str]:
    lines: list[str] = []
    for semantic_index, semantic in enumerate(CLASSES):
        record, test = _relation_lines(family, semantic, offset=scenario_index + semantic_index)
        lines.append(f"Example: {_rule_line(family)} {record} {test} Code: {mapping[semantic]}.")
    return lines


def factorial_case_specs(split: str) -> list[dict[str, Any]]:
    split = str(split).strip().upper()
    if split not in ("CALIBRATION", "HOLDOUT"):
        raise ValueError(f"SPLIT_INVALID:{split}")
    families = PHASE_FAMILIES[split]
    base_seed = 7300 if split == "CALIBRATION" else 8300
    rows: list[dict[str, Any]] = []
    for scenario_index, family in enumerate(families):
        mapping = CODE_ROTATIONS[scenario_index]
        demos = " ".join(_demo_lines(family, mapping, scenario_index))
        scenario_sha = canonical_sha({"schema": SCHEMA, "split": split, "scenario": family["family"]})
        lexical_sha = canonical_sha({
            "schema": SCHEMA,
            "split": split,
            "family": family["family"],
            "field": family["field"],
            "verb": family["verb"],
            "words": list(family["words"]),
        })
        codebook_sha = canonical_sha({"schema": SCHEMA, "split": split, "mapping": mapping})
        for semantic_index, semantic in enumerate(CLASSES):
            record, test = _relation_lines(family, semantic, offset=scenario_index + 2)
            prompt = (
                "/no_think\n"
                f"Examples: {demos} Case: {_rule_line(family)} {record} {test} "
                "Return only one code shown in the examples. Code:"
            )
            rows.append({
                "schema": producer.CASE_SPEC_SCHEMA,
                "case_id": f"abstract-{split.lower()}-s{scenario_index}-t{semantic_index}",
                "seed": base_seed + scenario_index * 10 + semantic_index,
                "semantic_target": semantic,
                "output_code_identity": mapping[semantic],
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "scenario_family_sha256": scenario_sha,
                "lexical_family_sha256": lexical_sha,
                "codebook_family_sha256": codebook_sha,
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
            })
    return rows


def expected_case_plans() -> dict[str, dict[str, Any]]:
    return {
        "CALIBRATION": producer.build_plan("CALIBRATION", factorial_case_specs("CALIBRATION")),
        "HOLDOUT": producer.build_plan("HOLDOUT", factorial_case_specs("HOLDOUT")),
    }


def validate_design() -> dict[str, Any]:
    failures: list[str] = []
    basis = basis_rows()
    specs = {
        "CALIBRATION": factorial_case_specs("CALIBRATION"),
        "HOLDOUT": factorial_case_specs("HOLDOUT"),
    }
    prompts_by_phase = {
        "BASIS": [row["prompt"] for row in basis],
        "CALIBRATION": [row["prompt"] for row in specs["CALIBRATION"]],
        "HOLDOUT": [row["prompt"] for row in specs["HOLDOUT"]],
    }
    for phase, prompts in prompts_by_phase.items():
        for index, prompt in enumerate(prompts):
            hits = forbidden_hits(prompt)
            if hits:
                failures.append(f"{phase}_MODEL_FACING_FORBIDDEN_TOKEN:{index}:{','.join(hits)}")
    lexicons = {phase: payload_lexicon(prompts) for phase, prompts in prompts_by_phase.items()}
    for left, right in (("BASIS", "CALIBRATION"), ("BASIS", "HOLDOUT"), ("CALIBRATION", "HOLDOUT")):
        overlap = sorted(lexicons[left] & lexicons[right])
        if overlap:
            failures.append(f"PAYLOAD_LEXICON_NOT_DISJOINT:{left}:{right}:{','.join(overlap)}")
    if len({row["family_group_id"] for row in basis}) != 6:
        failures.append("BASIS_EXACTLY_SIX_MATCHED_FAMILIES_REQUIRED")
    for family in {row["family_group_id"] for row in basis}:
        if {row["semantic_class"] for row in basis if row["family_group_id"] == family} != set(CLASSES):
            failures.append(f"BASIS_FAMILY_MISSING_CLASSES:{family}")
    plans: dict[str, dict[str, Any]] = {}
    try:
        plans = expected_case_plans()
    except Exception as exc:
        failures.append(f"FACTORIAL_CASE_PLAN_INVALID:{type(exc).__name__}:{exc}")
    for split, rows in specs.items():
        observed = {(row["semantic_target"], row["output_code_identity"]) for row in rows}
        expected = {(semantic, code) for semantic in CLASSES for code in CODES}
        if observed != expected:
            failures.append(f"{split}_FULL_THREE_BY_THREE_COUNTERBALANCE_REQUIRED")
    material = {
        "schema": SCHEMA,
        "basis_rows": [
            {k: row[k] for k in ("row_id", "family_group_id", "semantic_class", "prompt_sha256")}
            for row in basis
        ],
        "case_plan_sha256": {split: plan.get("plan_sha256") for split, plan in plans.items()},
        "payload_lexicon_sha256": {phase: canonical_sha(sorted(words)) for phase, words in lexicons.items()},
        "forbidden_model_tokens": sorted(FORBIDDEN_MODEL_TOKENS),
        "scaffold_tokens": sorted(SCAFFOLD_TOKENS),
    }
    return {
        "schema": ATTESTATION_SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "protocol_sha256": canonical_sha(material),
        "basis_design_sha256": canonical_sha({"schema": BASIS_SCHEMA, "rows": basis}),
        "case_plan_sha256": material["case_plan_sha256"],
        "payload_lexicon_sha256": material["payload_lexicon_sha256"],
        "payload_lexicon_pairwise_disjoint": not any(x.startswith("PAYLOAD_LEXICON_NOT_DISJOINT") for x in failures),
        "canonical_status_words_model_facing_absent": not any("FORBIDDEN_TOKEN" in x for x in failures),
        "semantic_x_output_code_counterbalanced": not any("COUNTERBALANCE" in x for x in failures),
        "generic_instruction_scaffold_common_mode": True,
        "explicit_yes_no_approval_compliance_vocabulary_absent": not any("FORBIDDEN_TOKEN" in x for x in failures),
        "basis_family_count": len({row["family_group_id"] for row in basis}),
        "calibration_case_count": len(specs["CALIBRATION"]),
        "holdout_case_count": len(specs["HOLDOUT"]),
        "model_executed": False,
        "holdout_opened": False,
        "canonical_credit_minted": False,
    }


def main() -> int:
    result = validate_design()
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
