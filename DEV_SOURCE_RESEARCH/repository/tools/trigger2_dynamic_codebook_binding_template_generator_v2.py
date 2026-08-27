#!/usr/bin/env python3
"""Trigger-2 dynamic codebook binding template generator v2.

Successor to v1 after a second-order shortcut review found residual target
information in deterministic codebook display order. v2 fully crosses display
order as an independent nuisance variable:

4 templates x 6 realized S3 mappings x 3 semantic classes x 6 display orders
= 432 METHOD_ONLY logical-alias rows.

ATOM_A/B/C are placeholders only. This generator intentionally cannot create
training-ready rows. A later evidence-bound materializer must substitute exact,
verified accepted ABI atoms while preserving split/provenance and independence
constraints.

No output from this tool mints accepted dataset, model-runtime, J-Space, HCU,
EntityOS, canonical-truth or training credit.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
ATOMS = ("ATOM_A", "ATOM_B", "ATOM_C")
S3 = tuple(permutations(ATOMS))
DISPLAY_ORDERS = tuple(permutations(CLASSES))
TEMPLATES = (
    "T1_CODEBOOK_THEN_CASE",
    "T2_CASE_THEN_CODEBOOK",
    "T3_TABLE_STYLE_CODEBOOK",
    "T4_DIALOGUE_STYLE_EPISODE",
)
SCENARIOS = {
    "ALLOW": "Facts: p=true; q=true. Rule condition: p AND q.",
    "DENY": "Facts: p=true; q=false. Rule condition: p AND q.",
    "ABSTAIN": "Facts: p=true; q=UNKNOWN. Rule condition: p AND q.",
}


def mapping_for(i: int) -> dict[str, str]:
    return dict(zip(CLASSES, S3[i]))


def codebook(mapping: dict[str, str], order: tuple[str, ...], style: str) -> str:
    if style == "lines":
        return "\n".join(f"{c} -> {mapping[c]}" for c in order)
    if style == "table":
        return " ".join(f"[{c} | {mapping[c]}]" for c in order)
    return "; ".join(f"{c} means {mapping[c]}" for c in order)


def prompt_for(template: str, mapping: dict[str, str], order: tuple[str, ...], scenario: str) -> str:
    if template == "T1_CODEBOOK_THEN_CASE":
        return (
            "CODEBOOK_BEGIN\n" + codebook(mapping, order, "lines") +
            "\nCODEBOOK_END\n\nCase:\n" + scenario +
            "\n\nReturn exactly one codebook symbol."
        )
    if template == "T2_CASE_THEN_CODEBOOK":
        return (
            "Case:\n" + scenario +
            "\n\nCODEBOOK_BEGIN\n" + codebook(mapping, order, "lines") +
            "\nCODEBOOK_END\n\nReturn exactly one codebook symbol."
        )
    if template == "T3_TABLE_STYLE_CODEBOOK":
        return (
            "CODEBOOK_BEGIN " + codebook(mapping, order, "table") +
            " CODEBOOK_END\nObservation: " + scenario +
            "\nOutput one mapped symbol only."
        )
    if template == "T4_DIALOGUE_STYLE_EPISODE":
        return (
            "Operator: CODEBOOK_BEGIN " + codebook(mapping, order, "dialogue") +
            " CODEBOOK_END.\nAnalyst: " + scenario +
            "\nOperator: Reply with one symbol only."
        )
    raise ValueError(template)


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for template in TEMPLATES:
        for permutation_i in range(6):
            mapping = mapping_for(permutation_i)
            for semantic_class in CLASSES:
                target = mapping[semantic_class]
                for order_i, order in enumerate(DISPLAY_ORDERS):
                    rows.append({
                        "schema": "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE/v2",
                        "evidence_class": "METHOD_ONLY",
                        "reality_level": "R2",
                        "family_id": f"DYNAMIC_CODEBOOK_BINDING_{template}",
                        "counterfactual_family_id": f"{template}:{semantic_class}",
                        "mapping_variant_id": f"P{permutation_i}",
                        "display_order_variant_id": f"O{order_i}",
                        "provenance_ancestry_id": "claude-xeno-vector-evidence:a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c",
                        "split": "TRAIN_TEMPLATE_ONLY",
                        "selected_using_holdout": False,
                        "class_word_policy": "CODEBOOK_ONLY_ALLOWED_CANDIDATE",
                        "model_visible_prompt_template": prompt_for(template, mapping, order, SCENARIOS[semantic_class]),
                        "target_template": target,
                        "materialization_required": True,
                        "materializer_private": {
                            "hidden_class": semantic_class,
                            "realized_mapping": mapping,
                            "display_order": order,
                            "target_symbol_slot": target,
                            "symbol_source_requirement": "EXACT_ACCEPTED_46_ABI_ATOMS_EXCLUDING_REJECTED_OR",
                            "distinct_symbols_required": True,
                            "atom_triplet_independence_required": True,
                            "counterfactual_family_must_not_cross_split": True,
                        },
                        "canonical_truth_allowed": False,
                        "direct_effect_authority": False,
                        "positive_jspace_label": False,
                    })
    return rows


def validate(rows: list[dict]) -> dict:
    if len(rows) != 432:
        raise AssertionError(f"rows={len(rows)} expected=432")

    template_counts = Counter()
    permutation_counts = Counter()
    order_counts = Counter()
    class_symbol_order = Counter()
    target_position = Counter()
    class_target_position = Counter()
    counterfactual_mapping_slots: dict[str, set[str]] = defaultdict(set)
    counterfactual_orders: dict[tuple[str, str], set[str]] = defaultdict(set)

    for row in rows:
        if row["evidence_class"] != "METHOD_ONLY" or row["positive_jspace_label"] is not False:
            raise AssertionError("evidence boundary")
        if row["materialization_required"] is not True:
            raise AssertionError("must remain unmaterialized")
        if row["canonical_truth_allowed"] is not False or row["direct_effect_authority"] is not False:
            raise AssertionError("authority boundary")

        private = row["materializer_private"]
        semantic_class = private["hidden_class"]
        mapping = private["realized_mapping"]
        order = tuple(private["display_order"])
        target = mapping[semantic_class]

        if set(mapping) != set(CLASSES) or sorted(mapping.values()) != sorted(ATOMS):
            raise AssertionError("realized mapping is not an S3 bijection")
        if row["target_template"] != target:
            raise AssertionError("target not derived from realized mapping")
        if sorted(order) != sorted(CLASSES):
            raise AssertionError("display order is not a class permutation")

        visible = row["model_visible_prompt_template"]
        for forbidden in ("hidden_class", "realized_mapping", "mapping_variant_id", "display_order_variant_id", "materializer_private"):
            if forbidden in visible:
                raise AssertionError("private metadata leak: " + forbidden)

        position = order.index(semantic_class)
        template_counts[row["family_id"]] += 1
        permutation_counts[row["mapping_variant_id"]] += 1
        order_counts[row["display_order_variant_id"]] += 1
        class_symbol_order[(semantic_class, target, row["display_order_variant_id"])] += 1
        target_position[(target, position)] += 1
        class_target_position[(semantic_class, target, position)] += 1
        counterfactual_mapping_slots[row["counterfactual_family_id"]].add(target)
        counterfactual_orders[(row["counterfactual_family_id"], row["mapping_variant_id"])].add(row["display_order_variant_id"])

    if sorted(template_counts.values()) != [108] * 4:
        raise AssertionError(f"template counts {template_counts}")
    if sorted(permutation_counts.values()) != [72] * 6:
        raise AssertionError(f"permutation counts {permutation_counts}")
    if sorted(order_counts.values()) != [72] * 6:
        raise AssertionError(f"order counts {order_counts}")
    if len(class_symbol_order) != 54 or any(v != 8 for v in class_symbol_order.values()):
        raise AssertionError("class-target-display-order not exactly crossed")
    if len(target_position) != 9 or any(v != 48 for v in target_position.values()):
        raise AssertionError("target-position not exactly balanced")
    if len(class_target_position) != 27 or any(v != 16 for v in class_target_position.values()):
        raise AssertionError("class-target-position not exactly balanced")
    if any(len(v) != 3 for v in counterfactual_mapping_slots.values()):
        raise AssertionError("semantic scenario does not span all target symbol slots")
    if any(len(v) != 6 for v in counterfactual_orders.values()):
        raise AssertionError("mapping variant does not span all display orders")

    return {
        "schema": "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE_SELFTEST/v2",
        "status": "PASS",
        "scope": "SOURCE_TEMPLATE_ONLY_NO_ACCEPTED_DATASET_OR_RUNTIME_CREDIT",
        "rows": 432,
        "templates": 4,
        "s3_permutations": 6,
        "semantic_classes": 3,
        "display_orders": 6,
        "class_target_display_order_exact_cross": True,
        "target_display_position_exact_balance": True,
        "class_target_display_position_exact_balance": True,
        "same_semantic_scenario_spans_all_three_symbol_slots": True,
        "each_mapping_variant_spans_all_six_display_orders": True,
        "positive_jspace_labels": 0,
        "materialization_required": True,
        "materialization_blocker": "EXACT_ACCEPTED_46_ABI_ATOM_MANIFEST_AND_TOKENIZER_BINDING_REQUIRED",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    rows = build_rows()
    report = validate(rows)
    if args.output:
        args.output.write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )
    if args.self_test or not args.output:
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
