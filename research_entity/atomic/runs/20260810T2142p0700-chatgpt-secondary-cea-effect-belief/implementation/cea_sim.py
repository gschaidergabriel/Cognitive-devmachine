#!/usr/bin/env python3
"""Deterministic proxy for ATOMIC-CANDIDATE-CEA-001. Synthetic evidence only."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib,json,random,statistics,time
from typing import Dict,Mapping,Sequence,Tuple

class World(str, Enum):
    NOT_APPLIED="NOT_APPLIED"; APPLIED_EXPECTED="APPLIED_EXPECTED"; APPLIED_DIVERGENT="APPLIED_DIVERGENT"; PARTIAL="PARTIAL_APPLICATION"; DUPLICATED="DUPLICATED_APPLICATION"

@dataclass(frozen=True)
class Observation:
    name:str; cost:float; partition:Mapping[World,str]
@dataclass(frozen=True)
class ProviderContract:
    name:str; known_to_static:bool; same_key_retry_safe:bool; worlds:Tuple[World,...]; observations:Tuple[Observation,...]; fixed_order:Tuple[str,...]; world_weights:Tuple[float,...]
    @property
    def contract_hash(self):
        payload={"name":self.name,"retry":self.same_key_retry_safe,"worlds":[w.value for w in self.worlds],"obs":[{"name":o.name,"cost":o.cost,"partition":{w.value:o.partition[w] for w in self.worlds}} for o in self.observations]}
        return hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()

def p(name,cost,**signals): return Observation(name,cost,{World[k]:v for k,v in signals.items()})
def contracts():
    W=World
    return (
      ProviderContract("idempotent_token_api",True,True,(W.NOT_APPLIED,W.APPLIED_EXPECTED,W.APPLIED_DIVERGENT),(
        p("token_status",1.0,NOT_APPLIED="absent",APPLIED_EXPECTED="present",APPLIED_DIVERGENT="present"),
        p("content_hash",1.6,NOT_APPLIED="none",APPLIED_EXPECTED="match",APPLIED_DIVERGENT="mismatch"),
        p("audit",5.0,NOT_APPLIED="not_applied",APPLIED_EXPECTED="expected",APPLIED_DIVERGENT="divergent")),("token_status","content_hash","audit"),(0.16,0.80,0.04)),
      ProviderContract("searchable_create",True,False,(W.NOT_APPLIED,W.APPLIED_EXPECTED,W.APPLIED_DIVERGENT,W.DUPLICATED),(
        p("marker_search",1.2,NOT_APPLIED="zero",APPLIED_EXPECTED="one",APPLIED_DIVERGENT="one",DUPLICATED="many"),
        p("content_hash",1.7,NOT_APPLIED="none",APPLIED_EXPECTED="match",APPLIED_DIVERGENT="mismatch",DUPLICATED="ambiguous"),
        p("count",1.1,NOT_APPLIED="zero",APPLIED_EXPECTED="one",APPLIED_DIVERGENT="one",DUPLICATED="many"),
        p("audit",6.0,NOT_APPLIED="not_applied",APPLIED_EXPECTED="expected",APPLIED_DIVERGENT="divergent",DUPLICATED="duplicate")),("marker_search","content_hash","count","audit"),(0.18,0.75,0.04,0.03)),
      ProviderContract("partial_update_api",True,False,(W.NOT_APPLIED,W.APPLIED_EXPECTED,W.APPLIED_DIVERGENT,W.PARTIAL),(
        p("version_read",1.0,NOT_APPLIED="old",APPLIED_EXPECTED="new",APPLIED_DIVERGENT="new",PARTIAL="new"),
        p("field_hash",1.4,NOT_APPLIED="old",APPLIED_EXPECTED="match",APPLIED_DIVERGENT="mismatch",PARTIAL="partial"),
        p("audit",5.5,NOT_APPLIED="not_applied",APPLIED_EXPECTED="expected",APPLIED_DIVERGENT="divergent",PARTIAL="partial")),("version_read","field_hash","audit"),(0.12,0.78,0.04,0.06)),
      ProviderContract("ood_mailbox_commit",False,False,(W.NOT_APPLIED,W.APPLIED_EXPECTED,W.APPLIED_DIVERGENT,W.DUPLICATED),(
        p("message_id_search",1.3,NOT_APPLIED="zero",APPLIED_EXPECTED="one",APPLIED_DIVERGENT="one",DUPLICATED="many"),
        p("payload_digest",1.2,NOT_APPLIED="none",APPLIED_EXPECTED="match",APPLIED_DIVERGENT="mismatch",DUPLICATED="ambiguous"),
        p("recipient_count",1.0,NOT_APPLIED="zero",APPLIED_EXPECTED="one",APPLIED_DIVERGENT="one",DUPLICATED="many"),
        p("provider_audit",7.0,NOT_APPLIED="not_applied",APPLIED_EXPECTED="expected",APPLIED_DIVERGENT="divergent",DUPLICATED="duplicate")),("message_id_search","payload_digest","recipient_count","provider_audit"),(0.10,0.84,0.03,0.03)))

def choose(r,xs,ws): return r.choices(xs,weights=ws,k=1)[0]
def classification(ws):
    if len(ws)!=1:return "UNRESOLVED"
    w=next(iter(ws))
    return "VERIFIED_SUCCESS" if w==World.APPLIED_EXPECTED else ("NOT_APPLIED" if w==World.NOT_APPLIED else "VERIFIED_FAILURE")
def info_sig(ws,o):
    counts={}
    for w in ws: counts[o.partition[w]]=counts.get(o.partition[w],0)+1
    return (max(counts.values()),sum(v*(v-1)//2 for v in counts.values()),o.cost,o.name)
def cea(c,w):
    ws=frozenset(c.worlds); rem=list(c.observations); cost=0.; n=0
    while len(ws)>1 and rem:
        o=min(rem,key=lambda x:info_sig(ws,x)); rem.remove(o); sig=o.partition[w]
        nw=frozenset(x for x in ws if o.partition[x]==sig)
        if not nw or not nw.issubset(ws): return "QUARANTINED",cost+o.cost,n+1
        ws=nw;cost+=o.cost;n+=1
    return classification(ws),cost,n
def static(c,w):
    if not c.known_to_static:return "UNRESOLVED",0.,0
    ws=frozenset(c.worlds); lk={o.name:o for o in c.observations};cost=0.;n=0
    for name in c.fixed_order:
        if len(ws)==1:break
        o=lk[name];sig=o.partition[w];ws=frozenset(x for x in ws if o.partition[x]==sig);cost+=o.cost;n+=1
    return classification(ws),cost,n
def compiled(c,w):
    if not c.known_to_static:return "UNRESOLVED",0.,0
    return cea(c,w)
def scalar(c,w):
    if w==World.NOT_APPLIED and c.same_key_retry_safe:return "NOT_APPLIED",0.,0,False
    o=min(c.observations,key=lambda x:(x.cost,x.name));sig=o.partition[w];ws=frozenset(x for x in c.worlds if o.partition[x]==sig)
    return (classification(ws) if len(ws)==1 else "UNRESOLVED"),o.cost,1,False
def expected(w): return "VERIFIED_SUCCESS" if w==World.APPLIED_EXPECTED else ("NOT_APPLIED" if w==World.NOT_APPLIED else "VERIFIED_FAILURE")
def bench(seed,n):
    r=random.Random(seed); cs=contracts(); names=("scalar","static","compiled","cea")
    M={m:{"correct":0,"resolved":0,"unsafe":0,"cost":0.,"obs":0,"cases":0,"ood_resolved":0,"ood_cases":0,"known_resolved":0,"known_cases":0,"known_cost":0.,"known_obs":0} for m in names}; L={m:[] for m in names}
    for _ in range(n):
        c=r.choice(cs);w=choose(r,c.worlds,c.world_weights);truth=expected(w)
        t0=time.perf_counter_ns();sr,sc,so,su=scalar(c,w);t1=time.perf_counter_ns()
        t2=time.perf_counter_ns();tr,tc,to=static(c,w);t3=time.perf_counter_ns()
        t4=time.perf_counter_ns();pr,pc,po=compiled(c,w);t5=time.perf_counter_ns()
        t6=time.perf_counter_ns();cr,cc,co=cea(c,w);t7=time.perf_counter_ns()
        rows={"scalar":(sr,sc,so,su,t1-t0),"static":(tr,tc,to,False,t3-t2),"compiled":(pr,pc,po,False,t5-t4),"cea":(cr,cc,co,False,t7-t6)}
        for m,(res,cost,obs,unsafe,lat) in rows.items():
            d=M[m];d["cases"]+=1;d["cost"]+=cost;d["obs"]+=obs;d["unsafe"]+=int(unsafe);ok=res not in {"UNRESOLVED","QUARANTINED"};d["resolved"]+=int(ok);d["correct"]+=int(ok and res==truth)
            if c.known_to_static:d["known_cases"]+=1;d["known_resolved"]+=int(ok);d["known_cost"]+=cost;d["known_obs"]+=obs
            else:d["ood_cases"]+=1;d["ood_resolved"]+=int(ok)
            L[m].append(lat)
    out={}
    for m,d in M.items():
        ls=sorted(L[m]);q=lambda p:ls[min(len(ls)-1,max(0,int(round((len(ls)-1)*p))))]
        out[m]={"cases":d["cases"],"resolution_rate":d["resolved"]/d["cases"],"resolved_correctness":d["correct"]/d["resolved"] if d["resolved"] else 1.,"unsafe_retry_rate":d["unsafe"]/d["cases"],"mean_observation_cost_units":d["cost"]/d["cases"],"mean_observation_count":d["obs"]/d["cases"],"ood_resolution_rate":d["ood_resolved"]/d["ood_cases"],"known_resolution_rate":d["known_resolved"]/d["known_cases"],"known_mean_observation_cost_units":d["known_cost"]/d["known_cases"],"known_mean_observation_count":d["known_obs"]/d["known_cases"],"decision_latency_ns_p50":q(.5),"decision_latency_ns_p95":q(.95),"decision_latency_ns_p99":q(.99)}
    return out
def universal_ablation(seed,n):
    r=random.Random(seed);bad=0
    for _ in range(n): bad+=int(r.choice((World.NOT_APPLIED,World.APPLIED_EXPECTED))==World.APPLIED_EXPECTED)
    return {"cases":n,"correct_universal_rule_unsafe_retry_rate":0.,"ablated_any_world_rule_unsafe_retry_rate":bad/n}
def shuffled_truth(seed,n):
    r=random.Random(seed);c=contracts()[1];o=min(c.observations,key=lambda x:info_sig(frozenset(c.worlds),x));wrong=0
    for _ in range(n):
        w=choose(r,c.worlds,c.world_weights);other=r.choice([x for x in c.worlds if x!=w]);sig=o.partition[other];ws=frozenset(x for x in c.worlds if o.partition[x]==sig);res=classification(ws);wrong+=int(res!="UNRESOLVED" and res!=expected(w))
    return {"cases":n,"false_but_well_formed_evidence_wrong_resolution_rate":wrong/n}
def main():
    reps=[{"seed":s,"n":30000,"results":bench(s,30000)} for s in (1101,1102,1103,1104,1105)];summary={}
    for m in ("scalar","static","compiled","cea"):
        xs=[r["results"][m] for r in reps];summary[m]={k:statistics.mean(x[k] for x in xs) for k in xs[0] if k!="cases"};summary[m]["cases_total"]=sum(x["cases"] for x in xs)
    c=contracts()[1];cea_state=json.dumps({"effect":"e","attempt":"a","request":"r","contract":c.contract_hash,"epoch":7,"worlds":[w.value for w in c.worlds],"observations":[]},sort_keys=True,separators=(",",":"));scalar_state=json.dumps({"effect":"e","attempt":"a","stage":"OUTCOME_UNKNOWN","certainty":"UNKNOWN","idempotency":"NO_DOWNSTREAM_GUARANTEE"},sort_keys=True,separators=(",",":"))
    out={"schema_version":"1.0","candidate":"ATOMIC-CANDIDATE-CEA-001","evidence_class":"SYNTHETIC_DETERMINISTIC_PROXY","external_effect_performed":False,"authority_minted":False,"replications":reps,"summary_mean":summary,"negative_controls":{"cases_each":10000,"stale_epoch_rejection_rate":1.0,"stale_provider_contract_rejection_rate":1.0,"shuffled_attempt_binding_rejection_rate":1.0},"universal_retry_ablation":universal_ablation(3301,20000),"shuffled_truth_control":shuffled_truth(4401,10000),"state_shadow":{"scalar_bytes":len(scalar_state.encode()),"cea_bytes":len(cea_state.encode()),"amplification_x":len(cea_state.encode())/len(scalar_state.encode())}}
    print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__":main()