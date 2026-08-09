#!/usr/bin/env python3
"""H-WP-02 source-contract differential probe. Synthetic; not live H1 evidence."""
from __future__ import annotations
import hashlib, json, random

FIRST_BLOB_SHA="1d0c5a5c39a17abe825e757bbfe77b78912f5f39"
SECOND_BLOB_SHA="821f023ea166e45975045b29ff2b120770573c3e"
FIRST_SCHEMA="h1-ledger-0.1"

def j(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)
def h(v): return hashlib.sha256((v if isinstance(v,str) else j(v)).encode()).hexdigest()

def first_root(rows):
    x=[{"domain":r["domain"],"key":r["key"],"value":r["value"],"epistemic_state":r["epistemic_state"]} for r in rows]
    x.sort(key=lambda r:(r["domain"],r["key"]))
    return h({"schema":FIRST_SCHEMA,"state":x})

def first_idem(existing_event_id,incoming_event_id):
    if existing_event_id is None: return "NEW"
    if existing_event_id != incoming_event_id: return "CONFLICT"
    return "IDEMPOTENT_REPLAY"

def canon(v):
    if isinstance(v,dict):
        k=v.get("$kind")
        if k in ("set","ordered"):
            xs=[canon(x) for x in v.get("items",[])]
            if k=="set":
                d={j(x):x for x in xs}; xs=[d[x] for x in sorted(d)]
            return {"$kind":k,"items":xs}
        return {str(k):canon(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(list,tuple)): return [canon(x) for x in v]
    if v is None or isinstance(v,(str,int,bool)): return v
    if isinstance(v,float) and v==v and v not in (float("inf"),float("-inf")): return v
    raise TypeError(type(v).__name__)

def h2(v): return hashlib.sha256(json.dumps(canon(v),ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
def sem_event(t,ops): return h2({"event_type":t,"ops":ops})
def idem2(eid,t,ops,prov,src): return h2({"event_id":eid,"semantic_event_hash":sem_event(t,ops),"provenance_hash":h2(prov),"source_hash":h2(src)})
def state2(epoch,deps,state,chain): return h2({"global_epoch":epoch,"domain_epochs":deps,"state":state,"semantic_chain_hash":chain})

def run(seed=20260809,n_payload=10000,n_history=2000):
    rng=random.Random(seed); prov={"origin_actor":"chatgpt-secondary"}; src={"ref":"H-WP-02"}
    base=[{"op":"SET","domain":"world","key":"door","value":0,"epistemic":"KNOWN","status":"CURRENT"}]
    basefp=idem2("e1","TEST",base,prov,src); false_replay=conflicts=0
    for i in range(1,n_payload+1):
        changed=[{"op":"SET","domain":"world","key":"door","value":i,"epistemic":"KNOWN","status":"CURRENT"}]
        false_replay += first_idem("e1","e1")=="IDEMPOTENT_REPLAY"
        conflicts += idem2("e1","TEST",changed,prov,src)!=basefp
    first_equal=second_diff=0
    for i in range(n_history):
        v={"x":rng.randrange(1000000),"flag":bool(rng.randrange(2))}
        rows=[{"domain":"goal","key":"primary","value":v,"epistemic_state":"KNOWN"},{"domain":"self","key":"name","value":"Frank","epistemic_state":"KNOWN"}]
        first_equal += first_root(rows)==first_root(list(reversed(rows)))
        state=[{"domain":"goal","key":"primary","value":v,"epistemic":"KNOWN","status":"CURRENT","domain_epoch":1,"semantic_hash":h2(v)}]
        second_diff += state2(1,{"goal":1},state,h2("A"+str(i))) != state2(2,{"goal":1},state,h2("B"+str(i)))
    return {"status":"DIVERGENCE_CONFIRMED","evidence_class":"LOCAL_SYNTHETIC_SOURCE_CONTRACT_DIFFERENTIAL","seed":seed,"source_blobs":{"first":FIRST_BLOB_SHA,"second":SECOND_BLOB_SHA},"changed_payload_same_idem":{"cases":n_payload,"first_false_replay":false_replay,"second_conflict":conflicts},"same_materialized_state_different_history":{"cases":n_history,"first_content_root_equal":first_equal,"second_semantic_state_hash_different":second_diff},"adjudication":"NEITHER_AS_IS","proposed_identity_lattice":["StateContentHash","SemanticEventHash","SemanticHistoryHash","VersionedStateRoot","ExecutionChainHash","TraceRootHash"],"h1_release_pass":False,"stage_advance":False}

if __name__=="__main__": print(json.dumps(run(),sort_keys=True,indent=2))
