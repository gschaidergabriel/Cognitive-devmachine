#!/usr/bin/env python3
"""Deterministic canonical syntax-IR roundtrip validation for ClayCode BASE WP02.

This tool sits after strict LALR construction/current-corpus parsing and before typed IR.
It proves a narrower contract:
- a parsed ClayCode source has one deterministic JSON canonical syntax IR;
- serialize -> deserialize -> serialize is byte-identical;
- ignored presentation (space/comments) is hash-stable;
- operator/literal/order/relation mutations are hash-distinguishable.

It does NOT claim typed semantic equivalence, WP03 closure, or CC-WP-02 PASS by itself.
V9 is the active frontend candidate. maybe_placeholders=False is deliberate: absent optional
syntax is represented by absence, not Python None nodes inside the canonical tree.
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
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V9.lark"
DEFAULT_SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
IR_SCHEMA = "claycode.canonical_syntax_ir.v0.1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def node_to_ir(node: Any) -> dict[str, Any]:
    if isinstance(node, Tree):
        return {
            "kind": "tree",
            "rule": str(node.data),
            "children": [node_to_ir(child) for child in node.children],
        }
    if isinstance(node, Token):
        return {"kind": "token", "type": node.type, "value": str(node)}
    raise TypeError(f"unsupported parse node: {type(node).__name__}")


def validate_ir(node: Any) -> None:
    if not isinstance(node, dict):
        raise TypeError("canonical IR node must be an object")
    kind = node.get("kind")
    if kind == "tree":
        if set(node) != {"kind", "rule", "children"}:
            raise ValueError("tree node has non-canonical keys")
        if not isinstance(node["rule"], str) or not node["rule"]:
            raise ValueError("tree.rule must be non-empty string")
        if not isinstance(node["children"], list):
            raise ValueError("tree.children must be a list")
        for child in node["children"]:
            validate_ir(child)
        return
    if kind == "token":
        if set(node) != {"kind", "type", "value"}:
            raise ValueError("token node has non-canonical keys")
        if not isinstance(node["type"], str) or not node["type"]:
            raise ValueError("token.type must be non-empty string")
        if not isinstance(node["value"], str):
            raise ValueError("token.value must be string")
        return
    raise ValueError(f"unknown canonical IR node kind: {kind!r}")


def encode_ir(ir: dict[str, Any]) -> bytes:
    validate_ir(ir)
    return json.dumps(
        {"schema": IR_SCHEMA, "root": ir},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def decode_ir(payload: bytes) -> dict[str, Any]:
    doc = json.loads(payload.decode("utf-8"))
    if not isinstance(doc, dict) or set(doc) != {"root", "schema"}:
        raise ValueError("invalid canonical IR envelope")
    if doc["schema"] != IR_SCHEMA:
        raise ValueError(f"unsupported IR schema: {doc['schema']!r}")
    validate_ir(doc["root"])
    return doc["root"]


def parse_ir(parser: Lark, source: str) -> dict[str, Any]:
    return node_to_ir(parser.parse(source))


def ir_hash(parser: Lark, source: str) -> str:
    return sha256(encode_ir(parse_ir(parser, source)))


def pair_case(parser: Lark, name: str, left: str, right: str, expect_same: bool) -> dict[str, Any]:
    lh = ir_hash(parser, left)
    rh = ir_hash(parser, right)
    observed_same = lh == rh
    return {
        "case": name,
        "expected_same": expect_same,
        "observed_same": observed_same,
        "left_hash": lh,
        "right_hash": rh,
        "pass": observed_same == expect_same,
    }


def source_receipt(parser: Lark, path: Path) -> dict[str, Any]:
    source = path.read_text(encoding="utf-8")
    tree = parser.parse(source)
    ir = node_to_ir(tree)
    encoded_1 = encode_ir(ir)
    decoded = decode_ir(encoded_1)
    encoded_2 = encode_ir(decoded)
    repeat = encode_ir(node_to_ir(parser.parse(source)))
    return {
        "path": str(path),
        "source_sha256": sha256(source.encode("utf-8")),
        "canonical_ir_sha256": sha256(encoded_1),
        "encoded_bytes": len(encoded_1),
        "roundtrip_byte_identical": encoded_1 == encoded_2,
        "repeat_parse_byte_identical": encoded_1 == repeat,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", action="append", dest="sources")
    ap.add_argument("--output")
    ap.add_argument(
        "--proxy-nonstrict",
        action="store_true",
        help="Disable Lark strict mode only for hosted proxy validation when interegular is unavailable.",
    )
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    source_paths = [Path(x) for x in args.sources] if args.sources else DEFAULT_SOURCES
    grammar = grammar_path.read_text(encoding="utf-8")
    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        strict=not args.proxy_nonstrict,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )

    sources = [source_receipt(parser, path) for path in source_paths]

    equivalence = [
        pair_case(parser, "ignored_space_comment", "rule x>0\n", "rule   x > 0 // comment\n", True),
    ]
    discrimination = [
        pair_case(parser, "greater_vs_less", "rule x>0\n", "rule x<0\n", False),
        pair_case(parser, "gte_vs_lte", "rule x>=0\n", "rule x<=0\n", False),
        pair_case(parser, "equal_vs_not_equal", "rule x=0\n", "rule x!=0\n", False),
        pair_case(parser, "plus_vs_minus", "rule x+1\n", "rule x-1\n", False),
        pair_case(parser, "and_vs_or", "rule x&&true\n", "rule x||true\n", False),
        pair_case(parser, "true_vs_false", "rule true\n", "rule false\n", False),
        pair_case(parser, "ordered_call_arguments", "rule f(a,b)\n", "rule f(b,a)\n", False),
        pair_case(parser, "dotted_relation_kind", "rule Needle.lowers X\n", "rule Needle.owns X\n", False),
        pair_case(parser, "bare_owns_vs_prefix_owns", "rule 4B_need_not_learn Needle.owns\n", "rule Needle.owns X\n", False),
    ]

    passed = (
        all(x["roundtrip_byte_identical"] and x["repeat_parse_byte_identical"] for x in sources)
        and all(x["pass"] for x in equivalence)
        and all(x["pass"] for x in discrimination)
    )
    out = {
        "schema_version": "1.1",
        "experiment": "ClayCode BASE WP02 canonical syntax-IR roundtrip/hash validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "ir_schema": IR_SCHEMA,
        "grammar_path": str(grammar_path),
        "grammar_sha256": sha256(grammar.encode("utf-8")),
        "parser_strict": not args.proxy_nonstrict,
        "maybe_placeholders": False,
        "sources": sources,
        "equivalence_cases": equivalence,
        "mutation_discrimination_cases": discrimination,
        "pass": passed,
        "evidence_class": "HOSTED_PROXY_NONSTRICT" if args.proxy_nonstrict else "TARGET_OR_STRICT_HOST_VALIDATION",
        "scope_guard": (
            "PASS proves deterministic lossless parsed syntax IR, byte-stable JSON roundtrip, "
            "presentation normalization and listed mutation discrimination. It does not prove "
            "typed semantic equivalence, WP03 closure, Ubuntu acceptance, or CC-WP-02 PASS by itself."
        ),
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
