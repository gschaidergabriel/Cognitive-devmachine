#!/usr/bin/env python3
"""Build the Run-2 successor label-free structural cases with a complete polarity factorial.

This module deliberately does NOT replace tools/trigger1_structural_label_free_cases.py.
The already-dispatched 9-case experiment remains frozen and reproducible. This successor
crosses semantic target x opaque output code x probe query polarity exactly once per split:

    3 targets x 3 codes x 2 polarities = 18 cases.

All semantic target identities and factorial audit fields remain evaluator-side metadata.
The model sees only the formal demonstrations, the formal probe and the opaque A/B/C codebook.
CALIBRATION and HOLDOUT retain the parent generator's disjoint content-symbol vocabularies.

This generator is execution-free. It performs no model intervention and mints no runtime
or J-Space credit.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

from tools import trigger1_structural_label_free_cases as v1

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v2"
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v2"
PARENT_GENERATOR_PATH = "tools/trigger1_structural_label_free_cases.py"
PARENT_GENERATOR_BLOB_SHA = "66bb2f5cfccad602ee9c759961a369ab2c61be41"

TARGETS = v1.TARGETS
CODES = v1.CODES
SPLITS = v1.SPLITS
BANNED_MODEL_FACING = v1.BANNED_MODEL_FACING
STRUCTURAL_WHITELIST = v1.STRUCTURAL_WHITELIST


def _mutual_information_bits(rows: list[dict[str, Any]], left: str, right: str) -> float:
    total = len(rows)
    if total == 0:
        return 0.0
    joint = Counter((row[left], row[right]) for row in rows)
    left_counts = Counter(row[left] for row in rows)
    right_counts = Counter(row[right] for row in rows)
    out = 0.0
    for (left_value, right_value), count in joint.items():
        p_xy = count / total
        p_x = left_counts[left_value] / total
        p_y = right_counts[right_value] / total
        out += p_xy * math.log2(p_xy / (p_x * p_y))
    return out


def _best_target_accuracy_using_query_polarity(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    correct = 0
    for polarity in (False, True):
        counts = Counter(
            row["semantic_target"]
            for row in rows
            if row["probe_query_negated"] is polarity
        )
        if counts:
            correct += max(counts.values())
    return correct / len(rows)


def _factorial_audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    expected = {
        (target, code, polarity)
        for target in TARGETS
        for code in CODES
        for polarity in (False, True)
    }
    cell_counts = Counter(
        (
            row["semantic_target"],
            row["output_code_identity"],
            row["probe_query_negated"],
        )
        for row in rows
    )
    observed = set(cell_counts)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise AssertionError(f"TARGET_CODE_POLARITY_FACTORIAL_FAILED:missing={missing}:extra={extra}")
    if any(count != 1 for count in cell_counts.values()):
        raise AssertionError(f"TARGET_CODE_POLARITY_CELL_REPLICATION_NOT_EXACT:{dict(cell_counts)}")

    target_polarity_counts = {
        target: {
            "positive_query": sum(
                1
                for row in rows
                if row["semantic_target"] == target
                and row["probe_query_negated"] is False
            ),
            "negated_query": sum(
                1
                for row in rows
                if row["semantic_target"] == target
                and row["probe_query_negated"] is True
            ),
        }
        for target in TARGETS
    }
    for target, counts in target_polarity_counts.items():
        if counts != {"positive_query": len(CODES), "negated_query": len(CODES)}:
            raise AssertionError(f"TARGET_QUERY_POLARITY_IMBALANCE:{target}:{counts}")

    target_query_mi = _mutual_information_bits(rows, "semantic_target", "probe_query_negated")
    code_query_mi = _mutual_information_bits(rows, "output_code_identity", "probe_query_negated")
    if abs(target_query_mi) > 1e-12:
        raise AssertionError(f"TARGET_QUERY_POLARITY_MI_NONZERO:{target_query_mi}")
    if abs(code_query_mi) > 1e-12:
        raise AssertionError(f"CODE_QUERY_POLARITY_MI_NONZERO:{code_query_mi}")

    return {
        "schema": "CLAY_TRIGGER1_TARGET_CODE_QUERY_POLARITY_FACTORIAL_AUDIT/v1",
        "case_count": len(rows),
        "expected_case_count": len(TARGETS) * len(CODES) * 2,
        "complete_target_x_code_x_query_polarity": True,
        "cell_replication_count": 1,
        "target_query_polarity_counts": target_polarity_counts,
        "target_query_polarity_mutual_information_bits": target_query_mi,
        "output_code_query_polarity_mutual_information_bits": code_query_mi,
        "best_target_accuracy_using_query_polarity_alone":
            _best_target_accuracy_using_query_polarity(rows),
        "balanced_target_prior_accuracy": 1.0 / len(TARGETS),
    }


def build_cases(split: str) -> dict[str, Any]:
    split = split.strip().upper()
    if split not in SPLITS:
        raise ValueError(f"SPLIT_INVALID:{split}")

    rows: list[dict[str, Any]] = []
    for scenario in range(3):
        mapping = v1._codebook_permutation(scenario)
        # Demo context is scenario/codebook-bound only, not probe-polarity-bound.
        demo = v1._demo_block(mapping, split, scenario)
        for target_index, target in enumerate(TARGETS):
            for polarity in (0, 1):
                sym = v1._symbols(split, scenario, target_index)
                probe = v1._relation_fragment(target, polarity, sym)
                prompt = f"/no_think\n{demo}|P[{probe}]=>"

                lowered_tokens = set(re.findall(r"[a-z_]+", prompt.lower()))
                leaked = [word for word in BANNED_MODEL_FACING if word in lowered_tokens]
                if leaked:
                    raise RuntimeError(
                        f"MODEL_FACING_BANNED_LEXEME:{target}:{','.join(leaked)}"
                    )

                output_code = mapping[target]
                scenario_descriptor = {
                    "schema": "STRUCTURAL_LOGIC_SCENARIO_FAMILY/v1",
                    "split": split,
                    "scenario": scenario,
                }
                lexical_descriptor = {
                    "schema": "STRUCTURAL_LOGIC_LEXICAL_FAMILY/v1",
                    "split": split,
                    "scenario": scenario,
                }
                codebook_descriptor = {"scenario": scenario, "mapping": mapping}
                factorial_descriptor = {
                    "schema": "TARGET_CODE_QUERY_POLARITY_CELL/v1",
                    "semantic_target": target,
                    "output_code_identity": output_code,
                    "probe_query_negated": bool(polarity),
                }

                rows.append(
                    {
                        "schema": CASE_SCHEMA,
                        "case_id": (
                            f"{split.lower()}-struct-v2-"
                            f"{scenario}-{target_index}-p{polarity}"
                        ),
                        "seed": (
                            (173000 if split == "CALIBRATION" else 183000)
                            + scenario * 1009
                            + target_index * 101
                            + polarity * 17
                        ),
                        "semantic_target": target,
                        "output_code_identity": output_code,
                        "prompt": prompt,
                        "prompt_sha256": v1._prompt_sha(prompt),
                        "scenario_family_sha256": v1._sha(scenario_descriptor),
                        "lexical_family_sha256": v1._sha(lexical_descriptor),
                        "codebook_family_sha256": v1._sha(codebook_descriptor),
                        "factorial_cell_sha256": v1._sha(factorial_descriptor),
                        "model_facing_target_identity_exposed": False,
                        "model_facing_explicit_semantic_labels": False,
                        "model_facing_query_polarity_phase_exposed": False,
                        "probe_query_negated": bool(polarity),
                    }
                )

    audit = _factorial_audit(rows)
    return {
        "schema": SCHEMA,
        "split": split,
        "case_count": len(rows),
        "parent_generator_path": PARENT_GENERATOR_PATH,
        "parent_generator_blob_sha": PARENT_GENERATOR_BLOB_SHA,
        "construction": "TARGET_X_CODE_X_QUERY_POLARITY_COMPLETE_FACTORIAL",
        "banned_model_facing_lexemes": list(BANNED_MODEL_FACING),
        "structural_overlap_whitelist": sorted(STRUCTURAL_WHITELIST),
        "content_vocabulary": sorted(
            set().union(*(v1._content_tokens(row["prompt"]) for row in rows))
        ),
        "query_polarity_factorial_audit": audit,
        "cases": rows,
    }


def build_bundle() -> dict[str, Any]:
    calibration = build_cases("CALIBRATION")
    holdout = build_cases("HOLDOUT")
    lexical_audit = v1.lexical_disjointness(calibration, holdout)
    if lexical_audit["basis_holdout_lexically_disjoint"] is not True:
        raise AssertionError(
            f"CONTENT_LEXICAL_OVERLAP:{lexical_audit['content_overlap']}"
        )

    out = {
        "schema": SCHEMA,
        "successor_of": "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v1",
        "frozen_v1_modified": False,
        "calibration": calibration,
        "holdout": holdout,
        "lexical_disjointness_audit": lexical_audit,
        "model_executed": False,
        "holdout_opened_by_generator": False,
        "runtime_credit_minted": False,
        "canonical_semantic_jspace_promotion": False,
    }
    out["bundle_sha256"] = v1._sha(out)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output")
    args = ap.parse_args()
    bundle = build_bundle()
    text = json.dumps(bundle, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
