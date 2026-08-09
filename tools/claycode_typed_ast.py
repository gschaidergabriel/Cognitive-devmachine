#!/usr/bin/env python3
"""Canonical typed syntax AST and semantic fingerprint for ClayCode BASE.

The representation is deliberately syntax-complete and source-location-free:
every grammar production is a ``Node`` and every significant terminal is a
``TokenNode``.  Ignored whitespace/comments therefore do not affect identity,
while operator, literal, ordering and relation mutations do.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from lark import Lark, Token, Tree


SCHEMA = "claycode.typed-syntax-ast.v1"


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class TokenNode:
    terminal: str
    lexeme: str

    def to_data(self) -> dict[str, str]:
        return {"tag": "token", "terminal": self.terminal, "lexeme": self.lexeme}


@dataclass(frozen=True, slots=True)
class Node:
    production: str
    children: tuple["AstValue", ...]

    def to_data(self) -> dict[str, Any]:
        return {
            "tag": "node",
            "production": self.production,
            "children": [child.to_data() for child in self.children],
        }


AstValue = Node | TokenNode
IGNORABLE_LAYOUT_TERMINALS = frozenset({"NEWLINE"})


@dataclass(frozen=True, slots=True)
class Document:
    root: Node
    schema: str = SCHEMA

    def to_data(self) -> dict[str, Any]:
        return {"schema": self.schema, "root": self.root.to_data()}

    def canonical_json(self) -> str:
        return _json_bytes(self.to_data()).decode("utf-8")

    def semantic_hash(self) -> str:
        return hashlib.sha256(_json_bytes(self.to_data())).hexdigest()

    @classmethod
    def from_data(cls, value: Mapping[str, Any]) -> "Document":
        if set(value) != {"schema", "root"} or value["schema"] != SCHEMA:
            raise ValueError("unknown or non-canonical ClayCode AST document")
        root = _decode(value["root"])
        if not isinstance(root, Node):
            raise ValueError("AST document root must be a node")
        return cls(root=root)

    @classmethod
    def from_json(cls, raw: str) -> "Document":
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("AST document must be a JSON object")
        return cls.from_data(value)


def _decode(value: Any) -> AstValue:
    if not isinstance(value, dict):
        raise ValueError("AST member must be an object")
    if value.get("tag") == "token" and set(value) == {"tag", "terminal", "lexeme"}:
        terminal, lexeme = value["terminal"], value["lexeme"]
        if not isinstance(terminal, str) or not isinstance(lexeme, str):
            raise ValueError("token fields must be strings")
        return TokenNode(terminal, lexeme)
    if value.get("tag") == "node" and set(value) == {"tag", "production", "children"}:
        production, children = value["production"], value["children"]
        if not isinstance(production, str) or not isinstance(children, list):
            raise ValueError("node fields have invalid types")
        return Node(production, tuple(_decode(child) for child in children))
    raise ValueError("unknown or non-canonical AST member")


def from_lark(value: Tree | Token) -> AstValue | None:
    if isinstance(value, Tree):
        children = tuple(
            converted
            for child in value.children
            if (converted := from_lark(child)) is not None
        )
        return Node(str(value.data), children)
    if isinstance(value, Token):
        if value.type in IGNORABLE_LAYOUT_TERMINALS:
            return None
        return TokenNode(value.type, str(value))
    raise TypeError(f"unsupported parser value: {type(value).__name__}")


class Frontend:
    def __init__(self, grammar: str):
        self.parser = Lark(
            grammar,
            parser="lalr",
            lexer="contextual",
            strict=True,
            start="start",
            keep_all_tokens=True,
            # Lark defaults [] EBNF optionals to explicit None children.  The
            # canonical AST represents absence by absence, not sentinel values.
            maybe_placeholders=False,
        )

    def parse(self, source: str) -> Document:
        root = from_lark(self.parser.parse(source))
        if not isinstance(root, Node):
            raise AssertionError("Lark start rule did not produce a Tree")
        return Document(root)


def verify_roundtrip(document: Document) -> dict[str, Any]:
    encoded = document.canonical_json()
    decoded = Document.from_json(encoded)
    reencoded = decoded.canonical_json()
    before, after = document.semantic_hash(), decoded.semantic_hash()
    return {
        "canonical_json_stable": encoded == reencoded,
        "structurally_equal": document == decoded,
        "hash_before": before,
        "hash_after": after,
        "hash_stable": before == after,
        "pass": encoded == reencoded and document == decoded and before == after,
    }


def compare(frontend: Frontend, left: str, right: str, expect_same: bool) -> dict[str, Any]:
    ldoc, rdoc = frontend.parse(left), frontend.parse(right)
    left_hash, right_hash = ldoc.semantic_hash(), rdoc.semantic_hash()
    same = left_hash == right_hash
    return {
        "left_hash": left_hash,
        "right_hash": right_hash,
        "expected_same": expect_same,
        "observed_same": same,
        "pass": same == expect_same,
    }


def validate(frontend: Frontend, sources: Sequence[tuple[str, str]]) -> dict[str, Any]:
    source_results = []
    for name, source in sources:
        first = frontend.parse(source)
        second = frontend.parse(source)
        rt = verify_roundtrip(first)
        source_results.append({
            "source": name,
            "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "semantic_hash": first.semantic_hash(),
            "repeat_semantic_hash": second.semantic_hash(),
            "deterministic_repeat": first.semantic_hash() == second.semantic_hash(),
            "roundtrip": rt,
        })

    different = {
        "greater_vs_less": ("rule x>0\n", "rule x<0\n"),
        "gte_vs_lte": ("rule x>=0\n", "rule x<=0\n"),
        "equal_vs_not_equal": ("rule x=0\n", "rule x!=0\n"),
        "plus_vs_minus": ("rule x+1\n", "rule x-1\n"),
        "and_vs_or": ("rule x&&true\n", "rule x||true\n"),
        "true_vs_false": ("rule true\n", "rule false\n"),
        "ordered_arguments": ("rule f(a,b)\n", "rule f(b,a)\n"),
        "relation_kind": ("rule Needle.lowers X\n", "rule Needle.owns X\n"),
        "relation_target": ("rule Needle.lowers X\n", "rule Needle.lowers Y\n"),
        "list_order": ("rule x=[a,b]\n", "rule x=[b,a]\n"),
    }
    equivalent = {
        "space_comment": ("rule x>0\n", "rule   x > 0 // ignored\n"),
        "blank_lines": ("rule x>0\n", "\n\nrule x>0\n\n"),
    }
    discrimination = [
        {"case": name, **compare(frontend, left, right, False)}
        for name, (left, right) in different.items()
    ]
    equivalence = [
        {"case": name, **compare(frontend, left, right, True)}
        for name, (left, right) in equivalent.items()
    ]
    passed = (
        all(item["deterministic_repeat"] and item["roundtrip"]["pass"] for item in source_results)
        and all(item["pass"] for item in discrimination)
        and all(item["pass"] for item in equivalence)
    )
    return {
        "schema_version": "1.0",
        "ast_schema": SCHEMA,
        "canonicalization": {
            "format": "UTF-8 JSON",
            "object_keys": "lexicographic",
            "separators": [",", ":"],
            "source_locations": "excluded",
            "ignored_layout_terminals": sorted(IGNORABLE_LAYOUT_TERMINALS),
            "note": "Deterministic ClayCode AST subset; no claim of general RFC 8785 compliance.",
        },
        "hash_algorithm": "SHA-256",
        "parser_contract": {
            "engine": "lark-lalr-contextual",
            "strict": True,
            "keep_all_tokens": True,
            "maybe_placeholders": False,
        },
        "sources": source_results,
        "semantic_discrimination": discrimination,
        "semantic_equivalence": equivalence,
        "pass": passed,
        "claim_boundary": (
            "PASS proves deterministic canonical typed-syntax AST construction, strict JSON "
            "roundtrip, and listed syntax-semantic equivalence/discrimination properties. "
            "It does not prove name resolution, static value typing, runtime lowering, or Ubuntu target acceptance."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grammar", required=True)
    parser.add_argument("--source", action="append", default=[])
    parser.add_argument("--output")
    args = parser.parse_args()
    grammar = Path(args.grammar).read_text(encoding="utf-8")
    frontend = Frontend(grammar)
    source_paths = [Path(path) for path in args.source]
    if not source_paths:
        raise SystemExit("at least one --source is required")
    result = validate(frontend, [(str(path), path.read_text(encoding="utf-8")) for path in source_paths])
    raw = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(raw, encoding="utf-8")
    print(raw, end="")
    if not result["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
