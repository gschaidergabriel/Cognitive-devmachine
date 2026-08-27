#!/usr/bin/env python3
"""Strict frontend regression suite for ClayCode D grammar repair candidate V4.

Closes the *known grammar-regression surface* only. It does not promote CC-WP-02.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
OUT = ROOT / "research_entity/claycode/autonomous/V4_FRONTEND_REGRESSION_RECEIPT.json"

VALID = {
    "minimal_module": "module clay.demo\n",
    "comparison_law": "module clay.demo\nlaw residual >= 0\n",
    "typed_interface_method": "module clay.demo\ninterface Runtime {\nroute(x: Bool) -> Bool\n}\n",
    "structured_if": "module clay.demo\ncycle (residual: Real) {\nif residual > 0 {\nresidual\n}\n}\n",
    "invariant": "module clay.demo\ninvariant residual <= 1\n",
    "comments_and_spacing": "// comment\nmodule   clay.demo\n\nlaw residual>=0\n",
}

INVALID = {
    "reserved_if_as_surface_name": "module clay.demo\nsurface if\n",
    "dangling_comparison": "module clay.demo\nlaw residual >=\n",
    "unclosed_cycle": "module clay.demo\ncycle () {\nresidual\n",
}

EQUIVALENCE = [
    (
        "module clay.demo\nlaw residual >= 0\n",
        "// provenance-neutral comment\nmodule   clay.demo\n\nlaw residual>=0\n",
    )
]


def normalized(node):
    """Canonical parse-tree view; layout tokens are intentionally non-semantic."""
    if isinstance(node, Tree):
        children = []
        for child in node.children:
            value = normalized(child)
            if value is not None:
                children.append(value)
        return [str(node.data), children]
    if isinstance(node, Token):
        if node.type == "NEWLINE":
            return None
        return [node.type, str(node)]
    return node


def tree_hash(tree: Tree) -> str:
    payload = json.dumps(normalized(tree), ensure_ascii=False, sort_keys=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    parser = Lark(grammar_text, parser="lalr", strict=True)
    valid = {}
    invalid = {}
    failures = []

    for name, source in VALID.items():
        try:
            tree = parser.parse(source)
            valid[name] = {"pass": True, "tree_hash": tree_hash(tree)}
        except Exception as exc:
            valid[name] = {"pass": False, "error": repr(exc)}
            failures.append(f"valid:{name}")

    for name, source in INVALID.items():
        try:
            parser.parse(source)
            invalid[name] = {"pass": False, "error": "unexpected_accept"}
            failures.append(f"invalid:{name}")
        except UnexpectedInput as exc:
            invalid[name] = {"pass": True, "error_type": type(exc).__name__}

    equivalence = []
    for i, (a, b) in enumerate(EQUIVALENCE):
        try:
            ha = tree_hash(parser.parse(a))
            hb = tree_hash(parser.parse(b))
            ok = ha == hb
            equivalence.append({"case": i, "pass": ok, "hash_a": ha, "hash_b": hb})
            if not ok:
                failures.append(f"equivalence:{i}")
        except Exception as exc:
            equivalence.append({"case": i, "pass": False, "error": repr(exc)})
            failures.append(f"equivalence:{i}")

    report = {
        "schema_version": "1.1",
        "scope": "KNOWN_FRONTEND_GRAMMAR_REGRESSION_ONLY_NOT_CC_WP_02_PROMOTION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": hashlib.sha256(grammar_text.encode("utf-8")).hexdigest(),
        "strict_lalr_constructed": True,
        "canonicalization_rule": "NEWLINE/layout and ignored comments are non-semantic in this frontend tree witness",
        "valid_cases": valid,
        "invalid_cases": invalid,
        "whitespace_comment_equivalence": equivalence,
        "failure_count": len(failures),
        "failures": failures,
        "pass": not failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "failures": failures, "out": str(OUT.relative_to(ROOT))}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
