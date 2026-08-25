#!/usr/bin/env python3
"""Fail-closed linter for Trigger-2 dynamic-binding golden generator cases.

This validates generator/evaluator specification only. It does not render ABI atoms,
admit canonical training data, run a model, or mint training/J-Space/EntityOS/HCU credit.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

SCHEMA = "TRIGGER2_DYNAMIC_BINDING_GOLDEN_LINTER/v1"
SEED_SCHEMA = "TRIGGER2_DYNAMIC_BINDING_GOLDEN_SEED/v1"
CLASSES = ("ALLOW", "DENY", "ABSTAIN")
PERM_IDS = tuple(f"P{i}" for i in range(6))
TRAIN_TEMPLATES = ("T1_CODEBOOK_FIRST", "T2_QUESTION_FIRST", "T3_STATEMENT", "T4_ICHFORM")
CLASS_WORD = re.compile(r"\b(?:ALLOW|DENY|ABSTAIN)\b", re.IGNORECASE)


def adjudicate(seed: Any) -> dict[str, Any]:
    failures: list[str] = []
    metrics: dict[str, Any] = {}

    if not isinstance(seed, dict):
        return _result(["SEED_OBJECT_REQUIRED"], metrics)
    if seed.get("schema") != SEED_SCHEMA:
        failures.append("SEED_SCHEMA_MISMATCH")
    if seed.get("direct_sft_ready") is not False:
        failures.append("GOLDEN_SEED_MUST_NOT_BE_DIRECT_SFT_READY")
    if seed.get("renderer_required") is not True:
        failures.append("MANIFEST_BOUND_RENDERER_REQUIRED")
    if tuple(seed.get("class_labels") or ()) != CLASSES:
        failures.append("CLASS_LABEL_SET_OR_ORDER_MISMATCH")

    permutations = seed.get("permutations")
    if not isinstance(permutations, dict) or set(permutations) != set(PERM_IDS):
        failures.append("FULL_S3_PERMUTATION_SET_REQUIRED")
        permutations = {}
    else:
        realized = set()
        for pid in PERM_IDS:
            m = permutations.get(pid)
            if not isinstance(m, dict) or set(m) != set(CLASSES):
                failures.append(f"PERMUTATION_MAPPING_INVALID:{pid}")
                continue
            vals = tuple(m[c] for c in CLASSES)
            if sorted(vals) != [0, 1, 2]:
                failures.append(f"PERMUTATION_NOT_BIJECTIVE:{pid}")
            realized.add(vals)
        if len(realized) != 6:
            failures.append("S3_REALIZED_MAPPING_CARDINALITY_NOT_6")

    examples = seed.get("examples")
    if not isinstance(examples, list):
        return _result(failures + ["EXAMPLES_LIST_REQUIRED"], metrics)

    ids = [x.get("id") for x in examples if isinstance(x, dict)]
    if len(ids) != len(examples) or any(not isinstance(x, str) or not x for x in ids):
        failures.append("EVERY_EXAMPLE_REQUIRES_ID")
    if len(set(ids)) != len(ids):
        failures.append("EXAMPLE_IDS_MUST_BE_UNIQUE")

    kinds = Counter(x.get("kind") for x in examples if isinstance(x, dict))
    metrics["kind_counts"] = dict(kinds)
    expected = seed.get("expected_counts") or {}
    if len(examples) != expected.get("total", 36):
        failures.append("TOTAL_COUNT_MISMATCH")
    if kinds.get("CORE_S3", 0) != expected.get("core_s3", 18):
        failures.append("CORE_S3_COUNT_MISMATCH")
    if kinds.get("CROSS_TEMPLATE", 0) != expected.get("cross_template", 12):
        failures.append("CROSS_TEMPLATE_COUNT_MISMATCH")
    if kinds.get("ADVERSARIAL_RELATION", 0) != expected.get("adversarial", 6):
        failures.append("ADVERSARIAL_COUNT_MISMATCH")

    core = [x for x in examples if isinstance(x, dict) and x.get("kind") == "CORE_S3"]
    core_cells = Counter((x.get("permutation"), x.get("latent_class")) for x in core)
    for pid in PERM_IDS:
        for cls in CLASSES:
            if core_cells[(pid, cls)] != 1:
                failures.append(f"CORE_CELL_NOT_EXACTLY_ONE:{pid}:{cls}")
    slot_balance = Counter()
    for x in core:
        pid, cls = x.get("permutation"), x.get("latent_class")
        if pid not in permutations or cls not in CLASSES:
            failures.append(f"CORE_IDENTITY_INVALID:{x.get('id')}")
            continue
        expected_slot = permutations[pid][cls]
        if x.get("target_slot") != expected_slot:
            failures.append(f"TARGET_SLOT_NOT_CAUSAL_FROM_MAPPING:{x.get('id')}")
        slot = x.get("target_slot")
        slot_balance[(cls, slot)] += 1
    metrics["core_class_slot_balance"] = {f"{c}:{s}": slot_balance[(c, s)] for c in CLASSES for s in range(3)}
    if any(slot_balance[(c, s)] != 2 for c in CLASSES for s in range(3)):
        failures.append("CORE_CLASS_SLOT_COUNTERBALANCE_NOT_EXACT")

    transfer = [x for x in examples if isinstance(x, dict) and x.get("kind") == "CROSS_TEMPLATE"]
    transfer_cells = Counter((x.get("template"), x.get("latent_class")) for x in transfer)
    for template in TRAIN_TEMPLATES:
        for cls in CLASSES:
            if transfer_cells[(template, cls)] != 1:
                failures.append(f"TRANSFER_CELL_NOT_EXACTLY_ONE:{template}:{cls}")
    for x in transfer:
        pid, cls = x.get("permutation"), x.get("latent_class")
        if pid not in permutations or cls not in CLASSES:
            failures.append(f"TRANSFER_IDENTITY_INVALID:{x.get('id')}")
            continue
        if x.get("target_slot") != permutations[pid][cls]:
            failures.append(f"TRANSFER_TARGET_SLOT_NOT_CAUSAL_FROM_MAPPING:{x.get('id')}")
        situation = x.get("situation")
        if not isinstance(situation, str) or not situation.strip():
            failures.append(f"TRANSFER_SITUATION_REQUIRED:{x.get('id')}")
        elif CLASS_WORD.search(situation):
            failures.append(f"CLASS_WORD_LEAK_OUTSIDE_CODEBOOK:{x.get('id')}")
        lexical = x.get("lexical_family")
        if not isinstance(lexical, str) or not lexical:
            failures.append(f"LEXICAL_FAMILY_REQUIRED:{x.get('id')}")

    required_relations = {
        "CF_REMAP_SAME_SEMANTICS",
        "CF_SEMANTIC_FLIP_SAME_CODEBOOK",
        "CF_CODEBOOK_ORDER_SHUFFLE",
        "CF_SURFACE_NUISANCE",
        "CF_SYMBOL_SWAP",
        "LEAKAGE_TRIPWIRE",
    }
    adversarial = [x for x in examples if isinstance(x, dict) and x.get("kind") == "ADVERSARIAL_RELATION"]
    relations = Counter(x.get("relation") for x in adversarial)
    metrics["adversarial_relations"] = dict(relations)
    if set(relations) != required_relations or any(v != 1 for v in relations.values()):
        failures.append("ADVERSARIAL_RELATION_SET_INCOMPLETE_OR_DUPLICATED")

    scenes = seed.get("semantic_scenes")
    if not isinstance(scenes, dict) or not scenes:
        failures.append("SEMANTIC_SCENES_REQUIRED")
    else:
        for sid, text in scenes.items():
            if not isinstance(text, str) or not text.strip():
                failures.append(f"SCENE_TEXT_REQUIRED:{sid}")
            elif CLASS_WORD.search(text):
                failures.append(f"CLASS_WORD_LEAK_IN_SCENE:{sid}")

    metrics["example_count"] = len(examples)
    metrics["full_s3_realized"] = len({tuple(permutations[p][c] for c in CLASSES) for p in permutations}) == 6 if permutations else False
    metrics["direct_sft_rows_emitted"] = 0
    return _result(failures, metrics)


def _result(failures: list[str], metrics: dict[str, Any]) -> dict[str, Any]:
    uniq = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "status": "PASS" if not uniq else "FAIL",
        "failures": uniq,
        "metrics": metrics,
        "rendered_training_rows": 0,
        "accepted_dataset_tokens": 0,
        "runtime_credit_minted": False,
        "training_credit_minted": False,
        "jspace_credit_minted": False,
        "evidence_boundary": "Golden generator/evaluator specification validation only. ABI rendering, tokenizer checks, rendered-data leakage/counterbalance derivation and canonical training admission are separate gates."
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("seed", type=Path)
    ns = ap.parse_args()
    result = adjudicate(json.loads(ns.seed.read_text(encoding="utf-8")))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
