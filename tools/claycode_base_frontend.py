#!/usr/bin/env python3
"""ClayCode BASE deterministic parser/canonical frontend.

The parser consumes the frozen BASE D grammar candidate. The canonical AST is deliberately
syntax-faithful and order-preserving. Type-directed collection normalization belongs to the
typed IR (CC-WP-03), not this surface frontend.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V5.lark"
DOMAIN = b"ClayCodeBaseFrontendAST/v1\x00"


class CanonicalizationError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_scalar_string(value: str) -> None:
    bad = [ord(ch) for ch in value if 0xD800 <= ord(ch) <= 0xDFFF]
    if bad:
        raise CanonicalizationError(f"invalid Unicode surrogate scalar(s): {[hex(x) for x in bad[:8]]}")


def _token_value(token: Token) -> Any:
    raw = str(token)
    if token.type == "STRING":
        try:
            value = json.loads(raw)
        except Exception as exc:
            raise CanonicalizationError(f"invalid escaped string: {exc}") from exc
        if not isinstance(value, str):
            raise CanonicalizationError("STRING token did not decode to str")
        _validate_scalar_string(value)
        return value
    # Preserve numeric lexemes exactly here. Numeric semantic normalization is typed-IR work.
    return raw


def canonical_node(node: Any) -> Any:
    """Return deterministic, order-preserving canonical AST JSON data."""
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            value = canonical_node(child)
            if value is not None:
                children.append(value)
        return {"kind": str(node.data), "children": children}
    if isinstance(node, Token):
        if node.type == "NEWLINE":
            return None
        return {"token": node.type, "value": _token_value(node)}
    raise CanonicalizationError(f"unsupported parse node: {type(node)!r}")


def canonical_bytes(ast: Any) -> bytes:
    return json.dumps(ast, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def build_parser(grammar_text: str, *, strict: bool = False) -> Lark:
    # strict=True is used by the separate build-time LALR gate with pinned interegular.
    return Lark(grammar_text, parser="lalr", strict=strict)


def compile_frontend(source: str, grammar_text: str) -> dict[str, Any]:
    parser = build_parser(grammar_text)
    tree = parser.parse(source)
    ast = canonical_node(tree)
    ast_bytes = canonical_bytes(ast)
    grammar_sha = _sha256(grammar_text.encode("utf-8"))
    semantic_hash = _sha256(DOMAIN + ast_bytes)
    source_hash = _sha256(source.encode("utf-8"))
    contract_payload = {
        "frontend_schema": "ClayCodeBaseFrontendAST/v1",
        "grammar_sha256": grammar_sha,
        "semantic_hash": semantic_hash,
    }
    contract_hash = _sha256(json.dumps(contract_payload, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return {
        "schema_version": "1.0",
        "frontend_schema": "ClayCodeBaseFrontendAST/v1",
        "source_sha256": source_hash,
        "grammar_sha256": grammar_sha,
        "semantic_hash": semantic_hash,
        "contract_hash": contract_hash,
        "canonical_ast": ast,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("--grammar", type=Path, default=DEFAULT_GRAMMAR)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    source = args.source.read_text(encoding="utf-8")
    grammar = args.grammar.read_text(encoding="utf-8")
    result = compile_frontend(source, grammar)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
