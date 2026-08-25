#!/usr/bin/env python3
"""Frozen source plan for the Trigger-1 abstract-state hard holdout.

No model is executed here.  The source deterministically expands 6 calibration and 6
holdout scenario families into 18 cases per split.  Within a scenario family all three
model-facing prompts have the exact same word multiset; only the nonlexical `*` marker
moves.  Target-to-marker-slot and target-to-output-code assignments use all six
permutations exactly once per split.  Calibration and holdout content lexicons are
disjoint after removal of the fixed structural scaffold.

The semantic target names are evaluator metadata only and never appear in model-facing
prompts.  This source is intended to be committed/frozen before any model holdout run.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

SCHEMA = "CLAY_TRIGGER1_ABSTRACT_STATE_CASE_PLAN/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
PERMUTATIONS = (
    (0, 1, 2), (0, 2, 1), (1, 0, 2),
    (1, 2, 0), (2, 0, 1), (2, 1, 0),
)
TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
FIXED_SCAFFOLD_TOKENS = frozenset(
    "triad card rule maps condition to action records marker star appears before exactly one "
    "record codebook return only code for the marked current case the a an when every one has "
    "of and or is are in slot all b c <num>".split()
)

CALIBRATION_FAMILIES = (
    (("launch", "halt", "examine"), ("all gate lamps glow steady", "a gate lamp blinks broken", "a gate lamp lacks a reading")),
    (("dispatch", "retain", "audit"), ("all ledger marks align cleanly", "a ledger mark conflicts sharply", "a ledger mark remains unmeasured")),
    (("continue", "terminate", "inspect"), ("all bridge sensors report stable", "a bridge sensor reports fracture", "a bridge sensor has absent telemetry")),
    (("unlock", "freeze", "check"), ("all vault seals show intact", "a vault seal shows rupture", "a vault seal carries missing evidence")),
    (("forward", "withhold", "assess"), ("all packet checksums match perfectly", "a packet checksum differs materially", "a packet checksum has unavailable bytes")),
    (("activate", "suspend", "verify"), ("all reactor indicators stay nominal", "a reactor indicator crosses danger", "a reactor indicator gives indeterminate data")),
)

HOLDOUT_FAMILIES = (
    (("transmit", "quarantine", "inquire"), ("all orchard tags read ripe", "an orchard tag reads spoiled", "an orchard tag displays unreadable status")),
    (("deploy", "sequester", "investigate"), ("all telescope traces look coherent", "a telescope trace displays corruption", "a telescope trace provides incomplete capture")),
    (("release", "isolate", "reconcile"), ("all cargo clasps appear sound", "a cargo clasp appears damaged", "a cargo clasp bears ambiguous scan")),
    (("execute", "contain", "clarify"), ("all clinic samples meet threshold", "a clinic sample breaches threshold", "a clinic sample yields inconclusive assay")),
    (("publish", "withdraw", "diagnose"), ("all manuscript citations resolve properly", "a manuscript citation contradicts source", "a manuscript citation bears unresolved provenance")),
    (("enable", "restrict", "resolve"), ("all network routes answer healthy", "a network route returns fault", "a network route yields insufficient observation")),
)


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    ).hexdigest()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_tokens(prompt: str) -> list[str]:
    prompt = prompt.lower().replace("/no_think", " ")
    out: list[str] = []
    for token in TOKEN_RE.findall(prompt):
        normalized = "<num>" if token.isdigit() else token
        if normalized not in FIXED_SCAFFOLD_TOKENS:
            out.append(normalized)
    return out


def _families(split: str):
    return CALIBRATION_FAMILIES if split == "CALIBRATION" else HOLDOUT_FAMILIES


def build_split(split: str) -> list[dict[str, Any]]:
    if split not in {"CALIBRATION", "HOLDOUT"}:
        raise ValueError("SPLIT_INVALID")
    rows: list[dict[str, Any]] = []
    for family_index, (actions, records_by_target) in enumerate(_families(split)):
        slot_perm = PERMUTATIONS[family_index]
        # This ordering is also a permutation of all six assignments, but is deliberately
        # decoupled from the target->slot schedule.
        code_perm = PERMUTATIONS[(family_index * 5 + 1) % len(PERMUTATIONS)]
        slots: list[str | None] = [None, None, None]
        for target_index, record in enumerate(records_by_target):
            slots[slot_perm[target_index]] = record
        code_for_target = {TARGETS[i]: CODES[code_perm[i]] for i in range(3)}
        action_for_target = {TARGETS[i]: actions[i] for i in range(3)}
        codebook = [f"{code_for_target[TARGETS[i]]}={action_for_target[TARGETS[i]]}" for i in range(3)]
        rule = (
            f"Rule maps condition to action: {records_by_target[0]} -> {actions[0]}; "
            f"{records_by_target[1]} -> {actions[1]}; {records_by_target[2]} -> {actions[2]}."
        )
        base_records = [f"slot {i + 1}: {slots[i]}" for i in range(3)]
        scenario_sha = _sha(f"trigger1-abstract-v1:{split}:scenario:{family_index}:{'|'.join(records_by_target)}")
        lexical_sha = _sha(f"trigger1-abstract-v1:{split}:lexical:{family_index}:{'|'.join(actions)}:{'|'.join(records_by_target)}")
        codebook_sha = _sha(f"trigger1-abstract-v1:{split}:codebook:{family_index}:{'|'.join(codebook)}")
        for target_index, target in enumerate(TARGETS):
            active_slot = slot_perm[target_index]
            marked = [("* " if i == active_slot else "") + text for i, text in enumerate(base_records)]
            prompt = (
                "/no_think\nTriad card. " + rule + " Records: " + "; ".join(marked) + ". "
                + "Codebook: " + "; ".join(codebook) + ". Return only the code for the * marked record."
            )
            rows.append({
                "case_id": f"{split.lower()}-f{family_index + 1}-s{target_index + 1}",
                "semantic_target": target,
                "output_code_identity": code_for_target[target],
                "prompt": prompt,
                "prompt_sha256": _sha(prompt),
                "scenario_family_sha256": scenario_sha,
                "lexical_family_sha256": lexical_sha,
                "codebook_family_sha256": codebook_sha,
                "marker_slot": active_slot + 1,
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
            })
    return rows


def build_plan() -> dict[str, Any]:
    core = {
        "schema": SCHEMA,
        "design": (
            "6x3 per split; evaluator-only targets; exact within-family lexical multiset; "
            "target-slot and target-code fully counterbalanced; calibration/holdout content "
            "lexicon disjoint after fixed scaffold removal"
        ),
        "fixed_scaffold_tokens": sorted(FIXED_SCAFFOLD_TOKENS),
        "calibration_case_rows": build_split("CALIBRATION"),
        "holdout_case_rows": build_split("HOLDOUT"),
        "model_executed": False,
        "holdout_opened_for_model_execution": False,
        "runtime_credit_minted": False,
        "canonical_semantics_promotion": False,
    }
    return {**core, "plan_sha256": canonical_sha(core)}


if __name__ == "__main__":
    print(json.dumps(build_plan(), indent=2, sort_keys=True, ensure_ascii=False))
