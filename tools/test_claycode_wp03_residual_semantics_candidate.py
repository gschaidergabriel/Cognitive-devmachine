#!/usr/bin/env python3
"""Differential test for the WP03 residual-semantics candidate.

Normal discriminating test; not an out-of-box experiment.
"""
from __future__ import annotations

import json
from pathlib import Path

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as candidate

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


def unit(label: str, source: str, grammar: str) -> typed.SourceUnit:
    return typed.SourceUnit(ROOT / f"{label}.clay", front.compile_frontend(source, grammar, strict=True))


def main() -> int:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    sources = {
        "preserves": "rule a preserves b\n",
        "required_before": "rule a required_before b\n",
        "postfix_brake": "rule brake cannot_be_silently_averaged_away\n",
    }
    units = {k: unit(k, v, grammar) for k, v in sources.items()}
    baseline = {k: typed.build_typed_ir([u])["typed_ir_sha256"] for k, u in units.items()}
    repaired = {k: candidate.build_typed_ir([u])["typed_ir_sha256"] for k, u in units.items()}
    baseline_unique = len(set(baseline.values()))
    repaired_unique = len(set(repaired.values()))

    # Control: layout-only variants remain equivalent at frontend and candidate TypedIR.
    layout_a = unit("layout_a", "rule a preserves b\n", grammar)
    layout_b = unit("layout_b", "// trivia\nrule   a preserves b // trivia\n", grammar)
    layout_frontend_same = layout_a.frontend["semantic_hash"] == layout_b.frontend["semantic_hash"]
    layout_candidate_same = candidate.build_typed_ir([layout_a])["typed_ir_sha256"] == candidate.build_typed_ir([layout_b])["typed_ir_sha256"]

    report = {
        "schema_version": "1.0",
        "test": "WP03_RULE_LOSS_BASELINE_VS_RESIDUAL_SEMANTICS_CANDIDATE",
        "baseline_typed_ir_hashes": baseline,
        "candidate_typed_ir_hashes": repaired,
        "baseline_unique_hashes": baseline_unique,
        "candidate_unique_hashes": repaired_unique,
        "baseline_rule_semantics_collapse_observed": baseline_unique == 1,
        "candidate_preserves_three_admitted_v18_rule_distinctions": repaired_unique == 3,
        "layout_frontend_equivalent": layout_frontend_same,
        "layout_candidate_equivalent": layout_candidate_same,
        "pass": baseline_unique == 1 and repaired_unique == 3 and layout_frontend_same and layout_candidate_same,
        "scope_guard": "Differential implementation candidate only. PASS does not close WP03; full exact-provenance G9/Dialect, type identity, recovery and Ubuntu receipts remain mandatory.",
        "promotion": "NONE",
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
