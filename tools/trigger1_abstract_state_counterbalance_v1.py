#!/usr/bin/env python3
"""Source-only hard semantic-state case design for Trigger-1.

The design removes the two easiest shortcuts still compatible with earlier evidence:
(1) fixed model-facing semantic labels / fixed output codes and (2) generic compliance
instructions such as "internally represent". It also freezes a calibration/holdout
lexical split and counterbalances an unrelated affect nuisance factor.

This module executes no model and mints no runtime/J-Space credit.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_COUNTERBALANCED_STATE_DESIGN/v1"
ROW_SCHEMA = "CLAY_TRIGGER1_ABSTRACT_COUNTERBALANCED_STATE_ROW/v1"
CLASSES = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
SPLITS = ("CALIBRATION", "HOLDOUT")
NUISANCE = ("POS", "NEG", "NEU")
SURFACE_FORMS = ("OUTCOME_FIRST", "DISTRACTOR_FIRST", "PARATAXIS")
FINAL_SUFFIX = "Context complete."

# Evaluator labels, output-code machinery and generic instruction/compliance scaffolds
# are forbidden model-facing. Synonymous outcome descriptions are intentionally allowed:
# cross-family/cross-split generalization over those descriptions is the scientific test.
FORBIDDEN_MODEL_FACING = (
    "affirmative", "negative", "neutral", "codebook", "semantic target",
    "internally represent", "internalize", "answer:", "reply", "respond",
    "choose", "select one", "output exactly", "return only", "follow the instruction",
)

# Function/scaffold lexemes are ignored by the lexical-disjointness check. Content
# lexemes must be disjoint between CALIBRATION and HOLDOUT.
LEXICAL_EXEMPT = frozenset(
    "the a an and or but after before following at in on for from to toward beyond against "
    "without another later kept remained stayed left appeared felt sounded looked smelled "
    "was stood lay crossed showed hung with of context complete record state this that one "
    "it its as by into awaiting during near no not yet then".split()
)

# Each family has three evaluator-only semantic states and three unrelated affect
# distractors. Holdout vocabulary is deliberately different from calibration vocabulary.
FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "split": "CALIBRATION", "family_id": "council",
        "outcome": {
            "AFFIRMATIVE": "The council ratified the charter after deliberation.",
            "NEGATIVE": "The council vetoed the charter after deliberation.",
            "NEUTRAL": "The council tabled the charter after deliberation.",
        },
        "distractor": {
            "POS": "The atrium flowers smelled fragrant.",
            "NEG": "The corridor radiator rattled harshly.",
            "NEU": "The foyer clock ticked steadily.",
        },
    },
    {
        "split": "CALIBRATION", "family_id": "guest",
        "outcome": {
            "AFFIRMATIVE": "The guest accepted the invitation before sunset.",
            "NEGATIVE": "The guest declined the invitation before sunset.",
            "NEUTRAL": "The guest kept the invitation undecided before sunset.",
        },
        "distractor": {
            "POS": "The garden lanterns glowed warmly.",
            "NEG": "The driveway gravel felt jagged.",
            "NEU": "The porch mailbox stood closed.",
        },
    },
    {
        "split": "CALIBRATION", "family_id": "patch",
        "outcome": {
            "AFFIRMATIVE": "The maintainer merged the patch following inspection.",
            "NEGATIVE": "The maintainer discarded the patch following inspection.",
            "NEUTRAL": "The maintainer queued the patch for later inspection.",
        },
        "distractor": {
            "POS": "The terminal wallpaper looked cheerful.",
            "NEG": "The rack fan sounded grating.",
            "NEU": "The desk cable lay coiled.",
        },
    },
    {
        "split": "CALIBRATION", "family_id": "voyage",
        "outcome": {
            "AFFIRMATIVE": "The captain committed the vessel to departure at dawn.",
            "NEGATIVE": "The captain cancelled the vessel departure at dawn.",
            "NEUTRAL": "The captain kept the vessel at berth awaiting another call.",
        },
        "distractor": {
            "POS": "The horizon shimmered beautifully.",
            "NEG": "The bilge odor seemed foul.",
            "NEU": "The mast shadow crossed the deck.",
        },
    },
    {
        "split": "CALIBRATION", "family_id": "guild",
        "outcome": {
            "AFFIRMATIVE": "The registrar enrolled the applicant in the guild.",
            "NEGATIVE": "The registrar excluded the applicant from the guild.",
            "NEUTRAL": "The registrar kept the application pending at the guild.",
        },
        "distractor": {
            "POS": "The courtyard music sounded lovely.",
            "NEG": "The stairwell draft felt unpleasant.",
            "NEU": "The archive lamp remained lit.",
        },
    },
    {
        "split": "CALIBRATION", "family_id": "circuit",
        "outcome": {
            "AFFIRMATIVE": "The operator energized the circuit following inspection.",
            "NEGATIVE": "The operator isolated the circuit following inspection.",
            "NEUTRAL": "The operator kept the circuit in standby following inspection.",
        },
        "distractor": {
            "POS": "The workshop tea tasted pleasant.",
            "NEG": "The cabinet hinge squealed annoyingly.",
            "NEU": "The ceiling gauge stayed motionless.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "tenancy",
        "outcome": {
            "AFFIRMATIVE": "The proprietor countersigned the tenancy and released the keys.",
            "NEGATIVE": "The proprietor annulled the tenancy and retained the keys.",
            "NEUTRAL": "The proprietor suspended the tenancy until resolution.",
        },
        "distractor": {
            "POS": "The terrace fountain sparkled brightly.",
            "NEG": "The basement pipe clanged terribly.",
            "NEU": "The hallway mat stayed flat.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "climber",
        "outcome": {
            "AFFIRMATIVE": "The climber continued beyond basecamp toward the ridge.",
            "NEGATIVE": "The climber turned back before basecamp toward the valley.",
            "NEUTRAL": "The climber paused at basecamp without onward movement.",
        },
        "distractor": {
            "POS": "The snow crystals glittered prettily.",
            "NEG": "The boot lining scratched painfully.",
            "NEU": "The compass needle pointed northward.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "manuscript",
        "outcome": {
            "AFFIRMATIVE": "The editor scheduled the manuscript for publication.",
            "NEGATIVE": "The editor withdrew the manuscript from publication.",
            "NEUTRAL": "The editor parked the manuscript in limbo.",
        },
        "distractor": {
            "POS": "The reading room carried a delightful aroma.",
            "NEG": "The trolley wheel screeched badly.",
            "NEU": "The shelf marker displayed twelve.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "funds",
        "outcome": {
            "AFFIRMATIVE": "The treasurer released the funds for disbursement.",
            "NEGATIVE": "The treasurer froze the funds against disbursement.",
            "NEUTRAL": "The treasurer escrowed the funds until settlement.",
        },
        "distractor": {
            "POS": "The lobby mural was charming.",
            "NEG": "The vault buzzer became irritating.",
            "NEU": "The ledger ribbon had blue stripes.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "booking",
        "outcome": {
            "AFFIRMATIVE": "The hotelier finalized the booking for the traveler.",
            "NEGATIVE": "The hotelier erased the booking for the traveler.",
            "NEUTRAL": "The hotelier marked the booking provisional for the traveler.",
        },
        "distractor": {
            "POS": "The lounge cushions were cozy.",
            "NEG": "The elevator bell became shrill.",
            "NEU": "The window blind rested halfway.",
        },
    },
    {
        "split": "HOLDOUT", "family_id": "process",
        "outcome": {
            "AFFIRMATIVE": "The controller launched the process after validation.",
            "NEGATIVE": "The controller suppressed the process after validation.",
            "NEUTRAL": "The controller parked the process in dormancy after validation.",
        },
        "distractor": {
            "POS": "The status panel shone pleasantly.",
            "NEG": "The chassis vibration proved abrasive.",
            "NEU": "The floor tile formed a square.",
        },
    },
)


def canonical_sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _lexemes(text: str) -> set[str]:
    return {x for x in re.findall(r"[a-z]+", text.lower()) if x not in LEXICAL_EXEMPT}


def _render(outcome: str, distractor: str, form: str) -> str:
    if form == "OUTCOME_FIRST":
        body = f"{outcome} {distractor}"
    elif form == "DISTRACTOR_FIRST":
        body = f"{distractor} {outcome}"
    elif form == "PARATAXIS":
        body = f"Record: {outcome} {distractor}"
    else:
        raise ValueError(f"UNKNOWN_SURFACE_FORM:{form}")
    return f"{body} {FINAL_SUFFIX}"


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    split_index = {"CALIBRATION": 0, "HOLDOUT": 0}
    for family in FAMILIES:
        split = family["split"]
        local = split_index[split]
        split_index[split] += 1
        presentation = CLASSES[local % 3:] + CLASSES[: local % 3]
        nuisance_order = NUISANCE[(2 * local) % 3:] + NUISANCE[: (2 * local) % 3]
        form_order = SURFACE_FORMS[(local + 1) % 3:] + SURFACE_FORMS[: (local + 1) % 3]
        nuisance_for = dict(zip(CLASSES, nuisance_order))
        form_for = dict(zip(CLASSES, form_order))
        for presentation_index, semantic_class in enumerate(presentation):
            nuisance = nuisance_for[semantic_class]
            form = form_for[semantic_class]
            prompt = _render(family["outcome"][semantic_class], family["distractor"][nuisance], form)
            rows.append({
                "schema": ROW_SCHEMA,
                "split": split,
                "family_group_id": family["family_id"],
                "presentation_index": presentation_index,
                "semantic_class": semantic_class,
                "nuisance_affect": nuisance,
                "surface_form": form,
                "prompt": prompt,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            })
    return rows


def validate(rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = build_rows() if rows is None else rows
    if len(rows) != 36:
        raise ValueError(f"EXACT_36_ROWS_REQUIRED:{len(rows)}")

    model_text = "\n".join(str(r.get("prompt") or "") for r in rows).lower()
    for forbidden in FORBIDDEN_MODEL_FACING:
        if forbidden in model_text:
            raise ValueError(f"MODEL_FACING_SHORTCUT_PRESENT:{forbidden}")

    family_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("split") not in SPLITS or row.get("semantic_class") not in CLASSES:
            raise ValueError("ROW_METADATA_INVALID")
        prompt = str(row.get("prompt") or "")
        if not prompt.endswith(FINAL_SUFFIX):
            raise ValueError("COMMON_FINAL_SUFFIX_REQUIRED")
        if row.get("prompt_sha256") != hashlib.sha256(prompt.encode("utf-8")).hexdigest():
            raise ValueError("PROMPT_HASH_MISMATCH")
        family_rows[(row["split"], row["family_group_id"])].append(row)

    for key, group in family_rows.items():
        if len(group) != 3 or {r["semantic_class"] for r in group} != set(CLASSES):
            raise ValueError(f"COMPLETE_TRIPLET_REQUIRED:{key}")
        if {r["nuisance_affect"] for r in group} != set(NUISANCE):
            raise ValueError(f"NUISANCE_LATIN_TRIPLET_REQUIRED:{key}")
        if {r["surface_form"] for r in group} != set(SURFACE_FORMS):
            raise ValueError(f"SURFACE_FORM_LATIN_TRIPLET_REQUIRED:{key}")
        if {r["presentation_index"] for r in group} != {0, 1, 2}:
            raise ValueError(f"PRESENTATION_ROTATION_REQUIRED:{key}")

    # Every semantic class sees every nuisance state, surface form and presentation
    # position exactly twice per split, so none can proxy the semantic target.
    for split in SPLITS:
        for semantic_class in CLASSES:
            subset = [r for r in rows if r["split"] == split and r["semantic_class"] == semantic_class]
            if len(subset) != 6:
                raise ValueError(f"SIX_FAMILIES_PER_CLASS_REQUIRED:{split}:{semantic_class}")
            for field, universe in (
                ("nuisance_affect", NUISANCE),
                ("surface_form", SURFACE_FORMS),
                ("presentation_index", (0, 1, 2)),
            ):
                counts = Counter(r[field] for r in subset)
                if set(counts) != set(universe) or set(counts.values()) != {2}:
                    raise ValueError(f"COUNTERBALANCE_FAILED:{split}:{semantic_class}:{field}:{dict(counts)}")

    # Strong lexical split: after removing function/scaffold words, calibration and holdout
    # share zero lexemes. This blocks direct memorization of a calibration content word.
    split_lexemes: dict[str, set[str]] = {s: set() for s in SPLITS}
    for row in rows:
        split_lexemes[row["split"]].update(_lexemes(row["prompt"]))
    overlap = split_lexemes["CALIBRATION"] & split_lexemes["HOLDOUT"]
    if overlap:
        raise ValueError(f"CALIBRATION_HOLDOUT_LEXICAL_OVERLAP:{','.join(sorted(overlap))}")

    material = {
        "schema": SCHEMA,
        "row_count": len(rows),
        "family_count": len(family_rows),
        "families_per_split": {s: len({r["family_group_id"] for r in rows if r["split"] == s}) for s in SPLITS},
        "model_facing_labels_absent": True,
        "generic_compliance_scaffold_absent": True,
        "calibration_holdout_content_lexeme_overlap": [],
        "nuisance_affect_counterbalanced": True,
        "surface_form_counterbalanced": True,
        "presentation_position_counterbalanced": True,
        "common_final_suffix": FINAL_SUFFIX,
        "rows_sha256": canonical_sha(rows),
    }
    material["design_receipt_sha256"] = canonical_sha(material)
    return material


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, indent=2))
