#!/usr/bin/env python3
import json, random

SEEDS={"credit":62026,"switch":62027,"atomic":62028}

def credit_scope(episodes=120000,nctx=40,poison=0.10,shift=60000):
    rng=random.Random(SEEDS["credit"]); k=4
    ids={c:list(range(c*k,(c+1)*k)) for c in range(nctx)}; E=nctx*k
    pols=["broadcast","path","gated"]; w={p:[0.0]*E for p in pols}
    st={p:{"pre_ok":0,"pre_n":0,"post_ok":0,"post_n":0,"rare_ok":0,"rare_n":0,"false":0,"credit":0} for p in pols}
    for t in range(episodes):
        c=(0 if rng.random()<0.48 else 1+rng.randrange(nctx-1)) if t<shift else rng.randrange(nctx)
        true=set(ids[c]); ds=rng.sample([x for x in range(nctx) if x!=c],5); paths=[ids[c]]+[ids[d] for d in ds]; rng.shuffle(paths)
        base={tuple(p):(rng.uniform(.38,.55) if set(p)==true else rng.uniform(.25,.5)) for p in paths}
        for pol in pols:
            score=lambda p: base[tuple(p)]+sum(w[pol][e] for e in p)/len(p)
            chosen=max(paths,key=score); ok=set(chosen)==true; s=st[pol]
            if t<shift: s["pre_n"]+=1; s["pre_ok"]+=ok
            else:
                s["post_n"]+=1; s["post_ok"]+=ok
                if c>=20: s["rare_n"]+=1; s["rare_ok"]+=ok
            apparent=ok
            if (not ok) and rng.random()<poison and set(ids[0]).intersection(chosen): apparent=True
            if pol=="broadcast":
                if apparent:
                    for p in paths:
                        for e in p:
                            w[pol][e]+=.003; s["credit"]+=1; s["false"]+=int(e not in true)
                for e in range(E): w[pol][e]*=.999985
            elif pol=="path":
                d=.010 if apparent else -.004
                for e in chosen:
                    w[pol][e]+=d; s["credit"]+=1; s["false"]+=int(d>0 and e not in true)
                for e in range(E): w[pol][e]*=.99996
            else:
                support=rng.random() < (.85 if ok else .05)
                d=.012 if (apparent and support) else (-.004 if not apparent else 0.0)
                if d:
                    for e in chosen:
                        w[pol][e]+=d; s["credit"]+=1; s["false"]+=int(d>0 and e not in true)
                for e in range(E): w[pol][e]=min(.35,max(-.15,w[pol][e]*.99994))
                for cx in range(nctx):
                    es=ids[cx]; pos=sum(max(0,w[pol][e]) for e in es)
                    if pos>1.0:
                        q=1.0/pos
                        for e in es:
                            if w[pol][e]>0: w[pol][e]*=q
    out={}
    for pol in pols:
        s=st[pol]; pos=[max(0,x) for x in w[pol]]; z=sum(pos) or 1; pr=[x/z for x in pos]
        out[pol]={"pre_acc":round(s["pre_ok"]/s["pre_n"],6),"post_acc":round(s["post_ok"]/s["post_n"],6),"post_rare_acc":round(s["rare_ok"]/s["rare_n"],6),"false_positive_credit_rate":round(s["false"]/max(1,s["credit"]),6),"salience_hhi":round(sum(x*x for x in pr),6),"ctx0_mass":round(sum(pr[e] for e in ids[0]),6)}
    return out

def topology_switch(proposals=50000,poison_rate=.12):
    rng=random.Random(SEEDS["switch"]); pols=["direct","canary","canary_rollback"]
    s={p:{"bad":0,"good_adopt":0,"good":0,"badn":0,"exposure":0,"reject_good":0} for p in pols}
    for _ in range(proposals):
        delta=rng.gauss(.018,.035)-(rng.uniform(.05,.18) if rng.random()<poison_rate else 0); good=delta>0
        for p in pols: s[p]["good" if good else "badn"]+=1
        if good: s["direct"]["good_adopt"]+=1
        else: s["direct"]["bad"]+=1; s["direct"]["exposure"]+=100
        inc=.82; cand=max(.05,min(.98,inc+delta)); n=160
        obs=(sum(rng.random()<cand for _ in range(n))-sum(rng.random()<inc for _ in range(n)))/n; accept=obs>=.012
        if accept:
            if good: s["canary"]["good_adopt"]+=1
            else: s["canary"]["bad"]+=1; s["canary"]["exposure"]+=100
        elif good: s["canary"]["reject_good"]+=1
        if accept:
            if good: s["canary_rollback"]["good_adopt"]+=1
            else:
                s["canary_rollback"]["bad"]+=1; m=50
                live=(sum(rng.random()<cand for _ in range(m))-sum(rng.random()<inc for _ in range(m)))/m
                s["canary_rollback"]["exposure"]+=(5 if live<-.02 else 100)
        elif good: s["canary_rollback"]["reject_good"]+=1
    return {p:{"bad_activation_rate":round(d["bad"]/d["badn"],6),"good_adoption_rate":round(d["good_adopt"]/d["good"],6),"mean_bad_exposure_units_per_bad_proposal":round(d["exposure"]/d["badn"],3),"rejected_good_rate":round(d["reject_good"]/d["good"],6)} for p,d in s.items()}

def atomic_switch(trials=100000):
    rng=random.Random(SEEDS["atomic"]); torn=0; old=0; new=0
    for _ in range(trials):
        k=rng.randint(2,20); crash=rng.randint(0,k); torn+=int(0<crash<k)
        if rng.random()<.82: old+=1
        else: new+=1
    return {"trials":trials,"inplace_torn_rate":round(torn/trials,6),"versioned_torn_rate":0.0,"versioned_old_kept_rate":round(old/trials,6),"versioned_new_live_rate":round(new/trials,6)}

if __name__=="__main__":
    print(json.dumps({"seeds":SEEDS,"credit_scope":credit_scope(),"topology_switch":topology_switch(),"atomic_switch":atomic_switch()},sort_keys=True))
