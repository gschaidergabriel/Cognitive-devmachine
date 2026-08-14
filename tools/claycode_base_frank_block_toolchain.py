#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from lark import Lark, Transformer

VERSION='claycode-frank-block-v8/0.1'
ROOT=Path(__file__).resolve().parents[1]
FRAME=ROOT/'research_entity/claycode/base/examples/FRANK_GRT_FRAME_V1.clay'
GRAMMAR=r'''
start: module_decl? fn_decl+
module_decl: "module" qid
fn_decl: "fn" NAME "(" [typed_params] ")" "->" type_expr block
typed_params: typed_param ("," typed_param)*
typed_param: NAME ":" type_expr
?type_expr: type_atom ("|" type_atom)*
?type_atom: qid ["<" type_expr ("," type_expr)* ">"] ["?"]
block: "{" stmt* "}"
?stmt: let_stmt | require_stmt | return_stmt | if_stmt | expr_stmt
let_stmt: "let" NAME [":" type_expr] "=" expr ";"?
require_stmt: "require" expr ";"?
return_stmt: "return" expr ";"?
if_stmt: "if" expr block ["else" block]
expr_stmt: expr ";"?
?expr: or_expr
?or_expr: and_expr (("||"|"or") and_expr)*
?and_expr: eq_expr (("&&"|"and") eq_expr)*
?eq_expr: rel_expr (("=="|"!=") rel_expr)*
?rel_expr: add_expr ((">="|"<="|">"|"<") add_expr)*
?add_expr: mul_expr (("+"|"-") mul_expr)*
?mul_expr: primary (("*"|"/") primary)*
?primary: call | symbol | qid -> var | STRING -> string | SIGNED_NUMBER -> number | BOOLEAN -> boolean | "(" expr ")"
call: qid "(" [call_args] ")"
call_args: call_arg ("," call_arg)*
?call_arg: qid "=" expr -> named_arg | expr -> positional_arg
symbol: "#" NAME
qid: NAME ("." NAME)*
BOOLEAN: "true"|"false"
NAME: /[A-Za-z_][A-Za-z0-9_-]*/
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS
%ignore /\/\/[^\n]*/
'''
PARSER=Lark(GRAMMAR,parser='lalr',start='start')

@dataclass(frozen=True)
class E:
    k:str; v:Any=None; a:tuple=()
@dataclass(frozen=True)
class S:
    k:str; name:str|None=None; e:E|None=None; body:tuple=(); alt:tuple=()
@dataclass(frozen=True)
class F:
    name:str; params:tuple[str,...]; param_types:tuple[str,...]; ret:str; body:tuple[S,...]

class T(Transformer):
    def qid(self,x): return '.'.join(map(str,x))
    def type_atom(self,x): return ''.join(map(str,x))
    def type_expr(self,x): return '|'.join(map(str,x))
    def typed_param(self,x): return (str(x[0]),str(x[1]))
    def typed_params(self,x): return list(x)
    def number(self,x):
        s=str(x[0]); return E('lit',float(s) if any(c in s for c in '.eE') else int(s))
    def string(self,x): return E('lit',json.loads(str(x[0])))
    def boolean(self,x): return E('lit',str(x[0])=='true')
    def symbol(self,x): return E('lit','#'+str(x[0]))
    def var(self,x): return E('var',str(x[0]))
    def positional_arg(self,x): return (None,x[0])
    def named_arg(self,x): return (str(x[0]),x[1])
    def call_args(self,x): return list(x)
    def call(self,x):
        args=x[1] if len(x)>1 and x[1] is not None else []
        return E('call',str(x[0]),tuple(args))
    def _bin(self,x):
        if len(x)==1:return x[0]
        raise ValueError('binary operator identity is intentionally fail-closed in this FRANK block slice')
    or_expr=_bin; and_expr=_bin; eq_expr=_bin; rel_expr=_bin; add_expr=_bin; mul_expr=_bin
    def let_stmt(self,x): return S('let',str(x[0]),x[-1])
    def require_stmt(self,x): return S('require',e=x[0])
    def return_stmt(self,x): return S('return',e=x[0])
    def expr_stmt(self,x): return S('expr',e=x[0])
    def block(self,x): return tuple(x)
    def if_stmt(self,x): return S('if',e=x[0],body=x[1],alt=(x[2] if len(x)>2 else ()))
    def fn_decl(self,x):
        name=str(x[0]); idx=1; params=[]; types=[]
        if isinstance(x[idx],list):
            params=[p[0] for p in x[idx]]; types=[p[1] for p in x[idx]]; idx+=1
        return F(name,tuple(params),tuple(types),str(x[idx]),x[idx+1])
    def module_decl(self,x): return ('module',str(x[0]))
    def start(self,x):
        module='anonymous'; funcs=[]
        for z in x:
            if isinstance(z,tuple) and len(z)==2 and z[0]=='module': module=z[1]
            elif isinstance(z,F): funcs.append(z)
        return module,tuple(funcs)

