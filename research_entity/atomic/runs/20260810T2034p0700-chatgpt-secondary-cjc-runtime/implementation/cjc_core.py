#!/usr/bin/env python3
"""Counterfactual Jet Commutator core algebra."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import hashlib, json
from typing import Iterable, Mapping
Number=int
Monomial=frozenset[str]
class Exactness(str,Enum):
    EXACT="EXACT"; TRUNCATED="TRUNCATED"; UNKNOWN="UNKNOWN"
class PairClass(str,Enum):
    FULL_COMMUTE="FULL_COMMUTE"; HIDDEN_CAUSAL_NONCOMMUTE="HIDDEN_CAUSAL_NONCOMMUTE"; STATE_NONCOMMUTE="STATE_NONCOMMUTE"; UNKNOWN="UNKNOWN"
class EffectClass(str,Enum):
    PURE="PURE"; READ_ONLY="READ_ONLY"; INTERNAL_STATE="INTERNAL_STATE"; EXTERNAL_EFFECT="EXTERNAL_EFFECT"; STOCHASTIC="STOCHASTIC"; OPAQUE="OPAQUE"
class CJCError(ValueError): pass
def _stable_json(value:object)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
def _sha256_domain(domain:bytes,value:object)->str:
    return hashlib.sha256(domain+_stable_json(value)).hexdigest()
@dataclass(frozen=True)
class StateIdentity:
    program_semantic_id:str; state_epoch:str; state_version:str; state_instance_id:str
    @classmethod
    def derive(cls,*,program_semantic_id:str,state_epoch:str|int,state_version:str|int)->"StateIdentity":
        epoch,version=str(state_epoch),str(state_version)
        payload={"program_semantic_id":program_semantic_id,"state_epoch":epoch,"state_version":version}
        sid="cjcstate:"+_sha256_domain(b"CJCStateIdentity/v1\x00",payload)
        return cls(program_semantic_id,epoch,version,sid)
@dataclass(frozen=True)
class JetPolicy:
    max_degree:int=8; max_terms:int=4096
    def validate(self):
        if self.max_degree<0: raise CJCError("max_degree must be >= 0")
        if self.max_terms<=0: raise CJCError("max_terms must be > 0")
@dataclass
class BoolJet:
    terms:dict[Monomial,Number]=field(default_factory=dict); exactness:Exactness=Exactness.EXACT; dropped_abs_mass:int=0
    def __post_init__(self): self._clean()
    def _clean(self):
        self.terms={m:int(c) for m,c in self.terms.items() if c!=0}
        if self.exactness==Exactness.UNKNOWN: self.terms={}
    @classmethod
    def const(cls,value:Number)->"BoolJet": return cls({frozenset():int(value)} if value else {})
    @classmethod
    def var(cls,name:str)->"BoolJet":
        if not name: raise CJCError("UseRef variable must be non-empty")
        return cls({frozenset({name}):1})
    @classmethod
    def unknown(cls)->"BoolJet": return cls({},Exactness.UNKNOWN)
    def copy(self)->"BoolJet": return BoolJet(dict(self.terms),self.exactness,self.dropped_abs_mass)
    @property
    def degree(self)->int: return max((len(m) for m in self.terms),default=0)
    @property
    def support(self)->frozenset[str]:
        out=set()
        for monomial in self.terms: out.update(monomial)
        return frozenset(out)
    @property
    def term_count(self)->int: return len(self.terms)
    def canonical(self)->dict:
        return {"exactness":self.exactness.value,"dropped_abs_mass":self.dropped_abs_mass,"terms":[{"uses":sorted(m),"coefficient":c} for m,c in sorted(self.terms.items(),key=lambda kv:(len(kv[0]),sorted(kv[0])))]}
    def _combine_exactness(self,other:"BoolJet")->Exactness:
        if Exactness.UNKNOWN in (self.exactness,other.exactness): return Exactness.UNKNOWN
        if Exactness.TRUNCATED in (self.exactness,other.exactness): return Exactness.TRUNCATED
        return Exactness.EXACT
    def __add__(self,other:"BoolJet|int")->"BoolJet":
        if isinstance(other,int): other=BoolJet.const(other)
        ex=self._combine_exactness(other)
        if ex==Exactness.UNKNOWN: return BoolJet.unknown()
        out=dict(self.terms)
        for m,c in other.terms.items(): out[m]=out.get(m,0)+c
        return BoolJet(out,ex,self.dropped_abs_mass+other.dropped_abs_mass)
    __radd__=__add__
    def __neg__(self)->"BoolJet": return BoolJet({m:-c for m,c in self.terms.items()},self.exactness,self.dropped_abs_mass)
    def __sub__(self,other:"BoolJet|int")->"BoolJet":
        if isinstance(other,int): other=BoolJet.const(other)
        return self+(-other)
    def __rsub__(self,other:int)->"BoolJet": return BoolJet.const(other)-self
    def scale(self,factor:Number)->"BoolJet":
        if self.exactness==Exactness.UNKNOWN: return BoolJet.unknown()
        return BoolJet({m:int(factor)*c for m,c in self.terms.items()},self.exactness,abs(int(factor))*self.dropped_abs_mass)
    def mul(self,other:"BoolJet",policy:JetPolicy)->"BoolJet":
        policy.validate(); ex=self._combine_exactness(other)
        if ex==Exactness.UNKNOWN: return BoolJet.unknown()
        out={}; dropped=self.dropped_abs_mass+other.dropped_abs_mass; truncated=ex==Exactness.TRUNCATED
        for ma,ca in self.terms.items():
            for mb,cb in other.terms.items():
                mon=frozenset(set(ma)|set(mb)); coeff=ca*cb
                if len(mon)>policy.max_degree: truncated=True; dropped+=abs(coeff); continue
                out[mon]=out.get(mon,0)+coeff
        out={m:c for m,c in out.items() if c}
        if len(out)>policy.max_terms: return BoolJet({},Exactness.UNKNOWN,dropped+sum(abs(c) for c in out.values()))
        return BoolJet(out,Exactness.TRUNCATED if truncated else Exactness.EXACT,dropped)
    def evaluate(self,enabled_uses:Iterable[str])->int:
        if self.exactness!=Exactness.EXACT: raise CJCError(f"cannot exact-evaluate {self.exactness.value} jet")
        enabled=frozenset(enabled_uses); total=0
        for monomial,coeff in self.terms.items():
            if monomial.issubset(enabled): total+=coeff
        return total
    def is_zero_polynomial(self)->bool: return self.exactness==Exactness.EXACT and not self.terms
@dataclass
class JetState:
    identity:StateIdentity; values:dict[str,BoolJet]
    @classmethod
    def from_concrete(cls,identity:StateIdentity,values:Mapping[str,int])->"JetState": return cls(identity,{k:BoolJet.const(v) for k,v in values.items()})
    def copy(self)->"JetState": return JetState(self.identity,{k:v.copy() for k,v in self.values.items()})
    @property
    def exactness(self)->Exactness:
        states={v.exactness for v in self.values.values()}
        if Exactness.UNKNOWN in states:return Exactness.UNKNOWN
        if Exactness.TRUNCATED in states:return Exactness.TRUNCATED
        return Exactness.EXACT
    @property
    def total_terms(self)->int:return sum(v.term_count for v in self.values.values())
    @property
    def max_degree(self)->int:return max((v.degree for v in self.values.values()),default=0)
    def full_value(self,uses:Iterable[str])->dict[str,int]:return {k:p.evaluate(uses) for k,p in self.values.items()}
    def canonical(self)->dict:return {"identity":self.identity.__dict__,"values":{k:self.values[k].canonical() for k in sorted(self.values)}}
@dataclass(frozen=True)
class TransitionContract:
    transition_id:str; use_ref:str; version:str; state_epoch:str; effect_class:EffectClass; reads:frozenset[str]; writes:frozenset[str]; evidence_refs:tuple[str,...]; deterministic:bool=True; reversible_internal:bool=True
    @property
    def semantic_hash(self)->str:
        payload={"transition_id":self.transition_id,"use_ref":self.use_ref,"version":self.version,"state_epoch":self.state_epoch,"effect_class":self.effect_class.value,"reads":sorted(self.reads),"writes":sorted(self.writes),"evidence_refs":sorted(self.evidence_refs),"deterministic":self.deterministic,"reversible_internal":self.reversible_internal}
        return _sha256_domain(b"CJCTransitionContract/v1\x00",payload)
    def exact_eligible(self,identity:StateIdentity)->bool:
        return self.state_epoch==identity.state_epoch and self.deterministic and self.reversible_internal and self.effect_class in {EffectClass.PURE,EffectClass.INTERNAL_STATE} and bool(self.evidence_refs)
