#!/usr/bin/env python3
"""Falsify whether explicit source grouping can close the exact 17 current V18 binding gaps.

This is a candidate-only source transformation in memory. It changes no grammar and writes no
canonical source. Every replacement must match exactly once. The test requires:
- baseline 64 explicit / 17 ambiguous;
- grouped candidate 81 explicit / 0 ambiguous;
- all previously explicit non-target binding semantic hashes remain identical;
- rule/invariant structural legality remains 81/81;
- zero execution/effect/truth authority.

The chosen parentheses are semantic hypotheses inferred from the current human-readable rule
shape. Passing this test proves expressibility and isolation, not that the grouping is the owner's
final intended semantics. Promotion remains NONE until the groupings are independently reviewed.
"""
from __future__ import annotations

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

GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark"
G9 = ROOT / "research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay"
DIALECT = ROOT / "research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay"

G9_REPLACEMENTS = {
    "rule diff>0 => ADD_OR_STRENGTHEN": "rule (diff>0) => ADD_OR_STRENGTHEN",
    "rule diff<0 => RETRACT_OR_WEAKEN": "rule (diff<0) => RETRACT_OR_WEAKEN",
    "rule diff=0 => NO_CHANGE": "rule (diff=0) => NO_CHANGE",
    "rule effect.commit requires possession(valid(CapabilityToken)) && Witness.aw && Witness.cw": "rule effect.commit requires (possession(valid(CapabilityToken)) && Witness.aw && Witness.cw)",
    "rule cross_dialect_transform requires interface_match + semantic_hash_compatibility": "rule cross_dialect_transform requires (interface_match + semantic_hash_compatibility)",
    "rule current_answer_context = AnswerCapsule + relevant(ViewDelta)": "rule current_answer_context = (AnswerCapsule + relevant(ViewDelta))",
    "rule reward.material_update requires verified_outcome + causal_credit": "rule reward.material_update requires (verified_outcome + causal_credit)",
    "rule reward.value_state preserves typed_dimensions + predictions([FAST,MEDIUM,SLOW])": "rule reward.value_state preserves (typed_dimensions + predictions([FAST,MEDIUM,SLOW]))",
    "rule reward.low_prediction_error + low_residual_pressure != automatic_boredom": "rule (reward.low_prediction_error + low_residual_pressure) != automatic_boredom",
    "rule reward.low_prediction_error + high_residual_pressure + low_route_diversity -> STAGNATION_CANDIDATE": "rule (reward.low_prediction_error + high_residual_pressure + low_route_diversity) -> STAGNATION_CANDIDATE",
    "rule extraction requires verified_equivalence + target_cost_model": "rule extraction requires (verified_equivalence + target_cost_model)",
    "rule permanent_context(fragment) iff amortized_value(fragment)>risk_calibrated_threshold": "rule permanent_context(fragment) iff (amortized_value(fragment)>risk_calibrated_threshold)",
    "rule reader_compaction = persist_canonical_state -> compact -> reload(stable_core+needed_dialects+current_delta)": "rule reader_compaction = (persist_canonical_state -> compact -> reload(stable_core+needed_dialects+current_delta))",
    "rule RAE.CHATGPT.endturn -> UsageObservation -> hypothesis+counterhypothesis+candidate": "rule RAE.CHATGPT.endturn -> UsageObservation -> (hypothesis+counterhypothesis+candidate)",
    "rule Claude_only consumes latest_stack + Claude_only writes task_receipts": "rule (Claude_only consumes latest_stack) + (Claude_only writes task_receipts)",
    "rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1": "rule valid_generation requires ((count(distinct(classes))>=2) && (count(executable)>=1))",
}
DIALECT_REPLACEMENTS = {
    "rule dialect_extension requires interface_conformance+semantic_hash_compatibility+rollback": "rule dialect_extension requires (interface_conformance+semantic_hash_compatibility+rollback)",
}


def apply_exact(text: str, replacements: dict[str, str]) -> str:
    out = text
    for old, new in replacements.items():
        count = out.count(old)
        if count != 1:
            raise AssertionError(f"replacement source occurrence drift: {old!r} count={count}")
        out = out.replace(old, new, 1)
    return out


def build_ir(g9_text: str, dialect_text: str) -> dict:
    grammar = GRAMMAR.read_text(encoding="utf-8")
    units=[]
    for path,text in ((G9,g9_text),(DIALECT,dialect_text)):
        art=front.compile_frontend(text,grammar,strict=True)
        units.append(typed.SourceUnit(path,art))
    a=residual_ir.build_typed_ir(units)
    b=residual_ir.build_typed_ir(units)
    assert a["typed_ir_sha256"]==b["typed_ir_sha256"]
    return a


