#!/usr/bin/env python3
"""Focused strict regressions for ClayCode D grammar repair candidate V5.

This suite guards the exact counterexamples that survived V4 full-corpus probing.
It does not by itself promote CC-WP-02.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lark import Lark
from lark.exceptions import UnexpectedInput

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V5.lark"
OUT = ROOT / "research_entity/claycode/autonomous/V5_FRONTEND_REGRESSION_RECEIPT.json"

VALID = {
    "dotted_lowers": "rule Needle.lowers EffectIntent -> concrete_adapter_plan\n",
    "dotted_owns_value": "rule Needle.owns [tool_schema,api_wire]\n",
    "dotted_owns_reference": "rule 4B_need_not_learn Needle.owns\n",
    "relation_assignment": "rule external_effect lifecycle=[REQUESTED,DONE]\n",
    "explicit_subject_chain": "rule Claude_only consumes latest_stack + Claude_only writes task_receipts\n",
}

INVALID = {
    "implicit_subject_english_phrase": "rule Claude_only consumes latest stack + writes task receipts\n",
    "unknown_dotted_relation": "rule Needle.foobar EffectIntent\n",
    "dangling_dotted_relation_value": "rule Needle.lowers\n",
}


def main() -> int:
    grammar_text = GRAMMAR.read_text(encoding="utf-8")
    parser = Lark(grammar_text, parser="lalr", lexer="contextual", strict=True, start="start")
    failures: list[str] = []
    valid = {}
    invalid = {}

    for name, source in VALID.items():
        try:
            parser.parse(source)
            valid[name] = {"pass": True}
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

    report = {
        "schema_version": "1.0",
        "scope": "V5_DOTTED_RELATION_AND_SOURCE_HYGIENE_REGRESSION_NOT_CC_WP_02_PROMOTION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "grammar_sha256": hashlib.sha256(grammar_text.encode("utf-8")).hexdigest(),
        "strict_lalr_constructed": True,
        "valid_cases": valid,
        "invalid_cases": invalid,
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
