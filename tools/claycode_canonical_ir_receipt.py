#!/usr/bin/env python3
"""Generate a deterministic, grammar-bound ClayCode parse-IR receipt.

Scope: CC-WP-02 parser/canonicalizer evidence only. This does not claim typed IR,
type/effect correctness, lowering, or BASE release acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import lark
from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V17_DECLARATIVE_TRIVIA_SAFE.lark"
DEFAULT_SOURCES = [
    ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay",
    ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay",
]
CANONICAL_FORMAT = "claycode-parse-ir-v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_node(node: Any) -> Any:
    if isinstance(node, Tree):
        return {
            "kind": "tree",
            "rule": str(node.data),
            "children": [canonical_node(child) for child in node.children],
        }
    if isinstance(node, Token):
        # Preserve token type/value exactly. Do not Unicode-normalize token text.
        return {"kind": "token", "type": str(node.type), "value": str(node)}
    raise TypeError(f"unsupported parse node: {type(node)!r}")


def canonical_bytes(tree: Tree) -> bytes:
    envelope = {"format": CANONICAL_FORMAT, "root": canonical_node(tree)}
    return json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def roundtrip_bytes(payload: bytes) -> bytes:
    decoded = json.loads(payload.decode("utf-8"))
    return json.dumps(
        decoded,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def parse_receipt(parser: Lark, source_path: Path, grammar_hash: str) -> dict[str, Any]:
    raw = source_path.read_bytes()
    text = raw.decode("utf-8")
    tree1 = parser.parse(text)
    tree2 = parser.parse(text)
    c1 = canonical_bytes(tree1)
    c2 = canonical_bytes(tree2)
    rt = roundtrip_bytes(c1)
    return {
        "path": str(source_path.relative_to(ROOT)),
        "source_sha256": sha256_bytes(raw),
        "grammar_sha256": grammar_hash,
        "canonical_format": CANONICAL_FORMAT,
        "canonical_sha256": sha256_bytes(c1),
        "repeat_canonical_sha256": sha256_bytes(c2),
        "roundtrip_canonical_sha256": sha256_bytes(rt),
        "canonical_bytes": len(c1),
        "repeat_deterministic": c1 == c2,
        "roundtrip_exact": c1 == rt,
    }


def pair_hash(parser: Lark, left: str, right: str) -> tuple[str, str]:
    return sha256_bytes(canonical_bytes(parser.parse(left))), sha256_bytes(canonical_bytes(parser.parse(right)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grammar", default=str(DEFAULT_GRAMMAR))
    ap.add_argument("--source", action="append", dest="sources")
    ap.add_argument("--output")
    ap.add_argument("--non-strict", action="store_true", help="local diagnostic only; receipts remain non-acceptance")
    args = ap.parse_args()

    grammar_path = Path(args.grammar)
    grammar_text = grammar_path.read_text(encoding="utf-8")
    strict = not args.non_strict
    parser = Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=strict,
        start="start",
        keep_all_tokens=True,
    )
    grammar_hash = sha256_bytes(grammar_text.encode("utf-8"))

    source_paths = [Path(p) for p in args.sources] if args.sources else DEFAULT_SOURCES
    source_results = [parse_receipt(parser, p, grammar_hash) for p in source_paths if p.exists()]

    # Regression oracles: semantic trivia must collapse; semantic mutations must not.
    trivia_l, trivia_r = pair_hash(parser, "rule Needle.owns(X)\n", "rule Needle.owns          (X) // trivia\n")
    op_l, op_r = pair_hash(parser, "rule x>0\n", "rule x<0\n")
    unicode_l, unicode_r = pair_hash(parser, 'rule "é"\n', 'rule "e\\u0301"\n')

    checks = {
        "all_repeat_deterministic": all(r["repeat_deterministic"] for r in source_results),
        "all_roundtrip_exact": all(r["roundtrip_exact"] for r in source_results),
        "trivia_invariant": trivia_l == trivia_r,
        "operator_mutation_discriminated": op_l != op_r,
        # Deliberately preserve Unicode code-point distinctions; no NFC/NFD rewrite.
        "unicode_not_normalized": unicode_l != unicode_r,
    }
    passed = bool(source_results) and all(checks.values())
    out = {
        "schema_version": "1.0",
        "experiment": "ClayCode CC-WP-02 grammar-bound canonical parse-IR receipt",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "grammar_path": str(grammar_path.relative_to(ROOT)),
        "grammar_sha256": grammar_hash,
        "canonical_format": CANONICAL_FORMAT,
        "runtime": {
            "python": sys.version.split()[0],
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "lark": getattr(lark, "__version__", "UNKNOWN"),
            "parser": "lalr",
            "lexer": "contextual",
            "strict": strict,
            "keep_all_tokens": True,
        },
        "sources": source_results,
        "checks": checks,
        "pass": passed,
        "scope_guard": "PASS is evidence for deterministic grammar-bound parse-IR serialization/hash roundtrip only. It does not close typed IR, type/effect, lowering, runtime, application, FRANK handoff, or BASE release gates.",
    }
    text = json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
