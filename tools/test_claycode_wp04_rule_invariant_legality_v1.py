#!/usr/bin/env python3
from __future__ import annotations
import copy, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import claycode_base_frontend as front
import claycode_wp04_rule_invariant_legality_v1 as chk

ROOT=Path(__file__).resolve().parents[1]
GRAMMAR=(ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark').read_text()

def residual(src:str)->dict:
    a=front.compile_frontend(src,GRAMMAR,strict=False)
    n=a['canonical_ast']['children'][0]
    return {'kind':n['kind'],'canonical_ast':n}

def req(x,msg):
    if not x: raise AssertionError(msg)

def main():
    positives=[
      'rule reward.material_update requires verified_outcome + causal_credit\n',
      'rule effect.commit requires possession(valid(CapabilityToken)) && Witness.aw && Witness.cw\n',
      'rule reward.control != effect_authority\n',
      'rule external_effect lifecycle=[REQUESTED,AUTHORIZED,CLAIMED,EXECUTED,VERIFIED,DONE]\n',
      'rule training_data personalizes_for_Andreas_when_FRANK_target && preserves_general_transfer_variants\n',
      'rule direct.search = bounded_equality_saturation(ProgramClass,Rewrite,SearchBudget)\n',
      'rule graph.derived_relation cannot_authorize effect\n',
      'rule reward.safety_or_resource_brake cannot_be_silently_averaged_away\n',
      'rule 4B_need_not_learn Needle.owns\n',
      'invariant provenance_and_authority_separate\n',
      'invariant model_intent_and_effect_authority_separate\n',
    ]
    rows=[residual(s) for s in positives]
    out=chk.lower_rows(rows); chk.validate_receipt(out)
    req(out['summary'][chk.LOWERED]==len(rows),'all positive fixtures should lower')
    plans=[chk.symbolic_consume(r) for r in out['rows']]
    req(all(p['effect_authority']=='NONE' and p['execution_authority']=='NONE' for p in plans),'consumer minted authority')

    a=chk.lower_rows([residual('rule reward.control != effect_authority\n')])['rows'][0]
    b=chk.lower_rows([residual('rule reward.control = effect_authority\n')])['rows'][0]
    req(a['constraint_sha256']!=b['constraint_sha256'],'semantic mutation collapsed')

    bad=copy.deepcopy(rows[0]); bad['canonical_ast']['children'].append({'kind':'future_expr','children':[]})
    bad_out=chk.lower_rows([bad])['rows'][0]
    req(bad_out['status']==chk.REJECTED and bad_out['evaluator_lowering']=='DENY','unknown node not rejected')
    mismatch=copy.deepcopy(rows[0]); mismatch['kind']='rule_decl'; mismatch['canonical_ast']['kind']='invariant_decl'
    req(chk.lower_rows([mismatch])['rows'][0]['status']==chk.REJECTED,'root mismatch not rejected')

    deferred=chk.lower_rows([{'kind':'cycle_decl','canonical_ast':{'kind':'cycle_decl','children':[]}}])['rows'][0]
    req(deferred['status']==chk.DEFERRED,'non-target class not deferred')
    denied=False
    try: chk.symbolic_consume(deferred)
    except chk.LegalityError: denied=True
    req(denied,'deferred row entered evaluator')

    tampered=copy.deepcopy(out); tampered['rows'][0]['constraint_sha256']='0'*64
    rejected=False
    try: chk.validate_receipt(tampered)
    except chk.LegalityError: rejected=True
    req(rejected,'constraint hash tamper accepted')
    tampered=copy.deepcopy(out); tampered['rows'][0]['effect_authority']='MINTED'
    rejected=False
    try: chk.validate_receipt(tampered)
    except chk.LegalityError: rejected=True
    req(rejected,'authority tamper accepted')

    full=[]
    for _ in range(67): full.append(residual('rule reward.control != effect_authority\n'))
    for _ in range(14): full.append(residual('invariant provenance_and_authority_separate\n'))
    for k,c in {'cycle_decl':1,'dialect_decl':9,'import_decl':2,'module_decl':2,'parent_decl':1,'status_decl':1,'tensor_decl':1,'version_decl':2}.items():
        full += [{'kind':k,'canonical_ast':{'kind':k,'children':[]}} for _ in range(c)]
    f=chk.lower_rows(full); chk.validate_receipt(f)
    req(f['summary']['total']==100,'full inventory total mismatch')
    req(f['summary'][chk.LOWERED]==81,'expected 81 dominant residuals lowered')
    req(f['summary'][chk.DEFERRED]==19,'expected 19 residuals deferred')
    req(f['summary'][chk.REJECTED]==0,'known classes unexpectedly rejected')

    print(json.dumps({
      'schema_version':'1.0','test':'CC_WP03_WP04_RULE_INVARIANT_LEGALITY_V1_LOCAL',
      'positive_realistic_fixtures':len(positives),'positive_lowered':len(rows),
      'semantic_mutation_discriminated':True,'malformed_fail_closed':True,
      'tamper_rejected':True,'authority_minting':'NONE',
      'symbolic_consumer_plans':len(plans),'synthetic_full_inventory_total':100,
      'synthetic_dominant_lowered':81,'synthetic_remaining_deferred':19,
      'promotion':'NONE','target_vps_required':True,'pass':True
    },sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
