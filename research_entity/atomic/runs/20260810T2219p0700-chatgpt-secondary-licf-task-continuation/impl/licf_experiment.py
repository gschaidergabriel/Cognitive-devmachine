#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,math,os,platform,random,statistics,sys,time
from collections import Counter,defaultdict

SEEDS=[101,211,307,401,503]; N=40000
CATS=["VALID","STALE_EXEC","STALE_TASK","WRONG_TASK","DUP","STALE_REV","WITNESS_SPLICE",
      "SWITCH_NO_CONSENT","SWITCH_CONSENT","PROACTIVE_BUSY","PROACTIVE_IDLE","COMPLETE","STALE_COMPLETE"]

def H(*x): return hashlib.sha256("\x1f".join(map(str,x)).encode()).hexdigest()
def ctx(r,active=True):
    le=r.randint(1,9999); te=r.randint(1,99); rev=r.randint(1,999); tid=f"task:{r.randint(1,9999)}"
    w=H("consent",le,te,tid); f=H("fiber",le,tid,te,rev,w)
    return {"le":le,"te":te,"rev":rev,"tid":tid if active else None,"w":w,"f":f,"active":active,"seen":"dup"}
def case(r,cat):
    c=ctx(r); o={"k":"MAT","le":c["le"],"te":c["te"],"rev":c["rev"],"tid":c["tid"],
                 "w":c["w"],"f":c["f"],"n":f"n:{r.randint(1,10**9)}","consent":False,"new":None}; ok=True
    if cat=="STALE_EXEC": o["le"]-=1; ok=False
    elif cat=="STALE_TASK": o["te"]-=1; ok=False
    elif cat=="WRONG_TASK": o["tid"]="task:other"; ok=False
    elif cat=="DUP": o["n"]=c["seen"]; ok=False
    elif cat=="STALE_REV": o["rev"]-=1; ok=False
    elif cat=="WITNESS_SPLICE": o["w"]=H("wrong",c["tid"]); ok=False
    elif cat=="SWITCH_NO_CONSENT": o.update(k="SWITCH",new="task:new"); ok=False
    elif cat=="SWITCH_CONSENT": o.update(k="SWITCH",new="task:new",consent=True)
    elif cat=="PROACTIVE_BUSY": o.update(k="PROACTIVE",tid=None,new="goal:new"); ok=False
    elif cat=="PROACTIVE_IDLE":
        c=ctx(r,False); o.update(k="PROACTIVE",le=c["le"],te=c["te"],rev=c["rev"],tid=None,w=c["w"],f=c["f"],new="goal:new")
    elif cat=="COMPLETE": o["k"]="COMPLETE"
    elif cat=="STALE_COMPLETE": o.update(k="COMPLETE",te=c["te"]-1); ok=False
    return c,o,ok

def lease(c,o):
    if o["le"]!=c["le"]: return False
    if o["k"]=="PROACTIVE" and c["active"]: return False
    return True
def epoch(c,o):
    if o["le"]!=c["le"]: return False
    if o["k"]=="PROACTIVE": return not c["active"]
    if not c["active"] or o["tid"]!=c["tid"] or o["te"]!=c["te"]: return False
    return bool(o["consent"] and o["new"]) if o["k"]=="SWITCH" else True
def strong(c,o):
    if not epoch(c,o): return False
    if o["k"]=="PROACTIVE": return True
    return o["rev"]==c["rev"] and o["w"]==c["w"] and o["n"]!=c["seen"]
def licf(c,o):
    if not strong(c,o): return False
    if o["k"]=="PROACTIVE": return True
    if o["f"]!=c["f"]: return False
    if o["k"]=="SWITCH": H("next",c["f"],"switch",o["new"],c["te"]+1,o["n"],o["w"])
    else: H("next",c["f"],o["k"],c["tid"],c["te"],c["rev"]+1,o["n"])
    return True

METHODS={"CURRENT_LEASE_ONLY":lease,"TASK_EPOCH_SIMPLE":epoch,"CONVENTIONAL_STRONG":strong,"LICF_001":licf}
cases=[]
for seed in SEEDS:
    r=random.Random(seed)
    for _ in range(N):
        cat=r.choice(CATS); cases.append((cat,*case(r,cat)))

rows=[]
for name,fn in METHODS.items():
    tp=tn=fp=fnn=0; errs=defaultdict(int); t0=time.perf_counter_ns()
    for cat,c,o,e in cases:
        p=fn(c,o)
        if p!=e: errs[cat]+=1
        if e and p: tp+=1
        elif not e and not p: tn+=1
        elif p: fp+=1
        else: fnn+=1
    dt=time.perf_counter_ns()-t0
    rows.append({"method":name,"n":len(cases),"tp":tp,"tn":tn,"fp":fp,"fn":fnn,
                 "accuracy":(tp+tn)/len(cases),"mean_ns_per_case":dt/len(cases),
                 "error_by_category":dict(sorted(errs.items()))})

sample=random.Random(999).sample(cases,50000); lat={}
for name,fn in METHODS.items():
    xs=[]
    for i in range(0,len(sample),100):
        b=sample[i:i+100]; t=time.perf_counter_ns()
        for _,c,o,_ in b: fn(c,o)
        xs.append((time.perf_counter_ns()-t)/len(b))
    xs.sort()
    q=lambda p: xs[min(len(xs)-1,math.ceil(p*len(xs))-1)]
    lat[name]={"p50_ns_per_call":q(.5),"p95_ns_per_call":q(.95),"p99_ns_per_call":q(.99),"mean_ns_per_call":statistics.mean(xs)}

r=random.Random(7); c,o,_=case(r,"VALID")
meta={
 "CURRENT_LEASE_ONLY":{"le":o["le"]},
 "TASK_EPOCH_SIMPLE":{"le":o["le"],"tid":o["tid"],"te":o["te"]},
 "CONVENTIONAL_STRONG":{"le":o["le"],"tid":o["tid"],"te":o["te"],"rev":o["rev"],"w":o["w"],"n":o["n"]},
 "LICF_001":{"le":o["le"],"tid":o["tid"],"te":o["te"],"rev":o["rev"],"w":o["w"],"f":o["f"],"n":o["n"]}}
wire={k:len(json.dumps(v,separators=(",",":")).encode()) for k,v in meta.items()}

crash={k:0 for k in METHODS}
for seed in range(1000):
    r=random.Random(10000+seed); old=ctx(r); nt=f"task:new:{seed}"; te=old["te"]+1; w=H("switch",old["w"],nt,te)
    new=dict(old,tid=nt,te=te,rev=1,w=w,f=H("fiber",old["le"],nt,te,1,w))
    stale={"k":"MAT","le":old["le"],"te":old["te"],"rev":old["rev"],"tid":old["tid"],"w":old["w"],"f":old["f"],"n":f"s:{seed}","consent":False,"new":None}
    for name,fn in METHODS.items(): crash[name]+=int(not fn(new,stale))

out={"schema_version":"1.0","experiment":"LICF-001 same-lease task-continuity discriminator",
     "seeds":SEEDS,"n_cases":len(cases),"categories":dict(Counter(x[0] for x in cases)),
     "classification":rows,"latency":lat,"wire_bytes":wire,
     "crash_replay":{"histories":1000,"stale_task_rejections":crash},
     "environment":{"python":sys.version.split()[0],"platform":platform.platform(),"machine":platform.machine()}}
print(json.dumps(out,indent=2,sort_keys=True))
