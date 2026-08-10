#!/usr/bin/env python3
"""Test a semantically simpler repair candidate for the one under-specified meta rule.

Sixteen mixed-flat rules are explicitly grouped as in the Target-VPS 17-grouping experiment.
The remaining meta rule
  rule Claude_only consumes latest_stack + Claude_only writes task_receipts
is instead split into two independent rule declarations. This avoids assigning a new higher-order
meaning to '+' between complete relation atoms.

PASS proves expressibility/isolation only. It does not establish equivalence between the original
ambiguous sentence and the split candidate or promote source semantics.
"""
from __future__ import annotations

import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))

import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual_ir
import claycode_wp03_rule_invariant_binding_gate_v1 as binding
import claycode_wp04_rule_invariant_legality_v1 as legality

GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark'
G9=ROOT/'research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay'
DIALECT=ROOT/'research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay'

REPLACEMENTS={
"rule diff>0 => ADD_OR_STRENGTHEN":"rule (diff>0) => ADD_OR_STRENGTHEN",
"rule diff<0 => RETRACT_OR_WEAKEN":"rule (diff<0) => RETRACT_OR_WEAKEN",
"rule diff=0 => NO_CHANGE":"rule (diff=0) => NO_CHANGE",
"rule effect.commit requires possession(valid(CapabilityToken)) && Witness.aw && Witness.cw":"rule effect.commit requires (possession(valid(CapabilityToken)) && Witness.aw && Witness.cw)",
"rule cross_dialect_transform requires interface_match + semantic_hash_compatibility":"rule cross_dialect_transform requires (interface_match + semantic_hash_compatibility)",
"rule current_answer_context = AnswerCapsule + relevant(ViewDelta)":"rule current_answer_context = (AnswerCapsule + relevant(ViewDelta))",
"rule reward.material_update requires verified_outcome + causal_credit":"rule reward.material_update requires (verified_outcome + causal_credit)",
"rule reward.value_state preserves typed_dimensions + predictions([FAST,MEDIUM,SLOW])":"rule reward.value_state preserves (typed_dimensions + predictions([FAST,MEDIUM,SLOW]))",
"rule reward.low_prediction_error + low_residual_pressure != automatic_boredom":"rule (reward.low_prediction_error + low_residual_pressure) != automatic_boredom",
"rule reward.low_prediction_error + high_residual_pressure + low_route_diversity -> STAGNATION_CANDIDATE":"rule (reward.low_prediction_error + high_residual_pressure + low_route_diversity) -> STAGNATION_CANDIDATE",
"rule extraction requires verified_equivalence + target_cost_model":"rule extraction requires (verified_equivalence + target_cost_model)",
"rule permanent_context(fragment) iff amortized_value(fragment)>risk_calibrated_threshold":"rule permanent_context(fragment) iff (amortized_value(fragment)>risk_calibrated_threshold)",
"rule reader_compaction = persist_canonical_state -> compact -> reload(stable_core+needed_dialects+current_delta)":"rule reader_compaction = (persist_canonical_state -> compact -> reload(stable_core+needed_dialects+current_delta))",
"rule RAE.CHATGPT.endturn -> UsageObservation -> hypothesis+counterhypothesis+candidate":"rule RAE.CHATGPT.endturn -> UsageObservation -> (hypothesis+counterhypothesis+candidate)",
"rule valid_generation requires count(distinct(classes))>=2 && count(executable)>=1":"rule valid_generation requires ((count(distinct(classes))>=2) && (count(executable)>=1))",
}
DIALECT_REPLACEMENTS={
"rule dialect_extension requires interface_conformance+semantic_hash_compatibility+rollback":"rule dialect_extension requires (interface_conformance+semantic_hash_compatibility+rollback)"
}
META_OLD="rule Claude_only consumes latest_stack + Claude_only writes task_receipts"
META_NEW="rule Claude_only consumes latest_stack\nrule Claude_only writes task_receipts"


def exact_replace(text:str,repls:dict[str,str])->str:
    out=text
    for old,new in repls.items():
        c=out.count(old)
        if c!=1: raise AssertionError((old,c))
        out=out.replace(old,new,1)
    return out


