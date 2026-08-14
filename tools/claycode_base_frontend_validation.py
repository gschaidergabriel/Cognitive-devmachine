#!/usr/bin/env python3
"""Evidence-oriented frontend validation for the active ClayCode BASE D grammar repair.

This is intentionally narrower than a canonical typed-AST proof. It establishes:
1) strict parser construction (including regex collisions when interegular is present),
2) full current G9 V3 + Dialect V3 source acceptance,
3) deterministic parse fingerprints across repeated parses,
4) explicit negative/positive keyword + newline boundary tests,
5) lexical-operator/literal discrimination and trivia invariance,
6) production-parser absence semantics for optional grammar elements (no synthetic None child).

V17 is the minimal declarative successor to V9. Besides preserving the V5/V6 repair
obligations, it must close the concrete V9/V10 trivia counterexample where
`Needle.owns(X)` and `Needle.owns (X)` could acquire different parse semantics.
Because V17 uses regex lookahead for the dotted relation/call boundary, strict parser
construction is not treated as complete regex-collision evidence by itself; explicit
metamorphic whitespace-boundary tests are mandatory.
It must not be used to claim CC-WP-02 PASS by itself; strict canonical/target evidence
and downstream typed/effect work remain separate requirements.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def canonical_tree(node):
    if isinstance(node, Tree):
        return [str(node.data), [canonical_tree(x) for x in node.children]]
    return [getattr(node, "type", type(node).__name__), str(node)]


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(canonical_tree(tree), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def count_none_children(node) -> int:
    """Count synthetic absent-option placeholders recursively in a Lark parse tree."""
    if node is None:
        return 1
    if isinstance(node, Tree):
        return sum(count_none_children(child) for child in node.children)
    return 0


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
        "left_none_placeholders": count_none_children(lt),
        "right_none_placeholders": count_none_children(rt),
        "pass": same == expect_same and count_none_children(lt) == 0 and count_none_children(rt) == 0,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--output")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")
    # Use the exact production parser constructor. This intentionally inherits the
    # explicit maybe_placeholders=False semantic-tree contract from the BASE frontend,
    # so validation cannot silently test a different Lark default than production.
    parser = front.build_parser(grammar, strict=True)

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
            "none_placeholder_count": count_none_children(t1),
            "tree_nodes": sum(1 for _ in t1.iter_subtrees()),
        })

    negative_cases = {
        "if_as_record_field_identifier": "record X { if:Int }\n",
        "invariant_as_record_field_identifier": "record X { invariant:Int }\n",
        "if_as_parameter_identifier": "needle f(if:Int)->Int\n",
        "invariant_as_parameter_identifier": "needle f(invariant:Int)->Int\n",
        "implicit_english_noun_phrase": "rule Claude_only consumes latest stack + writes task receipts\n",
        "dotted_relation_missing_object": "rule Needle.lowers\n",
        "reserved_lowers_call_with_trivia": "rule Needle.lowers (X)\n",
        "reserved_lowers_call_with_tab_trivia": "rule Needle.lowers\t(X)\n",
    }
    positive_cases = {
        "bare_needle_owns_operand": "rule 4B_need_not_learn Needle.owns\n",
        "if_statement": "cycle(input:Ref){\nif input {\ntrue\n}\n}\n",
        "invariant_statement": "invariant activation!=truth\n",
        "multiple_newlines_record": "record X {\n\n a:Int\n\n b:Int\n\n}\n",
        "multiple_newlines_cycle": "cycle(input:Ref){\n\n input\n\n}\n",
        "keyword_like_non_reserved_identifier": "record X { status:Int; dialect:Int; version:Int; requires:Int }\n",
        "dotted_relation_lowering": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "dotted_relation_lowering_tab": "rule Needle.lowers\tEffectIntent -> concrete_adapter_plan\n",
        "dotted_relation_owns": "rule Needle.owns [tool_schema,api_wire]\n",
        "dotted_relation_owns_tab": "rule Needle.owns\t[tool_schema,api_wire]\n",
        "qualified_owns_call_tight": "rule Needle.owns(X)\n",
        "qualified_owns_call_spaced": "rule Needle.owns (X)\n",
        "qualified_owns_call_tabbed": "rule Needle.owns\t(X)\n",
        "qualified_owns_call_mixed_trivia": "rule Needle.owns \t (X)\n",
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
        none_count = count_none_children(parser.parse(src)) if ok else None
        pos.append({
            "case": name,
            "expected": "ACCEPT",
            "accepted": ok,
            "none_placeholder_count": none_count,
            "pass": ok and none_count == 0,
            "error": err,
        })

    # Regression for the exact failure family seen in the first Hostinger V9/V17
    # discriminator: absent [] optionals must be represented by absence, never None.
    optional_absence_sources = {
        "record_without_typeparams_or_optional_type": "record X { a:Int }\n",
        "needle_without_params": "needle f()->Int\n",
        "record_without_field_default": "record X { a:Int; b:Ref }\n",
        "simple_module_law": "module clay.demo\nlaw residual>=0\n",
    }
    optional_absence = []
    for name, src in optional_absence_sources.items():
        tree = parser.parse(src)
        none_count = count_none_children(tree)
        optional_absence.append({
            "case": name,
            "source": src,
            "none_placeholder_count": none_count,
            "pass": none_count == 0,
        })

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
        "call_vs_prefix_owns": ("rule Needle.owns(X)\n", "rule Needle.owns X\n"),
    }
    discrimination = [
        {"case": name, **pair_check(parser, left, right, expect_same=False)}
        for name, (left, right) in discrimination_sources.items()
    ]

    equivalence_sources = {
        "ignored_space_comment": ("rule x>0\n", "rule   x > 0 // comment\n"),
        "qualified_owns_call_horizontal_trivia": ("rule Needle.owns(X)\n", "rule Needle.owns (X)\n"),
        "qualified_owns_call_long_horizontal_trivia": ("rule Needle.owns(X)\n", "rule Needle.owns          (X)\n"),
        "qualified_owns_call_tab_trivia": ("rule Needle.owns(X)\n", "rule Needle.owns\t(X)\n"),
        "qualified_owns_call_mixed_horizontal_trivia": ("rule Needle.owns(X)\n", "rule Needle.owns \t (X)\n"),
        "dotted_lowers_rhs_tab_trivia": ("rule Needle.lowers X\n", "rule Needle.lowers\tX\n"),
        "dotted_owns_rhs_tab_trivia": ("rule Needle.owns X\n", "rule Needle.owns\tX\n"),
    }
    equivalence = [
        {"case": name, **pair_check(parser, left, right, expect_same=True)}
        for name, (left, right) in equivalence_sources.items()
    ]

    regex_lookaround_present = "(?=" in grammar or "(?<=" in grammar or "(?!" in grammar or "(?<!" in grammar
    passed = (
        all(x["deterministic_repeat"] and x["none_placeholder_count"] == 0 for x in source_results)
        and all(x["pass"] for x in neg)
        and all(x["pass"] for x in pos)
        and all(x["pass"] for x in optional_absence)
        and all(x["pass"] for x in discrimination)
        and all(x["pass"] for x in equivalence)
    )
    out = {
        "schema_version": "1.7",
        "experiment": "ClayCode BASE D V17 trivia-safe production-frontend full-corpus validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "runtime": {
            "parser": "lark",
            "mode": "lalr/contextual",
            "strict": True,
            "keep_all_tokens": True,
            "production_parser_constructor": "claycode_base_frontend.build_parser",
            "maybe_placeholders": False,
            "lark_version": package_version("lark"),
            "interegular_version": package_version("interegular"),
        },
        "sources": source_results,
        "negative_cases": neg,
        "positive_cases": pos,
        "optional_placeholder_absence_cases": optional_absence,
        "lexical_discrimination_cases": discrimination,
        "lexical_equivalence_cases": equivalence,
        "v9_trivia_counterexample_guard_present": True,
        "metamorphic_relation_boundary_guard_present": True,
        "optional_placeholder_absence_guard_present": True,
        "regex_lookaround_present": regex_lookaround_present,
        "strict_collision_scope_guard": (
            "Lookaround is present: strict=True remains necessary but is not sufficient evidence for all regex collisions; explicit relation-boundary metamorphic tests are part of this gate."
            if regex_lookaround_present
            else "No regex lookaround detected by this static guard."
        ),
        "pass": passed,
        "scope_guard": "PASS proves production-parser strict construction, exact current G9/Dialect acceptance, absent-optional placeholder suppression, V5/V6 regression obligations, the V9 horizontal-trivia call repair and explicit V17 dotted relation/call boundary metamorphic guards for the selected grammar. It does not close CC-WP-02 without grammar-bound canonicalizer/target receipts and does not prove typed IR/type/effect semantics.",
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
