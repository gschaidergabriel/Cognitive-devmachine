#!/usr/bin/env python3
"""CC-WP-02 regression for grouping-only semantic hash equivalence.

Current supported counterexample: redundant grouping parentheses are surface syntax and must
not change the frontend semantic identity. This probe is intentionally small and may remain
red until the active canonicalizer worker lands the minimal grouping normalization. It is a
normal regression obligation, not an out-of-box experiment.
"""
from __future__ import annotations

import json
from pathlib import Path

import claycode_base_frontend as front

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = front.DEFAULT_GRAMMAR


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    checks = []

    def h(source: str) -> str:
        return front.compile_frontend(source, grammar, strict=False)["semantic_hash"]

    def same(name: str, left: str, right: str) -> None:
        lh, rh = h(left), h(right)
        checks.append({"name": name, "expected": "SAME", "left_hash": lh, "right_hash": rh, "pass": lh == rh})

    def different(name: str, left: str, right: str) -> None:
        lh, rh = h(left), h(right)
        checks.append({"name": name, "expected": "DIFFERENT", "left_hash": lh, "right_hash": rh, "pass": lh != rh})

    same("single_redundant_group", "rule x>0\n", "rule (x>0)\n")
    same("nested_redundant_group", "rule x>0\n", "rule ((x>0))\n")
    same("layout_comment_control", "rule x>0\n", "// ignored\nrule   x > 0\n")
    same("string_escape_control", 'rule label="a"\n', 'rule label="\\u0061"\n')
    different("operator_mutation_control", "rule x>0\n", "rule x<0\n")
    different("needle_relation_mutation_control", "rule Needle.owns X\n", "rule Needle.lowers X\n")

    failures = [x for x in checks if not x["pass"]]
    report = {
        "schema_version": "1.0",
        "test": "CC_WP02_GROUPING_SEMANTIC_HASH_REGRESSION",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "checks": checks,
        "passed": len(checks) - len(failures),
        "total": len(checks),
        "failures": [x["name"] for x in failures],
        "pass": not failures,
        "expected_current_state": "RED_UNTIL_GROUPING_ONLY_PRIMARY_NORMALIZATION_LANDS",
        "scope_guard": "Regression seed only; PASS would still require strict/full-corpus Ubuntu receipts before WP02 promotion.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
