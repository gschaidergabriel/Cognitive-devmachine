#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json, random, re, time

CANDIDATE_VERSION = "cc-lab-effect-closure-0.1"
SPEC_BLOB = "1a17bba3c835520baff2ac8fa432749ba2165d8e"
HARNESS_ORACLE_COMMIT = "89dfb8bf08d9082cfa85bb5f48cf3fac0c3a02fa"
SEED = 202608091728

TOK=re.compile(r'(?P<WS>\s+)|(?P<ARROW>->)|(?P<NUM>-?\d+)|(?P<STR>"(?:\\.|[^"\\])*")|(?P<ID>[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*)|(?P<SYM>[:,()=+\-*/;])')
class CCError(Exception): pass
class CapabilityDenied(CCError): pass

@dataclass(frozen=True)
class Num: v:int
@dataclass(frozen=True)
class Var: n:str
@dataclass(frozen=True)
class Call: n:str; a:tuple
@dataclass(frozen=True)
class Bin: op:str; x:object; y:object
@dataclass(frozen=True)
class Fn: n:str; p:tuple; r:str; b:object

HOST = {
    "host.fs_read": {"p":["Int"], "r":"Int", "effect":"FS_READ", "cap":"cap.fs.read"},
    "host.fs_write": {"p":["Int"], "r":"Int", "effect":"FS_WRITE", "cap":"cap.fs.write"},
    "host.db_put": {"p":["Int"], "r":"Int", "effect":"DB_WRITE", "cap":"cap.db.write"},
    "host.http_send": {"p":["Int"], "r":"Int", "effect":"HTTP", "cap":"cap.http"},
}
EFFECT_TO_CAP = {v["effect"]:v["cap"] for v in HOST.values()}

class Parser:
    def __init__(self,s):
        self.src=s; self.t=[]; i=0
        while i<len(s):
            m=TOK.match(s,i)
            if not m: raise CCError(f"lex@{i}")
            i=m.end()
            if m.lastgroup!="WS": self.t.append((m.lastgroup,m.group()))
        self.t.append(("EOF","")); self.i=0
    def at(self,v=None,k=None):
        kk,vv=self.t[self.i]; return (v is None or vv==v) and (k is None or kk==k)
    def eat(self,v=None,k=None):
        if not self.at(v,k): raise CCError(f"expected {v or k}, got {self.t[self.i]}")
        x=self.t[self.i][1]; self.i+=1; return x
    def expr(self):
        x=self.term()
        while self.at("+") or self.at("-"):
            op=self.eat(); x=Bin(op,x,self.term())
        return x
    def term(self):
        x=self.atom()
        while self.at("*") or self.at("/"):
            op=self.eat(); x=Bin(op,x,self.atom())
        return x
    def atom(self):
        if self.at(k="NUM"): return Num(int(self.eat(k="NUM")))
        if self.at("("):
            self.eat("("); x=self.expr(); self.eat(")"); return x
        n=self.eat(k="ID")
        if not self.at("("): return Var(n)
        self.eat("("); a=[]
        if not self.at(")"):
            while True:
                a.append(self.expr())
                if self.at(","): self.eat(",")
                else: break
        self.eat(")"); return Call(n,tuple(a))
    def program(self):
        self.eat("module"); module=self.eat(k="ID")
        version=None
        if self.at("version"): self.eat("version"); version=json.loads(self.eat(k="STR"))
        fs={}
        while not self.at(k="EOF"):
            self.eat("fn"); n=self.eat(k="ID")
            if n.startswith("host."): raise CCError("reserved host namespace")
            self.eat("("); ps=[]
            if not self.at(")"):
                while True:
                    pn=self.eat(k="ID"); self.eat(":"); pt=self.eat(k="ID"); ps.append((pn,pt))
                    if self.at(","): self.eat(",")
                    else: break
            self.eat(")"); self.eat("->"); rt=self.eat(k="ID"); self.eat("="); body=self.expr()
            if self.at(";"): self.eat(";")
            if n in fs: raise CCError("duplicate function")
            fs[n]=Fn(n,tuple(ps),rt,body)
        return module,version,fs

def walk(e):
    yield e
    if isinstance(e,Bin): yield from walk(e.x); yield from walk(e.y)
    elif isinstance(e,Call):
        for a in e.a: yield from walk(a)

