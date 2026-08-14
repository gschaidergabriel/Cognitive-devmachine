#!/usr/bin/env python3
"""ClayCode BASE deterministic parser/canonical frontend for declarative BASE-D V18.

V18 is the minimal reward-surface successor to V17. It preserves V17's declarative
trivia/call behavior and grouping normalization while adding only the three relation tokens
required by the current G9 reward/value section. Procedural structured ClayCode
(block-bodied fn/let/require/return/loops) remains owned by the generic structured backend.

Selecting V18 here is an evidence-backed implementation candidate, not a release promotion.
Strict Ubuntu full-corpus/canonical evidence remains mandatory before CC-WP-02 PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
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
    return raw


def _is_redundant_grouping(node: Tree) -> bool:
    """True only for the concrete `( expr )` primary wrapper shared by V17/V18.

    This intentionally does not generalize over arbitrary `primary` nodes or punctuation.
    Calls, lists, sets and postfix constructs keep their own semantic structure. The shape
    was reproduced on the Ubuntu proxy before this normalization was admitted.
    """
    if str(node.data) != "primary" or len(node.children) != 3:
        return False
    left, _, right = node.children
    return (
        isinstance(left, Token)
        and isinstance(right, Token)
        and left.type == "LPAR"
        and right.type == "RPAR"
        and str(left) == "("
        and str(right) == ")"
    )


def canonical_node(node: Any) -> Any:
    """Return deterministic, order-preserving canonical AST JSON data."""
    if isinstance(node, Tree):
        if _is_redundant_grouping(node):
            return canonical_node(node.children[1])
        children = []
        for child in node.children:
            value = canonical_node(child)
            if value is not None:
                children.append(value)
        return {"kind": str(node.data), "children": children}
    if isinstance(node, Token):
        if node.type in {"NEWLINE", "SEMICOLON"} or str(node) == ";":
            return None
        return {"token": node.type, "value": _token_value(node)}
    raise CanonicalizationError(f"unsupported parse node: {type(node)!r}")


def canonical_bytes(ast: Any) -> bytes:
    return json.dumps(ast, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def build_parser(grammar_text: str, *, strict: bool = False) -> Lark:
    return Lark(
        grammar_text,
        parser="lalr",
        lexer="contextual",
        strict=strict,
        start="start",
        keep_all_tokens=True,
        maybe_placeholders=False,
    )


def compile_frontend(source: str, grammar_text: str, *, strict: bool = False) -> dict[str, Any]:
    parser = build_parser(grammar_text, strict=strict)
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
        "schema_version": "1.4",
        "frontend_schema": "ClayCodeBaseFrontendAST/v1",
        "surface": "BASE_D_V18_REWARD_RELATIONS",
        "strict": strict,
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
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    source = args.source.read_text(encoding="utf-8")
    grammar = args.grammar.read_text(encoding="utf-8")
    result = compile_frontend(source, grammar, strict=args.strict)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
