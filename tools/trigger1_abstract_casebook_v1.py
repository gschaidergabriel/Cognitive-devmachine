#!/usr/bin/env python3
"""Frozen model-facing text for the hard label-free/cross-lexical Trigger-1 discriminator.

Semantic class names remain evaluator metadata only. The model sees consequence-coded
situations and an independently rotated A/B/C codebook in calibration/holdout. Basis,
calibration and holdout use disjoint content vocabularies under the companion abstraction
gate; direct polarity words are excluded from all semantic prompts.
"""
from __future__ import annotations

import hashlib
from typing import Any

from tools import trigger1_semantic_abstraction_gate_v1 as abstraction

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_LABEL_FREE_CASEBOOK/v1"
TARGETS = abstraction.TARGETS
CODES = ("A", "B", "C")

BASIS_TRIPLETS: tuple[tuple[str, dict[str, str]], ...] = (
    ("quay", {
        "AFFIRMATIVE": "A crate crosses the quay onto the freighter; manifest seal turns cobalt.",
        "NEGATIVE": "The crate returns beneath the warehouse canopy; manifest seal turns amber.",
        "NEUTRAL": "The crate rests beside the customs cage; manifest seal stays violet.",
    }),
    ("press", {
        "AFFIRMATIVE": "Typeset pages enter the press queue; folio marker becomes cedar.",
        "NEGATIVE": "Draft sheets move back toward the author tray; folio marker becomes ochre.",
        "NEUTRAL": "Proof sheets sit beside the editor lamp; folio marker remains lilac.",
    }),
    ("turnstile", {
        "AFFIRMATIVE": "A badge releases the turnstile latch; corridor beacon shows indigo.",
        "NEGATIVE": "The card reader keeps the gate latched; corridor beacon shows rust.",
        "NEUTRAL": "The credential waits near the inspection desk; corridor beacon shows pearl.",
    }),
    ("capsule", {
        "AFFIRMATIVE": "Thrusters lift the capsule beyond the tower; telemetry flag reads azure.",
        "NEGATIVE": "Clamps carry the capsule toward the service bay; telemetry flag reads umber.",
        "NEUTRAL": "The vehicle circles upon the pad beside technicians; telemetry flag reads mauve.",
    }),
    ("ledger", {
        "AFFIRMATIVE": "Coins settle inside the merchant ledger; remittance rune glows teal.",
        "NEGATIVE": "Funds roll backward toward the sender purse; remittance rune glows sienna.",
        "NEUTRAL": "Value sits inside the clearing buffer; remittance rune glows opal.",
    }),
    ("itinerary", {
        "AFFIRMATIVE": "A seat number appears upon the boarding slip; itinerary glyph shines coral.",
        "NEGATIVE": "The berth returns toward inventory; itinerary glyph shines charcoal.",
        "NEUTRAL": "The traveler stays upon standby; itinerary glyph shines ivory.",
    }),
)

CALIBRATION_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "family_id": "greenhouse",
        "mapping": {"AFFIRMATIVE": "A", "NEGATIVE": "B", "NEUTRAL": "C"},
        "descriptions": {
            "AFFIRMATIVE": "irrigation valves open and mist reaches the fern beds",
            "NEGATIVE": "supply pipes drain toward the cistern and the fern beds stay dry",
            "NEUTRAL": "pressure gauges oscillate while the fern beds await another reading",
        },
    },
    {
        "family_id": "archive",
        "mapping": {"AFFIRMATIVE": "B", "NEGATIVE": "C", "NEUTRAL": "A"},
        "descriptions": {
            "AFFIRMATIVE": "catalog cards move into the public drawer and shelf tags turn vermilion",
            "NEGATIVE": "folders travel back into the vault and shelf tags turn sepia",
            "NEUTRAL": "folders remain upon the curator cart and shelf tags turn alabaster",
        },
    },
    {
        "family_id": "bakery",
        "mapping": {"AFFIRMATIVE": "C", "NEGATIVE": "A", "NEUTRAL": "B"},
        "descriptions": {
            "AFFIRMATIVE": "dough enters the oven and the batch clock lights scarlet",
            "NEGATIVE": "dough returns toward the cold rack and the batch clock lights walnut",
            "NEUTRAL": "dough waits near the tasting bench and the batch clock lights cream",
        },
    },
)