def build_ir(g9_text:str,dialect_text:str)->dict:
    grammar=GRAMMAR.read_text(encoding='utf-8')
    units=[]
    for path,text in ((G9,g9_text),(DIALECT,dialect_text)):
        art=front.compile_frontend(text,grammar,strict=True)
        units.append(typed.SourceUnit(path,art))
    a=residual_ir.build_typed_ir(units); b=residual_ir.build_typed_ir(units)
    assert a['typed_ir_sha256']==b['typed_ir_sha256']
    return a


def explicit_hash_multiset(bundle:dict)->list[str]:
    return sorted(x['binding_semantic_sha256'] for x in bundle['clauses'] if x['binding_status']=='LOWERED_AND_VALIDATED_EXPLICIT_BINDING')


def main()->int:
    g9=G9.read_text(encoding='utf-8'); dialect=DIALECT.read_text(encoding='utf-8')
    base_ir=build_ir(g9,dialect); base=binding.lower_bundle(base_ir)
    assert base['summary']['accepted']==64 and base['summary']['rejected_ambiguous']==17
    base_explicit=set(explicit_hash_multiset(base))

    grouped=exact_replace(g9,REPLACEMENTS)
    if grouped.count(META_OLD)!=1: raise AssertionError('meta ambiguous source drift')
    grouped=grouped.replace(META_OLD,META_NEW,1)
    dialect2=exact_replace(dialect,DIALECT_REPLACEMENTS)
    cand_ir=build_ir(grouped,dialect2); cand=binding.lower_bundle(cand_ir)

    assert cand['summary']['total']==82,cand['summary']
    assert cand['summary']['accepted']==82,cand['summary']
    assert cand['summary']['rejected_ambiguous']==0,cand['summary']
    structural=legality.lower_rows(cand_ir['opaque_unlowered_semantics']); legality.validate_receipt(structural)
    assert structural['summary'][legality.LOWERED]==82,structural['summary']
    assert structural['summary'][legality.REJECTED]==0,structural['summary']
    assert structural['summary'][legality.DEFERRED]==19,structural['summary']

    cand_hashes=set(explicit_hash_multiset(cand))
    missing_baseline=sorted(base_explicit-cand_hashes)
    assert not missing_baseline,missing_baseline
    # The two split relations must each be explicit and must not contain a '+' operator.
    split_rows=[]
    for row in cand['clauses']:
        plan=row['plan']
        tokens=' '.join(binding.token_values(cand_ir['opaque_unlowered_semantics'][int(row['index'])]['canonical_ast']))
        if tokens in {'rule Claude_only consumes latest_stack','rule Claude_only writes task_receipts'}:
            split_rows.append({'index':row['index'],'tokens':tokens,'binding_semantic_sha256':row['binding_semantic_sha256'],'plan':plan})
    assert len(split_rows)==2,split_rows
    assert all(r['plan'].get('operator',{}).get('name') in {'consumes','writes'} for r in split_rows),split_rows

    out={
      'status':'PASS_GROUPING16_PLUS_META_SPLIT_ISOLATED',
      'scope':'WP03_REAL_V18_GROUPING16_META_SPLIT_V1',
      'baseline_total':81,'baseline_explicit':64,'baseline_ambiguous':17,
      'candidate_total':82,'candidate_explicit':82,'candidate_ambiguous':0,
      'candidate_structural_lowered':82,'candidate_structural_rejected':0,
      'baseline_explicit_hashes_preserved':64,'baseline_explicit_hashes_missing':0,
      'meta_split_rows':split_rows,
      'baseline_typed_ir_sha256':base_ir['typed_ir_sha256'],
      'candidate_typed_ir_sha256':cand_ir['typed_ir_sha256'],
      'baseline_binding_bundle_sha256':base['bundle_sha256'],
      'candidate_binding_bundle_sha256':cand['bundle_sha256'],
      'structural_receipt_sha256':structural['receipt_sha256'],
      'execution_admitted':0,'effect_authority':'NONE','truth_authority':'NONE',
      'semantic_status':'SIMPLER_META_SPLIT_CANDIDATE_NOT_PROVEN_EQUIVALENT_NOT_PROMOTED','promotion':'NONE',
      'interpretation':'Sixteen context-supported groupings plus splitting the under-specified Claude meta sentence into two independent relations yields a fully explicit 82-clause rule/invariant corpus without grammar change and preserves every previously explicit baseline binding hash. This avoids inventing higher-order + semantics between relation atoms; equivalence to the original ambiguous sentence still requires architecture review.'
    }
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)); return 0

if __name__=='__main__': raise SystemExit(main())
