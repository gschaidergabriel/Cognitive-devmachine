#!/usr/bin/env python3
"""Trigger-2 dynamic codebook binding template generator v3.

v3 fuses the preregistered query-polarity factor into the retained order-crossed
v2 donor while preserving a single-symbol output contract and binding every
model-visible render to the exact hidden factorial state used to derive it.

Factorial:
4 templates x 6 realized S3 mappings x 3 base semantic states
x 2 query polarities x 6 display orders = 864 METHOD_ONLY logical-alias rows.

DIRECT evaluates the stated rule. INVERTED evaluates its logical complement:
ALLOW <-> DENY while unresolved ABSTAIN remains ABSTAIN. Polarity pairs stay in
the same counterfactual family.

ATOM_A/B/C are logical aliases only. This source generator cannot create
training-ready rows. Exact accepted ABI atoms, checkpoint/tokenizer identity,
single-token verification, split-isolated lexical families and frozen holdouts
remain mandatory before materialization/admission.

No output mints accepted-dataset, model-runtime, J-Space, HCU, EntityOS,
canonical-truth or training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from itertools import permutations
from pathlib import Path
from typing import Iterable

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
ATOMS = ("ATOM_A", "ATOM_B", "ATOM_C")
POLARITIES = ("DIRECT", "INVERTED")
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
QUERY = {
    "DIRECT": "Evaluate the stated rule as written.",
    "INVERTED": "Evaluate the logical complement of the stated rule outcome.",
}
SOURCE_ANCESTRY = (
    "claude-xeno-vector-evidence:"
    "a2babae93dfe39e4e452a06bd8b848337f29766e38c422f05fb395126229b05c"
)
SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE/v3"
SELFTEST_SCHEMA = "TRIGGER2_DYNAMIC_CODEBOOK_BINDING_TEMPLATE_SELFTEST/v3"
OUTPUT_CONTRACT = "EXACTLY_ONE_EPISODE_LOCAL_SYMBOL"
POLARITY_RULE = "TRIGGER2_POLARITY_SWAP_ALLOW_DENY_PRESERVE_ABSTAIN/v1"


def effective_class(base_class: str, polarity: str) -> str:
    if polarity == "DIRECT":
        if base_class not in CLASSES:
            raise ValueError(base_class)
        return base_class
    if polarity != "INVERTED":
        raise ValueError(polarity)
    if base_class == "ALLOW":
        return "DENY"
    if base_class == "DENY":
        return "ALLOW"
    if base_class == "ABSTAIN":
        return "ABSTAIN"
    raise ValueError(base_class)


def mapping_for(i: int) -> dict[str, str]:
    return dict(zip(CLASSES, S3[i]))


def codebook(mapping: dict[str, str], order: tuple[str, ...], style: str) -> str:
    if style == "lines":
        return "\n".join(f"{c} -> {mapping[c]}" for c in order)
    if style == "table":
        return " ".join(f"[{c} | {mapping[c]}]" for c in order)
    if style == "dialogue":
        return "; ".join(f"{c} means {mapping[c]}" for c in order)
    raise ValueError(style)


def prompt_for(
    template: str,
    mapping: dict[str, str],
    order: tuple[str, ...],
    scenario: str,
    polarity: str,
) -> str:
    query = QUERY[polarity]
    if template == "T1_CODEBOOK_THEN_CASE":
        return (
            "CODEBOOK_BEGIN\n" + codebook(mapping, order, "lines")
            + "\nCODEBOOK_END\n\nCase:\n" + scenario
            + "\n\nQuery: " + query
            + "\nReturn exactly one codebook symbol."
        )
    if template == "T2_CASE_THEN_CODEBOOK":
        return (
            "Case:\n" + scenario
            + "\n\nCODEBOOK_BEGIN\n" + codebook(mapping, order, "lines")
            + "\nCODEBOOK_END\n\nQuery: " + query
            + "\nReturn exactly one codebook symbol."
        )
    if template == "T3_TABLE_STYLE_CODEBOOK":
        return (
            "CODEBOOK_BEGIN " + codebook(mapping, order, "table")
            + " CODEBOOK_END\nObservation: " + scenario
            + "\nQuery: " + query
            + "\nOutput one mapped symbol only."
        )
    if template == "T4_DIALOGUE_STYLE_EPISODE":
        return (
            "Operator: CODEBOOK_BEGIN " + codebook(mapping, order, "dialogue")
            + " CODEBOOK_END.\nAnalyst: " + scenario
            + "\nOperator: " + query
            + " Reply with one symbol only."
        )
    raise ValueError(template)


def visible_render_sha256(prompt: str, target: str) -> str:
    payload = json.dumps(
        {"prompt": prompt, "target": target},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def outside_codebook(prompt: str) -> str:
    prompt = re.sub(
        r"CODEBOOK_BEGIN\n.*?\nCODEBOOK_END",
        "",
        prompt,
        flags=re.DOTALL,
    )
    prompt = re.sub(
        r"CODEBOOK_BEGIN .*? CODEBOOK_END",
        "",
        prompt,
        flags=re.DOTALL,
    )
    return prompt


def mutual_information(xs: Iterable[str], ys: Iterable[str]) -> float:
    pairs = list(zip(xs, ys))
    if not pairs:
        return 0.0
    n = len(pairs)
    cx = Counter(x for x, _ in pairs)
    cy = Counter(y for _, y in pairs)
    cxy = Counter(pairs)
    result = 0.0
    for (x, y), count in cxy.items():
        pxy = count / n
        px = cx[x] / n
        py = cy[y] / n
        result += pxy * math.log2(pxy / (px * py))
    return result


def build_rows() -> list[dict]:
    rows: list[dict] = []
    for template in TEMPLATES:
        for permutation_i in range(6):
            mapping = mapping_for(permutation_i)
            for base_class in CLASSES:
                scenario = SCENARIOS[base_class]
                for order_i, order in enumerate(DISPLAY_ORDERS):
                    pair_id = f"{template}:P{permutation_i}:O{order_i}:{base_class}"
                    for polarity in POLARITIES:
                        target_class = effective_class(base_class, polarity)
                        target = mapping[target_class]
                        prompt = prompt_for(template, mapping, order, scenario, polarity)
                        rows.append({
                            "schema": SCHEMA,
                            "evidence_class": "METHOD_ONLY",
                            "reality_level": "R2",
                            "family_id": f"DYNAMIC_CODEBOOK_BINDING_{template}",
                            "counterfactual_family_id": pair_id,
                            "mapping_variant_id": f"P{permutation_i}",
                            "display_order_variant_id": f"O{order_i}",
                            "query_polarity": polarity,
                            "polarity_rule": POLARITY_RULE,
                            "provenance_ancestry_id": SOURCE_ANCESTRY,
                            "split": "TRAIN_TEMPLATE_ONLY",
                            "selected_using_holdout": False,
                            "class_word_policy": "CODEBOOK_ONLY_ALLOWED_CANDIDATE",
                            "output_contract": OUTPUT_CONTRACT,
                            "model_visible_prompt_template": prompt,
                            "target_template": target,
                            "model_visible_render_sha256": visible_render_sha256(prompt, target),
                            "materialization_required": True,
                            "training_eligible": False,
                            "hard_negative_channel": False,
                            "materializer_private": {
                                "template_family": template,
                                "base_semantic_class": base_class,
                                "effective_target_class": target_class,
                                "realized_mapping": mapping,
                                "display_order": order,
                                "target_symbol_slot": target,
                                "symbol_source_requirement": (
                                    "EXACT_ACCEPTED_46_ABI_ATOMS_EXCLUDING_REJECTED_OR"
                                ),
                                "distinct_symbols_required": True,
                                "atom_triplet_independence_required": True,
                                "counterfactual_family_must_not_cross_split": True,
                                "polarity_pair_must_stay_same_split": True,
                                "model_visible_serializer_must_emit_only_prompt_and_target": True,
                            },
                            "canonical_truth_allowed": False,
                            "direct_effect_authority": False,
                            "positive_jspace_label": False,
                        })
    return rows


def validate(rows: list[dict]) -> dict:
    if len(rows) != 864:
        raise AssertionError(f"rows={len(rows)} expected=864")

    pair_members: dict[str, dict[str, dict]] = defaultdict(dict)
    template_counts = Counter()
    permutation_counts = Counter()
    order_counts = Counter()
    polarity_counts = Counter()
    base_class_counts = Counter()
    effective_class_counts = Counter()
    target_counts = Counter()
    polarity_target_counts = Counter()
    base_polarity_target_counts = Counter()
    class_symbol_order_polarity = Counter()
    target_position_polarity = Counter()
    leaks: list[str] = []
    target_list: list[str] = []
    order_list: list[str] = []
    polarity_list: list[str] = []
    combined_nuisance_list: list[str] = []
    effective_class_list: list[str] = []

    for row in rows:
        if (
            row["evidence_class"] != "METHOD_ONLY"
            or row["positive_jspace_label"] is not False
            or row["training_eligible"] is not False
            or row["hard_negative_channel"] is not False
        ):
            raise AssertionError("evidence/output-channel boundary")
        if row["materialization_required"] is not True:
            raise AssertionError("must remain unmaterialized")
        if (
            row["canonical_truth_allowed"] is not False
            or row["direct_effect_authority"] is not False
        ):
            raise AssertionError("authority boundary")
        if row["output_contract"] != OUTPUT_CONTRACT:
            raise AssertionError("output-contract drift")
        if row["polarity_rule"] != POLARITY_RULE:
            raise AssertionError("polarity-rule drift")

        private = row["materializer_private"]
        template = private["template_family"]
        base_class = private["base_semantic_class"]
        target_class = private["effective_target_class"]
        mapping = private["realized_mapping"]
        order = tuple(private["display_order"])
        polarity = row["query_polarity"]

        if target_class != effective_class(base_class, polarity):
            raise AssertionError("polarity semantics mismatch")
        if set(mapping) != set(CLASSES) or sorted(mapping.values()) != sorted(ATOMS):
            raise AssertionError("realized mapping is not an S3 bijection")
        target = mapping[target_class]
        if row["target_template"] != target:
            raise AssertionError("target not derived from polarity plus mapping")
        if sorted(order) != sorted(CLASSES):
            raise AssertionError("display order is not a class permutation")

        visible = row["model_visible_prompt_template"]
        expected_visible = prompt_for(template, mapping, order, SCENARIOS[base_class], polarity)
        if visible != expected_visible:
            raise AssertionError("visible prompt not derived from hidden factorial state")
        if row["model_visible_render_sha256"] != visible_render_sha256(visible, target):
            raise AssertionError("model-visible render digest mismatch")
        for forbidden in (
            "base_semantic_class",
            "effective_target_class",
            "realized_mapping",
            "mapping_variant_id",
            "display_order_variant_id",
            "materializer_private",
        ):
            if forbidden in visible:
                raise AssertionError("private metadata leak: " + forbidden)

        outside = outside_codebook(visible).upper()
        leaked = [
            c for c in CLASSES if re.search(rf"\b{re.escape(c)}\b", outside)
        ]
        if leaked:
            leaks.append(f"{row['counterfactual_family_id']}:{polarity}:{leaked}")

        pair_members[row["counterfactual_family_id"]][polarity] = row
        position = order.index(target_class)
        template_counts[row["family_id"]] += 1
        permutation_counts[row["mapping_variant_id"]] += 1
        order_counts[row["display_order_variant_id"]] += 1
        polarity_counts[polarity] += 1
        base_class_counts[base_class] += 1
        effective_class_counts[target_class] += 1
        target_counts[target] += 1
        polarity_target_counts[(polarity, target)] += 1
        base_polarity_target_counts[(base_class, polarity, target)] += 1
        class_symbol_order_polarity[
            (base_class, polarity, target, row["display_order_variant_id"])
        ] += 1
        target_position_polarity[(polarity, target, position)] += 1
        target_list.append(target)
        order_list.append(row["display_order_variant_id"])
        polarity_list.append(polarity)
        combined_nuisance_list.append(row["display_order_variant_id"] + "|" + polarity)
        effective_class_list.append(target_class)

    if leaks:
        raise AssertionError(f"class words outside codebook: {leaks[:3]}")
    if len(pair_members) != 432:
        raise AssertionError(f"pairs={len(pair_members)} expected=432")
    if any(set(v) != set(POLARITIES) for v in pair_members.values()):
        raise AssertionError("missing polarity pair member")

    for pair_id, members in pair_members.items():
        direct = members["DIRECT"]
        inverted = members["INVERTED"]
        d = direct["materializer_private"]
        i = inverted["materializer_private"]
        for key in ("template_family", "base_semantic_class", "realized_mapping", "display_order"):
            if d[key] != i[key]:
                raise AssertionError(f"pair nuisance mismatch:{pair_id}:{key}")
        if direct["mapping_variant_id"] != inverted["mapping_variant_id"]:
            raise AssertionError("pair mapping-id mismatch")
        if direct["display_order_variant_id"] != inverted["display_order_variant_id"]:
            raise AssertionError("pair order-id mismatch")
        base = d["base_semantic_class"]
        if base == "ABSTAIN":
            if direct["target_template"] != inverted["target_template"]:
                raise AssertionError("ABSTAIN changed under inversion")
        else:
            if direct["target_template"] == inverted["target_template"]:
                raise AssertionError("known truth did not flip target under inversion")

    if sorted(template_counts.values()) != [216] * 4:
        raise AssertionError(f"template counts {template_counts}")
    if sorted(permutation_counts.values()) != [144] * 6:
        raise AssertionError(f"permutation counts {permutation_counts}")
    if sorted(order_counts.values()) != [144] * 6:
        raise AssertionError(f"order counts {order_counts}")
    if set(polarity_counts.values()) != {432}:
        raise AssertionError(f"polarity counts {polarity_counts}")
    if set(base_class_counts.values()) != {288}:
        raise AssertionError(f"base counts {base_class_counts}")
    if set(effective_class_counts.values()) != {288}:
        raise AssertionError(f"effective counts {effective_class_counts}")
    if set(target_counts.values()) != {288}:
        raise AssertionError(f"target counts {target_counts}")
    if len(polarity_target_counts) != 6 or any(v != 144 for v in polarity_target_counts.values()):
        raise AssertionError("polarity-target not exactly independent")
    if len(base_polarity_target_counts) != 18 or any(v != 48 for v in base_polarity_target_counts.values()):
        raise AssertionError("base-polarity-target not exactly crossed")
    if len(class_symbol_order_polarity) != 108 or any(v != 8 for v in class_symbol_order_polarity.values()):
        raise AssertionError("base-polarity-target-display-order not exactly crossed")
    if len(target_position_polarity) != 18 or any(v != 48 for v in target_position_polarity.values()):
        raise AssertionError("polarity-target-position not exactly balanced")

    mi = {
        "target_vs_display_order": mutual_information(target_list, order_list),
        "target_vs_query_polarity": mutual_information(target_list, polarity_list),
        "target_vs_display_order_and_polarity": mutual_information(target_list, combined_nuisance_list),
        "effective_class_vs_target_symbol": mutual_information(effective_class_list, target_list),
    }
    if any(abs(v) > 1e-12 for v in mi.values()):
        raise AssertionError(f"nonzero target shortcut MI: {mi}")

    return {
        "schema": SELFTEST_SCHEMA,
        "status": "PASS",
        "scope": "SOURCE_TEMPLATE_ONLY_NO_ACCEPTED_DATASET_OR_RUNTIME_CREDIT",
        "rows": 864,
        "counterfactual_pairs": 432,
        "templates": 4,
        "s3_permutations": 6,
        "base_semantic_classes": 3,
        "query_polarities": 2,
        "display_orders": 6,
        "polarity_pair_integrity": True,
        "known_truth_target_flip_under_inversion": True,
        "abstain_invariant_under_inversion": True,
        "class_words_outside_codebook": 0,
        "polarity_target_exact_independence": True,
        "base_polarity_target_exact_cross": True,
        "base_polarity_target_display_order_exact_cross": True,
        "polarity_target_display_position_exact_balance": True,
        "mutual_information_bits": mi,
        "model_visible_prompt_factorial_derivation_bound": True,
        "model_visible_render_digest_bound": True,
        "model_visible_private_metadata_leak": 0,
        "positive_jspace_labels": 0,
        "hard_negative_rows": 0,
        "training_eligible_rows": 0,
        "materialization_required": True,
        "materialization_blocker": (
            "EXACT_ACCEPTED_46_ABI_ATOM_MANIFEST_CHECKPOINT_TOKENIZER_AND_SPLIT_BINDING_REQUIRED"
        ),
        "holdout_generated": False,
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
            "".join(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
                for row in rows
            ),
            encoding="utf-8",
        )
    if args.self_test or not args.output:
        print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