def type_check(fs):
    sigs={n:([t for _,t in f.p],f.r) for n,f in fs.items()}
    def typ(e,env):
        if isinstance(e,Num): return "Int"
        if isinstance(e,Var):
            if e.n not in env: raise CCError("undefined var "+e.n)
            return env[e.n]
        if isinstance(e,Bin):
            if typ(e.x,env)!="Int" or typ(e.y,env)!="Int": raise CCError("arith type")
            return "Int"
        if isinstance(e,Call):
            spec=HOST.get(e.n)
            if spec is not None: ps,rt=spec["p"],spec["r"]
            elif e.n in sigs: ps,rt=sigs[e.n]
            else: raise CCError("undefined function "+e.n)
            if len(ps)!=len(e.a): raise CCError("arity")
            for x,t in zip(e.a,ps):
                if typ(x,env)!=t: raise CCError("arg type")
            return rt
        raise CCError("unknown expr")
    for f in fs.values():
        if typ(f.b,dict(f.p))!=f.r: raise CCError("return type")
    return sigs

def direct_summary(fs):
    out={}
    for n,f in fs.items():
        eff=set(); caps=set(); calls=set()
        for e in walk(f.b):
            if isinstance(e,Call):
                if e.n in HOST:
                    eff.add(HOST[e.n]["effect"]); caps.add(HOST[e.n]["cap"])
                else: calls.add(e.n)
        out[n]={"effects":eff,"caps":caps,"calls":calls}
    return out

def lfp_summary(fs):
    d=direct_summary(fs)
    s={n:{"effects":set(v["effects"]),"caps":set(v["caps"])} for n,v in d.items()}
    changed=True; rounds=0
    while changed:
        changed=False; rounds+=1
        if rounds > len(fs)+1: raise AssertionError("lfp nonconvergence")
        for n,v in d.items():
            ne=set(v["effects"]); nc=set(v["caps"])
            for callee in v["calls"]:
                if callee not in s: raise CCError("undefined function "+callee)
                ne |= s[callee]["effects"]; nc |= s[callee]["caps"]
            if ne!=s[n]["effects"] or nc!=s[n]["caps"]:
                s[n]={"effects":ne,"caps":nc}; changed=True
    return s,rounds

def graph_oracle(d):
    out={}
    for start in d:
        seen=set(); stack=[start]; eff=set(); caps=set()
        while stack:
            n=stack.pop()
            if n in seen: continue
            seen.add(n); eff |= d[n]["effects"]; caps |= d[n]["caps"]
            stack.extend(d[n]["calls"])
        out[start]={"effects":eff,"caps":caps}
    return out

class Gateway:
    def __init__(self,caps): self.caps=set(caps); self.trace=[]
    def effect(self,effect,cap,x):
        if cap not in self.caps: raise CapabilityDenied(f"missing {cap}")
        self.trace.append((effect,cap,x))
        if effect=="FS_READ": return x+1000
        if effect=="FS_WRITE": return x
        if effect=="DB_WRITE": return x*2
        if effect=="HTTP": return x+7
        raise CCError("unknown effect")

def interpret(fs,entry,args,gw,depth=0):
    if depth>100: raise CCError("depth")
    def ev(e,env):
        if isinstance(e,Num): return e.v
        if isinstance(e,Var): return env[e.n]
        if isinstance(e,Bin):
            x,y=ev(e.x,env),ev(e.y,env)
            return {"+":lambda:x+y,"-":lambda:x-y,"*":lambda:x*y,"/":lambda:int(x/y)}[e.op]()
        if isinstance(e,Call):
            vals=[ev(a,env) for a in e.a]
            if e.n in HOST:
                sp=HOST[e.n]; return gw.effect(sp["effect"],sp["cap"],vals[0])
            f=fs[e.n]; return interpret(fs,e.n,vals,gw,depth+1)
        raise CCError("unknown expr")
    f=fs[entry]
    if len(args)!=len(f.p): raise CCError("arity")
    return ev(f.b,dict(zip([n for n,_ in f.p],args)))

def ast_obj(e):
    if isinstance(e,Num): return ["num",e.v]
    if isinstance(e,Var): return ["var",e.n]
    if isinstance(e,Bin): return ["bin",e.op,ast_obj(e.x),ast_obj(e.y)]
    if isinstance(e,Call): return ["call",e.n,[ast_obj(a) for a in e.a]]
    raise TypeError(e)

