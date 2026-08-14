#!/usr/bin/env python3
"""Reproduce the ClayCode G9 function-definition/call closure proxy."""
from dataclasses import dataclass
import hashlib, json, random, re

GRAMMAR_BLOB="ec2f17077333955cfdabe6c64868d597e7e734e3"
SPEC_BLOB="1a17bba3c835520baff2ac8fa432749ba2165d8e"
DIALECT_BLOB="dbb72460bc5a049c784d1acd1aaef152fa37f797"
CURRENT_STATEMENT="statement = module_decl | version_decl | status_decl | parent_decl | import_decl | interface_decl | dialect_decl | law_decl | rule_decl | invariant_decl | class_decl | record_decl | tensor_decl | codec_decl | surface_decl | metric_decl | hash_decl | needle_decl | cycle_decl ;"
CURRENT_PRIMARY="primary = literal | qid | call | list | object | \"(\", expr, \")\" ;"
assert "fn_decl" not in CURRENT_STATEMENT and "call" in CURRENT_PRIMARY

TOK=re.compile(r'(?P<WS>\s+)|(?P<ARROW>->)|(?P<NUM>-?\d+)|(?P<STR>"(?:\\.|[^"\\])*")|(?P<ID>[A-Za-z_][A-Za-z0-9_-]*(?:\.[A-Za-z_][A-Za-z0-9_-]*)*)|(?P<SYM>[:,()=+\-*/;])')
class CCError(Exception): pass
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

class Parser:
    def __init__(self,s):
        self.t=[]; i=0
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
        if self.at("version"): self.eat("version"); self.eat(k="STR")
        fs={}
        while not self.at(k="EOF"):
            self.eat("fn"); n=self.eat(k="ID"); self.eat("("); ps=[]
            if not self.at(")"):
                while True:
                    pn=self.eat(k="ID"); self.eat(":"); pt=self.eat(k="ID"); ps.append((pn,pt))
                    if self.at(","): self.eat(",")
                    else: break
            self.eat(")"); self.eat("->"); rt=self.eat(k="ID"); self.eat("="); body=self.expr()
            if self.at(";"): self.eat(";")
            if n in fs: raise CCError("duplicate function")
            fs[n]=Fn(n,tuple(ps),rt,body)
        return module,fs

def typ(e,env,sigs):
    if isinstance(e,Num): return "Int"
    if isinstance(e,Var):
        if e.n not in env: raise CCError("undefined var "+e.n)
        return env[e.n]
    if isinstance(e,Bin):
        if typ(e.x,env,sigs)!="Int" or typ(e.y,env,sigs)!="Int": raise CCError("arith type")
        return "Int"
    if isinstance(e,Call):
        if e.n not in sigs: raise CCError("undefined function "+e.n)
        ps,rt=sigs[e.n]
        if len(ps)!=len(e.a): raise CCError("arity")
        for x,t in zip(e.a,ps):
            if typ(x,env,sigs)!=t: raise CCError("arg type")
        return rt

def check(fs):
    sigs={n:([t for _,t in f.p],f.r) for n,f in fs.items()}
    for f in fs.values():
        if typ(f.b,dict(f.p),sigs)!=f.r: raise CCError("return type")

def ev(e,env,fs,depth=0):
    if depth>100: raise CCError("depth")
    if isinstance(e,Num): return e.v
    if isinstance(e,Var): return env[e.n]
    if isinstance(e,Bin):
        x,y=ev(e.x,env,fs,depth),ev(e.y,env,fs,depth)
        return {"+":lambda:x+y,"-":lambda:x-y,"*":lambda:x*y,"/":lambda:int(x/y)}[e.op]()
    f=fs[e.n]; vals=[ev(x,env,fs,depth) for x in e.a]
    return ev(f.b,dict(zip([n for n,_ in f.p],vals)),fs,depth+1)

def invoke(fs,n,*a):
    f=fs[n]
    if len(a)!=len(f.p): raise CCError("arity")
    return ev(f.b,dict(zip([x for x,_ in f.p],a)),fs,1)

SRC='''module app.function_bridge
version "0.1"
fn add(a:Int,b:Int)->Int = a+b;
fn mul_add(a:Int,b:Int,c:Int)->Int = add(a*b,c);
fn twice_mix(x:Int,y:Int)->Int = mul_add(x,2,y)+add(x,y);
'''
_,fs=Parser(SRC).program(); check(fs)
r=random.Random(202608091711); mism=0
for _ in range(20000):
    x=r.randint(-100000,100000); y=r.randint(-100000,100000)
    mism += invoke(fs,"twice_mix",x,y) != ((x*2+y)+(x+y))
neg={}
for n,s in {
 "undefined_function":"module x\nfn f(a:Int)->Int = missing(a);",
 "arity_mismatch":"module x\nfn g(a:Int)->Int = a;\nfn f(a:Int)->Int = g(a,a);",
 "undefined_variable":"module x\nfn f(a:Int)->Int = a+z;"
}.items():
    try:
        _,z=Parser(s).program(); check(z); neg[n]="UNEXPECTED_ACCEPT"
    except CCError as e: neg[n]="REJECT:"+str(e)
print(json.dumps({
 "grammar_blob":GRAMMAR_BLOB,"spec_blob":SPEC_BLOB,"dialect_blob":DIALECT_BLOB,
 "current_has_call":True,"current_has_fn_decl":False,"randomized_calls":20000,
 "differential_mismatches":mism,"negative_tests":neg,
 "candidate_source_sha256":hashlib.sha256(SRC.encode()).hexdigest()
},sort_keys=True,indent=2))
