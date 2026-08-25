#!/usr/bin/env python3
"""Deterministically author the frozen abstract-relational Trigger-1 design.

This is an external case-authoring source for trigger1_v7_factorial_case_evidence.py;
the producer itself still performs no model-facing prompt synthesis. Run this tool before
model execution, persist/hash its JSON output, and bind that exact output into the
preregistration receipt.

The target-varying model-facing content is structural:
  direct  = query pair is explicitly one of two listed one-way links
  reverse = the reversed query pair is explicitly listed
  absent  = neither query direction is explicitly listed

Evaluator metadata maps those three structural states to the legacy semantic target
names only outside the model-facing text. Basis, calibration and holdout use mutually
disjoint nonce entity lexicons. Output codes are Latin-square counterbalanced.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_DESIGN/v1"
BASIS_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_BASIS/v1"
FACTORIAL_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_RELATIONAL_FACTORIAL_CASES/v1"
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v1"

CODES = ("A", "B", "C")
STATE_TO_TARGET = {
    "direct": "AFFIRMATIVE",
    "reverse": "NEGATIVE",
    "absent": "NEUTRAL",
}

BASIS_FAMILIES = (
    ("b01", ("miv", "zor", "pel")),
    ("b02", ("dak", "vul", "kes")),
    ("b03", ("rin", "tob", "fex")),
    ("b04", ("sag", "nur", "wem")),
    ("b05", ("jol", "qir", "bap")),
    ("b06", ("xet", "lod", "pum")),
)
CALIBRATION_FAMILIES = (
    ("c01", ("gim", "rax", "tev")),
    ("c02", ("wok", "bis", "fyn")),
    ("c03", ("hep", "sul", "vad")),
)
HOLDOUT_FAMILIES = (
    ("h01", ("cim", "yot", "lef")),
    ("h02", ("pag", "ruk", "zen")),
    ("h03", ("dov", "mek", "sif")),
)
CODEBOOKS = (
    {"A": "direct", "B": "reverse", "C": "absent"},
    {"A": "absent", "B": "direct", "C": "reverse"},
    {"A": "reverse", "B": "absent", "C": "direct"},
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    ).hexdigest()


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payloads(entities: tuple[str, str, str]) -> dict[str, str]:
    a, b, c = entities
    links = f"{a}>{b},{b}>{c}"
    return {
        "direct": f"links={links};query={a}>{b}",
        "reverse": f"links={links};query={b}>{a}",
        "absent": f"links={links};query={a}>{c}",
    }


def basis_prompt(payload: str) -> str:
    return (
        "/no_think\n"
        "Use only the one-way links explicitly listed; no transitive rule is available. "
        "Keep the query-to-links relation active internally without naming a category.\n"
        "STATE_PAYLOAD_BEGIN\n"
        f"{payload}\n"
        "STATE_PAYLOAD_END"
    )


def factorial_prompt(payload: str, codebook: dict[str, str]) -> str:
    key = ";".join(f"{code}={codebook[code]}" for code in CODES)
    return (
        "/no_think\n"
        "Use only the one-way links explicitly listed; no transitive rule is available.\n"
        f"KEY {key}\n"
        "STATE_PAYLOAD_BEGIN\n"
        f"{payload}\n"
        "STATE_PAYLOAD_END\n"
        "Emit only the temporary code."
    )


def build_basis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id, entities in BASIS_FAMILIES:
        for state, payload in payloads(entities).items():
            prompt = basis_prompt(payload)
            rows.append(
                {
                    "row_id": f"{family_id}:{state}",
                    "family_group_id": family_id,
                    "semantic_class": STATE_TO_TARGET[state],
                    "prompt": prompt,
                    "prompt_sha256": text_sha(prompt),
                }
            )
    return rows


def build_factorial_cases(
    split: str,
    families: tuple[tuple[str, tuple[str, str, str]], ...],
    seed_base: int,
) -> list[dict[str, Any]]:
    split = split.upper()
    rows: list[dict[str, Any]] = []
    for family_index, (family_id, entities) in enumerate(families):
        codebook = CODEBOOKS[family_index]
        key_text = ";".join(f"{code}={codebook[code]}" for code in CODES)
        state_to_code = {
            state: next(code for code in CODES if codebook[code] == state)
            for state in STATE_TO_TARGET
        }
        scenario_sha = canonical_sha(
            {"design": "abstract-relational-v1", "split": split, "scenario": family_id}
        )
        lexical_sha = canonical_sha({"nonce_entities": sorted(entities)})
        codebook_sha = canonical_sha({"operational_codebook": key_text})
        for state_index, (state, payload) in enumerate(payloads(entities).items()):
            prompt = factorial_prompt(payload, codebook)
            rows.append(
                {
                    "schema": CASE_SCHEMA,
                    "case_id": f"{split.lower()}-{family_id}-{state}",
                    "seed": seed_base + family_index * 10 + state_index,
                    "semantic_target": STATE_TO_TARGET[state],
                    "output_code_identity": state_to_code[state],
                    "prompt": prompt,
                    "prompt_sha256": text_sha(prompt),
                    "scenario_family_sha256": scenario_sha,
                    "lexical_family_sha256": lexical_sha,
                    "codebook_family_sha256": codebook_sha,
                    "model_facing_target_identity_exposed": False,
                    "model_facing_explicit_semantic_labels": False,
                }
            )
    return rows


def build_design() -> dict[str, Any]:
    design: dict[str, Any] = {
        "schema": SCHEMA,
        "design_id": "trigger1-abstract-relational-v1",
        "basis_calibration": {
            "schema": BASIS_SCHEMA,
            "rows": build_basis_rows(),
        },
        "factorial_calibration": {
            "schema": FACTORIAL_SCHEMA,
            "cases": build_factorial_cases("CALIBRATION", CALIBRATION_FAMILIES, 9200),
        },
        "holdout": {
            "schema": FACTORIAL_SCHEMA,
            "cases": build_factorial_cases("HOLDOUT", HOLDOUT_FAMILIES, 9300),
        },
        "frozen_before_model_execution": True,
        "semantic_labels_model_facing": False,
        "target_variable_lexical_content": "STRUCTURAL_ONLY",
        "shared_instruction_content_balanced_within_family": True,
        "payload_lexicon_disjointness_intent": "BASIS_X_CALIBRATION_X_HOLDOUT",
    }
    design["design_sha256"] = canonical_sha(design)
    return design


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    design = build_design()
    text = json.dumps(design, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
