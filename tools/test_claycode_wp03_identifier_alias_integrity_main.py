#!/usr/bin/env python3
"""Fail-closed gate for the WP03 AST-context identifier extraction main port.

This is a semantic-integrity regression, not a release receipt. For every current V17
ident_* alias, valid parser-shaped alias/token identity must pass, while mismatched,
zero-token and multi-token replay/corruption shapes must fail closed. Direct NAME remains
valid. PASS cannot close WP03 or grant effect authority.
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


def name_node(value: str) -> dict:
    return {"kind": "field", "children": [{"token": "NAME", "value": value}]}


def rejected(node: dict) -> bool:
    try:
        value = tir.direct_identifier(node)
    except tir.TypedIRError:
        return True
    return value is None


def main() -> int:
    rows = []
    direct = tir.direct_identifier(name_node("ordinary_name"))
    rows.append({"case": "direct_NAME", "pass": direct == "ordinary_name", "observed": direct})

    for alias in ALIASES:
        observed = tir.direct_identifier(alias_node(alias, alias))
        rows.append({"case": f"valid:{alias}", "pass": observed == alias, "observed": observed})

        wrong = "status" if alias != "status" else "record"
        rows.append({"case": f"mismatch:{alias}->{wrong}", "pass": rejected(alias_node(alias, wrong))})
        rows.append({"case": f"multi_token:{alias}", "pass": rejected(alias_node(alias, alias, token_count=2))})
        rows.append({"case": f"zero_token:{alias}", "pass": rejected(alias_node(alias, alias, token_count=0))})

    failures = [row for row in rows if not row["pass"]]
    out = {
        "schema_version": "1.0",
        "scope": "WP03_MAIN_AST_CONTEXT_IDENTIFIER_ALIAS_INTEGRITY",
        "alias_count": len(ALIASES),
        "case_count": len(rows),
        "pass_count": len(rows) - len(failures),
        "failure_count": len(failures),
        "failures": failures,
        "pass": not failures,
        "authority": "NONE",
        "promotion": "NONE",
        "scope_guard": "PASS validates only AST-context identifier extraction integrity. It does not select a parser, close WP03, change work-package status, authorize Frank Harness mutation, or grant effect authority.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