def parse(src:str): return T().transform(PARSER.parse(src))

def canon(module,funcs):
    def e(x:E): return {'k':x.k,'v':x.v,'a':[[n,e(y)] for n,y in x.a] if x.k=='call' else [e(y) for y in x.a]}
    def s(x:S): return {'k':x.k,'name':x.name,'e':e(x.e) if x.e else None,'body':[s(y) for y in x.body],'alt':[s(y) for y in x.alt]}
    obj={'schema':'claycode.frank-block-ir.v0','module':module,'functions':[{'name':f.name,'params':list(zip(f.params,f.param_types)),'return':f.ret,'body':[s(x) for x in f.body]} for f in funcs]}
    raw=json.dumps(obj,sort_keys=True,separators=(',',':')).encode()
    return obj,hashlib.sha256(raw).hexdigest()

class RT:
    def __init__(self,bindings:dict[str,Callable]): self.bindings=bindings; self.trace=[]
    def call(self,name,*args,**kwargs):
        if name not in self.bindings: raise KeyError(name)
        v=self.bindings[name](*args,**kwargs)
        self.trace.append({'call':name,'args_hash':hashlib.sha256(repr((args,kwargs)).encode()).hexdigest()})
        return v
    def record(self,name,*args,**kwargs):
        d={'__type__':name}
        if args:d['__args__']=list(args)
        d.update(kwargs); return d
    @staticmethod
    def get(v,k): return v[k] if isinstance(v,dict) else getattr(v,k)

def getvar(env,name):
    p=name.split('.'); v=env[p[0]]
    for k in p[1:]: v=RT.get(v,k)
    return v

def ev(e:E,env,rt:RT):
    if e.k=='lit':return e.v
    if e.k=='var':return getvar(env,e.v)
    if e.k=='call':
        pos=[]; kw={}
        for n,x in e.a:
            val=ev(x,env,rt)
            if n is None: pos.append(val)
            else: kw[n]=val
        if e.v and e.v[0].isupper(): return rt.record(e.v,*pos,**kw)
        return rt.call(e.v,*pos,**kw)
    raise ValueError(e.k)

def run(f:F,args,rt:RT,extra=None):
    env=dict(extra or {});env.update(zip(f.params,args))
    def execs(stmts):
        for s in stmts:
            if s.k=='let':env[s.name]=ev(s.e,env,rt)
            elif s.k=='require':
                if not ev(s.e,env,rt):raise RuntimeError('require failed')
            elif s.k=='return':return True,ev(s.e,env,rt)
            elif s.k=='expr':ev(s.e,env,rt)
            elif s.k=='if':
                ok,val=execs(s.body if ev(s.e,env,rt) else s.alt)
                if ok:return ok,val
        return False,None
    return execs(f.body)[1]

