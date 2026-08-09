#!/usr/bin/env python3
"""ClayCode BASE production frontend core: strict LALR parse + deterministic canonical IR.

This module is intentionally syntax/serialization only. It does not assign types, effects,
or execution authority. The canonical representation is grammar-bound and preserves token
identity/value while excluding ignored trivia via the grammar/lexer.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from lark import Lark, Token, Tree

CANON_SCHEMA = "claycode.frontend.canon.v1"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _node(node: Any) -> list[Any] | None:
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            encoded = _node(child)
            if encoded is not None:
                children.append(encoded)
        return ["tree", str(node.data), children]
    if isinstance(node, Token):
        value = str(node)
        # NEWLINE and ';' are grammar-declared interchangeable block separators. They are
        # syntax trivia for semantic identity; all other tokens remain hash-significant.
        if str(node.type) == "NEWLINE" or value == ";":
            return None
        return ["token", str(node.type), value]
    raise TypeError(f"unsupported parse node: {type(node).__name__}")


def canonical_json_bytes(obj: Any) -> bytes:
    # The IR uses arrays for ordered semantic structure and a fixed-key envelope. sort_keys
    # removes host dict insertion-order as a hashing dependency. No insignificant whitespace.
    return json.dumps(
        obj,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class CanonicalDocument:
    schema: str
    grammar_sha256: str
    root: list[Any]

    def envelope(self) -> dict[str, Any]:
        return {"schema": self.schema, "grammar_sha256": self.grammar_sha256, "root": self.root}

    def bytes(self) -> bytes:
        return canonical_json_bytes(self.envelope())

    def semantic_hash(self) -> str:
        return sha256_bytes(self.bytes())

    def roundtrip(self) -> "CanonicalDocument":
        raw = json.loads(self.bytes().decode("utf-8"))
        if raw.get("schema") != CANON_SCHEMA:
            raise ValueError("canonical schema mismatch")
        grammar_sha = raw.get("grammar_sha256")
        root = raw.get("root")
        if not isinstance(grammar_sha, str) or not isinstance(root, list):
            raise ValueError("invalid canonical document")
        return CanonicalDocument(CANON_SCHEMA, grammar_sha, root)


class ClayCodeFrontend:
    def __init__(self, grammar_text: str, *, strict: bool = True):
        self.grammar_text = grammar_text
        self.grammar_sha256 = sha256_bytes(grammar_text.encode("utf-8"))
        self.parser = Lark(
            grammar_text,
            parser="lalr",
            lexer="contextual",
            strict=strict,
            start="start",
            keep_all_tokens=True,
            maybe_placeholders=False,
        )

    @classmethod
    def from_path(cls, path: str | Path, *, strict: bool = True) -> "ClayCodeFrontend":
        return cls(Path(path).read_text(encoding="utf-8"), strict=strict)

    def parse(self, source: str) -> Tree:
        return self.parser.parse(source)

    def canonicalize(self, source: str) -> CanonicalDocument:
        root = _node(self.parse(source))
        if root is None:
            raise ValueError("empty canonical root")
        return CanonicalDocument(CANON_SCHEMA, self.grammar_sha256, root)

    def semantic_hash(self, source: str) -> str:
        return self.canonicalize(source).semantic_hash()
