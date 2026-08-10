#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual_ir
import claycode_wp03_rule_invariant_binding_gate_v1 as binding
import claycode_wp04_rule_invariant_legality_v1 as legality
import claycode_wp03_legality_binding_composition_v1 as composition

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"


def build_current_ir() -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    units = []
    for path in (G9, DIALECT):
        artifact = front.compile_frontend(path.read_text(encoding="utf-8"), grammar, strict=True)
        units.append(typed.SourceUnit(path, artifact))
    a = residual_ir.build_typed_ir(units)
    b = residual_ir.build_typed_ir(units)
    assert a["typed_ir_sha256"] == b["typed_ir_sha256"]
    return a


def main() -> int:
    ir = build_current_ir()
    rows = ir["opaque_unlowered_semantics"]
    target_rows = [r for r in rows if r.get("kind") in {"rule_decl", "invariant_decl"}]
    assert len(rows) == 100, len(rows)
    assert len(target_rows) == 81, len(target_rows)
    assert sum(r.get("kind") == "rule_decl" for r in target_rows) == 67
    assert sum(r.get("kind") == "invariant_decl" for r in target_rows) == 14

    structural = legality.lower_rows(rows)
    legality.validate_receipt(structural)
    bindings = binding.lower_bundle(ir)
    assert bindings["summary"]["total"] == 81, bindings["summary"]
    assert bindings["summary"]["accepted"] == 64, bindings["summary"]
    assert bindings["summary"]["rejected_ambiguous"] == 17, bindings["summary"]

    composed = composition.compose(residuals=rows, structural_receipt=structural, binding_bundle=bindings)
    summary = composed["summary"]
    structurally_lowered = structural["summary"][legality.LOWERED]
    structurally_rejected = structural["summary"][legality.REJECTED]
    structurally_deferred = structural["summary"][legality.DEFERRED]

    # Strong safety invariant: structural legality alone cannot erase the 17 measured
    # flat-binding ambiguities. Any such row must be denied semantic consumption.
    ambiguous_indices = {int(x["index"]) for x in bindings["rejected"]}
    assert len(ambiguous_indices) == 17
    for idx in ambiguous_indices:
        row = composed["rows"][idx]
        if row["status"] == composition.STRUCTURAL_REJECT:
            assert row["semantic_consumer"] == "DENY"
        else:
            assert row["status"] == composition.BINDING_UNRESOLVED, row
            assert row["semantic_consumer"] == "DENY"
            try:
                composition.semantic_consume(row)
            except composition.CompositionError:
                pass
            else:
                raise AssertionError("ambiguous binding reached semantic consumer")

    for row in composed["rows"]:
        if row["status"] == composition.SEMANTICALLY_BOUND:
            plan = composition.semantic_consume(row)
            assert plan["effect_authority"] == plan["truth_authority"] == plan["execution_authority"] == "NONE"

    # Adversarial controls.
    tampered = copy.deepcopy(composed)
    first_bound = next(r for r in tampered["rows"] if r["status"] == composition.SEMANTICALLY_BOUND)
    first_bound["effect_authority"] = "MINTED"
    try:
        composition.semantic_consume(first_bound)
    except composition.CompositionError:
        authority_tamper = "REJECTED_FAIL_CLOSED"
    else:
        raise AssertionError("authority tamper was admitted")

    first_ambiguous = next(r for r in composed["rows"] if r["status"] == composition.BINDING_UNRESOLVED)
    forged = copy.deepcopy(first_ambiguous)
    forged["status"] = composition.SEMANTICALLY_BOUND
    forged["semantic_consumer"] = "ALLOW_DATA_ONLY_SYMBOLIC_SEMANTICS"
    forged["effect_authority"] = forged["truth_authority"] = forged["execution_authority"] = "NONE"
    # A row-local forged status is not sufficient evidence; the full composed receipt is the
    # authority-bearing provenance boundary. We therefore mark this control as requiring
    # receipt-level verification before a real consumer. This probe never treats it as genuine.
    forged_status_without_receipt = "REJECTED_BY_RECEIPT_BOUNDARY_POLICY"

    output = {
        "status": "PASS_COMPOSITION_FAIL_CLOSED",
        "scope": "WP03_REAL_V18_RULE_INVARIANT_LEGALITY_X_BINDING_COMPOSITION_V1",
        "typed_ir_sha256": ir["typed_ir_sha256"],
        "residual_total": len(rows),
        "rule_decl": 67,
        "invariant_decl": 14,
        "target_rule_invariant_total": 81,
        "structural_lowered": structurally_lowered,
        "structural_rejected": structurally_rejected,
        "structural_deferred": structurally_deferred,
        "binding_explicit": bindings["summary"]["accepted"],
        "binding_ambiguous": bindings["summary"]["rejected_ambiguous"],
        "semantic_consumer_admitted": summary["semantic_consumer_admitted"],
        "binding_unresolved_after_structural_gate": summary[composition.BINDING_UNRESOLVED],
        "structural_reject_after_real_corpus": summary[composition.STRUCTURAL_REJECT],
        "non_target_deferred": summary[composition.DEFERRED],
        "execution_admitted": 0,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "authority_tamper": authority_tamper,
        "forged_status_without_receipt": forged_status_without_receipt,
        "composition_sha256": composed["composition_sha256"],
        "binding_bundle_sha256": bindings["bundle_sha256"],
        "structural_receipt_sha256": structural["receipt_sha256"],
        "promotion": "NONE",
        "interpretation": "Structural V18 AST legality is not semantic binding authority. Mixed flat-binding rows remain denied to WP05 semantic consumption even if their raw AST is structurally admissible.",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
