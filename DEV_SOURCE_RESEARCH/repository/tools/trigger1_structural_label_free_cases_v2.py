#!/usr/bin/env python3
"""Generate exact-balanced label-free Trigger-1 structural case specs.

This is a successor to trigger1_structural_label_free_cases.py. It intentionally does
not modify the already-dispatched/frozen v1 experiment. V2 closes a residual nuisance:
with three scenarios, query polarity was only set-balanced, not count-balanced by class.

V2 uses six scenarios, giving an exact 3 (semantic target) x 3 (opaque output code) x
2 (query polarity) factorial once per split. Probe lexical identities are shared across
targets within each scenario, so arbitrary content symbols cannot identify the target.
CALIBRATION and HOLDOUT use disjoint content-symbol vocabularies.

The semantic class exists only in evaluator metadata; model-facing prompts contain no
canonical class names or decision/compliance synonyms.
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
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v2"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
SPLITS = ("CALIBRATION", "HOLDOUT")
SCENARIO_COUNT = 6
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
        "CALIBRATION": (
            "kav", "lem", "sir", "tup", "wex", "bim", "cor", "fyn", "guz",
            "mep", "lod", "rax", "vib", "nex", "sul", "pav", "jor", "ket",
        ),
        "HOLDOUT": (
            "zop", "nuf", "qir", "vel", "dax", "jom", "pex", "ryl", "huc",
            "taf", "min", "sov", "gek", "lur", "bap", "cex", "wid", "voq",
        ),
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


def _relation_fragment(target: str, polarity: int, sym: dict[str, str]) -> str:
    """Return a formal mini-world whose query has the evaluator-side target relation."""
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
    # Two complete Latin-square rotations across six scenarios. Combined with the
    # alternating polarity rule, every target x code cell appears once per polarity.
    rotation = scenario % len(CODES)
    return {target: CODES[(i + rotation) % len(CODES)] for i, target in enumerate(TARGETS)}


def _demo_block(mapping: dict[str, str], split: str, scenario: int) -> str:
    chunks = []
    for i, target in enumerate(TARGETS, start=1):
        polarity = (scenario + i) % 2
        sym = _symbols(split, scenario, i + 3)
        chunks.append(f"D{i}[{_relation_fragment(target, polarity, sym)}]=>{mapping[target]}")
    return "|".join(chunks)


def _content_tokens(prompt: str) -> set[str]:
    raw = set(re.findall(r"[A-Za-z_]+[A-Za-z0-9_]*", prompt))
    return {x for x in raw if x not in STRUCTURAL_WHITELIST}


def build_cases(split: str) -> dict[str, Any]:
    split = split.strip().upper()
    if split not in SPLITS:
        raise ValueError(f"SPLIT_INVALID:{split}")

    cases: list[dict[str, Any]] = []
    for scenario in range(SCENARIO_COUNT):
        mapping = _codebook_permutation(scenario)
        demo = _demo_block(mapping, split, scenario)

        # Crucially, all three target cases in a scenario reuse the same arbitrary
        # probe symbols. Lexical identity therefore cannot identify semantic target.
        probe_symbols = _symbols(split, scenario, 0)
        lexical_descriptor = {
            "schema": "STRUCTURAL_LOGIC_LEXICAL_FAMILY/v2",
            "split": split,
            "scenario": scenario,
            "probe_symbols": probe_symbols,
        }
        lexical_family_sha = _sha(lexical_descriptor)

        for target_index, target in enumerate(TARGETS):
            polarity = (scenario + target_index) % 2
            probe = _relation_fragment(target, polarity, probe_symbols)
            prompt = f"/no_think\n{demo}|P[{probe}]=>"
            lowered_tokens = set(re.findall(r"[a-z_]+", prompt.lower()))
            leaked = [word for word in BANNED_MODEL_FACING if word in lowered_tokens]
            if leaked:
                raise RuntimeError(f"MODEL_FACING_BANNED_LEXEME:{target}:{','.join(leaked)}")

            output_code = mapping[target]
            scenario_descriptor = {
                "schema": "STRUCTURAL_LOGIC_SCENARIO_FAMILY/v2",
                "split": split,
                "scenario": scenario,
            }
            codebook_descriptor = {
                "schema": "STRUCTURAL_LOGIC_CODEBOOK_FAMILY/v2",
                "scenario": scenario,
                "mapping": mapping,
            }
            case = {
                "schema": CASE_SCHEMA,
                "case_id": f"{split.lower()}-struct-v2-{scenario}-{target_index}",
                "seed": (173000 if split == "CALIBRATION" else 183000) + scenario * 101 + target_index * 17,
                "semantic_target": target,
                "output_code_identity": output_code,
                "prompt": prompt,
                "prompt_sha256": _prompt_sha(prompt),
                "scenario_family_sha256": _sha(scenario_descriptor),
                "lexical_family_sha256": lexical_family_sha,
                "codebook_family_sha256": _sha(codebook_descriptor),
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
                "probe_query_negated": bool(polarity),
                "factorial_cell": {
                    "semantic_target": target,
                    "output_code_identity": output_code,
                    "probe_query_negated": bool(polarity),
                },
            }
            cases.append(case)

    triple_counts = Counter(
        (c["semantic_target"], c["output_code_identity"], c["probe_query_negated"])
        for c in cases
    )
    expected_triples = {(t, code, neg) for t in TARGETS for code in CODES for neg in (False, True)}
    if set(triple_counts) != expected_triples or any(n != 1 for n in triple_counts.values()):
        raise AssertionError("FULL_THREE_BY_THREE_BY_TWO_FACTORIAL_FAILED")

    target_code_counts = Counter((c["semantic_target"], c["output_code_identity"]) for c in cases)
    if any(target_code_counts[(t, code)] != 2 for t in TARGETS for code in CODES):
        raise AssertionError("TARGET_CODE_REPLICATION_FAILED")

    target_polarity_counts = Counter((c["semantic_target"], c["probe_query_negated"]) for c in cases)
    if any(target_polarity_counts[(t, neg)] != 3 for t in TARGETS for neg in (False, True)):
        raise AssertionError("TARGET_POLARITY_EXACT_BALANCE_FAILED")

    return {
        "schema": SCHEMA,
        "split": split,
        "case_count": len(cases),
        "factorial_design": {
            "semantic_targets": 3,
            "output_codes": 3,
            "query_polarities": 2,
            "cell_count": 18,
            "replicates_per_target_code": 2,
            "replicates_per_target_polarity": 3,
            "exact_target_x_code_x_polarity_once": True,
            "probe_lexical_identity_shared_across_targets_within_scenario": True,
        },
        "banned_model_facing_lexemes": list(BANNED_MODEL_FACING),
        "structural_overlap_whitelist": sorted(STRUCTURAL_WHITELIST),
        "content_vocabulary": sorted(set().union(*(_content_tokens(c["prompt"]) for c in cases))),
        "cases": cases,
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
