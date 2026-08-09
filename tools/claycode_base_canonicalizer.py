#!/usr/bin/env python3
"""Deterministic syntax canonicalizer for the active ClayCode BASE repaired frontend.

Scope: CC-WP-02 only. This converts an accepted Lark syntax tree into a stable JSON
representation that is insensitive to comments and newline-layout multiplicity while
preserving every non-layout lexical literal that can change program meaning. It does
NOT claim typed canonical IR; that remains CC-WP-03.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V5.lark"
DEFAULT_SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_node(node: Any) -> Any | None:
    """Return deterministic syntax identity, dropping layout-only NEWLINE tokens."""
    if isinstance(node, Token):
        if node.type == "NEWLINE":
            return None
        return {"token": node.type, "value": str(node)}
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            cooked = canonical_node(child)
            if cooked is not None:
                children.append(cooked)
        return {"kind": str(node.data), "children": children}
    return {"literal": str(node)}


def canonical_bytes(tree: Tree) -> bytes:
    return json.dumps(
        canonical_node(tree),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def parse_canonical(parser: Lark, source: str) -> tuple[Any, str]:
    tree = parser.parse(source)
    payload = canonical_node(tree)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return payload, sha256_bytes(raw)


def layout_variant(source: str) -> str:
    # Comments and repeated NEWLINE separators are lexical/layout concerns and must not
    # change canonical syntax identity. Deliberate punctuation is retained.
    return "// canonicalizer-layout-variant\n\n" + source.replace("\n", "\n\n") + "\n// canonicalizer-layout-end\n"


def pair_receipt(parser: Lark, left: str, right: str, expect_same: bool) -> dict[str, Any]:
    _, lh = parse_canonical(parser, left)
    _, rh = parse_canonical(parser, right)
    observed_same = lh == rh
    return {
        "left": left,
        "right": right,
        "left_hash": lh,
        "right_hash": rh,
        "expected_same": expect_same,
        "observed_same": observed_same,
        "pass": observed_same == expect_same,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", action="append", dest="sources")
    ap.add_argument("--output")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")
    # Critical: Lark normally drops anonymous string-literal terminals from the tree.
    # keep_all_tokens=True makes operator/punctuation identity available to canonical_node.
    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
    )

    source_paths = [Path(x) for x in args.sources] if args.sources else list(DEFAULT_SOURCES)
    rows = []
    overall = True
    for path in source_paths:
        text = path.read_text(encoding="utf-8")
        ast1, h1 = parse_canonical(parser, text)
        _, h2 = parse_canonical(parser, text)
        _, hv = parse_canonical(parser, layout_variant(text))
        repeat_ok = h1 == h2
        layout_ok = h1 == hv
        overall = overall and repeat_ok and layout_ok
        rows.append({
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "source_sha256": sha256_bytes(text.encode("utf-8")),
            "canonical_syntax_sha256": h1,
            "repeat_canonical_sha256": h2,
            "layout_variant_canonical_sha256": hv,
            "repeat_deterministic": repeat_ok,
            "comment_whitespace_layout_invariant": layout_ok,
            "canonical_root_kind": ast1.get("kind") if isinstance(ast1, dict) else None,
        })

    distinct_cases = {
        "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
        "gte_vs_lte": ("rule x>=0\n", "rule x<=0\n"),
        "equal_vs_not_equal": ("rule x=0\n", "rule x!=0\n"),
        "plus_vs_minus": ("rule x+1\n", "rule x-1\n"),
        "and_vs_or": ("rule x&&true\n", "rule x||true\n"),
        "boolean_value": ("rule true\n", "rule false\n"),
        "argument_order": ("rule f(a,b)\n", "rule f(b,a)\n"),
        "dotted_relation_kind": ("rule Needle.lowers X\n", "rule Needle.owns X\n"),
        "lifecycle_order": (
            "rule external_effect lifecycle=[REQUESTED,AUTHORIZED,DONE]\n",
            "rule external_effect lifecycle=[AUTHORIZED,REQUESTED,DONE]\n",
        ),
    }
    distinct = [
        {"case": name, **pair_receipt(parser, left, right, expect_same=False)}
        for name, (left, right) in distinct_cases.items()
    ]

    equivalent_cases = {
        "space_comment_layout": ("rule x>0\n", "// ignored\nrule   x > 0 // ignored\n"),
    }
    equivalent = [
        {"case": name, **pair_receipt(parser, left, right, expect_same=True)}
        for name, (left, right) in equivalent_cases.items()
    ]

    overall = overall and all(x["pass"] for x in distinct) and all(x["pass"] for x in equivalent)
    receipt = {
        "schema_version": "1.1",
        "experiment": "ClayCode BASE deterministic literal-safe syntax canonicalization",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)) if grammar_path.is_relative_to(ROOT) else str(grammar_path),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "runtime": {"parser": "lark", "mode": "lalr/contextual", "strict": True, "keep_all_tokens": True},
        "canonicalizer": "literal-preserving tree->sorted compact JSON; layout NEWLINE tokens dropped; lexical comments/WS already ignored by grammar",
        "sources": rows,
        "semantic_surface_discrimination": distinct,
        "layout_equivalence": equivalent,
        "pass": overall,
        "scope_guard": "PASS proves deterministic layout-insensitive and lexical-meaning-sensitive canonical syntax identity for the listed admitted sources and mutation pairs. It is CC-WP-02 evidence only and does not prove typed canonical IR/type/effect semantics (CC-WP-03/04)."
    }
    rendered = json.dumps(receipt, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not overall:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
