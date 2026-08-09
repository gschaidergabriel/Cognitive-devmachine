#!/usr/bin/env python3
"""Evidence-oriented frontend validation for the ClayCode BASE D grammar repair.

This is intentionally narrower than a canonical typed-AST proof. It establishes:
1) strict parser construction (including regex collisions when interegular is present),
2) full current G9 V3 + Dialect V3 source acceptance,
3) deterministic parse fingerprints across repeated parses,
4) explicit negative/positive keyword + newline boundary tests.

It must not be used to claim CC-WP-02 PASS by itself; typed canonical AST/semantic-hash
integration remains a separate downstream requirement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from lark import Lark, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_tree(node):
    if isinstance(node, Tree):
        return [node.data, [canonical_tree(x) for x in node.children]]
    # Tokens deliberately include both terminal class and exact lexical value.
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--output")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar = grammar_path.read_text(encoding="utf-8")
    parser = Lark(grammar, parser="lalr", lexer="contextual", strict=True, start="start")

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
    }
    positive_cases = {
        "if_statement": "cycle(input:Ref){\nif input {\ntrue\n}\n}\n",
        "invariant_statement": "invariant activation!=truth\n",
        "multiple_newlines_record": "record X {\n\n a:Int\n\n b:Int\n\n}\n",
        "multiple_newlines_cycle": "cycle(input:Ref){\n\n input\n\n}\n",
        "keyword_like_non_reserved_identifier": "record X { status:Int; dialect:Int; version:Int; requires:Int }\n",
    }

    neg = []
    for name, src in negative_cases.items():
        ok, err = try_parse(parser, src)
        neg.append({"case": name, "expected": "REJECT", "accepted": ok, "pass": not ok, "error": err})
    pos = []
    for name, src in positive_cases.items():
        ok, err = try_parse(parser, src)
        pos.append({"case": name, "expected": "ACCEPT", "accepted": ok, "pass": ok, "error": err})

    passed = (
        all(x["deterministic_repeat"] for x in source_results)
        and all(x["pass"] for x in neg)
        and all(x["pass"] for x in pos)
    )
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode BASE D repaired-frontend full-corpus validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)),
        "grammar_sha256": sha256_bytes(grammar.encode("utf-8")),
        "runtime": {"parser": "lark", "mode": "lalr/contextual", "strict": True},
        "sources": source_results,
        "negative_cases": neg,
        "positive_cases": pos,
        "pass": passed,
        "scope_guard": "PASS proves strict parser construction, current-corpus acceptance, deterministic parse fingerprints and listed boundary cases only. It does not prove canonical typed-AST or semantic-hash equivalence and does not close CC-WP-02 by itself."
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
