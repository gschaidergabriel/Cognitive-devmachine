#!/usr/bin/env python3
"""Deterministic canonical parse-IR + semantic hash for ClayCode BASE WP-02.

Scope is deliberately parser/canonicalization only. It does not claim typed-IR,
checker, evaluator or release-gate closure. Exact source bytes remain separately
hashed; semantic hashing removes presentation-only newline/separator tokens while
retaining operator/literal/identifier distinctions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

SCHEMA_VERSION = "1.0"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V6.lark"
STRUCTURAL_TOKEN_VALUES = {"{", "}", "(", ")", "[", "]", ",", ";", ":"}
PRESENTATION_TOKEN_TYPES = {"NEWLINE"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_node(node: Tree | Token | None) -> Any | None:
    if node is None:
        return None
    if isinstance(node, Token):
        value = str(node)
        if node.type in PRESENTATION_TOKEN_TYPES or value in STRUCTURAL_TOKEN_VALUES:
            return None
        return {"token": node.type, "value": value}
    children = []
    for child in node.children:
        item = canonical_node(child)
        if item is not None:
            children.append(item)
    return {"node": str(node.data), "children": children}


def line_endings(data: bytes) -> dict[str, int]:
    crlf = data.count(b"\r\n")
    cr = data.count(b"\r") - crlf
    lf = data.count(b"\n") - crlf
    return {"lf": lf, "crlf": crlf, "cr": cr}


def semantic_hash(ir: Any) -> str:
    return sha256_bytes(stable_json(ir))


@dataclass(frozen=True)
class CanonicalResult:
    source_sha256: str
    source_lf_normalized_sha256: str
    grammar_sha256: str
    semantic_sha256: str
    ir: Any
    line_endings: dict[str, int]
    roundtrip_stable: bool

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "source_sha256": self.source_sha256,
            "source_lf_normalized_sha256": self.source_lf_normalized_sha256,
            "grammar_sha256": self.grammar_sha256,
            "semantic_sha256": self.semantic_sha256,
            "line_endings": self.line_endings,
            "unicode_policy": "PRESERVE_EXACT_CODEPOINTS_IN_TOKENS",
            "presentation_policy": "DROP_NEWLINE_AND_STRUCTURAL_SEPARATOR_TOKENS_FROM_SEMANTIC_HASH",
            "roundtrip_stable": self.roundtrip_stable,
            "canonical_ir": self.ir,
        }


def build_parser(grammar_text: str) -> Lark:
    return Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=True,
        start="start",
        keep_all_tokens=True,
    )


def canonicalize(parser: Lark, grammar_bytes: bytes, source_bytes: bytes) -> CanonicalResult:
    text = source_bytes.decode("utf-8")
    tree = parser.parse(text)
    ir = canonical_node(tree)
    s_hash = semantic_hash(ir)
    encoded = stable_json(ir)
    decoded = json.loads(encoded.decode("utf-8"))
    roundtrip = semantic_hash(decoded) == s_hash
    lf_normalized = source_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return CanonicalResult(
        source_sha256=sha256_bytes(source_bytes),
        source_lf_normalized_sha256=sha256_bytes(lf_normalized),
        grammar_sha256=sha256_bytes(grammar_bytes),
        semantic_sha256=s_hash,
        ir=ir,
        line_endings=line_endings(source_bytes),
        roundtrip_stable=roundtrip,
    )


def pair_test(parser: Lark, grammar_bytes: bytes, left: bytes, right: bytes, expect_same: bool) -> dict[str, Any]:
    l = canonicalize(parser, grammar_bytes, left)
    r = canonicalize(parser, grammar_bytes, right)
    same = l.semantic_sha256 == r.semantic_sha256
    return {
        "left_semantic_sha256": l.semantic_sha256,
        "right_semantic_sha256": r.semantic_sha256,
        "expect_same": expect_same,
        "observed_same": same,
        "pass": same == expect_same,
    }


def self_test(parser: Lark, grammar_bytes: bytes) -> dict[str, Any]:
    equivalence = {
        "space_comment": (b"rule x>0\n", b"rule   x > 0 // ignored\n"),
        "blank_lines": (b"record X {\na:Int\nb:Int\n}\n", b"record X {\n\na:Int\n\nb:Int\n\n}\n"),
        "separator_newline_vs_semicolon": (b"record X {\na:Int\nb:Int\n}\n", b"record X { a:Int; b:Int }\n"),
        "lf_vs_crlf": (b"record X {\na:Int\n}\n", b"record X {\r\na:Int\r\n}\r\n"),
    }
    discrimination = {
        "greater_vs_less": (b"rule x>0\n", b"rule x<0\n"),
        "plus_vs_minus": (b"rule x+1\n", b"rule x-1\n"),
        "true_vs_false": (b"rule true\n", b"rule false\n"),
        "argument_order": (b"rule f(a,b)\n", b"rule f(b,a)\n"),
        "dotted_relation": (b"rule Needle.lowers X\n", b"rule Needle.owns X\n"),
        "unicode_string_mutation": ('rule "ä"\n'.encode("utf-8"), 'rule "a"\n'.encode("utf-8")),
    }
    eq = {k: pair_test(parser, grammar_bytes, *v, expect_same=True) for k, v in equivalence.items()}
    diff = {k: pair_test(parser, grammar_bytes, *v, expect_same=False) for k, v in discrimination.items()}
    base = canonicalize(parser, grammar_bytes, b"rule x>0\n")
    passed = base.roundtrip_stable and all(v["pass"] for v in eq.values()) and all(v["pass"] for v in diff.values())
    return {"pass": passed, "roundtrip_stable": base.roundtrip_stable, "equivalence": eq, "discrimination": diff}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", action="append", default=[])
    ap.add_argument("--output")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar_bytes = grammar_path.read_bytes()
    parser = build_parser(grammar_bytes.decode("utf-8"))

    out: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment": "ClayCode BASE WP-02 deterministic canonical parse-IR",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path),
        "grammar_sha256": sha256_bytes(grammar_bytes),
        "scope_guard": "Evidence for deterministic parser-level canonical IR and semantic-hash roundtrip only; not typed-IR or CC-WP-02 PASS by itself.",
        "sources": [],
    }
    for source_name in args.source:
        path = Path(source_name)
        result = canonicalize(parser, grammar_bytes, path.read_bytes())
        out["sources"].append({"path": str(path), **result.to_json()})
    if args.self_test:
        out["self_test"] = self_test(parser, grammar_bytes)
    out["pass"] = all(x["roundtrip_stable"] for x in out["sources"]) and (not args.self_test or out["self_test"]["pass"])

    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")
    if not out["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
