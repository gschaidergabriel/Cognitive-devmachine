#!/usr/bin/env python3
"""Fail-closed regression for PR145 grammar-admitted identifier extraction.

Candidate-only test. It intentionally fails on a direct_identifier implementation that
trusts an ident_* branch without checking that its single literal matches the alias name.
Valid production-parser shapes must continue to pass unchanged.
"""
from __future__ import annotations

import json

import claycode_base_typed_ir as tir

ALIASES = [
    "module", "version", "status", "parent", "import", "interface", "dialect", "law",
    "rule", "class", "type", "record", "tensor", "codec", "surface", "metric", "hash",
    "needle", "cycle", "or", "iff", "requires", "in", "subset_of",
]


def alias_node(alias: str, value: str, *, token_count: int = 1) -> dict:
    return {
        "kind": "field",
        "children": [
            {
                "kind": f"ident_{alias}",
                "children": [
                    {"token": value.upper(), "value": value}
                    for _ in range(token_count)
                ],
            },
            {"token": "COLON", "value": ":"},
        ],
    }


def rejected(node: dict) -> bool:
    try:
        value = tir.direct_identifier(node)
    except tir.TypedIRError:
        return True
    return value is None


def main() -> int:
    rows = []

    for alias in ALIASES:
        observed = tir.direct_identifier(alias_node(alias, alias))
        rows.append({
            "case": f"valid:{alias}",
            "pass": observed == alias,
            "observed": observed,
            "expected": alias,
        })

        wrong = "status" if alias != "status" else "record"
        rows.append({
            "case": f"mismatch:{alias}->{wrong}",
            "pass": rejected(alias_node(alias, wrong)),
            "expected": "TypedIRError_or_None",
        })

        rows.append({
            "case": f"multi_token:{alias}",
            "pass": rejected(alias_node(alias, alias, token_count=2)),
            "expected": "TypedIRError_or_None",
        })

        rows.append({
            "case": f"zero_token:{alias}",
            "pass": rejected(alias_node(alias, alias, token_count=0)),
            "expected": "TypedIRError_or_None",
        })

    failures = [row for row in rows if not row["pass"]]
    out = {
        "schema_version": "1.0",
        "scope": "WP03_PR145_IDENTIFIER_ALIAS_INTEGRITY",
        "alias_count": len(ALIASES),
        "case_count": len(rows),
        "pass_count": len(rows) - len(failures),
        "failure_count": len(failures),
        "failures": failures,
        "pass": not failures,
        "promotion": "NONE",
        "scope_guard": "PASS means valid grammar-admitted alias shapes are preserved and malformed/replayed ident_* alias-token shapes fail closed. It does not select a parser, merge PR145, close WP03, or grant effect authority.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