def by_index(bundle: dict) -> dict[int, dict]:
    return {int(x["index"]):x for x in bundle["clauses"]}


def main() -> int:
    g9=G9.read_text(encoding="utf-8")
    dialect=DIALECT.read_text(encoding="utf-8")
    baseline_ir=build_ir(g9,dialect)
    baseline=binding.lower_bundle(baseline_ir)
    assert baseline["summary"]["total"]==81
    assert baseline["summary"]["accepted"]==64
    assert baseline["summary"]["rejected_ambiguous"]==17
    target_indices={int(x["index"]) for x in baseline["rejected"]}
    assert len(target_indices)==17

    g9_grouped=apply_exact(g9,G9_REPLACEMENTS)
    dialect_grouped=apply_exact(dialect,DIALECT_REPLACEMENTS)
    candidate_ir=build_ir(g9_grouped,dialect_grouped)
    candidate=binding.lower_bundle(candidate_ir)
    assert candidate["summary"]["total"]==81,candidate["summary"]
    assert candidate["summary"]["accepted"]==81,candidate["summary"]
    assert candidate["summary"]["rejected_ambiguous"]==0,candidate["summary"]

    structural=legality.lower_rows(candidate_ir["opaque_unlowered_semantics"])
    legality.validate_receipt(structural)
    assert structural["summary"][legality.LOWERED]==81,structural["summary"]
    assert structural["summary"][legality.REJECTED]==0,structural["summary"]
    assert structural["summary"][legality.DEFERRED]==19,structural["summary"]

    before=by_index(baseline); after=by_index(candidate)
    stable_non_target=[]
    drift=[]
    for idx,row in before.items():
        if idx in target_indices:
            continue
        same=row["binding_semantic_sha256"]==after[idx]["binding_semantic_sha256"]
        stable_non_target.append(idx)
        if not same:
            drift.append({"index":idx,"before":row["binding_semantic_sha256"],"after":after[idx]["binding_semantic_sha256"]})
    assert len(stable_non_target)==64
    assert not drift,drift

    target_after=[]
    for idx in sorted(target_indices):
        row=after[idx]
        assert row["binding_status"]=="LOWERED_AND_VALIDATED_EXPLICIT_BINDING",row
        assert row["effect_authority"]==row["truth_authority"]=="NONE"
        target_after.append({
            "index":idx,
            "binding_id":row["binding_id"],
            "binding_semantic_sha256":row["binding_semantic_sha256"],
            "plan":row["plan"],
        })

    assert candidate_ir["typed_ir_sha256"]!=baseline_ir["typed_ir_sha256"]
    output={
        "status":"PASS_EXPLICIT_GROUPING_CANDIDATE_ISOLATED",
        "scope":"WP03_REAL_V18_17_CLAUSE_EXPLICIT_GROUPING_CANDIDATE_V1",
        "baseline_typed_ir_sha256":baseline_ir["typed_ir_sha256"],
        "candidate_typed_ir_sha256":candidate_ir["typed_ir_sha256"],
        "baseline_binding_bundle_sha256":baseline["bundle_sha256"],
        "candidate_binding_bundle_sha256":candidate["bundle_sha256"],
        "structural_receipt_sha256":structural["receipt_sha256"],
        "replacement_count":len(G9_REPLACEMENTS)+len(DIALECT_REPLACEMENTS),
        "baseline_explicit":64,
        "baseline_ambiguous":17,
        "candidate_explicit":81,
        "candidate_ambiguous":0,
        "candidate_structural_lowered":81,
        "candidate_structural_rejected":0,
        "non_target_binding_hashes_preserved":len(stable_non_target),
        "non_target_binding_hash_drift":0,
        "target_indices":sorted(target_indices),
        "target_after":target_after,
        "execution_admitted":0,
        "effect_authority":"NONE",
        "truth_authority":"NONE",
        "semantic_status":"CANDIDATE_GROUPING_HYPOTHESIS_NOT_OWNER_PROMOTED",
        "promotion":"NONE",
        "interpretation":"The existing V18 surface can express an ambiguity-free version of all 17 current rules using explicit grouping alone, and the candidate leaves all 64 previously explicit binding semantic hashes unchanged. This proves a minimal no-grammar-change repair path exists; it does not prove the selected grouping is the final intended semantics."
    }
    print(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
