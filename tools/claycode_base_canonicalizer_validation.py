#!/usr/bin/env python3
"""Executable validation for the production BASE surface canonicalizer."""
from __future__ import annotations

import json
from pathlib import Path

from lark.exceptions import UnexpectedInput

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V4.lark"
OUT = ROOT / "research_entity/claycode/autonomous/BASE_CANONICALIZER_RECEIPT.json"


def run() -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    checks = []

    def result(name, ok, detail=None):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    # Layout/comments must not alter semantic identity.
    a = front.compile_frontend("module clay.demo\nlaw residual >= 0\n", grammar)
    b = front.compile_frontend("// ignored comment\nmodule   clay.demo\n\nlaw residual>=0\n", grammar)
    result("layout_comment_semantic_equivalence", a["semantic_hash"] == b["semantic_hash"], {"a": a["semantic_hash"], "b": b["semantic_hash"]})
    result("source_identity_remains_exact", a["source_sha256"] != b["source_sha256"])

    # Semantic operator/order mutations must remain distinguishable in this surface AST.
    gt = front.compile_frontend("module clay.demo\nlaw residual > 0\n", grammar)
    result("operator_mutation_discriminated", a["semantic_hash"] != gt["semantic_hash"])
    ordered_a = front.compile_frontend("module clay.demo\nrule external_effect lifecycle=[REQUESTED,AUTHORIZED,EXECUTED]\n", grammar)
    ordered_b = front.compile_frontend("module clay.demo\nrule external_effect lifecycle=[AUTHORIZED,REQUESTED,EXECUTED]\n", grammar)
    result("ordered_sequence_mutation_discriminated", ordered_a["semantic_hash"] != ordered_b["semantic_hash"])

    # Generic String identity is exact after escape decoding: escape spelling can vary, scalar sequence cannot.
    literal = front.compile_frontend('module clay.demo\nrule label="é"\n', grammar)
    escaped = front.compile_frontend('module clay.demo\nrule label="\\u00e9"\n', grammar)
    decomposed = front.compile_frontend('module clay.demo\nrule label="e\\u0301"\n', grammar)
    result("string_escape_equivalence", literal["semantic_hash"] == escaped["semantic_hash"])
    result("string_exact_scalar_identity", literal["semantic_hash"] != decomposed["semantic_hash"])

    # Canonical serialization must be byte-stable.
    again = front.compile_frontend("module clay.demo\nlaw residual >= 0\n", grammar)
    result("repeat_determinism", a["semantic_hash"] == again["semantic_hash"] and a["contract_hash"] == again["contract_hash"])
    result("canonical_json_repeat_determinism", front.canonical_bytes(a["canonical_ast"]) == front.canonical_bytes(again["canonical_ast"]))

    # Invalid syntax / reserved-keyword misuse must reject.
    for name, source in {
        "reserved_if_identifier_rejected": "module clay.demo\nsurface if\n",
        "dangling_operator_rejected": "module clay.demo\nlaw residual >=\n",
    }.items():
        try:
            front.compile_frontend(source, grammar)
            result(name, False, "unexpected_accept")
        except UnexpectedInput as exc:
            result(name, True, type(exc).__name__)

    # Lone surrogate is syntactically escaped JSON but is not a Unicode scalar value.
    try:
        front.compile_frontend('module clay.demo\nrule label="\\ud800"\n', grammar)
        result("lone_surrogate_rejected", False, "unexpected_accept")
    except front.CanonicalizationError as exc:
        result("lone_surrogate_rejected", True, str(exc))

    failures = [x["name"] for x in checks if not x["pass"]]
    return {
        "schema_version": "1.0",
        "scope": "PRODUCTION_BASE_SURFACE_PARSER_CANONICALIZER",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": failures,
        "pass": not failures,
        "limitations": [
            "typed collection Set/Ordered normalization belongs to CC-WP-03 typed IR",
            "strict LALR conflict freedom is proven by the separate strict frontend CI gate",
            "this receipt alone does not promote CC-WP-02 until full admitted G9+Dialect and differential receipts also pass"
        ]
    }


def main() -> int:
    report = run()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"pass": report["pass"], "passed": report["passed"], "total": report["total"], "failures": report["failures"]}))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
