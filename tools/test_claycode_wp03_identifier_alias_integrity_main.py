#!/usr/bin/env python3
"""Fail-closed gate for the WP03 AST-context identifier extraction main port.

This is a semantic-integrity regression, not a release receipt. For every current
V18/V17-compatible ident_* alias, valid parser-shaped alias/token identity must pass,
while mismatched, zero-token and multi-token replay/corruption shapes must fail closed.
Direct NAME remains valid. The gate also checks that grammar-admitted contextual keyword
identifiers survive actual field and record declaration extraction instead of being skipped
by value-based KEYWORDS filtering. PASS cannot close WP03 or grant effect authority.
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


def typed_alias_field(alias: str, value: str) -> dict:
    node = alias_node(alias, value)
    node["children"].append({"token": "NAME", "value": "Int"})
    return node


def alias_record(alias: str, value: str) -> dict:
    return {
        "kind": "record_decl",
        "children": [
            {"token": "RECORD", "value": "record"},
            {
                "kind": f"ident_{alias}",
                "children": [{"token": value.upper(), "value": value}],
            },
            {
                "kind": "record_block",
                "children": [
                    {
                        "kind": "field",
                        "children": [
                            {"token": "NAME", "value": "x"},
                            {"token": "COLON", "value": ":"},
                            {"token": "NAME", "value": "Int"},
                        ],
                    }
                ],
            },
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

        field = tir.parse_field(typed_alias_field(alias, alias))
        rows.append({
            "case": f"field_binding:{alias}",
            "pass": field.get("name") == alias and field.get("type") == "Int",
            "observed": {"name": field.get("name"), "type": field.get("type")},
        })

        record = tir.parse_record_like(alias_record(alias, alias), "record")
        rows.append({
            "case": f"record_binding:{alias}",
            "pass": record.get("name") == alias,
            "observed": record.get("name"),
        })

        wrong = "status" if alias != "status" else "record"
        rows.append({"case": f"mismatch:{alias}->{wrong}", "pass": rejected(alias_node(alias, wrong))})
        rows.append({"case": f"multi_token:{alias}", "pass": rejected(alias_node(alias, alias, token_count=2))})
        rows.append({"case": f"zero_token:{alias}", "pass": rejected(alias_node(alias, alias, token_count=0))})

    failures = [row for row in rows if not row["pass"]]
    out = {
        "schema_version": "1.1",
        "scope": "WP03_MAIN_AST_CONTEXT_IDENTIFIER_ALIAS_INTEGRITY",
        "alias_count": len(ALIASES),
        "case_count": len(rows),
        "pass_count": len(rows) - len(failures),
        "failure_count": len(failures),
        "failures": failures,
        "pass": not failures,
        "authority": "NONE",
        "promotion": "NONE",
        "scope_guard": "PASS validates only AST-context identifier extraction and declaration binding integrity. It does not select a parser, close WP03, change work-package status, authorize Frank Harness mutation, or grant effect authority.",
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