def canonical_ir(module,fs,summaries):
    return {
      "module":module,
      "functions":[{
        "name":n,"params":list(fs[n].p),"return":fs[n].r,"body":ast_obj(fs[n].b),
        "effect_summary":sorted(summaries[n]["effects"]),
        "required_capabilities":sorted(summaries[n]["caps"])
      } for n in sorted(fs)]
    }

def h(obj):
    if not isinstance(obj,(str,bytes)): obj=json.dumps(obj,sort_keys=True,separators=(",",":"))
    if isinstance(obj,str): obj=obj.encode()
    return hashlib.sha256(obj).hexdigest()

def py_expr(e):
    if isinstance(e,Num): return str(e.v)
    if isinstance(e,Var): return e.n.replace("-","_")
    if isinstance(e,Bin): return f"({py_expr(e.x)} {e.op} {py_expr(e.y)})"
    if isinstance(e,Call):
        args=",".join(py_expr(a) for a in e.a)
        if e.n in HOST:
            sp=HOST[e.n]; return f"gw.effect({sp['effect']!r},{sp['cap']!r},{args})"
        return f"fn_{e.n.replace('.','_').replace('-','_')}(gw,{args})"
    raise TypeError(e)

def lower_python(fs,entry="main"):
    lines=["# generated by "+CANDIDATE_VERSION]
    for n in sorted(fs):
        f=fs[n]; params=",".join(x.replace('-','_') for x,_ in f.p)
        sig=(","+params) if params else ""
        lines.append(f"def fn_{n.replace('.','_').replace('-','_')}(gw{sig}):")
        lines.append("    return "+py_expr(f.b))
    lines.append("def __entry(gw,x):")
    lines.append(f"    return fn_{entry}(gw,x)")
    return "\n".join(lines)+"\n"

def exec_lowered(code,gw,x):
    ns={}; exec(compile(code,"<claycode-lowered>","exec"),ns,ns); return ns["__entry"](gw,x)

SRC='''module app.effect_bridge
version "0.1"
fn read(x:Int)->Int = host.fs_read(x);
fn store(x:Int)->Int = host.db_put(read(x));
fn mix(x:Int)->Int = store(x)+host.http_send(x);
fn main(x:Int)->Int = mix(x)+read(x);
'''
SRC_FMT='''module   app.effect_bridge\nversion "0.1"\n\nfn read ( x : Int ) -> Int = host.fs_read ( x ) ;\nfn store(x:Int)->Int=host.db_put( read(x) );\nfn mix(x:Int)->Int = store(x) + host.http_send(x) ;\nfn main(x:Int)->Int=mix(x)+read(x);\n'''

start=time.perf_counter()
mod,ver,fs=Parser(SRC).program(); type_check(fs); sums,rounds=lfp_summary(fs)
mod2,ver2,fs2=Parser(SRC_FMT).program(); type_check(fs2); sums2,_=lfp_summary(fs2)
ir=canonical_ir(mod,fs,sums); ir2=canonical_ir(mod2,fs2,sums2)
sem_hash=h(ir); sem_hash2=h(ir2)
source_hash=h(SRC); source_hash2=h(SRC_FMT)
contract_hash=h({"candidate":CANDIDATE_VERSION,"source":source_hash,"semantic":sem_hash})
contract_hash2=h({"candidate":CANDIDATE_VERSION,"source":source_hash2,"semantic":sem_hash2})
code=lower_python(fs); code2=lower_python(fs2)
lowered_hash=h(code); lowered_hash2=h(code2)

caps={"cap.fs.read","cap.db.write","cap.http"}
r=random.Random(SEED); mism=0; trace_mism=0; NEXEC=5000
for _ in range(NEXEC):
    x=r.randint(-100000,100000)
    g1=Gateway(caps); a=interpret(fs,"main",[x],g1)
    g2=Gateway(caps); b=exec_lowered(code,g2,x)
    mism += (a!=b)
    trace_mism += (g1.trace!=g2.trace)

