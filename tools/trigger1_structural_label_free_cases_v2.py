#!/usr/bin/env python3
"""Generate joint-counterbalanced label-free Trigger-1 structural case specs.

This is the non-interventional successor to the frozen v1 experiment and the first
marginally-balanced v2 design. It closes a stricter nuisance leak: balancing probe
query polarity marginally is insufficient when model-facing demonstration context
co-varies with probe polarity.

The construction uses three Latin-square codebook scenarios. Inside every scenario,
all three evaluator-side semantic targets are crossed with both probe polarities while
reusing the *same* model-facing demonstration block and the same arbitrary probe lexical
identity. Therefore every scenario contains:

    3 targets x 2 probe polarities = 6 cases,

and across the three codebook scenarios each target x opaque-code x probe-polarity cell
occurs exactly once (18 cases per split).

Semantic target identity and nuisance audits remain evaluator-side metadata. The model
sees only the formal demonstrations, formal probe, and opaque A/B/C codebook.
CALIBRATION and HOLDOUT keep disjoint content-symbol vocabularies.

This generator is execution-free and mints no runtime, J-Space, HCU, EntityOS, or
training credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER1_STRUCTURAL_LABEL_FREE_CASESET/v2"
CASE_SCHEMA = "CLAY_TRIGGER1_LABEL_FREE_FACTORIAL_CASE_SPEC/v2"
TARGETS = ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL")
CODES = ("A", "B", "C")
SPLITS = ("CALIBRATION", "HOLDOUT")
SCENARIO_COUNT = 3
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
    rotation = scenario % len(CODES)
    return {target: CODES[(i + rotation) % len(CODES)] for i, target in enumerate(TARGETS)}


def _demo_polarity_signature(scenario: int) -> tuple[bool, bool, bool]:
    return tuple(bool((scenario + i) % 2) for i in range(1, 4))


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


def _mutual_information_bits(xs: list[Any], ys: list[Any]) -> float:
    if len(xs) != len(ys):
        raise ValueError("MI_LENGTH_MISMATCH")
    total = len(xs)
    if total == 0:
        return 0.0
    x_counts = Counter(xs)
    y_counts = Counter(ys)
    joint = Counter(zip(xs, ys))
    out = 0.0
    for (x, y), count in joint.items():
        p_xy = count / total
        p_x = x_counts[x] / total
        p_y = y_counts[y] / total
        out += p_xy * math.log2(p_xy / (p_x * p_y))
    return out


def _best_target_accuracy_from_joint_nuisance(cases: list[dict[str, Any]]) -> float:
    if not cases:
        return 0.0
    grouped: dict[tuple[str, bool], Counter[str]] = {}
    for case in cases:
        key = (case["demo_context_sha256"], case["probe_query_negated"])
        grouped.setdefault(key, Counter())[case["semantic_target"]] += 1
    correct = sum(max(counts.values()) for counts in grouped.values())
    return correct / len(cases)


def _joint_nuisance_audit(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Fail closed if demo context + probe polarity jointly predict semantic target."""
    targets = [c["semantic_target"] for c in cases]
    probe_polarities = [c["probe_query_negated"] for c in cases]
    joint_keys = [
        (c["demo_context_sha256"], c["probe_query_negated"])
        for c in cases
    ]
    marginal_mi = _mutual_information_bits(targets, probe_polarities)
    joint_mi = _mutual_information_bits(targets, joint_keys)
    best_joint_accuracy = _best_target_accuracy_from_joint_nuisance(cases)
    prior = 1.0 / len(TARGETS)

    strata = Counter(
        (
            c["demo_context_sha256"],
            c["probe_query_negated"],
            c["semantic_target"],
        )
        for c in cases
    )
    context_polarity_keys = {
        (c["demo_context_sha256"], c["probe_query_negated"])
        for c in cases
    }
    for context_sha, polarity in context_polarity_keys:
        counts = {
            target: strata[(context_sha, polarity, target)]
            for target in TARGETS
        }
        if len(set(counts.values())) != 1 or next(iter(counts.values())) != 1:
            raise AssertionError(
                f"JOINT_DEMO_QUERY_TARGET_IMBALANCE:{context_sha}:{polarity}:{counts}"
            )

    if abs(marginal_mi) > 1e-12:
        raise AssertionError(f"TARGET_QUERY_POLARITY_MI_NONZERO:{marginal_mi}")
    if abs(joint_mi) > 1e-12:
        raise AssertionError(f"TARGET_JOINT_DEMO_QUERY_POLARITY_MI_NONZERO:{joint_mi}")
    if abs(best_joint_accuracy - prior) > 1e-12:
        raise AssertionError(
            f"JOINT_NUISANCE_TARGET_ACCURACY_ABOVE_PRIOR:{best_joint_accuracy}:{prior}"
        )

    return {
        "schema": "CLAY_TRIGGER1_JOINT_DEMO_QUERY_NUISANCE_AUDIT/v1",
        "target_query_polarity_mutual_information_bits": marginal_mi,
        "target_joint_demo_context_query_polarity_mutual_information_bits": joint_mi,
        "best_target_accuracy_using_demo_context_plus_query_polarity": best_joint_accuracy,
        "balanced_target_prior_accuracy": prior,
        "every_demo_context_x_query_polarity_stratum_contains_all_targets_once": True,
    }


