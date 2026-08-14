#!/usr/bin/env python3
"""TRSE-001 local synthetic discriminator. No Frank/runtime/effect mutation."""
from __future__ import annotations
import json, os, platform, statistics, time
import numpy as np
SEED=20260811; N_PER_CLASS=6000; PROBES=16; NOISE_LEVELS=[.005,.01,.02,.03,.05,.08]

def rho(M): return float(np.max(np.abs(np.linalg.eigvals(M))))
def compose(seq):
    M=np.eye(seq[0].shape[0])
    for A in seq: M=A@M
    return M
def q2(rng):
    t=rng.uniform(0,2*np.pi); c,s=np.cos(t),np.sin(t)
    return np.array([[c,-s],[s,c]])
def stable_sequence(rng):
    e=rng.uniform(1.05,1.35); sh=rng.uniform(-1.5,1.5); c=rng.uniform(.30,.55); sh2=rng.uniform(-.8,.8)
    mats=[np.array([[e,sh],[0,.75]]),np.array([[c,0],[0,.55]]),np.array([[.95,sh2],[0,.80]]),np.array([[.85,0],[0,.75]])]
    Q=q2(rng); return [Q@A@Q.T for A in mats]
def unstable_sequence(rng):
    while True:
        s=rng.uniform(.60,.72); k=rng.uniform(1,1.5); a3=rng.uniform(.86,.94); a4=rng.uniform(.86,.94)
        mats=[s*np.array([[1,k],[0,1]]),s*np.array([[1,0],[k,1]]),a3*np.eye(2),a4*np.eye(2)]
        M=compose(mats)
        if 1.02<rho(M)<1.30 and max(rho(A) for A in mats)<1:
            Q=q2(rng); return [Q@A@Q.T for A in mats]
def fit_map(F,probes,sigma,rng):
    d=F.shape[0]; X=rng.normal(size=(d,probes)); X/=np.linalg.norm(X,axis=0,keepdims=True)+1e-12
    Y=F@X+rng.normal(scale=sigma,size=(d,probes)); return Y@X.T@np.linalg.inv(X@X.T)
def classify_exact(seq):
    M=compose(seq); local=[rho(A) for A in seq]; F=np.zeros((3,3)); F[0,0]=1; F[1:,1:]=M
    return {"max_local_rho":max(local),"product_local_rho":float(np.prod(local)),"full_return_rho":rho(F),"transverse_return_rho":rho(M)}
def lesion_control():
    rows=[]
    for k in np.linspace(1,1.5,51):
        s=.66; A=s*np.array([[1,k],[0,1]]); B=s*np.array([[1,0],[k,1]]); C=.9*np.eye(2); D=.9*np.eye(2)
        rows.append((rho(compose([A,B,C,D])),rho(compose([s*np.eye(2),B,C,D])),rho(compose([A,s*np.eye(2),C,D]))))
    return {"n":len(rows),"both_couplings_median_rho":statistics.median(x[0] for x in rows),"lesion_first_coupling_median_rho":statistics.median(x[1] for x in rows),"lesion_second_coupling_median_rho":statistics.median(x[2] for x in rows),"both_unstable_fraction":sum(x[0]>1 for x in rows)/len(rows),"first_lesion_stable_fraction":sum(x[1]<1 for x in rows)/len(rows),"second_lesion_stable_fraction":sum(x[2]<1 for x in rows)/len(rows)}
def qs(xs):
    a=np.asarray(xs); return {"p05":float(np.quantile(a,.05)),"p50":float(np.quantile(a,.5)),"p95":float(np.quantile(a,.95))}

def main():
    rng=np.random.default_rng(SEED); systems=[]
    for label in (0,1):
        for _ in range(N_PER_CLASS):
            seq=stable_sequence(rng) if label==0 else unstable_sequence(rng); systems.append((label,seq,classify_exact(seq)))
    names=["SCALAR_HISTORY_ONLY","MAX_LOCAL_RHO","PRODUCT_LOCAL_RHO","FULL_RETURN_RHO","TRANSVERSE_RETURN_RHO"]; ok={k:0 for k in names}
    dist={"stable_transverse_rho":[],"unstable_transverse_rho":[],"stable_max_local_rho":[],"unstable_max_local_rho":[]}
    for label,seq,m in systems:
        preds=[0,0 if m["max_local_rho"]<=1 else 1,0 if m["product_local_rho"]<=1 else 1,0 if m["full_return_rho"]<=1+1e-9 else 1,0 if m["transverse_return_rho"]<1 else 1]
        for k,p in zip(names,preds): ok[k]+=int(p==label)
        pref="stable" if label==0 else "unstable"; dist[pref+"_transverse_rho"].append(m["transverse_return_rho"]); dist[pref+"_max_local_rho"].append(m["max_local_rho"])
    noisy={}; n=len(systems)
    for sigma in NOISE_LEVELS:
        rr=np.random.default_rng(SEED+int(sigma*1e6)); fok=tok=ffp=ffn=tfp=tfn=0; t0=time.perf_counter_ns()
        for label,seq,m in systems:
            M=compose(seq); F=np.zeros((3,3)); F[0,0]=1; F[1:,1:]=M
            pf=0 if rho(fit_map(F,PROBES,sigma,rr))<=1.02 else 1; pt=0 if rho(fit_map(M,PROBES,sigma,rr))<=1 else 1
            fok+=pf==label; tok+=pt==label; ffp+=(label==0 and pf==1); ffn+=(label==1 and pf==0); tfp+=(label==0 and pt==1); tfn+=(label==1 and pt==0)
        noisy[str(sigma)]={"full_return_accuracy":fok/n,"transverse_phase_aligned_accuracy":tok/n,"full_return_false_positive":ffp,"full_return_false_negative":ffn,"transverse_false_positive":tfp,"transverse_false_negative":tfn,"elapsed_s":(time.perf_counter_ns()-t0)/1e9}
    out={"schema_version":"1.0","candidate":"TRSE-001 Transverse Recurrence Stability Envelope","evidence_class":"LOCAL_SYNTHETIC_REFERENCE_MODEL_ONLY","seed":SEED,"systems_per_class":N_PER_CLASS,"total_systems":n,"phase_steps_per_return":4,"transverse_dimensions":2,"neutral_phase_dimensions":1,"probes_per_noisy_fit":PROBES,"exact_classifier_accuracy":{k:v/n for k,v in ok.items()},"distribution":{k:qs(v) for k,v in dist.items()},"noisy_return_estimation":noisy,"coupling_lesion_control":lesion_control(),"meaning":{"stable_counterexample":"a locally expansive phase can belong to a stable full recurrence","unstable_counterexample":"all local phase spectral radii can be <1 while non-normal cross-phase coupling makes the full recurrence unstable","phase_law":"productive recurrence may carry a neutral tangent/phase mode; transverse perturbation decay is the relevant orbital-stability quantity","nonclaim":"does not establish real Frank loop stability, optimal thresholds, target-VPS cost, or unique architecture benefit"},"environment":{"python":platform.python_version(),"numpy":np.__version__,"os":platform.platform(),"machine":platform.machine(),"processor":platform.processor() or "UNKNOWN","cpu_count":os.cpu_count(),"network":"NOT_USED","gpu":"NOT_USED","target_vps":False}}
    print(json.dumps(out,sort_keys=True,indent=2))
if __name__=="__main__": main()
