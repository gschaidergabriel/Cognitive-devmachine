#!/usr/bin/env python3
"""Executable counterexample probe for the owner-fixed proactive-agency/web-ingress directive.

The current BASE policy says new owner-fixed requirements should first be expressed by the
selected frozen ClayCode semantics; only an executable failure may justify reopening language
semantics. This probe therefore feeds the owner directive unchanged through the exact selected
V18 frontend. If frontend admission succeeds it also attempts the current Structural TypedIR v2.

A rejection is preserved as a measured language/IR counterexample, not hidden by rewriting the
owner directive. No promotion, execution or authority is produced by this probe.
"""
from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_typed_ir_v2_state_identity as typed_v2

ROOT = Path(__file__).resolve().parents[1]
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
DIRECTIVE = ROOT / "research_entity/global/SELF_ROOT_AUTOTELIC_PROACTIVE_AGENCY_AND_WEB_INGRESS_DIRECTIVE.clay"


def error_record(stage: str, exc: BaseException) -> dict[str, Any]:
    out: dict[str, Any] = {
        "stage": stage,
        "error_type": type(exc).__name__,
        "message": str(exc),
    }
    for attr in ("line", "column", "pos_in_stream"):
        value = getattr(exc, attr, None)
        if value is not None:
            out[attr] = value
    expected = getattr(exc, "expected", None)
    if expected:
        out["expected"] = sorted(str(x) for x in expected)
    token = getattr(exc, "token", None)
    if token is not None:
        out["token_type"] = str(getattr(token, "type", ""))
        out["token_value"] = str(getattr(token, "value", token))
    return out


def run_probe() -> dict[str, Any]:
    source = DIRECTIVE.read_text(encoding="utf-8")
    grammar = GRAMMAR.read_text(encoding="utf-8")
    report: dict[str, Any] = {
        "scope": "WP03_OWNER_AGENCY_WEB_INGRESS_V18_REPRESENTABILITY",
        "directive": str(DIRECTIVE.relative_to(ROOT)),
        "grammar": str(GRAMMAR.relative_to(ROOT)),
        "frontend": "NOT_RUN",
        "structural_typed_ir": "NOT_RUN",
        "promotion": "NONE",
        "effect_authority": "NONE",
        "truth_authority": "NONE",
    }
    try:
        doc = front.compile_frontend(source, grammar, strict=True)
    except Exception as exc:  # executable language counterexample is data, not process failure
        report.update({
            "status": "COUNTEREXAMPLE_FRONTEND_REJECTED_OWNER_DIRECTIVE",
            "frontend": "REJECTED",
            "counterexample": error_record("FRONTEND_V18", exc),
            "language_change_policy_implication": "EXECUTABLE_COUNTEREXAMPLE_EXISTS_REQUIRES_MINIMAL_SEMANTIC_AMENDMENT_OR_DIRECTIVE_LOWERING_PROOF",
        })
        return report

    report["frontend"] = "PASS"
    unit = typed.SourceUnit(DIRECTIVE, doc)
    try:
        ir = typed_v2.build_typed_ir_v2([unit])
    except Exception as exc:
        report.update({
            "status": "COUNTEREXAMPLE_TYPED_IR_REJECTED_OWNER_DIRECTIVE",
            "structural_typed_ir": "REJECTED",
            "counterexample": error_record("STRUCTURAL_TYPED_IR_V2", exc),
            "language_change_policy_implication": "FRONTEND_EXPRESSIBLE_BUT_CURRENT_TYPED_IR_INSUFFICIENT",
        })
        return report

    opaque = ir.get("opaque_unlowered_semantics", [])
    report.update({
        "status": "PASS_REPRESENTABLE_CURRENT_STACK",
        "structural_typed_ir": "PASS",
        "typed_ir_sha256": ir.get("typed_ir_sha256"),
        "declaration_count": len(ir.get("declarations", [])),
        "structural_record_count": len(ir.get("structural_records", [])),
        "opaque_semantic_count": len(opaque),
        "opaque_kinds": sorted({str(x.get("kind")) for x in opaque if isinstance(x, dict)}),
        "language_change_policy_implication": "NO_LANGUAGE_CHANGE_JUSTIFIED_BY_THIS_PROBE",
    })
    return report


def main() -> int:
    print(json.dumps(run_probe(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
