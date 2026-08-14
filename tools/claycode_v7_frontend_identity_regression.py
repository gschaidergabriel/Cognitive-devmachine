#!/usr/bin/env python3
"""Strict V7 frontend identity regression for the WP02 parser/canonical boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lark import Lark, Token, Tree
from lark.exceptions import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
OUT = ROOT / "research_entity/claycode/autonomous/V7_FRONTEND_IDENTITY_RECEIPT.json"

SYMBOLIC = [">=", "<=", "!=", "==", "->", "=>", ">", "<", "=", "|", "+", "-", "*", "/", "&&", "||"]


def norm(node):
    if isinstance(node, Tree):
        return [str(node.data), [norm(x) for x in node.children]]
    if isinstance(node, Token):
        return [node.type, str(node)]
    return node


def h(parser: Lark, source: str) -> str:
    payload = json.dumps(norm(parser.parse(source)), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def main() -> int:
    text = GRAMMAR.read_text(encoding="utf-8")
    p = Lark(text, parser="lalr", lexer="contextual", strict=True, start="start")
    failures = []
    spacing = []
    identities = {}

    # Tight and spaced symbolic operators must canonicalize identically.
    for op in SYMBOLIC:
        ret = "Bool" if op in {">=", "<=", "!=", "==", ">", "<"} else "Int"
        a = f"fn f(a:Int,b:Int)->{ret}=a{op}b\n"
        b = f"fn f(a:Int,b:Int)->{ret}=a {op} b\n"
        try:
            ha, hb = h(p, a), h(p, b)
            ok = ha == hb
            spacing.append({"operator": op, "pass": ok, "tight": ha, "spaced": hb})
            identities[op] = ha
            if not ok:
                failures.append(f"spacing:{op}")
        except Exception as exc:
            spacing.append({"operator": op, "pass": False, "error": repr(exc)})
            failures.append(f"parse:{op}")

    # Operators must not collapse to one parse-tree identity.
    distinct = len(set(identities.values())) == len(identities)
    if not distinct:
        failures.append("operator_identity_collapse")

    valid = {
        "current_dotted_lowers": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
        "current_dotted_owns": "rule Needle.owns [tool_schema,api_wire]\n",
        "dotted_owns_reference": "rule 4B_need_not_learn Needle.owns\n",
        "relation_assignment": "rule external_effect lifecycle=[REQUESTED,DONE]\n",
        "typed_fn": "fn add(a:Int,b:Int)->Int=a+b\n",
        "fn_contextual_field": "record X { fn:Int }\n",
    }
    invalid = {
        "hyphen_identifier_removed": "record X { a-b:Int }\n",
        "untyped_fn_param": "fn bad(a)->Int=a\n",
        "reserved_if_field": "record X { if:Int }\n",
    }
    valid_results = {}
    invalid_results = {}
    for name, src in valid.items():
        try:
            p.parse(src)
            valid_results[name] = {"pass": True}
        except Exception as exc:
            valid_results[name] = {"pass": False, "error": repr(exc)}
            failures.append(f"valid:{name}")
    for name, src in invalid.items():
        try:
            p.parse(src)
            invalid_results[name] = {"pass": False, "error": "unexpected_accept"}
            failures.append(f"invalid:{name}")
        except UnexpectedInput as exc:
            invalid_results[name] = {"pass": True, "error_type": type(exc).__name__}

    out = {
        "schema_version": "1.0",
        "scope": "V7_STRICT_FRONTEND_OPERATOR_IDENTITY_NOT_FULL_WP02_PROMOTION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "strict_lalr_constructed": True,
        "operator_spacing": spacing,
        "operator_identities_distinct": distinct,
        "valid_cases": valid_results,
        "invalid_cases": invalid_results,
        "failures": failures,
        "pass": not failures,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": out["pass"], "failures": failures, "out": str(OUT.relative_to(ROOT))}))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
