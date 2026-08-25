#!/usr/bin/env python3
"""Calibration-only rank gate for Trigger-1 three-state J-Space geometry.

Input is already-extracted label-free class centroids from lexically disjoint
calibration families. This tool never runs a model and must never open holdout.
It can only return ONE_DIMENSIONAL_SUPPORTED, TWO_DIMENSIONAL_REQUIRED, or
UNRESOLVED. No canonical/model/training/HCU/EntityOS credit is minted.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, random
from typing import Any

INPUT_SCHEMA="CLAY_TRIGGER1_SEMANTIC_SIMPLEX_CALIBRATION/v1"
OUTPUT_SCHEMA="CLAY_TRIGGER1_SEMANTIC_SIMPLEX_RANK_DECISION/v1"
CLASSES=("AFFIRMATIVE","NEGATIVE","NEUTRAL")
ONE="ONE_DIMENSIONAL_SUPPORTED"; TWO="TWO_DIMENSIONAL_REQUIRED"; UNRESOLVED="UNRESOLVED"
DECISION_ONE=ONE; DECISION_TWO=TWO; DECISION_UNRESOLVED=UNRESOLVED

def csha(x:Any)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def sha(x:Any)->bool:
    if not isinstance(x,str) or len(x)!=64:return False
    try:int(x,16);return True
    except ValueError:return False
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,s):return [x*s for x in a]
def norm(a):return math.sqrt(max(0.0,dot(a,a)))
def mean(vs):
    out=[0.0]*len(vs[0])
    for v in vs:out=add(out,v)
    return mul(out,1/len(vs))
def unit(v):
    n=norm(v)
    return None if n<=1e-15 else mul(v,1/n)
def cosine(a,b):
    ua,ub=unit(a),unit(b)
    return None if ua is None or ub is None else max(-1.0,min(1.0,dot(ua,ub)))

def geometry(means):
    a,n,u=(means[k] for k in CLASSES)
    center=mul(add(add(a,n),u),1/3)
    centered=[sub(x,center) for x in (a,n,u)]
    h1=sub(a,mul(add(n,u),.5)); u1=unit(h1)
    if u1 is None:return {"bad":True,"h1":h1,"h2":[0.0]*len(h1),"second":None,"eig":[0.0,0.0]}
    raw2=sub(n,u); h2=sub(raw2,mul(u1,dot(raw2,u1))); u2=unit(h2)
    if u2 is None:l1,l2=sum(dot(v,u1)**2 for v in centered),0.0
    else:
        s11=sum(dot(v,u1)**2 for v in centered); s22=sum(dot(v,u2)**2 for v in centered)
        s12=sum(dot(v,u1)*dot(v,u2) for v in centered)
        d=math.sqrt(max(0.0,(s11-s22)**2+4*s12*s12))
        l1,l2=.5*(s11+s22+d),.5*(s11+s22-d)
    total=l1+l2
    return {"bad":False,"h1":h1,"h2":h2,"second":0.0 if total<=1e-15 else max(0.0,l2/total),"eig":[l1,l2]}

def global_means(fams):
    return {k:mean([f[k] for f in fams.values()]) for k in CLASSES}

def coherent_score(fams):
    g=geometry(global_means(fams))
    if g["bad"]:return 0.0
    pc=[];sc=[]
    for f in fams.values():
        z=geometry(f); p=cosine(z["h1"],g["h1"]); s=cosine(z["h2"],g["h2"])
        if p is None or s is None:return 0.0
        pc.append(p);sc.append(s)
    return float(g["second"])*max(0.0,min(pc))*max(0.0,min(sc))

def null_test(fams, observed, max_exact, samples, seed):
    ids=sorted(fams); perms=list(itertools.permutations(CLASSES)); space=6**len(ids)
    def score(indices):
        r={}
        for fid,idx in zip(ids,indices):
            old=fams[fid]; p=perms[idx]
            r[fid]={target:old[source] for target,source in zip(CLASSES,p)}
        return coherent_score(r)
    vals=[]
    if space<=max_exact:
        mode="EXACT"
        vals=[score(x) for x in itertools.product(range(6),repeat=len(ids))]
    else:
        mode="DETERMINISTIC_MONTE_CARLO"; rng=random.Random(int(hashlib.sha256(seed.encode()).hexdigest(),16))
        vals=[score(tuple(rng.randrange(6) for _ in ids)) for _ in range(samples)]
    vals.sort(); ge=sum(v>=observed-1e-15 for v in vals)
    return {"mode":mode,"assignment_space":space,"samples":len(vals),
            "statistic":"SECOND_ENERGY_X_MIN_SIGNED_PRIMARY_ALIGNMENT_X_MIN_SIGNED_SECONDARY_ALIGNMENT",
            "observed":observed,"p_ge_observed":(ge+1)/(len(vals)+1),"p_value_ge_observed":(ge+1)/(len(vals)+1),
            "q95":vals[max(0,math.ceil(.95*len(vals))-1)],"max":vals[-1]}

def parse(c):
    fail=[]; cfg=c.get("config") if isinstance(c.get("config"),dict) else {}
    if c.get("schema")!=INPUT_SCHEMA:fail.append("INPUT_SCHEMA_INVALID")
    if c.get("phase")!="CALIBRATION_ONLY":fail.append("CALIBRATION_ONLY_PHASE_REQUIRED")
    if c.get("fresh_holdout_opened") is not False:fail.append("FRESH_HOLDOUT_MUST_REMAIN_CLOSED")
    if c.get("model_facing_pole_labels_absent") is not True:fail.append("MODEL_FACING_POLE_LABELS_MUST_BE_ABSENT")
    if c.get("lexically_disjoint_families") is not True:fail.append("LEXICALLY_DISJOINT_FAMILIES_REQUIRED")
    if not isinstance(c.get("activation_site"),str) or not c["activation_site"].strip():fail.append("ACTIVATION_SITE_REQUIRED")
    for k in ("checkpoint_sha256","tokenizer_sha256","runtime_build_sha256"):
        if not sha(c.get(k)):fail.append("IDENTITY_SHA256_REQUIRED:"+k)
    keys=("one_dim_max_second_energy_fraction","two_dim_min_second_energy_fraction",
          "min_primary_axis_cosine","min_secondary_axis_cosine","permutation_alpha")
    for k in keys:
        v=cfg.get(k)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)):fail.append("FINITE_CONFIG_REQUIRED:"+k)
    if all(isinstance(cfg.get(k),(int,float)) and not isinstance(cfg.get(k),bool) for k in keys):
        if not 0<=cfg[keys[0]]<cfg[keys[1]]<=.5:fail.append("DIMENSION_THRESHOLDS_INVALID")
        if not 0<=cfg[keys[2]]<=1 or not 0<=cfg[keys[3]]<=1:fail.append("COSINE_THRESHOLDS_INVALID")
        if not 0<cfg[keys[4]]<1:fail.append("PERMUTATION_ALPHA_INVALID")
    for k,minimum in (("min_families",3),("max_exact_permutations",216),("null_samples",100)):
        v=cfg.get(k)
        if not isinstance(v,int) or isinstance(v,bool) or v<minimum:fail.append(k.upper()+"_INVALID")
    rows=c.get("families"); fams={}; dim=None
    if not isinstance(rows,list) or not rows:fail.append("NONEMPTY_FAMILIES_REQUIRED");rows=[]
    for r in rows:
        if not isinstance(r,dict):fail.append("FAMILY_ROW_OBJECT_REQUIRED");continue
        fid=r.get("family_id")
        if not isinstance(fid,str) or not fid.strip():fail.append("FAMILY_ID_REQUIRED");continue
        if fid in fams:fail.append("DUPLICATE_FAMILY_ID:"+fid);continue
        if r.get("label_free_basis") is not True:fail.append("LABEL_FREE_BASIS_REQUIRED:"+fid)
        if not sha(r.get("family_receipt_sha256")):fail.append("FAMILY_RECEIPT_SHA256_REQUIRED:"+fid)
        cc=r.get("class_centroids")
        if not isinstance(cc,dict) or set(cc)!=set(CLASSES):fail.append("EXACT_THREE_CLASSES_REQUIRED:"+fid);continue
        parsed={}
        try:
            for k in CLASSES:
                v=cc[k]
                if not isinstance(v,list) or not v:raise ValueError
                z=[]
                for x in v:
                    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(float(x)):raise ValueError
                    z.append(float(x))
                if dim is None:dim=len(z)
                if len(z)!=dim:raise ValueError
                parsed[k]=z
        except ValueError:fail.append("FINITE_EQUAL_DIMENSION_CENTROIDS_REQUIRED:"+fid);continue
        fams[fid]=parsed
    if isinstance(cfg.get("min_families"),int) and len(fams)<cfg["min_families"]:fail.append("INSUFFICIENT_FAMILIES")
    return fams,cfg,sorted(set(fail))

def adjudicate(c):
    fams,cfg,fail=parse(c)
    base={"schema":OUTPUT_SCHEMA,"input_sha256":csha(c),"decision":UNRESOLVED,
          "canonical_credit_minted":False,"jspace_model_runtime_credit":False,
          "training_credit":False,"whole_hcu_credit":False,"whole_entityos_credit":False,"failures":fail}
    if fail:return base
    g=geometry(global_means(fams))
    if g["bad"]:return {**base,"failures":["PRIMARY_CONTRAST_DEGENERATE"]}
    family=[];pc=[];sc=[]
    for fid in sorted(fams):
        z=geometry(fams[fid]);p=cosine(z["h1"],g["h1"]);s=cosine(z["h2"],g["h2"])
        family.append({"family_id":fid,"second":z["second"],"primary_cosine":p,"secondary_cosine":s})
        if p is not None:pc.append(p)
        if s is not None:sc.append(s)
    loo=[]
    for ex in sorted(fams):
        z=geometry(global_means({k:v for k,v in fams.items() if k!=ex}))
        loo.append({"excluded":ex,"second":z["second"],"primary_cosine":cosine(z["h1"],g["h1"]),
                    "secondary_cosine":cosine(z["h2"],g["h2"])})
    obs=float(g["second"]); score=coherent_score(fams)
    null=null_test(fams,score,int(cfg["max_exact_permutations"]),int(cfg["null_samples"]),csha(c))
    pmin=float(cfg["min_primary_axis_cosine"]);smin=float(cfg["min_secondary_axis_cosine"])
    pstable=len(pc)==len(fams) and min(pc)>=pmin and all(x["primary_cosine"] is not None and x["primary_cosine"]>=pmin for x in loo)
    sstable=len(sc)==len(fams) and min(sc)>=smin and all(x["secondary_cosine"] is not None and x["secondary_cosine"]>=smin for x in loo)
    fs=[float(x["second"]) for x in family if x["second"] is not None]; ls=[float(x["second"]) for x in loo if x["second"] is not None]
    one=pstable and obs<=cfg["one_dim_max_second_energy_fraction"] and max(fs)<=cfg["one_dim_max_second_energy_fraction"] and max(ls)<=cfg["one_dim_max_second_energy_fraction"]
    two=pstable and sstable and obs>=cfg["two_dim_min_second_energy_fraction"] and min(fs)>=cfg["two_dim_min_second_energy_fraction"] and min(ls)>=cfg["two_dim_min_second_energy_fraction"] and null["p_ge_observed"]<=cfg["permutation_alpha"]
    decision=TWO if two else ONE if one else UNRESOLVED
    reasons=[]
    if decision==UNRESOLVED:
        if not pstable:reasons.append("PRIMARY_AXIS_NOT_STABLE")
        if cfg["one_dim_max_second_energy_fraction"]<obs<cfg["two_dim_min_second_energy_fraction"]:reasons.append("SECOND_ENERGY_GRAY_ZONE")
        if obs>=cfg["two_dim_min_second_energy_fraction"] and not sstable:reasons.append("SECOND_AXIS_NOT_STABLE")
        if obs>=cfg["two_dim_min_second_energy_fraction"] and null["p_ge_observed"]>cfg["permutation_alpha"]:reasons.append("RANK2_NOT_SIGNIFICANT_VS_LABEL_PERMUTATION")
        if obs<=cfg["one_dim_max_second_energy_fraction"] and max(fs)>cfg["one_dim_max_second_energy_fraction"]:reasons.append("FAMILY_LEVEL_ONE_DIMENSIONALITY_NOT_STABLE")
        if not reasons:reasons.append("PREREGISTERED_CRITERIA_NOT_MET")
    return {**base,"decision":decision,"failures":[],"unresolved_reasons":reasons,
            "observed":{"family_count":len(fams),"activation_dimension":len(next(iter(next(iter(fams.values())).values()))),
                        "global_second_energy_fraction":obs,"coherent_rank2_score":score,"global_eigenvalues":g["eig"],
                        "primary_axis_stable":pstable,"secondary_axis_stable":sstable},
            "family_diagnostics":family,"leave_one_family_out":loo,"permutation_null":null,
            "interpretation_boundary":"CALIBRATION_ONLY_GEOMETRY_DIAGNOSTIC_NO_RUNTIME_OR_CANONICAL_PROMOTION"}

def main():
    ap=argparse.ArgumentParser();ap.add_argument("candidate");ap.add_argument("--output");a=ap.parse_args()
    with open(a.candidate,encoding="utf-8") as f:c=json.load(f)
    v=adjudicate(c);raw=json.dumps(v,sort_keys=True,indent=2,ensure_ascii=False)+"\n"
    if a.output:open(a.output,"w",encoding="utf-8").write(raw)
    else:print(raw,end="")
    return 2 if v["failures"] else 0
if __name__=="__main__":raise SystemExit(main())
