#!/usr/bin/env python3
from __future__ import annotations

import copy,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'tools'
if str(TOOLS) not in sys.path: sys.path.insert(0,str(TOOLS))
import claycode_base_frontend as front
import claycode_base_typed_ir as typed
import claycode_wp03_residual_semantics_candidate as residual
import claycode_wp03_metadata_residual_ir_v1 as meta

GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V18_REWARD_RELATIONS.lark'
SOURCES=[ROOT/'research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay',ROOT/'research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay']
SUPERVISOR=ROOT/'research_entity/claycode/autonomous/SUPERVISOR_STATE.json'
FRONTEND=ROOT/'tools/claycode_base_frontend.py'; TYPED=ROOT/'tools/claycode_base_typed_ir.py'; RESIDUAL=ROOT/'tools/claycode_wp03_residual_semantics_candidate.py'

def git(*a): return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def blob(p): return git('hash-object',str(p.relative_to(ROOT)))
def work_revision():
    s=json.loads(SUPERVISOR.read_text()); ref=s['steering_ref']; steering=ROOT/ref
    return {'repo_head':git('rev-parse','HEAD'),'supervisor_blob_sha':blob(SUPERVISOR),'steering_ref':ref,'steering_blob_sha':blob(steering),
            'frontend_blob_sha':blob(FRONTEND),'grammar_blob_sha':blob(GRAMMAR),'typed_ir_blob_sha':blob(TYPED),'residual_builder_blob_sha':blob(RESIDUAL)}
def real_ir():
    g=GRAMMAR.read_text(); units=[]
    for p in SOURCES: units.append(typed.SourceUnit(p,front.compile_frontend(p.read_text(),g,strict=True)))
    a=residual.build_typed_ir(units); b=residual.build_typed_ir(units); assert a==b; return a
def expect(fn,mark=None):
    try: fn()
    except meta.MetadataIRError as e:
        s=str(e); assert mark is None or mark in s,(mark,s); return
    raise AssertionError('expected MetadataIRError')
def first(ir,kind): return next(x for x in ir['opaque_unlowered_semantics'] if x.get('kind')==kind)
def mutate_scalar(row):
    x=copy.deepcopy(row); stack=[x['canonical_ast']]
    while stack:
        n=stack.pop()
        if isinstance(n,dict):
            if n.get('token') in {'NAME','STRING','REF'} and isinstance(n.get('value'),str): n['value'] += '_MUT'; return x
            stack.extend(reversed(n.get('children',[])))
    raise AssertionError('no mutable scalar')
def mutate_import_ref_invalid(row):
    x=copy.deepcopy(row); stack=[x['canonical_ast']]
    while stack:
        n=stack.pop()
        if isinstance(n,dict):
            if n.get('token')=='REF': n['value']='not-a-ref'; return x
            stack.extend(reversed(n.get('children',[])))
    raise AssertionError('no REF')

def main():
    ir=real_ir(); work=work_revision(); r=meta.lower_bundle(ir,work_revision=work); meta.validate_bundle(r,expected_work_revision=work)
    expected={'DIALECT_DEFINITION':9,'IMPORT_BINDING':2,'MODULE_IDENTITY':2,'PARENT_SET':1,'STATUS_MARKER':1,'TENSOR_LITERAL':1,'VERSION_LITERAL':2}
    assert r['summary']['lowered_count']==18,r['summary']; assert r['summary']['lowered_kind_counts']==expected,r['summary']
    assert r['summary']['deferred_count']==82 and r['summary']['rejected_count']==0,r['summary']
    cycles=[x for x in r['deferred'] if x.get('kind')=='cycle_decl']; assert len(cycles)==1 and cycles[0]['reason']=='OWNED_BY_WP05_CONTROL_FLOW_EVALUATOR'
    c=meta.consume_metadata(r,expected_work_revision=work); assert len(c['registry'])==18 and c['implicit_execution_count']==0
    assert len(c['control_flow_deferred'])==1 and c['effect_authority']==c['runtime_execution_authority']=='NONE'
    for kind in meta.SUPPORTED:
        row=first(ir,kind); a=meta.lower_metadata(row,index=0,work_revision=work); b=meta.lower_metadata(mutate_scalar(row),index=0,work_revision=work)
        assert a['metadata_semantic_sha256']!=b['metadata_semantic_sha256'],kind
    badref=mutate_import_ref_invalid(first(ir,'import_decl')); expect(lambda:meta.lower_metadata(badref,index=0,work_revision=work),'valid REF')
    expect(lambda:meta.lower_metadata(first(ir,'cycle_decl'),index=0,work_revision=work),'unsupported metadata residual class')
    stale=dict(work); stale['grammar_blob_sha']='0'*40; expect(lambda:meta.validate_bundle(r,expected_work_revision=stale),'STALE_EXECUTION_RECEIPT')
    bad=copy.deepcopy(r); bad['lowered'][0]['runtime_execution_authority']='FORGED'; expect(lambda:meta.validate_bundle(bad,expected_work_revision=work),'authority')
    print(json.dumps({'status':'PASS','scope':'REAL_G9_V18_METADATA_RESIDUAL_IR','typed_ir_sha256':ir['typed_ir_sha256'],
      'metadata_receipt_sha256':r['metadata_receipt_sha256'],'consumer_receipt_sha256':c['consumer_receipt_sha256'],'summary':r['summary'],
      'cycle_decl':'EXPLICITLY_DEFERRED_FAIL_CLOSED_TO_WP05','semantic_mutation_identity':'PASS','invalid_import_ref':'REJECTED',
      'stale_work_revision':'REJECTED','authority_tamper':'REJECTED','implicit_execution_count':0,'effect_authority':'NONE','promotion':'NONE','wp03_status':'OPEN'},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
