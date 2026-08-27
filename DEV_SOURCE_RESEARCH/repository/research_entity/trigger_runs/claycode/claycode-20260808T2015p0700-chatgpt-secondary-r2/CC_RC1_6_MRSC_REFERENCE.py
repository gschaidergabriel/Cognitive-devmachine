#!/usr/bin/env python3
"""CC-RC1.6 MRSC executable reference mechanism.

Research-only reference:
- one canonical semantic item
- deterministic discrete projection with dual-binding receipt
- deterministic reconciliation
- no execution authority
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256, blake2s
import json

CLASSES = ("FACT_EXACT","OBSERVATION","ACTIVATION_PRIOR","PROPOSAL","AUTHORITY_CAP","EFFECT_INTENT")

def _hash(obj) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

@dataclass(frozen=True)
class Canonical:
    semantic_id: str
    semantic_class: str
    roles: tuple
    epoch: int
    value: object
    def payload(self) -> dict:
        return {"semantic_id":self.semantic_id,"semantic_class":self.semantic_class,"roles":list(self.roles),"epoch":self.epoch,"value":self.value}

def canonical_hash(c: Canonical) -> str:
    return _hash(c.payload())

def projected_payload(view: dict) -> dict:
    return {k:view[k] for k in ("h","c","r","epoch","v")}

def project_discrete(c: Canonical, *, compiler_version="cc11-ref-1") -> dict:
    if c.semantic_class not in CLASSES:
        raise ValueError("unknown semantic class")
    payload={"h":blake2s(c.semantic_id.encode(),digest_size=3).hexdigest(),"c":CLASSES.index(c.semantic_class),"r":list(c.roles),"epoch":c.epoch,"v":c.value}
    payload["receipt"]={"canonical_input_hash":canonical_hash(c),"projected_view_hash":_hash(payload),"semantic_id":c.semantic_id,"semantic_class":c.semantic_class,"roles":list(c.roles),"epoch":c.epoch,"compiler_version":compiler_version,"authority":"IDENTITY_AND_TRANSLATION_EVIDENCE_ONLY"}
    return payload

def reconcile_discrete(view: dict, canonical: Canonical) -> dict:
    r=view.get("receipt") or {}
    checks={
        "canonical_input":r.get("canonical_input_hash")==canonical_hash(canonical),
        "projected_view":r.get("projected_view_hash")==_hash(projected_payload(view)),
        "semantic_id":r.get("semantic_id")==canonical.semantic_id,
        "semantic_class_receipt":r.get("semantic_class")==canonical.semantic_class,
        "semantic_class_view":view.get("c")==CLASSES.index(canonical.semantic_class),
        "roles_receipt":tuple(r.get("roles",()))==canonical.roles,
        "roles_view":tuple(view.get("r",()))==canonical.roles,
        "epoch_receipt":r.get("epoch")==canonical.epoch,
        "epoch_view":view.get("epoch")==canonical.epoch,
        "value":view.get("v")==canonical.value,
    }
    return {"status":"VERIFIED" if all(checks.values()) else "REJECTED","checks":checks,"authority":"SEMANTIC_FIDELITY_EVIDENCE_ONLY"}

def self_test() -> None:
    c=Canonical("rel:42","FACT_EXACT",("src",1,"dst",2),7,{"x":3})
    v=project_discrete(c)
    assert reconcile_discrete(v,c)["status"]=="VERIFIED"
    for mutation in ("role","class","epoch","value","receipt_id"):
        x=json.loads(json.dumps(v))
        if mutation=="role": x["r"][1],x["r"][3]=x["r"][3],x["r"][1]
        elif mutation=="class": x["c"]=(x["c"]+1)%len(CLASSES)
        elif mutation=="epoch": x["epoch"]-=1
        elif mutation=="value": x["v"]={"x":4}
        else: x["receipt"]["semantic_id"]="attacker:rel:42"
        assert reconcile_discrete(x,c)["status"]=="REJECTED", mutation
    print("CC-RC1.6 MRSC reference self-test: PASS")

if __name__=="__main__":
    self_test()