class Lower:
    def e(self,e:E):
        if e.k=='lit':return repr(e.v)
        if e.k=='var':
            p=e.v.split('.');code=p[0]
            for k in p[1:]:code=f'rt.get({code},{k!r})'
            return code
        if e.k=='call':
            pos=[]; kw=[]
            for n,x in e.a:
                (kw if n is not None else pos).append(f'{n}={self.e(x)}' if n is not None else self.e(x))
            args=', '.join(pos+kw)
            if e.v and e.v[0].isupper():return f"rt.record({e.v!r}{', ' if args else ''}{args})"
            return f"rt.call({e.v!r}{', ' if args else ''}{args})"
        raise ValueError(e.k)
    def stmts(self,ss,ind=1):
        p='    '*ind; out=[]
        for s in ss:
            if s.k=='let':out.append(f'{p}{s.name} = {self.e(s.e)}')
            elif s.k=='require':out += [f'{p}if not ({self.e(s.e)}):',f"{p}    raise RuntimeError('require failed')"]
            elif s.k=='return':out.append(f'{p}return {self.e(s.e)}')
            elif s.k=='expr':out.append(f'{p}{self.e(s.e)}')
            elif s.k=='if':
                out.append(f'{p}if {self.e(s.e)}:');out += self.stmts(s.body,ind+1) or [p+'    pass']
                if s.alt:out.append(f'{p}else:');out += self.stmts(s.alt,ind+1)
        return out
    def fn(self,f:F):
        return '\n'.join([f"def {f.name}(rt{', ' if f.params else ''}{', '.join(f.params)}):"]+self.stmts(f.body))+'\n'

def selftest():
    src=FRAME.read_text(encoding='utf-8')
    module,funcs=parse(src); assert len(funcs)==1 and funcs[0].name=='frame'
    _,semantic_hash=canon(module,funcs)
    bindings={
      'current_constraints':lambda current,goal:{'goal':goal,'secure':True},
      'construct_admissible_possibility_space':lambda current,constraints:['stay','explore'],
      'current_causal_precedence':lambda:['observe','decide','act'],
      'bounded_counterfactuals':lambda M:[f'cf:{x}' for x in M],
      'current_observation_interfaces':lambda:['user','state'],
      'current_authorized_interventions':lambda:['answer'],
      'calibrate_frame_uncertainty':lambda current,M:0.25,
    }
    extra={'THINKING_FRAMEWORK_NOT_WORLD_FACT':'THINKING_FRAMEWORK_NOT_WORLD_FACT'}
    rt1=RT(bindings); reference=run(funcs[0],[{'epoch':1},'#goal'],rt1,extra)
    generated=Lower().fn(funcs[0]); ns=dict(extra);exec(compile(generated,'<frank-frame>','exec'),ns)
    rt2=RT(bindings); lowered=ns['frame'](rt2,{'epoch':1},'#goal')
    assert reference==lowered and reference['source_status']=='THINKING_FRAMEWORK_NOT_WORLD_FACT'
    assert rt1.trace==rt2.trace
    receipt={'schema_version':'1.0','candidate':VERSION,'pass':True,'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'semantic_hash':semantic_hash,'reference_result':reference,'lowered_result':lowered,'trace_equivalent':True,'generated_python_sha256':hashlib.sha256(generated.encode()).hexdigest(),'upstream_repo':'gschaidergabriel/Dr.-Unterweger','upstream_path':'claycode/frank_grt.clay','upstream_blob':'b9027118e886b8da4110c0801f7d5e1cf9d1c3b9','counts_as_target_acceptance':False,'counts_as_wp13_pass':False,'claim_boundary':'Real frozen FRANK GRT frame source compiles through block-body/named-arg frontend and differential evaluator/lowering; target Ubuntu and wider frozen FRANK subsystem still required.'}
    out=ROOT/'research_entity/claycode/autonomous/FRANK_GRT_BLOCK_TOOLCHAIN_RECEIPT.json'
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'pass':True,'semantic_hash':semantic_hash,'trace_equivalent':True}))

if __name__=='__main__':selftest()
