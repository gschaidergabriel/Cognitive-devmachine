#!/usr/bin/env python3
"""Deterministic semantic-counterbalance contract for Trigger-1 J-Space experiments."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any

SCHEMA = "CLAY_TRIGGER1_SEMANTIC_COUNTERBALANCE/v1"
TARGET_CONCEPT = "living_organism"
LABELS = ("A", "B", "C")

# Derivation examples contain no evaluation answer-label mapping. They define only a
# semantic contrast used to derive the internal activation direction.
DERIVATION_POSITIVE = (
    (4101, "A sparrow is alive: it metabolizes, grows, and responds to its environment."),
    (4102, "An oak tree is alive: it grows, exchanges gases, and reproduces."),
    (4103, "A yeast cell is alive: it metabolizes nutrients and reproduces."),
)
DERIVATION_NEGATIVE = (
    (4201, "A granite pebble is nonliving: it does not metabolize, grow biologically, or reproduce."),
    (4202, "A brass key is nonliving: it has no metabolism, biological growth, or reproduction."),
    (4203, "A glass marble is nonliving: it does not metabolize or reproduce."),
)

# Correct output labels are deliberately balanced and rotated. Calibration and holdout
# use disjoint semantic items, so the output-token mapping cannot be the vector source.
CALIBRATION_CASES = (
    (5101, "A", "Which listed item is a living organism? A) fern B) ceramic mug C) quartz crystal"),
    (5102, "B", "Which listed item is a living organism? A) steel bolt B) salmon C) glass bead"),
    (5103, "C", "Which listed item is a living organism? A) brick B) copper wire C) mushroom"),
    (5111, "A", "Choose the living organism. A) ant B) plastic cap C) basalt chip"),
    (5112, "B", "Choose the living organism. A) aluminum spoon B) moss C) porcelain tile"),
    (5113, "C", "Choose the living organism. A) coin B) sand grain C) sunflower"),
)
HOLDOUT_CASES = (
    (6101, "A", "Which option names a living organism? A) dolphin B) limestone C) wrench"),
    (6102, "B", "Which option names a living organism? A) ceramic plate B) bacterium C) granite block"),
    (6103, "C", "Which option names a living organism? A) glass bottle B) iron nail C) cactus"),
    (6111, "A", "Select the living organism. A) earthworm B) marble C) copper pipe"),
    (6112, "B", "Select the living organism. A) sandstone B) orchid C) steel washer"),
    (6113, "C", "Select the living organism. A) plastic cube B) silver coin C) lichen"),
)

METRIC_DEFINITION = {
    "schema": "CLAY_TRIGGER1_COUNTERBALANCED_TOKEN_METRIC/v1",
    "target_concept": TARGET_CONCEPT,
    "score": "logit(correct_counterbalanced_label)-mean(logits(other_two_labels))",
    "uses_output_tokens": True,
    "mapping_policy": "equal A/B/C target frequency independently in calibration and holdout",
}


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _balanced(cases: tuple[tuple[int, str, str], ...]) -> bool:
    counts = Counter(label for _, label, _ in cases)
    return set(counts) == set(LABELS) and len(set(counts.values())) == 1


def validate_contract() -> dict[str, Any]:
    derivation_prompts = [text for _, text in (*DERIVATION_POSITIVE, *DERIVATION_NEGATIVE)]
    calibration_prompts = [text for _, _, text in CALIBRATION_CASES]
    holdout_prompts = [text for _, _, text in HOLDOUT_CASES]
    derivation_seeds = {seed for seed, _ in (*DERIVATION_POSITIVE, *DERIVATION_NEGATIVE)}
    calibration_seeds = {seed for seed, _, _ in CALIBRATION_CASES}
    holdout_seeds = {seed for seed, _, _ in HOLDOUT_CASES}
    failures: list[str] = []

    if not _balanced(CALIBRATION_CASES):
        failures.append("CALIBRATION_LABEL_MAPPING_NOT_BALANCED")
    if not _balanced(HOLDOUT_CASES):
        failures.append("HOLDOUT_LABEL_MAPPING_NOT_BALANCED")
    if derivation_seeds & calibration_seeds or derivation_seeds & holdout_seeds or calibration_seeds & holdout_seeds:
        failures.append("SEED_FAMILIES_NOT_DISJOINT")
    if set(derivation_prompts) & set(calibration_prompts + holdout_prompts):
        failures.append("DERIVATION_PROMPT_REUSED_FOR_EVALUATION")
    if set(calibration_prompts) & set(holdout_prompts):
        failures.append("CALIBRATION_HOLDOUT_PROMPT_REUSE")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "target_concept": TARGET_CONCEPT,
        "derivation_family_id": canonical_sha(
            {"positive": DERIVATION_POSITIVE, "negative": DERIVATION_NEGATIVE}
        ),
        "calibration_family_id": canonical_sha(CALIBRATION_CASES),
        "holdout_family_id": canonical_sha(HOLDOUT_CASES),
        "metric_definition_sha256": canonical_sha(METRIC_DEFINITION),
        "calibration_label_counts": dict(Counter(label for _, label, _ in CALIBRATION_CASES)),
        "holdout_label_counts": dict(Counter(label for _, label, _ in HOLDOUT_CASES)),
    }


def scientific_independence_metadata(derivation_receipt_sha256: str) -> dict[str, Any]:
    contract = validate_contract()
    if not contract["pass"]:
        raise RuntimeError(f"SEMANTIC_COUNTERBALANCE_CONTRACT_INVALID:{contract['failures']}")
    if not isinstance(derivation_receipt_sha256, str) or len(derivation_receipt_sha256) != 64:
        raise ValueError("DERIVATION_RECEIPT_SHA256_REQUIRED")
    int(derivation_receipt_sha256, 16)
    return {
        "vector_derivation": {
            "method": "nonterminal_contrastive_internal_activation_semantic_transport",
            "uses_output_head_weights": False,
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": contract["derivation_family_id"],
            "derivation_receipt_sha256": derivation_receipt_sha256,
        },
        "holdout_science": {
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": contract["metric_definition_sha256"],
            "metric_uses_output_tokens": True,
            "label_mapping_counterbalanced": True,
        },
    }


def score_token_logits(token_logits: dict[str, float], correct_label: str) -> float:
    if correct_label not in LABELS or set(token_logits) != set(LABELS):
        raise ValueError("EXACT_ABC_TOKEN_LOGITS_AND_CORRECT_LABEL_REQUIRED")
    distractors = [float(token_logits[label]) for label in LABELS if label != correct_label]
    return float(token_logits[correct_label]) - sum(distractors) / 2.0


if __name__ == "__main__":
    print(json.dumps(validate_contract(), sort_keys=True))
