#!/usr/bin/env python3
"""Bounded falsifier for ClayCode BASE V19 delimiter-normalizable grammar.

Research scope only. This probe asks whether V19 removes the two concrete V18 defect
families without silently stealing longer valid qids:
  1. strict LALR construction under interegular;
  2. full current G9 V3 + Dialect V3 acceptance;
  3. reserved-prefix/namespace shadow resistance;
  4. exact owns-call vs owns/lowers-relation delimiter classification;
  5. horizontal-trivia metamorphic stability of the special-token normalization sketch.

It does NOT prove canonical AST/hash equivalence to V17 and cannot promote CC-WP-02.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from lark import Token, Tree

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V19_DELIMITER_NORMALIZABLE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
SPECIAL = {"NEEDLE_OWNS_CALL", "NEEDLE_OWNS_REL", "NEEDLE_LOWERS_REL"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def token_types(tree: Tree) -> list[str]:
    return [t.type for t in tree.scan_values(lambda v: isinstance(v, Token))]


def special_tokens(tree: Tree) -> list[dict[str, str]]:
    out = []
    for t in tree.scan_values(lambda v: isinstance(v, Token) and v.type in SPECIAL):
        out.append({"type": t.type, "value": str(t)})
    return out


def try_parse(parser, source: str):
    try:
        return parser.parse(source), None
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def normalization_sketch(tok_type: str, value: str) -> str:
    if tok_type == "NEEDLE_OWNS_CALL":
        return "Needle.owns("
    if tok_type == "NEEDLE_OWNS_REL":
        return "Needle.owns"
    if tok_type == "NEEDLE_LOWERS_REL":
        return "Needle.lowers"
    raise ValueError(tok_type)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path)
    ap.add_argument("--seed", type=int, default=190017)
    ap.add_argument("--fuzz-cases", type=int, default=2000)
    args = ap.parse_args()

    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    parser = front.build_parser(grammar_text, strict=True)

    source_results = []
    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        tree1 = parser.parse(text)
        tree2 = parser.parse(text)
        c1 = front.canonical_bytes(front.canonical_node(tree1))
        c2 = front.canonical_bytes(front.canonical_node(tree2))
        source_results.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256(text.encode("utf-8")),
            "canonical_sha256": sha256(c1),
            "repeat_canonical_sha256": sha256(c2),
            "deterministic_repeat": c1 == c2,
            "special_token_count": len(special_tokens(tree1)),
        })

    fixed = []
    cases = [
        ("bare_owns", "rule Needle.owns\n", True, []),
        ("bare_lowers", "rule Needle.lowers\n", False, []),
        ("owns_call_tight", "rule Needle.owns(X)\n", True, ["NEEDLE_OWNS_CALL"]),
        ("owns_call_space", "rule Needle.owns (X)\n", True, ["NEEDLE_OWNS_CALL"]),
        ("owns_call_tab", "rule Needle.owns\t(X)\n", True, ["NEEDLE_OWNS_CALL"]),
        ("owns_relation_space", "rule Needle.owns X\n", True, ["NEEDLE_OWNS_REL"]),
        ("owns_relation_tab", "rule Needle.owns\tX\n", True, ["NEEDLE_OWNS_REL"]),
        ("lowers_relation_space", "rule Needle.lowers X\n", True, ["NEEDLE_LOWERS_REL"]),
        ("lowers_relation_tab", "rule Needle.lowers\tX\n", True, ["NEEDLE_LOWERS_REL"]),
        ("owns_extra_qid", "rule Needle.owns_extra\n", True, []),
        ("ownership_qid", "rule Needle.ownership\n", True, []),
        ("lowers_more_qid", "rule Needle.lowers_more\n", True, []),
        ("lowersuffix_qid", "rule Needle.lowersuffix\n", True, []),
    ]
    for name, src, expect_accept, expect_special in cases:
        tree, err = try_parse(parser, src)
        got_accept = tree is not None
        got_special = [x["type"] for x in special_tokens(tree)] if tree is not None else []
        fixed.append({
            "case": name,
            "source": src,
            "expected_accept": expect_accept,
            "observed_accept": got_accept,
            "expected_special": expect_special,
            "observed_special": got_special,
            "pass": got_accept == expect_accept and (not got_accept or got_special == expect_special),
            "error": err,
        })

    trivia_groups = []
    group_defs = {
        "owns_call": ["rule Needle.owns(X)\n", "rule Needle.owns (X)\n", "rule Needle.owns\t(X)\n", "rule Needle.owns \t (X)\n"],
        "owns_relation": ["rule Needle.owns X\n", "rule Needle.owns  X\n", "rule Needle.owns\tX\n", "rule Needle.owns \t X\n"],
        "lowers_relation": ["rule Needle.lowers X\n", "rule Needle.lowers  X\n", "rule Needle.lowers\tX\n", "rule Needle.lowers \t X\n"],
    }
    for name, variants in group_defs.items():
        observed = []
        for src in variants:
            tree = parser.parse(src)
            toks = special_tokens(tree)
            observed.append({
                "source": src,
                "tokens": toks,
                "normalized_special": [normalization_sketch(x["type"], x["value"]) for x in toks],
            })
        signatures = {tuple(x["normalized_special"]) for x in observed}
        trivia_groups.append({"group": name, "variants": observed, "pass": len(signatures) == 1 and all(len(x["tokens"]) == 1 for x in observed)})

    rng = random.Random(args.seed)
    fuzz_failures = []
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    prefixes = ["owns", "lowers"]
    for i in range(args.fuzz_cases):
        base = rng.choice(prefixes)
        # Force a longer identifier, never an exact reserved spelling.
        suffix = rng.choice(["_", "X", "hip", "More", "2"]) + "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 12)))
        ident = base + suffix
        src = f"rule Needle.{ident}\n"
        tree, err = try_parse(parser, src)
        if tree is None:
            fuzz_failures.append({"i": i, "source": src, "reason": "rejected_longer_qid", "error": err})
            continue
        specials = special_tokens(tree)
        if specials:
            fuzz_failures.append({"i": i, "source": src, "reason": "special_prefix_shadow", "special": specials})
        if len(fuzz_failures) >= 25:
            break

    passed = (
        all(x["deterministic_repeat"] for x in source_results)
        and all(x["pass"] for x in fixed)
        and all(x["pass"] for x in trivia_groups)
        and not fuzz_failures
    )

    result = {
        "schema_version": "1.0",
        "experiment": "V19_DELIMITER_NAMESPACE_FUZZ_AND_TRIVIA_METAMORPHIC",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "truth_scope": "BOUNDED_PARSER_CANDIDATE_FALSIFIER_NOT_PROMOTION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": sha256(grammar_text.encode("utf-8")),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "lark_version": package_version("lark"),
            "interegular_version": package_version("interegular"),
            "parser": "lalr/contextual",
            "strict": True,
            "maybe_placeholders": False,
            "keep_all_tokens": True,
        },
        "sources": source_results,
        "fixed_cases": fixed,
        "trivia_metamorphic_groups": trivia_groups,
        "namespace_fuzz": {
            "seed": args.seed,
            "requested_cases": args.fuzz_cases,
            "failures": fuzz_failures,
            "pass": not fuzz_failures,
        },
        "pass": passed,
        "scope_guard": "PASS only falsifies V18-style strict/prefix-shadow defects for this V19 candidate over current full sources plus bounded metamorphic/namespace tests. It does not prove V17 canonical semantic-hash equivalence, typed IR correctness, Ubuntu target acceptance, CC-WP-02 PASS, or BASE promotion.",
    }
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