def build_cases(split: str) -> dict[str, Any]:
    split = split.strip().upper()
    if split not in SPLITS:
        raise ValueError(f"SPLIT_INVALID:{split}")

    cases: list[dict[str, Any]] = []
    for scenario in range(SCENARIO_COUNT):
        mapping = _codebook_permutation(scenario)
        demo = _demo_block(mapping, split, scenario)
        demo_context = f"/no_think\n{demo}"
        demo_context_sha = _prompt_sha(demo_context)
        demo_polarity_signature = _demo_polarity_signature(scenario)

        # Share arbitrary lexical identity across all targets and both probe polarities
        # so neither target nor a polarity phase can be encoded by content symbols.
        probe_symbols = _symbols(split, scenario, 0)
        lexical_descriptor = {
            "schema": "STRUCTURAL_LOGIC_LEXICAL_FAMILY/v2",
            "split": split,
            "scenario": scenario,
            "probe_symbols": probe_symbols,
        }
        lexical_family_sha = _sha(lexical_descriptor)

        scenario_descriptor = {
            "schema": "STRUCTURAL_LOGIC_SCENARIO_FAMILY/v2",
            "split": split,
            "scenario": scenario,
            "demo_context_sha256": demo_context_sha,
        }
        scenario_family_sha = _sha(scenario_descriptor)
        codebook_descriptor = {
            "schema": "STRUCTURAL_LOGIC_CODEBOOK_FAMILY/v2",
            "scenario": scenario,
            "mapping": mapping,
        }
        codebook_family_sha = _sha(codebook_descriptor)

        for target_index, target in enumerate(TARGETS):
            for polarity in (0, 1):
                probe = _relation_fragment(target, polarity, probe_symbols)
                prompt = f"{demo_context}|P[{probe}]=>"
                lowered_tokens = set(re.findall(r"[a-z_]+", prompt.lower()))
                leaked = [word for word in BANNED_MODEL_FACING if word in lowered_tokens]
                if leaked:
                    raise RuntimeError(
                        f"MODEL_FACING_BANNED_LEXEME:{target}:{','.join(leaked)}"
                    )

                output_code = mapping[target]
                case = {
                    "schema": CASE_SCHEMA,
                    "case_id": f"{split.lower()}-struct-v2-{scenario}-{target_index}-p{polarity}",
                    "seed": (
                        (173000 if split == "CALIBRATION" else 183000)
                        + scenario * 1009
                        + target_index * 101
                        + polarity * 17
                    ),
                    "semantic_target": target,
                    "output_code_identity": output_code,
                    "prompt": prompt,
                    "prompt_sha256": _prompt_sha(prompt),
                    "demo_context_sha256": demo_context_sha,
                    "demo_query_negation_signature": list(demo_polarity_signature),
                    "scenario_family_sha256": scenario_family_sha,
                    "lexical_family_sha256": lexical_family_sha,
                    "codebook_family_sha256": codebook_family_sha,
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
    expected_triples = {
        (target, code, negated)
        for target in TARGETS
        for code in CODES
        for negated in (False, True)
    }
    if set(triple_counts) != expected_triples or any(n != 1 for n in triple_counts.values()):
        raise AssertionError("FULL_THREE_BY_THREE_BY_TWO_FACTORIAL_FAILED")

    target_code_counts = Counter(
        (c["semantic_target"], c["output_code_identity"])
        for c in cases
    )
    if any(target_code_counts[(t, code)] != 2 for t in TARGETS for code in CODES):
        raise AssertionError("TARGET_CODE_REPLICATION_FAILED")

    target_polarity_counts = Counter(
        (c["semantic_target"], c["probe_query_negated"])
        for c in cases
    )
    if any(target_polarity_counts[(t, neg)] != 3 for t in TARGETS for neg in (False, True)):
        raise AssertionError("TARGET_POLARITY_EXACT_BALANCE_FAILED")

    # Stronger than marginal counterbalancing: within each exact model-facing demo
    # context, every target appears once with each probe polarity.
    by_scenario: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_scenario.setdefault(case["scenario_family_sha256"], []).append(case)
    if len(by_scenario) != SCENARIO_COUNT:
        raise AssertionError("SCENARIO_COUNT_MISMATCH")
    for scenario_sha, group in by_scenario.items():
        if len(group) != len(TARGETS) * 2:
            raise AssertionError(f"SCENARIO_CELL_COUNT_MISMATCH:{scenario_sha}")
        if len({c["demo_context_sha256"] for c in group}) != 1:
            raise AssertionError(f"DEMO_CONTEXT_NOT_SHARED_WITHIN_SCENARIO:{scenario_sha}")
        if len({c["lexical_family_sha256"] for c in group}) != 1:
            raise AssertionError(f"PROBE_LEXICAL_IDENTITY_NOT_SHARED_WITHIN_SCENARIO:{scenario_sha}")
        for target in TARGETS:
            polarities = {
                c["probe_query_negated"]
                for c in group
                if c["semantic_target"] == target
            }
            if polarities != {False, True}:
                raise AssertionError(
                    f"TARGET_NOT_CROSSED_WITH_POLARITY_WITHIN_DEMO:{scenario_sha}:{target}"
                )

    joint_audit = _joint_nuisance_audit(cases)

    return {
        "schema": SCHEMA,
        "split": split,
        "case_count": len(cases),
        "factorial_design": {
            "semantic_targets": 3,
            "output_codes": 3,
            "query_polarities": 2,
            "codebook_scenarios": SCENARIO_COUNT,
            "cases_per_scenario": 6,
            "cell_count": 18,
            "replicates_per_target_code": 2,
            "replicates_per_target_polarity": 3,
            "exact_target_x_code_x_polarity_once": True,
            "probe_lexical_identity_shared_across_targets_and_polarities_within_scenario": True,
            "demo_context_shared_across_targets_and_polarities_within_scenario": True,
        },
        "joint_nuisance_audit": joint_audit,
        "banned_model_facing_lexemes": list(BANNED_MODEL_FACING),
        "structural_overlap_whitelist": sorted(STRUCTURAL_WHITELIST),
        "content_vocabulary": sorted(
            set().union(*(_content_tokens(c["prompt"]) for c in cases))
        ),
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
        "canonical_semantic_jspace_promotion": False,
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
