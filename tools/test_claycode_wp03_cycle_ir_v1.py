#!/usr/bin/env python3
from __future__ import annotations
import copy,json,tempfile
from pathlib import Path

import claycode_base_frontend as front
import claycode_wp03_frontend_artifact_bridge_v3 as bridge
import claycode_wp03_cycle_ir_v1 as cycleir

ROOT=Path(__file__).resolve().parents[1]
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark'
SOURCES=[ROOT/'research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay',ROOT/'research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay']
SURFACE='BASE_D_V18_REWARD_RELATIONS'

def expect(fn,marker):
    try:fn()
    except cycleir.CycleIRError as e:
        assert marker in str(e),(marker,str(e));return 'REJECTED'
    raise AssertionError(f'expected CycleIRError containing {marker!r}')

def materialize():
    grammar=GRAMMAR.read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='cycleir-v1-') as td:
        t=Path(td);g=t/'V18.lark';g.write_text(grammar,encoding='utf-8');specs=[]
        for i,s in enumerate(SOURCES):
            sc=t/f's{i}.clay';sc.write_bytes(s.read_bytes());doc=front.compile_frontend(sc.read_text(encoding='utf-8'),grammar,strict=True);a=t/f'a{i}.json';a.write_text(json.dumps(doc,ensure_ascii=False,indent=2,sort_keys=True)+'\n');specs.append({'artifact':str(a),'source':str(sc),'grammar':str(g),'expected_surface':SURFACE})
        original=front.build_parser;calls=0
        def forbidden(*a,**k):
            nonlocal calls;calls+=1;raise AssertionError('silent downstream reparse attempted')
        front.build_parser=forbidden
        try:b=bridge.compile_manifest({'units':specs})
        finally:front.build_parser=original
        return b,calls

def main():
    bridged,parser_calls=materialize(); ir=bridged['typed_ir']; rows=[x for x in ir['opaque_unlowered_semantics'] if x.get('kind')=='cycle_decl'];assert len(rows)==1
    row=rows[0]; c=cycleir.lower_cycle_residual(row)
    assert [p['name'] for p in c['params']]==['input','node']
    assert c['invocation_semantics']=='ONE_REGION_EXECUTION_PER_EXTERNAL_CYCLE_INVOCATION'
    assert c['internal_repetition_inferred'] is False
    assert c['effect_authority']=='NONE' and c['truth_authority']=='NONE'
    top_ifs=[x for x in c['region']['ops'] if x['kind']=='IF'];assert len(top_ifs)==2

    false=cycleir.evaluate_control_flow(c,{'input':'x','node':{'organ':'OTHER'}},assignment_values={'residual':{'effect':False}},symbols={'CHATGPT':'CHATGPT'})
    true=cycleir.evaluate_control_flow(c,{'input':'x','node':{'organ':'CHATGPT'}},assignment_values={'residual':{'effect':True}},symbols={'CHATGPT':'CHATGPT'})
    ftxt=' '.join(''.join(x.get('token_values',[])) for x in false['trace']);ttxt=' '.join(''.join(x.get('token_values',[])) for x in true['trace'])
    assert 'Needle.execute' not in ftxt and 'meta.analyze_explicit_turn' not in ftxt
    assert 'Needle.execute' in ttxt and 'meta.analyze_explicit_turn' in ttxt
    assert [x['decision'] for x in false['branches']]==[False,False]
    assert [x['decision'] for x in true['branches']]==[True,True]
    assert false['external_call_invocations']==0 and true['external_call_invocations']==0

    missing=expect(lambda:cycleir.evaluate_control_flow(c,{'input':'x','node':{'organ':'OTHER'}},symbols={'CHATGPT':'CHATGPT'}),'unbound condition path')
    unsupported_stmt=expect(lambda:cycleir.lower_expr_stmt({'kind':'while_stmt','children':[]}),'unsupported cycle expression statement')

    mut=copy.deepcopy(row); ast=mut['canonical_ast']; block=next(x for x in ast['children'] if isinstance(x,dict) and x.get('kind')=='cycle_block'); semantic=[i for i,x in enumerate(block['children']) if isinstance(x,dict) and x.get('kind') in {'expr','call','if_stmt','qid','postfix_optional'}];assert len(semantic)>3;block['children'][semantic[0]],block['children'][semantic[1]]=block['children'][semantic[1]],block['children'][semantic[0]]
    cm=cycleir.lower_cycle_residual(mut);assert cm['cycle_semantic_id']!=c['cycle_semantic_id']

    dup=copy.deepcopy(row); params=next(x for x in dup['canonical_ast']['children'] if isinstance(x,dict) and x.get('kind')=='params'); first=next(x for x in params['children'] if isinstance(x,dict) and x.get('kind')=='param');params['children'].append(copy.deepcopy(first))
    duplicate_param=expect(lambda:cycleir.lower_cycle_residual(dup),'duplicate cycle parameter')

    badcond=copy.deepcopy(top_ifs[1]['condition_ast']); ops=[x for x in badcond.get('children',[]) if isinstance(x,dict) and x.get('kind')=='operator'];assert len(ops)==1;ops[0]['children'][0]['value']='+';unsupported_op=expect(lambda:cycleir.eval_condition(badcond,{'node':{'organ':'CHATGPT'}},{'CHATGPT':'CHATGPT'}),'unsupported control-flow operator')

    report={'status':'PASS','scope':'WP03_CYCLE_REGION_IR_V1_REAL_G9_CONTROL_FLOW','cycle_semantic_id':c['cycle_semantic_id'],'top_level_ops':len(c['region']['ops']),'top_level_ifs':len(top_ifs),'params':[p['name'] for p in c['params']],
      'false_branch_trace_len':len(false['trace']),'true_branch_trace_len':len(true['trace']),'true_branch_decisions':[x['decision'] for x in true['branches']],
      'effect_path':'TAKEN_ONLY_WHEN_RESIDUAL_EFFECT_TRUE','chatgpt_meta_path':'TAKEN_ONLY_WHEN_NODE_ORGAN_CHATGPT','external_call_invocations':0,'parser_calls_after_frontend_artifact_creation':parser_calls,
      'mutation_identity':'DISTINCT_ON_STATEMENT_ORDER_CHANGE','missing_condition_value':missing,'unsupported_statement':unsupported_stmt,'duplicate_param':duplicate_param,'unsupported_condition_operator':unsupported_op,
      'internal_repetition_inferred':False,'effect_authority':'NONE','truth_authority':'NONE','promotion':'NONE','wp03_status':'OPEN'}
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