HOLDOUT_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "family_id": "vineyard",
        "mapping": {"AFFIRMATIVE": "C", "NEGATIVE": "B", "NEUTRAL": "A"},
        "descriptions": {
            "AFFIRMATIVE": "grapes descend into the crusher and the harvest pennant turns turquoise",
            "NEGATIVE": "baskets travel back toward the hillside and the harvest pennant turns maroon",
            "NEUTRAL": "baskets rest beside the assay table and the harvest pennant turns flaxen",
        },
    },
    {
        "family_id": "quarry",
        "mapping": {"AFFIRMATIVE": "A", "NEGATIVE": "C", "NEUTRAL": "B"},
        "descriptions": {
            "AFFIRMATIVE": "quarried slabs ride onto the rail wagon and the quarry lantern burns cyan",
            "NEGATIVE": "quarried slabs roll toward the cutting shed and the quarry lantern burns auburn",
            "NEUTRAL": "quarried slabs stand beside the survey tripod and the quarry lantern burns porcelain",
        },
    },
    {
        "family_id": "theater",
        "mapping": {"AFFIRMATIVE": "B", "NEGATIVE": "A", "NEUTRAL": "C"},
        "descriptions": {
            "AFFIRMATIVE": "curtains rise above the stage and the rehearsal medallion shows emerald",
            "NEGATIVE": "curtains fold behind the proscenium and the rehearsal medallion shows bronze",
            "NEUTRAL": "curtains hang beside the rigging check and the rehearsal medallion shows porcelain",
        },
    },
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def basis_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_id, prompts in BASIS_TRIPLETS:
        for target in TARGETS:
            prompt = prompts[target]
            rows.append({
                "family_id": family_id,
                "semantic_target": target,
                "prompt": prompt,
                "prompt_sha256": _sha(prompt),
                "lexical_content_sha256": abstraction.lexical_family_sha(abstraction.lexical_tokens(prompt)),
            })
    return rows


def _eval_rows(split: str, scenarios: tuple[dict[str, Any], ...], seed_base: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    n = 0
    for scenario in scenarios:
        mapping = scenario["mapping"]
        descriptions = scenario["descriptions"]
        codebook = {mapping[target]: descriptions[target] for target in TARGETS}
        codebook_text = "; ".join(f"{code} means {codebook[code]}" for code in CODES)
        family_rows: list[dict[str, Any]] = []
        for target in TARGETS:
            n += 1
            prompt = (
                f"Mapping: {codebook_text}. Hold the following outcome: {descriptions[target]}. "
                "Emit only the matching symbol."
            )
            family_rows.append({
                "split": split,
                "case_id": f"{split.lower()}-{scenario['family_id']}-{n}",
                "seed": seed_base + n,
                "family_id": scenario["family_id"],
                "semantic_target": target,
                "output_code_identity": mapping[target],
                "prompt": prompt,
                "prompt_sha256": _sha(prompt),
            })
        family_tokens = set().union(*(abstraction.lexical_tokens(row["prompt"]) for row in family_rows))
        lexical_sha = abstraction.lexical_family_sha(family_tokens)
        scenario_sha = abstraction.canonical_sha({
            "schema": "CLAY_TRIGGER1_ABSTRACT_SCENARIO_FAMILY/v1",
            "split": split,
            "family_id": scenario["family_id"],
            "prompt_sha256": sorted(row["prompt_sha256"] for row in family_rows),
        })
        codebook_sha = abstraction.canonical_sha({
            "schema": "CLAY_TRIGGER1_ABSTRACT_CODEBOOK_FAMILY/v1",
            "split": split,
            "family_id": scenario["family_id"],
            "mapping": mapping,
            "codebook": codebook,
        })
        for row in family_rows:
            row["lexical_content_sha256"] = abstraction.lexical_family_sha(abstraction.lexical_tokens(row["prompt"]))
            row["scenario_family_sha256"] = scenario_sha
            row["lexical_family_sha256"] = lexical_sha
            row["codebook_family_sha256"] = codebook_sha
            rows.append(row)
    return rows


def producer_case_specs(split: str) -> list[dict[str, Any]]:
    split = split.strip().upper()
    rows = calibration_rows() if split == "CALIBRATION" else holdout_rows() if split == "HOLDOUT" else None
    if rows is None:
        raise ValueError(f"SPLIT_INVALID:{split}")
    return [
        {
            "schema": "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v1",
            "case_id": row["case_id"],
            "seed": row["seed"],
            "semantic_target": row["semantic_target"],
            "output_code_identity": row["output_code_identity"],
            "prompt": row["prompt"],
            "prompt_sha256": row["prompt_sha256"],
            "scenario_family_sha256": row["scenario_family_sha256"],
            "lexical_family_sha256": row["lexical_family_sha256"],
            "codebook_family_sha256": row["codebook_family_sha256"],
            "model_facing_target_identity_exposed": False,
            "model_facing_explicit_semantic_labels": False,
        }
        for row in rows
    ]


def calibration_rows() -> list[dict[str, Any]]:
    return _eval_rows("CALIBRATION", CALIBRATION_SCENARIOS, 7100)


def holdout_rows() -> list[dict[str, Any]]:
    return _eval_rows("HOLDOUT", HOLDOUT_SCENARIOS, 8100)


def casebook() -> dict[str, Any]:
    core = {
        "schema": SCHEMA,
        "basis_rows": basis_rows(),
        "calibration_rows": calibration_rows(),
        "holdout_rows": holdout_rows(),
        "semantic_target_metadata_only": True,
        "direct_pole_lexemes_model_facing": False,
        "basis_calibration_holdout_content_vocab_disjoint": True,
        "output_code_counterbalance": "Latin-square rotation across three scenario families per split",
    }
    return {**core, "casebook_sha256": abstraction.canonical_sha(core)}
