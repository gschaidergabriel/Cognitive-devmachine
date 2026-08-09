#!/usr/bin/env python3
"""ClayCode BASE typed pure-core vertical slice.

Clay source -> V7 parser -> typed IR -> type/effect check -> evaluator -> C lowering.
This is evidence toward CC-WP-03..06, not whole-package promotion.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
from typing import Any
from lark import Lark, Token, Tree

ROOT=Path(__file__).resolve().parents[1]
GRAMMAR=ROOT/'research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark'
IR_DOMAIN=b'ClayCodeTypedPureIR/v1\x00'
VERSION='claycode-base-pure-toolchain/0.1'
SCALARS={'Int','Real','Bool'}
OPS={'op_add':'+','op_sub':'-','op_mul':'*','op_div':'/','op_gt':'>','op_lt':'<','op_ge':'>=','op_le':'<=','op_eqeq':'==','op_ne':'!=','op_and':'&&','op_oror':'||'}

class ClayError(Exception): pass
class TypeFailure(ClayError): pass
class Unsupported(ClayError): pass

def sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def is_tree(x,n):return isinstance(x,Tree) and str(x.data)==n

def qid(x):
    if isinstance(x,Token): return str(x)
    if not is_tree(x,'qid'): raise Unsupported(f'expected qid: {x!r}')
    out=[]
    for c in x.children:
        if isinstance(c,Token): out.append(str(c))
        elif isinstance(c,Tree) and str(c.data).startswith('ident_'): out.append(str(c.data)[6:])
        else: raise Unsupported(f'bad qid part: {c!r}')
    return '.'.join(out)

def type_name(x):
    if isinstance(x,Tree) and str(x.data) in {'type_atom','type_expr'}:
        cs=[c for c in x.children if c is not None]
        if len(cs)!=1: raise Unsupported('generic/optional/union type outside pure-core subset')
        return type_name(cs[0])
    n=qid(x)
    if n not in SCALARS: raise Unsupported(f'unsupported pure-core type {n}')
    return n

def rexpr(x):
    if isinstance(x,Token):
        if x.type=='SIGNED_NUMBER':
            s=str(x); return {'kind':'Literal','type':'Real' if any(c in s for c in '.eE') else 'Int','value':float(s) if any(c in s for c in '.eE') else int(s)}
        if x.type=='BOOLEAN': return {'kind':'Literal','type':'Bool','value':str(x)=='true'}
        raise Unsupported(f'literal {x.type}')
    if not isinstance(x,Tree): raise Unsupported(repr(x))
    k=str(x.data)
    if k=='qid': return {'kind':'Name','name':qid(x)}
    if k=='call': return {'kind':'Call','callee':qid(x.children[0]),'args':[rexpr(c) for c in x.children[1:]]}
    if k=='expr':
        cs=list(x.children); left=rexpr(cs[0]); i=1
        while i<len(cs):
            op=cs[i]
            if not isinstance(op,Tree) or str(op.data) not in OPS: raise Unsupported(f'non-pure operator {op!r}')
            left={'kind':'Binary','op':OPS[str(op.data)],'left':left,'right':rexpr(cs[i+1])}; i+=2
        return left
    if len(x.children)==1 and k in {'term','primary'}: return rexpr(x.children[0])
    raise Unsupported(f'expr kind {k}')

def parse_program(src,grammar):
    p=Lark(grammar,parser='lalr',lexer='contextual',start='start')
    t=p.parse(src); funcs=[]; module=None
    for s in t.children:
        if isinstance(s,Token): continue
        if is_tree(s,'module_decl'):
            qs=[c for c in s.children if is_tree(c,'qid')]; module=qid(qs[-1]) if qs else None; continue
        if not is_tree(s,'fn_decl'): continue
        cs=list(s.children); names=[str(c) for c in cs if isinstance(c,Token) and c.type=='NAME']
        if not names: raise Unsupported('fn name missing')
        name=names[0]; tp=next((c for c in cs if is_tree(c,'typed_params')),None); params=[]
        if tp:
            for pc in tp.children:
                if not is_tree(pc,'typed_param'): continue
                pn=next((str(c) for c in pc.children if isinstance(c,Token) and c.type=='NAME'),None)
                ts=[c for c in pc.children if isinstance(c,Tree)]
                if pn is None or not ts: raise Unsupported('bad typed parameter')
                params.append({'name':pn,'type':type_name(ts[-1])})
        body=cs[-1]
        tc=[c for c in cs[:-1] if isinstance(c,Tree) and str(c.data) in {'qid','type_atom','type_expr'}]
        if not tc: raise Unsupported(f'{name}: return type missing')
        funcs.append({'kind':'Function','name':name,'params':params,'return_type':type_name(tc[-1]),'body':rexpr(body)})
    if not funcs: raise Unsupported('no fn declarations')
    return {'kind':'Program','module':module,'functions':funcs}

def infer(e,env,sigs):
    k=e['kind']
    if k=='Literal': return dict(e)
    if k=='Name':
        if e['name'] not in env: raise TypeFailure('unknown name '+e['name'])
        return {**e,'type':env[e['name']]}
    if k=='Call':
        if e['callee'] not in sigs: raise TypeFailure('unknown pure function '+e['callee'])
        wants,ret=sigs[e['callee']]
        if len(wants)!=len(e['args']): raise TypeFailure('arity mismatch '+e['callee'])
        args=[infer(a,env,sigs) for a in e['args']]
        for i,(a,w) in enumerate(zip(args,wants)):
            if a['type']!=w: raise TypeFailure(f"{e['callee']} arg {i}: {a['type']} != {w}")
        return {'kind':'Call','callee':e['callee'],'args':args,'type':ret}
    if k=='Binary':
        l,r=infer(e['left'],env,sigs),infer(e['right'],env,sigs); op=e['op']; lt,rt=l['type'],r['type']
        if op in {'+','-','*'}:
            if lt not in {'Int','Real'} or rt not in {'Int','Real'}: raise TypeFailure(op+' requires numeric')
            ot='Real' if 'Real' in {lt,rt} else 'Int'
        elif op=='/':
            if lt not in {'Int','Real'} or rt not in {'Int','Real'}: raise TypeFailure('/ requires numeric')
            ot='Real'
        elif op in {'>','<','>=','<='}:
            if lt not in {'Int','Real'} or rt not in {'Int','Real'}: raise TypeFailure(op+' requires numeric')
            ot='Bool'
        elif op in {'==','!='}:
            if lt!=rt: raise TypeFailure(op+' requires equal types')
            ot='Bool'
        elif op in {'&&','||'}:
            if (lt,rt)!=('Bool','Bool'): raise TypeFailure(op+' requires Bool')
            ot='Bool'
        else: raise Unsupported(op)
        return {'kind':'Binary','op':op,'left':l,'right':r,'type':ot}
    raise Unsupported(k)

def typecheck(p):
    sig={f['name']:([x['type'] for x in f['params']],f['return_type']) for f in p['functions']}
    if len(sig)!=len(p['functions']): raise TypeFailure('duplicate function')
    fs=[]
    for f in p['functions']:
        env={x['name']:x['type'] for x in f['params']}
        if len(env)!=len(f['params']): raise TypeFailure('duplicate parameter '+f['name'])
        b=infer(f['body'],env,sig)
        if b['type']!=f['return_type']: raise TypeFailure(f"return mismatch {f['name']}: {b['type']} != {f['return_type']}")
        fs.append({**f,'body':b,'effects':[]})
    ir={'kind':'TypedProgram','module':p['module'],'functions':fs,'effect_summary':[]}
    raw=json.dumps(ir,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return {'schema_version':'1.0','ir_schema':'ClayCodeTypedPureIR/v1','compiler_version':VERSION,'semantic_hash':sha(IR_DOMAIN+raw),'typed_ir':ir}

def evbin(op,a,b):
    return {'+':lambda:a+b,'-':lambda:a-b,'*':lambda:a*b,'/':lambda:float(a)/float(b),'>':lambda:a>b,'<':lambda:a<b,'>=':lambda:a>=b,'<=':lambda:a<=b,'==':lambda:a==b,'!=':lambda:a!=b,'&&':lambda:bool(a) and bool(b),'||':lambda:bool(a) or bool(b)}[op]()
def evaluate(t,entry,args):
    fs={f['name']:f for f in t['typed_ir']['functions']}
    def call(n,vs):
        if n not in fs: raise TypeFailure('unknown entry '+n)
        f=fs[n]
        if len(vs)!=len(f['params']): raise TypeFailure('arity '+n)
        env={p['name']:v for p,v in zip(f['params'],vs)}
        def e(x):
            if x['kind']=='Literal': return x['value']
            if x['kind']=='Name': return env[x['name']]
            if x['kind']=='Call': return call(x['callee'],[e(a) for a in x['args']])
            if x['kind']=='Binary': return evbin(x['op'],e(x['left']),e(x['right']))
            raise Unsupported(x['kind'])
        return e(f['body'])
    return call(entry,args)
CT={'Int':'int64_t','Real':'double','Bool':'bool'}
def ce(x):
    if x['kind']=='Literal': return ('true' if x['value'] else 'false') if x['type']=='Bool' else (repr(float(x['value'])) if x['type']=='Real' else str(int(x['value'])))
    if x['kind']=='Name': return x['name']
    if x['kind']=='Call': return 'cc_'+x['callee']+'('+', '.join(ce(a) for a in x['args'])+')'
    if x['kind']=='Binary':
        l,r=ce(x['left']),ce(x['right'])
        return f'(((double)({l}))/((double)({r})))' if x['op']=='/' else f'(({l}) {x["op"]} ({r}))'
    raise Unsupported(x['kind'])
def lower_c(t):
    fs=t['typed_ir']['functions']; out=['/* '+VERSION+' */','#include <stdint.h>','#include <stdbool.h>','']
    for f in fs:
        out.append(f"{CT[f['return_type']]} cc_{f['name']}({', '.join(CT[p['type']]+' '+p['name'] for p in f['params'])});")
    out.append('')
    for f in fs:
        out += [f"{CT[f['return_type']]} cc_{f['name']}({', '.join(CT[p['type']]+' '+p['name'] for p in f['params'])}) {{",'    return '+ce(f['body'])+';','}','']
    return '\n'.join(out)
def compile_source(src):
    g=GRAMMAR.read_text(); t=typecheck(parse_program(src,g)); t['source_sha256']=sha(src.encode()); t['grammar_sha256']=sha(g.encode()); return t

def differential(t,entry,args,cc='cc'):
    interp=evaluate(t,entry,args); fs={f['name']:f for f in t['typed_ir']['functions']}; f=fs[entry]
    carg=[]
    for p,v in zip(f['params'],args): carg.append('true' if p['type']=='Bool' and v else 'false' if p['type']=='Bool' else repr(float(v)) if p['type']=='Real' else str(int(v)))
    call='cc_'+entry+'('+', '.join(carg)+')'
    if f['return_type']=='Bool': fmt,val='%d','(int)('+call+')'; expected='1' if interp else '0'
    elif f['return_type']=='Real': fmt,val='%.17g','(double)('+call+')'; expected=format(float(interp),'.17g')
    else: fmt,val='%lld','(long long)('+call+')'; expected=str(interp)
    unit=lower_c(t)+f'\n#include <stdio.h>\nint main(void){{printf("{fmt}\\n",{val});return 0;}}\n'
    with tempfile.TemporaryDirectory() as d:
        d=Path(d); c=d/'x.c'; exe=d/'x'; c.write_text(unit)
        cp=subprocess.run([cc,'-std=c11','-O2','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],text=True,capture_output=True)
        if cp.returncode: raise ClayError(cp.stderr)
        rp=subprocess.run([str(exe)],text=True,capture_output=True)
        if rp.returncode: raise ClayError(rp.stderr)
        obs=rp.stdout.strip()
    return {'entry':entry,'args':args,'interpreter_result':interp,'native_stdout':obs,'expected_stdout':expected,'match':obs==expected,'generated_c_sha256':sha(unit.encode())}

def parse_arg(s,t):
    if t=='Int':return int(s)
    if t=='Real':return float(s)
    if t=='Bool':return s.lower() in {'1','true'}
    raise Unsupported(t)
def main():
    a=argparse.ArgumentParser(); a.add_argument('source',type=Path); a.add_argument('--emit',choices=['typed-ir','c'],default='typed-ir'); a.add_argument('--entry'); a.add_argument('--arg',action='append',default=[]); a.add_argument('--native-differential',action='store_true'); a.add_argument('--output',type=Path); z=a.parse_args()
    t=compile_source(z.source.read_text())
    if z.native_differential:
        f=next(f for f in t['typed_ir']['functions'] if f['name']==z.entry); vals=[parse_arg(v,p['type']) for v,p in zip(z.arg,f['params'])]; text=json.dumps(differential(t,z.entry,vals),indent=2,sort_keys=True)+'\n'
    elif z.emit=='c': text=lower_c(t)
    else:text=json.dumps(t,indent=2,sort_keys=True)+'\n'
    if z.output:z.output.parent.mkdir(parents=True,exist_ok=True);z.output.write_text(text)
    else:print(text,end='')
if __name__=='__main__':
    try:main()
    except ClayError as e: print(json.dumps({'error':type(e).__name__,'message':str(e)})); raise SystemExit(2)
