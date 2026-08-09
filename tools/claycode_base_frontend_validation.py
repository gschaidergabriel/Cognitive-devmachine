#!/usr/bin/env python3
"""Evidence-oriented frontend validation for the active ClayCode BASE D grammar repair.

This is intentionally narrower than a canonical typed-AST proof. It establishes:
1) strict parser construction (including regex collisions when interegular is present),
2) full current G9 V3 + Dialect V3 source acceptance,
3) deterministic parse fingerprints across repeated parses,
4) explicit negative/positive keyword + newline boundary tests,
5) lexical-operator/literal discrimination in the parse fingerprint.

It must not be used to claim CC-WP-02 PASS by itself; typed canonical IR/type semantics
remain downstream requirements. V9 resolves both the V5 strict-LALR ambiguity and V6's
current-corpus regression by contextually distinguishing bare Needle.owns from dotted
Needle.lowers/Needle.owns prefix relations with an explicit same-line argument.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_tree(node):
    if isinstance(node, Tree):
        return [str(node.data), [canonical_tree(x) for x in node.children]]
    return [getattr(node, "type", type(node).__name__), str(node)]


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(canonical_tree(tree), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def try_parse(parser: Lark, source: str) -> tuple[bool, str | None]:
    try:
        parser.parse(source)
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def pair_check(parser: Lark, left: str, right: str, expect_same: bool) -> dict:
    lt = parser.parse(left)
    rt = parser.parse(right)
    lh, rh = tree_hash(lt), tree_hash(rt)
    same = lh == rh
    return {
        "left": left,
        "right": right,
        "left_hash": lh,
        "right_hash": rh,
        "expected_same": expect_same,
        "observed_same": same,
        "pass": same == expect_same,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--output")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")
    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
    )

    source_results = []
    for path in SOURCES:
        text = path.read_text(encoding="utf-8")
        t1 = parser.parse(text)
        t2 = parser.parse(text)
        h1, h2 = tree_hash(t1), tree_hash(t2)
        source_results.append({
            "path": str(path.relative_to(ROOT)),
            "source_sha256": sha256_bytes(text.encode("utf-8")),
            "parse_tree_hash": h1,
            "repeat_parse_tree_hash": h2,
            "deterministic_repeat": h1 == h2,
            "tree_nodes": sum(1 for _ in t1.iter_subtrees()),
        })

    negative_cases = {
        "if_as_record_field_identifier": "record X { if:Int }\n",
        "invariant_as_record_field_identifier": "record X { invariant:Int }\n",
        "if_as_parameter_identifier": "needle f(if:Int)->Int\n",
        "invariant_as_parameter_identifier": "needle f(invariant:Int)->Int\n",
        "implicit_english_noun_phrase": "rule Claude_only consumes latest stack + writes task receipts\n",
        "dotted_relation_missing_object": "rule Needle.lowers\n",
    }
    positive_cases = {
        "bare_needle_owns_operand": "rule 4B_need_not_learn Needle.owns\n",
        "if_statement": "cycle(input:Ref){\nif input {\ntrue\n}\n}\n",
        "invariant_statement": "invariant activation!=truth\n",
        "multiple_newlines_record": "record X {\n\n a:Int\n\n b:Int\n\n}\n",
        "multiple_newlines_cycle": "cycle(input:Ref){\n\n input\n\n}\n",
        "keyword_like_non_reserved_identifier": "record X { status:Int; dialect:Int; version:Int; requires:Int }\n",
        "dotted_relation_lowering": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "dotted_relation_owns": "rule Needle.owns [tool_schema,api_wire]\n",
        "relation_assignment": "rule external_effect lifecycle=[REQUESTED,AUTHORIZED,DONE]\n",
        "explicit_relation_chain": "rule Claude_only consumes latest_stack + Claude_only writes task_receipts\n",
    }

    neg = []
    for name, src in negative_cases.items():
        ok, err = try_parse(parser, src)
        neg.append({"case": name, "expected": "REJECT", "accepted": ok, "pass": not ok, "error": err})
    pos = []
    for name, src in positive_cases.items():
        ok, err = try_parse(parser, src)
        pos.append({"case": name, "expected": "ACCEPT", "accepted": ok, "pass": ok, "error": err})

    discrimination_sources = {
        "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
        "gte_vs_lte": ("rule x>=0\n", "rule x<=0\n"),
        "equal_vs_not_equal": ("rule x=0\n", "rule x!=0\n"),
        "plus_vs_minus": ("rule x+1\n", "rule x-1\n"),
        "and_vs_or": ("rule x&&true\n", "rule x||true\n"),
        "true_vs_false": ("rule true\n", "rule false\n"),
        "ordered_call_arguments": ("rule f(a,b)\n", "rule f(b,a)\n"),
        "dotted_relation_kind": ("rule Needle.lowers X\n", "rule Needle.owns X\n"),
        "bare_owns_vs_prefix_owns": ("rule 4B_need_not_learn Needle.owns\n", "rule Needle.owns X\n"),
    }
    discrimination = [
        {"case": name, **pair_check(parser, left, right, expect_same=False)}
        for name, (left, right) in discrimination_sources.items()
    ]

    equivalence_sources = {
        "ignored_space_comment": ("rule x>0\n", "rule   x > 0 // comment\n"),
    }
    equivalence = [
        {"case": name, **pair_check(parser, left, right, expect_same=True)}
        for name, (left, right) in equivalence_sources.items()
    ]

    passed = (
        all(x["deterministic_repeat"] for x in source_results)
        and all(x["pass"] for x in neg)
        and all(x["pass"] for x in pos)
        and all(x["pass"] for x in discrimination)
        and all(x["pass"] for x in equivalence)
    )
    out = {
        "schema_version": "1.4",
        "experiment": "ClayCode BASE D repaired-frontend full-corpus validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "runtime": {
            "parser": "lark",
            "mode": "lalr/contextual",
            "strict": True,
            "keep_all_tokens": True,
        },
        "sources": source_results,
        "negative_cases": neg,
        "positive_cases": pos,
        "lexical_discrimination_cases": discrimination,
        "lexical_equivalence_cases": equivalence,
        "pass": passed,
        "scope_guard": "PASS proves strict parser construction, exact current G9/Dialect acceptance, deterministic literal-preserving parse fingerprints and listed V5/V6 regression/boundary cases only. It does not close CC-WP-02 without the canonicalizer/differential receipts and does not prove typed IR/type/effect semantics."
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
