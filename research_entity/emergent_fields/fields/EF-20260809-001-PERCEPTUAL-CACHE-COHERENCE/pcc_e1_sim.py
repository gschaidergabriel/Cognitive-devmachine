#!/usr/bin/env python3
"""PCC-E1 synthetic perceptual-cache-coherence experiment.
Synthetic evidence only; no FRANK/Retina hardware claim.
"""
import math, numpy as np

def run(seed, tau=0.70, T=12000):
    rng=np.random.default_rng(seed); d=32; n=20; known_p=0.8; drift_t=int(T*0.4)
    noise=0.10; hard_noise=0.08; hard_mix=0.98
    base=rng.normal(size=(n,d)); base/=np.linalg.norm(base,axis=1,keepdims=True)
    drift=base.copy()
    for c in range(6):
        ort=rng.normal(size=d); ort-=ort.dot(base[c])*base[c]; ort/=np.linalg.norm(ort)
        v=0.55*base[c]+math.sqrt(1-0.55**2)*ort; drift[c]=v/np.linalg.norm(v)
    hard=[]
    for c in range(6):
        ort=rng.normal(size=d); ort-=ort.dot(base[c])*base[c]; ort/=np.linalg.norm(ort)
        v=hard_mix*base[c]+math.sqrt(1-hard_mix**2)*ort; hard.append(v/np.linalg.norm(v))
    hard=np.asarray(hard)
    naive=base.copy(); coherent={(c,0):base[c].copy() for c in range(n)}
    M={k:dict(deep=0,fast=0,false_fast=0) for k in ("naive","coherent")}
    for t in range(T):
        known=rng.random()<known_p
        if known:
            c=int(rng.integers(0,n)); center=drift[c] if (t>=drift_t and c<6) else base[c]
            x=center+noise*rng.normal(size=d); x/=np.linalg.norm(x); epoch=1 if (t>=drift_t and c<6) else 0
        else:
            c=None
            if t>=drift_t and rng.random()<0.7:
                cc=int(rng.integers(0,6)); center=hard[cc]
                x=center+hard_noise*rng.normal(size=d); x/=np.linalg.norm(x); epoch=1
            else:
                center=rng.normal(size=d); center/=np.linalg.norm(center)
                x=center+noise*rng.normal(size=d); x/=np.linalg.norm(x); epoch=1 if t>=drift_t else 0

        sims=naive@x; pred=int(np.argmax(sims)); score=float(sims[pred]); m=M["naive"]
        if score>=tau:
            m["fast"]+=1
            if not (known and pred==c): m["false_fast"]+=1
        else:
            m["deep"]+=1
            if known:
                p=.8*naive[c]+.2*x; naive[c]=p/np.linalg.norm(p)

        cand=[(cc,p) for (cc,e),p in coherent.items() if e==epoch]; m=M["coherent"]
        if cand:
            cs=np.asarray([cc for cc,p in cand]); ps=np.stack([p for cc,p in cand])
            sims=ps@x; j=int(np.argmax(sims)); pred=int(cs[j]); score=float(sims[j])
        else: pred=None; score=-1.0
        if score>=tau:
            m["fast"]+=1
            if not (known and pred==c): m["false_fast"]+=1
        else:
            m["deep"]+=1
            if known:
                key=(c,epoch)
                if key in coherent:
                    p=.8*coherent[key]+.2*x; coherent[key]=p/np.linalg.norm(p)
                else:
                    coherent[key]=x.copy()
    out={}
    for k,m in M.items():
        out[k]=dict(
            false_per_fast=m["false_fast"]/max(1,m["fast"]),
            deep_rate=m["deep"]/T,
            compute_saving=1-(m["deep"]+0.05*m["fast"])/T
        )
    return out

if __name__=="__main__":
    rows=[run(1000+i) for i in range(30)]
    for policy in ("naive","coherent"):
        for metric in ("false_per_fast","deep_rate","compute_saving"):
            a=np.asarray([r[policy][metric] for r in rows])
            print(policy, metric, float(a.mean()), float(a.std()))
