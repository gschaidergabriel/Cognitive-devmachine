#!/usr/bin/env python3
"""CC-WP-03 falsifier: V18 rule meaning must survive TypedIR identity.

This is a normal discriminating test, not an out-of-box experiment. It intentionally returns
non-zero when distinct V18 rule semantics collapse to one TypedIR semantic identity.
"""
from __future__ import annotations

import json
from pathlib import Path

import claycode_base_frontend as front
import claycode_base_typed_ir as typed

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


def lower(label: str, source: str, grammar: str) -> dict:
    artifact = front.compile_frontend(source, grammar, strict=True)
    unit = typed.SourceUnit(ROOT / f"{label}.clay", artifact)
    ir = typed.build_typed_ir([unit])
    return {
        "label": label,
        "source": source,
        "frontend_semantic_hash": artifact["semantic_hash"],
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "declarations": ir["declarations"],
        "types": ir["types"],
    }


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    cases = [
        lower("preserves", "rule a preserves b\n", grammar),
        lower("required_before", "rule a required_before b\n", grammar),
        lower("postfix_brake", "rule brake cannot_be_silently_averaged_away\n", grammar),
    ]
    frontend_unique = len({x["frontend_semantic_hash"] for x in cases}) == len(cases)
    typed_unique = len({x["typed_ir_sha256"] for x in cases}) == len(cases)
    report = {
        "schema_version": "1.0",
        "test": "WP03_V18_REWARD_RELATION_TYPED_IDENTITY_FALSIFIER",
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "cases": cases,
        "frontend_semantics_distinct": frontend_unique,
        "typed_ir_semantics_distinct": typed_unique,
        "pass": frontend_unique and typed_unique,
        "expected": "Distinct admitted V18 rule semantics remain distinct after TypedIR lowering.",
        "failure_meaning": "If frontend hashes are distinct but TypedIR hashes collapse, CC-WP-03 drops rule semantics from semantic identity and must remain OPEN.",
        "scope_guard": "Bounded WP03 identity discriminator only; no BASE, Harness, Andreas-target or final Frank acceptance credit.",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
