#!/usr/bin/env python3
"""Frozen strict label-free design for the next native Qwen3-0.6B Trigger-1 run.

The semantic class names in this module are evaluator metadata only. Model-facing BASIS
prompts contain no canonical labels and no A/B/C code identities. Each matched basis family
uses a distinct three-word discriminative lexicon. CALIBRATION and HOLDOUT use additional
lexicons disjoint from BASIS and from each other, while their A/B/C output codebooks are
Latin-square counterbalanced.

This is a design producer only: it does not load a model, open a runtime holdout, choose a
gain, or mint J-Space/runtime/product credit.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from tools import trigger1_v7_factorial_case_evidence as producer

SCHEMA = "CLAY_TRIGGER1_STRICT_LABEL_FREE_DESIGN/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")

BASIS_FAMILIES: tuple[tuple[str, tuple[str, str, str]], ...] = (
    ("b01", ("ratified", "vetoed", "unsettled")),
    ("b02", ("admitted", "barred", "unresolved")),
    ("b03", ("endorsed", "spurned", "undetermined")),
    ("b04", ("activated", "disabled", "unspecified")),
    ("b05", ("included", "excluded", "unclassified")),
    ("b06", ("validated", "invalidated", "unascertained")),
)

CALIBRATION_FAMILIES: tuple[tuple[str, tuple[str, str, str]], ...] = (
    ("c01", ("sanctioned", "prohibited", "pending")),
    ("c02", ("welcomed", "rebuffed", "uncommitted")),
    ("c03", ("authorized", "forbidden", "unresolvedly")),
)

HOLDOUT_FAMILIES: tuple[tuple[str, tuple[str, str, str]], ...] = (
    ("h01", ("confirmed", "cancelled", "indeterminate")),
    ("h02", ("chosen", "discarded", "unselected")),
    ("h03", ("opened", "sealed", "unknown")),
)

ROTATIONS = (
    {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
    {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
    {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
)
CODEBOOKS = (
    "A=proceed; B=decline; C=defer",
    "A=defer; B=proceed; C=decline",
    "A=decline; B=defer; C=proceed",
)


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def basis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id, words in BASIS_FAMILIES:
        for target, word in zip(TARGETS, words):
            prompt = f"/no_think\nInternally represent the disposition as {word}. Do not answer with a code or class label."
            rows.append({
                "row_id": f"{family_id}:{target.lower()}",
                "family_group_id": family_id,
                "semantic_class": target,
                "prompt": prompt,
                "prompt_sha256": sha_text(prompt),
            })
    return rows


def _families(split: str) -> tuple[tuple[str, tuple[str, str, str]], ...]:
    key = split.upper()
    if key == "CALIBRATION":
        return CALIBRATION_FAMILIES
    if key == "HOLDOUT":
        return HOLDOUT_FAMILIES
    raise ValueError(f"SPLIT_INVALID:{split}")


def factorial_case_specs(split: str) -> list[dict[str, Any]]:
    key = split.upper()
    rows: list[dict[str, Any]] = []
    seed_base = 9100 if key == "CALIBRATION" else 10100
    for family_index, (family_name, words) in enumerate(_families(key)):
        scenario_sha = sha_text(f"{SCHEMA}:{key}:scenario:{family_name}")
        lexical_sha = sha_text(f"{SCHEMA}:{key}:lexical:{family_name}:{'|'.join(words)}")
        codebook_sha = sha_text(f"{SCHEMA}:{key}:codebook:{CODEBOOKS[family_index]}")
        for target_index, (target, word) in enumerate(zip(TARGETS, words)):
            prompt = (
                f"/no_think\nDecision record {key.lower()}-{family_index}-{target_index}. "
                f"The observed disposition is {word}. Temporary action codes: {CODEBOOKS[family_index]}. "
                "Return only the action code that follows from the record."
            )
            rows.append({
                "schema": producer.CASE_SPEC_SCHEMA,
                "case_id": f"{key.lower()}-{family_name}-{target_index}",
                "seed": seed_base + family_index,
                "semantic_target": target,
                "output_code_identity": ROTATIONS[family_index][target],
                "prompt": prompt,
                "prompt_sha256": sha_text(prompt),
                "scenario_family_sha256": scenario_sha,
                "lexical_family_sha256": lexical_sha,
                "codebook_family_sha256": codebook_sha,
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
            })
    return rows


def factorial_plan(split: str) -> dict[str, Any]:
    return producer.build_plan(split.upper(), factorial_case_specs(split))


def design_packet() -> dict[str, Any]:
    packet = {
        "schema": SCHEMA,
        "basis_rows": basis_rows(),
        "calibration_case_specs": factorial_case_specs("CALIBRATION"),
        "holdout_case_specs": factorial_case_specs("HOLDOUT"),
        "basis_family_count": len(BASIS_FAMILIES),
        "calibration_family_count": len(CALIBRATION_FAMILIES),
        "holdout_family_count": len(HOLDOUT_FAMILIES),
        "model_facing_canonical_labels_absent_by_construction": True,
        "basis_output_code_identities_absent_by_construction": True,
        "semantic_metadata_is_evaluator_only": True,
        "target_x_output_code_counterbalanced": True,
        "runtime_executed": False,
        "holdout_opened": False,
        "canonical_credit_minted": False,
    }
    return {**packet, "design_sha256": canonical_sha(packet)}


if __name__ == "__main__":
    print(json.dumps(design_packet(), indent=2, sort_keys=True, ensure_ascii=False))
