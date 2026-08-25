#!/usr/bin/env python3
"""Generate a label-free complete target x code x query-polarity Trigger-1 successor.

This is the execution-free successor to the frozen 9-case structural generator. It does
not alter the already queued experiment. Each split contains the complete 3 x 3 x 2
factorial: every evaluator-side semantic target is paired once with every opaque output
code under both positive and negated probe-query polarity.

The evaluator-side target names never appear in model-facing prompts. CALIBRATION and
HOLDOUT use disjoint content-symbol vocabularies. Paired polarity cases deliberately
share the same demonstrations and symbols, so demonstration formatting cannot identify
probe polarity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v2"
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_COMPLETE_FACTORIAL_CASE_SPEC/v2"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
POLARITIES = (False, True)
SPLITS = ("CALIBRATION", "HOLDOUT")
BANNED_MODEL_FACING = (
    "affirmative", "negative", "neutral",
    "approve", "approval", "approved",
    "reject", "rejection", "rejected",
    "accept", "accepted", "decline", "declined",
    "grant", "granted", "refuse", "refused",
    "support", "oppose", "yes", "no",
    "entail", "entailed", "contradict", "contradiction",
    "unknown", "undecided", "defer", "deferred",
    "allow", "allowed", "disallow", "disallowed",
)
STRUCTURAL_WHITELIST = {
    "no_think", "D1", "D2", "D3", "P", "F", "R", "Q", "A", "B", "C", "v", "w"
}


def _sha(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _prompt_sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _symbols(split: str, scenario: int, slot: int) -> dict[str, str]:
    banks = {
        "CALIBRATION": ("kav", "lem", "sir", "tup", "wex", "bim", "cor", "fyn", "guz"),
        "HOLDOUT": ("zop", "nuf", "qir", "vel", "dax", "jom", "pex", "ryl", "huc"),
    }
    bank = banks[split]
    base = (scenario * 3 + slot) % len(bank)
    return {
        "p": bank[base],
        "r": bank[(base + 1) % len(bank)],
        "s": bank[(base + 2) % len(bank)],
        "a": f"{bank[base]}{scenario + 2}",
        "b": f"{bank[(base + 1) % len(bank)]}{slot + 5}",
    }


def _relation_fragment(target: str, polarity: bool, sym: dict[str, str]) -> str:
    p, r, s, a, b = sym["p"], sym["r"], sym["s"], sym["a"], sym["b"]
    q = f"{r}({b},{a})"
    nq = f"!{q}"
    query = nq if polarity else q
    if target == "AFFIRMATIVE":
        facts = nq if polarity else f"{p}({a},{b})"
        rule = "-" if polarity else f"{p}(v,w)>{r}(w,v)"
    elif target == "NEGATIVE":
        facts = q if polarity else nq
        rule = "-"
    elif target == "NEUTRAL":
        facts = f"{p}({a},{b})"
        rule = f"{p}(v,w)>{s}(w,v)"
    else:
        raise ValueError(target)
    return f"F:{facts};R:{rule};Q:{query}"


def _codebook_permutation(scenario: int) -> dict[str, str]:
    return {target: CODES[(i + scenario) % len(CODES)] for i, target in enumerate(TARGETS)}


def _demo_block(mapping: dict[str, str], split: str, scenario: int) -> str:
    # Deliberately independent of probe polarity. Each paired +Q/-Q case for a fixed
    # target/code/scenario sees exactly the same demonstrations.
    chunks = []
    for i, target in enumerate(TARGETS, start=1):
        demo_polarity = bool((scenario + i) % 2)
        sym = _symbols(split, scenario, i + 3)
        chunks.append(f"D{i}[{_relation_fragment(target, demo_polarity, sym)}]=>{mapping[target]}")
    return "|".join(chunks)


def _content_tokens(prompt: str) -> set[str]:
    raw = set(re.findall(r"[A-Za-z_]+[A-Za-z0-9_]*", prompt))
    return {x for x in raw if x not in STRUCTURAL_WHITELIST}


def _assert_complete_factorial(cases: list[dict[str, Any]]) -> None:
    cells = Counter(
        (c["semantic_target"], c["output_code_identity"], c["probe_query_negated"])
        for c in cases
    )
    expected = {(t, c, p) for t in TARGETS for c in CODES for p in POLARITIES}
    if set(cells) != expected:
        missing = sorted(expected - set(cells))
        extra = sorted(set(cells) - expected)
        raise AssertionError(
            f"COMPLETE_THREE_BY_THREE_BY_TWO_FACTORIAL_FAILED:missing={missing}:extra={extra}"
        )
    unequal = {cell: count for cell, count in cells.items() if count != 1}
    if unequal:
        raise AssertionError(f"COMPLETE_FACTORIAL_REPLICATE_COUNT_MISMATCH:{unequal}")

    target_polarity = Counter((c["semantic_target"], c["probe_query_negated"]) for c in cases)
    for target in TARGETS:
        if target_polarity[(target, False)] != target_polarity[(target, True)]:
            raise AssertionError(f"TARGET_QUERY_POLARITY_IMBALANCE:{target}")

    target_code_polarity = Counter(
        (c["semantic_target"], c["output_code_identity"], c["probe_query_negated"])
        for c in cases
    )
    for target in TARGETS:
        for code in CODES:
            if target_code_polarity[(target, code, False)] != target_code_polarity[(target, code, True)]:
                raise AssertionError(f"TARGET_CODE_QUERY_POLARITY_IMBALANCE:{target}:{code}")


def build_cases(split: str) -> dict[str, Any]:
    split = split.strip().upper()
    if split not in SPLITS:
        raise ValueError(f"SPLIT_INVALID:{split}")
    rows: list[dict[str, Any]] = []
    for scenario in range(3):
        mapping = _codebook_permutation(scenario)
        demo = _demo_block(mapping, split, scenario)
        for target_index, target in enumerate(TARGETS):
            sym = _symbols(split, scenario, target_index)
            output_code = mapping[target]
            for polarity in POLARITIES:
                probe = _relation_fragment(target, polarity, sym)
                prompt = f"/no_think\n{demo}|P[{probe}]=>"
                lowered_tokens = set(re.findall(r"[a-z_]+", prompt.lower()))
                leaked = [word for word in BANNED_MODEL_FACING if word in lowered_tokens]
                if leaked:
                    raise RuntimeError(f"MODEL_FACING_BANNED_LEXEME:{target}:{','.join(leaked)}")
                scenario_descriptor = {
                    "schema": "STRUCTURAL_LOGIC_SCENARIO_FAMILY/v2",
                    "split": split,
                    "scenario": scenario,
                }
                lexical_descriptor = {
                    "schema": "STRUCTURAL_LOGIC_LEXICAL_FAMILY/v2",
                    "split": split,
                    "scenario": scenario,
                }
                codebook_descriptor = {"scenario": scenario, "mapping": mapping}
                paired_descriptor = {
                    "split": split,
                    "scenario": scenario,
                    "target_index": target_index,
                    "target": target,
                    "output_code": output_code,
                }
                rows.append({
                    "schema": CASE_SCHEMA,
                    "case_id": f"{split.lower()}-struct-v2-{scenario}-{target_index}-p{int(polarity)}",
                    "seed": (
                        (173000 if split == "CALIBRATION" else 183000)
                        + scenario * 1009 + target_index * 101 + int(polarity) * 17
                    ),
                    "semantic_target": target,
                    "output_code_identity": output_code,
                    "prompt": prompt,
                    "prompt_sha256": _prompt_sha(prompt),
                    "scenario_family_sha256": _sha(scenario_descriptor),
                    "lexical_family_sha256": _sha(lexical_descriptor),
                    "codebook_family_sha256": _sha(codebook_descriptor),
                    "paired_polarity_family_sha256": _sha(paired_descriptor),
                    "model_facing_target_identity_exposed": False,
                    "model_facing_explicit_semantic_labels": False,
                    "probe_query_negated": polarity,
                })

    _assert_complete_factorial(rows)
    return {
        "schema": SCHEMA,
        "split": split,
        "case_count": len(rows),
        "factorial": {
            "semantic_targets": len(TARGETS),
            "output_codes": len(CODES),
            "query_polarities": len(POLARITIES),
            "replicates_per_cell": 1,
            "target_query_polarity_mutual_information_bits_by_construction": 0.0,
        },
        "banned_model_facing_lexemes": list(BANNED_MODEL_FACING),
        "structural_overlap_whitelist": sorted(STRUCTURAL_WHITELIST),
        "content_vocabulary": sorted(set().union(*(_content_tokens(c["prompt"]) for c in rows))),
        "cases": rows,
    }


def lexical_disjointness(calibration: dict[str, Any], holdout: dict[str, Any]) -> dict[str, Any]:
    c = set(calibration["content_vocabulary"])
    h = set(holdout["content_vocabulary"])
    overlap = sorted(c & h)
    return {
        "content_overlap": overlap,
        "content_overlap_count": len(overlap),
        "basis_holdout_lexically_disjoint": not overlap,
        "calibration_content_vocabulary_sha256": _sha(sorted(c)),
        "holdout_content_vocabulary_sha256": _sha(sorted(h)),
        "audit_sha256": _sha({"calibration": sorted(c), "holdout": sorted(h), "overlap": overlap}),
    }


def build_bundle() -> dict[str, Any]:
    calibration = build_cases("CALIBRATION")
    holdout = build_cases("HOLDOUT")
    audit = lexical_disjointness(calibration, holdout)
    if audit["basis_holdout_lexically_disjoint"] is not True:
        raise AssertionError(f"CONTENT_LEXICAL_OVERLAP:{audit['content_overlap']}")
    out = {
        "schema": SCHEMA,
        "calibration": calibration,
        "holdout": holdout,
        "lexical_disjointness_audit": audit,
        "model_executed": False,
        "holdout_opened_by_generator": False,
        "runtime_credit_minted": False,
        "frozen_v1_generator_modified": False,
    }
    out["bundle_sha256"] = _sha(out)
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
