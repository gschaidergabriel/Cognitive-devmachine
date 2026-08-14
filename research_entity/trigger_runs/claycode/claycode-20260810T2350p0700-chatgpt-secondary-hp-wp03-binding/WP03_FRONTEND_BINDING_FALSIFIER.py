#!/usr/bin/env python3
"""Fail-closed discriminator for the accepted V18 frontend -> WP03 TypedIR bridge.

This test deliberately fails on the observed 2026-08-10 main if TypedIR silently selects a
different grammar than the receipt-bound production frontend. It also checks that a ClayCode
class declaration is not silently lost from typed declaration identity.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tools"))

import claycode_base_frontend as front  # noqa: E402
import claycode_base_typed_ir as typed  # noqa: E402

EXPECTED_SURFACE = "BASE_D_V18_REWARD_RELATIONS"
EXPECTED_GRAMMAR = "D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"


def main() -> int:
    failures: list[str] = []
    observed = {
        "frontend_default_grammar": front.DEFAULT_GRAMMAR.name,
        "typedir_default_grammar": typed.DEFAULT_GRAMMAR.name,
        "expected_grammar": EXPECTED_GRAMMAR,
        "expected_surface": EXPECTED_SURFACE,
    }

    if front.DEFAULT_GRAMMAR.name != EXPECTED_GRAMMAR:
        failures.append("production frontend no longer binds the accepted V18 grammar")
    if typed.DEFAULT_GRAMMAR.name != front.DEFAULT_GRAMMAR.name:
        failures.append("TypedIR default grammar differs from production frontend: silent reparse risk")

    source = 'module hp.binding.test\nclass ReductionComparator = CLIQUE_PAIRWISE | REIFIED_RELATION_NODE | PAIRWISE_STATE_MACHINE\nrecord Probe { comparator:ReductionComparator }\n'
    grammar = front.DEFAULT_GRAMMAR.read_text(encoding="utf-8")
    artifact = front.compile_frontend(source, grammar)
    observed["frontend_surface"] = artifact.get("surface")
    observed["frontend_grammar_sha256"] = artifact.get("grammar_sha256")
    if artifact.get("surface") != EXPECTED_SURFACE:
        failures.append("frontend artifact surface mismatch")

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "probe.clay"
        path.write_text(source, encoding="utf-8")
        ir = typed.build_typed_ir([typed.SourceUnit(path=path, frontend=artifact)])

    declarations = {(d.get("kind"), d.get("name")) for d in ir.get("declarations", [])}
    observed["typed_declarations"] = sorted([list(x) for x in declarations])
    if ("record", "Probe") not in declarations:
        failures.append("record declaration disappeared from TypedIR")
    if not any(name == "ReductionComparator" for _, name in declarations):
        failures.append("class/type declaration identity disappeared from TypedIR")

    result = {
        "test": "CC-WP03-V18-FRONTEND-BINDING-AND-CLASS-IDENTITY",
        "status": "PASS" if not failures else "FAIL",
        "failures": failures,
        "observed": observed,
        "promotion": "NONE",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
