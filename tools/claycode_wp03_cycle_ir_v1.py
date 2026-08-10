#!/usr/bin/env python3
"""WP03/WP05 research candidate: structured CycleRegionIR for exact V18 `cycle_decl`.

This candidate consumes the already-admitted canonical cycle AST from TypedIR. It does not
reparse source and does not infer an internal loop: V18 `cycle_decl` carries a parameterized
block of expressions/if-statements but no while/for/continue construct. One CycleRegionIR
invocation therefore models one externally scheduled cycle invocation until a stronger runtime
contract proves additional recurrence semantics.

Calls and assignments are preserved structurally. The reference evaluator executes control-flow
selection only; it never invokes a call target. Values needed by conditions must be supplied by
an explicit invocation environment / assignment-result binding or evaluation fails closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

SCHEMA='ClayCodeCycleRegionIR/v1-research'
DOMAIN=b'ClayCodeCycleRegionIR/v1-research\x00'
OP_DOMAIN=b'ClayCodeCycleRegionOp/v1\x00'
COND_DOMAIN=b'ClayCodeCycleCondition/v1\x00'

class CycleIRError(ValueError): pass

def stable_json(v:Any)->bytes:
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()

def digest(domain:bytes,v:Any)->str:
    return hashlib.sha256(domain+stable_json(v)).hexdigest()

def tokens(node:Any)->list[str]:
    out=[]
    def rec(x):
        if isinstance(x,dict):
            if 'token' in x and 'value' in x: out.append(str(x['value']))
            else:
                for c in x.get('children',[]): rec(c)
        elif isinstance(x,list):
            for c in x: rec(c)
    rec(node);return out

def qid(node:dict[str,Any])->str:
    if node.get('kind')!='qid': raise CycleIRError(f'expected qid, got {node.get("kind")!r}')
    vals=tokens(node)
    if not vals: raise CycleIRError('empty qid')
    return ''.join(vals)

def semantic_children(node:dict[str,Any])->list[dict[str,Any]]:
    return [c for c in node.get('children',[]) if isinstance(c,dict) and c.get('kind')]

def op_id(core:dict[str,Any])->str: return 'cycleop:'+digest(OP_DOMAIN,core)
def cond_id(ast:dict[str,Any])->str: return 'cyclecond:'+digest(COND_DOMAIN,ast)

def lower_expr_stmt(node:dict[str,Any])->dict[str,Any]:
    kind=node.get('kind')
    if kind=='expr':
        kids=semantic_children(node)
        if len(kids)>=3 and kids[0].get('kind')=='qid' and kids[1].get('kind')=='operator' and tokens(kids[1])==['=']:
            if len(kids)!=3: raise CycleIRError('assignment must have exactly target, =, rhs structural children')
            core={'kind':'ASSIGN','target':qid(kids[0]),'rhs_ast':copy.deepcopy(kids[2]),'source_ast':copy.deepcopy(node),'token_values':tokens(node),'effect_authority':'NONE'}
        else:
            core={'kind':'EXPR','expr_ast':copy.deepcopy(node),'source_ast':copy.deepcopy(node),'token_values':tokens(node),'effect_authority':'NONE'}
    elif kind in {'call','qid','postfix_optional'}:
        core={'kind':'EXPR','expr_ast':copy.deepcopy(node),'source_ast':copy.deepcopy(node),'token_values':tokens(node),'effect_authority':'NONE'}
    else:
        raise CycleIRError(f'unsupported cycle expression statement kind {kind!r}')
    return {**core,'op_semantic_id':op_id(core)}

def lower_if(node:dict[str,Any])->dict[str,Any]:
    if node.get('kind')!='if_stmt': raise CycleIRError('expected if_stmt')
    kids=semantic_children(node)
    blocks=[x for x in kids if x.get('kind')=='cycle_block']
    conds=[x for x in kids if x.get('kind')!='cycle_block']
    if len(blocks)!=1 or len(conds)!=1: raise CycleIRError(f'if_stmt requires one condition and one block, got {len(conds)}/{len(blocks)}')
    condition=copy.deepcopy(conds[0]); body=lower_block(blocks[0])
    core={'kind':'IF','condition_ast':condition,'condition_semantic_id':cond_id(condition),'then_region':body,'else_region':None,'effect_authority':'NONE'}
    return {**core,'op_semantic_id':op_id(core)}

def lower_block(node:dict[str,Any])->dict[str,Any]:
    if node.get('kind')!='cycle_block': raise CycleIRError(f'expected cycle_block, got {node.get("kind")!r}')
    ops=[]
    for child in node.get('children',[]):
        if not isinstance(child,dict) or not child.get('kind'): continue
        if child['kind']=='if_stmt': ops.append(lower_if(child))
        else: ops.append(lower_expr_stmt(child))
    core={'kind':'REGION','ops':ops,'execution_semantics':'SEQUENTIAL_ONCE_PER_INVOCATION','effect_authority':'NONE'}
    return {**core,'region_semantic_id':'cycleregion:'+digest(DOMAIN,core)}

def lower_cycle_residual(row:dict[str,Any])->dict[str,Any]:
    if row.get('kind')!='cycle_decl': raise CycleIRError(f'expected cycle_decl residual, got {row.get("kind")!r}')
    ast=row.get('canonical_ast')
    if not isinstance(ast,dict) or ast.get('kind')!='cycle_decl': raise CycleIRError('cycle residual missing canonical cycle_decl AST')
    kids=semantic_children(ast)
    params_nodes=[x for x in kids if x.get('kind')=='params']
    blocks=[x for x in kids if x.get('kind')=='cycle_block']
    if len(blocks)!=1 or len(params_nodes)>1: raise CycleIRError('cycle_decl structural shape mismatch')
    params=[]
    if params_nodes:
        for p in semantic_children(params_nodes[0]):
            if p.get('kind')!='param': raise CycleIRError(f'unsupported params child {p.get("kind")!r}')
            vals=tokens(p)
            if not vals: raise CycleIRError('empty cycle param')
            params.append({'name':vals[0],'source_ast':copy.deepcopy(p)})
    names=[p['name'] for p in params]
    if len(names)!=len(set(names)): raise CycleIRError('duplicate cycle parameter')
    region=lower_block(blocks[0])
    core={'schema':SCHEMA,'params':params,'region':region,'source_ast':copy.deepcopy(ast),'source_tokens':tokens(ast),'invocation_semantics':'ONE_REGION_EXECUTION_PER_EXTERNAL_CYCLE_INVOCATION','internal_repetition_inferred':False,'call_execution':'EXPLICITLY_UNBOUND_FAIL_CLOSED','effect_authority':'NONE','truth_authority':'NONE'}
    return {**core,'cycle_semantic_id':'cycleir:'+digest(DOMAIN,core),'promotion':'NONE','wp03_status':'OPEN'}

def _lookup(name:str,env:dict[str,Any],symbols:dict[str,Any])->Any:
    if name in symbols: return symbols[name]
    parts=name.split('.')
    if parts[0] not in env: raise CycleIRError(f'unbound condition value {parts[0]!r}')
    cur=env[parts[0]]
    for part in parts[1:]:
        if isinstance(cur,dict) and part in cur: cur=cur[part]
        else: raise CycleIRError(f'unbound condition path {name!r}')
    return cur

def eval_term(node:dict[str,Any],env:dict[str,Any],symbols:dict[str,Any])->Any:
    kind=node.get('kind')
    if kind=='qid': return _lookup(qid(node),env,symbols)
    if kind=='expr': return eval_condition(node,env,symbols)
    if 'token' in node:
        typ=node.get('token'); value=node.get('value')
        if typ=='BOOLEAN': return str(value).lower()=='true'
        if typ=='SIGNED_NUMBER': return float(value) if '.' in str(value) else int(value)
        if typ=='STRING': return value
    raise CycleIRError(f'unsupported condition term kind {kind!r}/{node.get("token")!r}')

def eval_condition(node:dict[str,Any],env:dict[str,Any],symbols:dict[str,Any])->bool:
    if node.get('kind')=='qid':
        value=eval_term(node,env,symbols)
        if not isinstance(value,bool): raise CycleIRError('bare condition qid must resolve to bool')
        return value
    if node.get('kind')!='expr': raise CycleIRError(f'unsupported condition AST kind {node.get("kind")!r}')
    kids=semantic_children(node)
    if len(kids)==1: return eval_condition(kids[0],env,symbols)
    if len(kids)!=3 or kids[1].get('kind')!='operator': raise CycleIRError('unsupported condition expression shape')
    op=tokens(kids[1])
    if op!=['==']: raise CycleIRError(f'unsupported control-flow operator {op!r}')
    return eval_term(kids[0],env,symbols)==eval_term(kids[2],env,symbols)

def evaluate_control_flow(cycle:dict[str,Any],invocation_env:dict[str,Any],*,assignment_values:dict[str,Any]|None=None,symbols:dict[str,Any]|None=None)->dict[str,Any]:
    if cycle.get('schema')!=SCHEMA: raise CycleIRError('wrong CycleRegionIR schema')
    env=copy.deepcopy(invocation_env); assignment_values=assignment_values or {}; symbols=symbols or {}
    trace=[]; branches=[]
    def run_region(region):
        for op in region['ops']:
            if op['kind']=='IF':
                decision=eval_condition(op['condition_ast'],env,symbols); branches.append({'condition_semantic_id':op['condition_semantic_id'],'decision':decision}); trace.append({'kind':'IF','op_semantic_id':op['op_semantic_id'],'decision':decision,'token_values':tokens(op['condition_ast'])})
                if decision: run_region(op['then_region'])
            else:
                trace.append({'kind':op['kind'],'op_semantic_id':op['op_semantic_id'],'token_values':op['token_values']})
                if op['kind']=='ASSIGN':
                    target=op['target']
                    if target in assignment_values: env[target]=copy.deepcopy(assignment_values[target])
                    else: env[target]={'symbolic_unexecuted_expr':op['op_semantic_id']}
    run_region(cycle['region'])
    return {'status':'PASS','trace':trace,'branches':branches,'final_env':env,'external_call_invocations':0,'effect_authority':'NONE','truth_authority':'NONE'}