rng=random.Random(SEED+1); graph_mism=0; GRAPHS=20000; max_rounds=0
for _ in range(GRAPHS):
    n=rng.randint(1,14); names=[f"f{i}" for i in range(n)]
    d={}
    for name in names:
        eff=set(rng.sample(list(EFFECT_TO_CAP), rng.randint(0,min(2,len(EFFECT_TO_CAP)))))
        calls=set(rng.sample(names, rng.randint(0,min(3,n))))
        d[name]={"effects":eff,"caps":{EFFECT_TO_CAP[e] for e in eff},"calls":calls}
    s={k:{"effects":set(v["effects"]),"caps":set(v["caps"])} for k,v in d.items()}
    changed=True; rr=0
    while changed:
        changed=False; rr+=1
        for k,v in d.items():
            ne=set(v["effects"]); nc=set(v["caps"])
            for c in v["calls"]: ne |= s[c]["effects"]; nc |= s[c]["caps"]
            if ne!=s[k]["effects"] or nc!=s[k]["caps"]: s[k]={"effects":ne,"caps":nc}; changed=True
    max_rounds=max(max_rounds,rr)
    o=graph_oracle(d)
    if s!=o: graph_mism += 1

rec_src='''module app.rec_effect
fn f(x:Int)->Int = g(x);
fn g(x:Int)->Int = f(host.http_send(x));
'''
_,_,recfs=Parser(rec_src).program(); type_check(recfs); recs,_=lfp_summary(recfs)
recursive_ok=(recs["f"]["effects"]=={"HTTP"} and recs["g"]["effects"]=={"HTTP"})

neg={}
negative_sources={
 "reserved_host_shadow":"module x\nfn host.fs_read(x:Int)->Int=x;",
 "undefined_function":"module x\nfn f(x:Int)->Int=missing(x);",
 "arity_mismatch":"module x\nfn f(x:Int)->Int=host.fs_read(x,x);",
}
for name,s in negative_sources.items():
    try:
        _,_,z=Parser(s).program(); type_check(z); lfp_summary(z); neg[name]="UNEXPECTED_ACCEPT"
    except CCError as e: neg[name]="REJECT:"+str(e)
try:
    gw=Gateway({"cap.fs.read","cap.db.write"})
    interpret(fs,"main",[7],gw)
    neg["missing_http_capability"]="UNEXPECTED_ACCEPT"
except CapabilityDenied as e:
    neg["missing_http_capability"]="REJECT:"+str(e)

forge='''module x
fn cap.fs.read(x:Int)->Int=x;
fn main(x:Int)->Int=host.fs_read(cap.fs.read(x));
'''
_,_,ffs=Parser(forge).program(); type_check(ffs); lfp_summary(ffs)
try:
    interpret(ffs,"main",[3],Gateway(set()))
    neg["textual_capability_name"]="UNEXPECTED_ACCEPT"
except CapabilityDenied as e:
    neg["textual_capability_name"]="REJECT:"+str(e)

probe=Gateway(caps); out=interpret(fs,"main",[11],probe)
observed_effects={t[0] for t in probe.trace}
summary_runtime_match=(observed_effects==sums["main"]["effects"])
trace_root=h(probe.trace)

elapsed=time.perf_counter()-start
result={
 "candidate_version":CANDIDATE_VERSION,
 "spec_blob":SPEC_BLOB,
 "harness_oracle_commit":HARNESS_ORACLE_COMMIT,
 "seed":SEED,
 "source_hash":source_hash,
 "semantic_hash":sem_hash,
 "contract_hash":contract_hash,
 "lowered_hash":lowered_hash,
 "format_variant":{
   "source_hash":source_hash2,"semantic_hash":sem_hash2,"contract_hash":contract_hash2,"lowered_hash":lowered_hash2,
   "semantic_equal":sem_hash==sem_hash2,"contract_distinct":contract_hash!=contract_hash2,"lowered_equal":lowered_hash==lowered_hash2
 },
 "main_effect_summary":sorted(sums["main"]["effects"]),
 "main_required_capabilities":sorted(sums["main"]["caps"]),
 "effect_lfp_rounds":rounds,
 "recursive_cycle_effect_closure":recursive_ok,
 "random_call_graphs":GRAPHS,
 "graph_closure_mismatches":graph_mism,
 "graph_max_lfp_rounds":max_rounds,
 "lowered_execution_cases":NEXEC,
 "interpreter_vs_lowered_output_mismatches":mism,
 "interpreter_vs_lowered_trace_mismatches":trace_mism,
 "summary_matches_observed_unconditional_effect_classes":summary_runtime_match,
 "probe_output":out,
 "probe_trace_root":trace_root,
 "negative_tests":neg,
 "elapsed_seconds":round(elapsed,6)
}
print(json.dumps(result,sort_keys=True,indent=2))
