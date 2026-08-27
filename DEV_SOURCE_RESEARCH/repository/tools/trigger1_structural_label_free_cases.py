#!/usr/bin/env python3
"""Generate external label-free 3x3 Trigger-1 case specs from structural logic.

The semantic class exists only in evaluator metadata. Model-facing prompts never contain
the canonical class names or decision/compliance synonyms. Instead, each prompt contains
three formal demonstrations mapping three logical relation types to a rotated opaque
A/B/C codebook, followed by a probe. The probe's relation is derived from symbols/rules,
not requested by a semantic label.

Query polarity is counterbalanced across all classes so the `!` token is not a NEGATIVE
shortcut. CALIBRATION and HOLDOUT use disjoint content-symbol vocabularies; only a frozen
structural syntax/code whitelist may overlap.

Output feeds tools/trigger1_v7_factorial_case_evidence.py as external case specs.
This generator is execution-free and opens no model holdout by itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v1"
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v1"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
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
    # Latin-square rotation: across the three scenarios every semantic target is
    # paired exactly once with every opaque output code.
    return {target: CODES[(i + scenario) % len(CODES)] for i, target in enumerate(TARGETS)}


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
    for scenario in range(3):
        mapping = _codebook_permutation(scenario)
        demo = _demo_block(mapping, split, scenario)
        for target_index, target in enumerate(TARGETS):
            # Rotate query polarity by scenario and class. Each class therefore appears
            # with both positive and negated query forms across the 3 scenarios.
            polarity = (scenario + target_index) % 2
            sym = _symbols(split, scenario, target_index)
            probe = _relation_fragment(target, polarity, sym)
            prompt = f"/no_think\n{demo}|P[{probe}]=>"
            lowered_tokens = set(re.findall(r"[a-z_]+", prompt.lower()))
            leaked = [word for word in BANNED_MODEL_FACING if word in lowered_tokens]
            if leaked:
                raise RuntimeError(f"MODEL_FACING_BANNED_LEXEME:{target}:{','.join(leaked)}")
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
            case = {
                "schema": CASE_SCHEMA,
                "case_id": f"{split.lower()}-struct-{scenario}-{target_index}",
                "seed": (73000 if split == "CALIBRATION" else 83000) + scenario * 101 + target_index * 17,
                "semantic_target": target,
                "output_code_identity": output_code,
                "prompt": prompt,
                "prompt_sha256": _prompt_sha(prompt),
                "scenario_family_sha256": _sha(scenario_descriptor),
                "lexical_family_sha256": _sha(lexical_descriptor),
                "codebook_family_sha256": _sha(codebook_descriptor),
                "model_facing_target_identity_exposed": False,
                "model_facing_explicit_semantic_labels": False,
                "probe_query_negated": bool(polarity),
            }
            cases.append(case)

    observed = {(c["semantic_target"], c["output_code_identity"]) for c in cases}
    expected = {(t, c) for t in TARGETS for c in CODES}
    if observed != expected:
        raise AssertionError("FULL_THREE_BY_THREE_FACTORIAL_FAILED")
    return {
        "schema": SCHEMA,
        "split": split,
        "case_count": len(cases),
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
