import json, math
import numpy as np

OUT={"schema_version":"1.0","class":"synthetic_analytic_proxy","seed_family":"G7-20260808"}

def rho(M):
    return float(max(abs(np.linalg.eigvals(M))))

# EXP-G7-MULTITYPE-RDELTA-001
rng=np.random.default_rng(7082026)
regimes={
    "safe_uniform":np.array([[0.4,0.4],[0.4,0.4]]),
    "hidden_A":np.array([[1.2,0.0],[0.0,0.4]]),
    "hidden_B":np.array([[0.4,0.0],[0.0,1.2]]),
    "cross_damped":np.array([[0.0,1.2],[0.4,0.0]]),
    "nearcritical":np.array([[0.9,0.1],[0.1,0.5]])}
def sim_multi(M,n=5000,cap=5000):
    sizes=[]
    for _ in range(n):
        q=[int(rng.integers(0,2))]; total=1
        while q and total<cap:
            t=q.pop(); kids=[]
            for j in range(2):
                c=int(rng.poisson(M[t,j])); kids.extend([j]*c)
            total+=len(kids); q.extend(kids)
        sizes.append(total)
    return np.array(sizes)
rows=[]
for name,M in regimes.items():
    s=sim_multi(M)
    rows.append({"regime":name,"scalar_avg_row_sum":float(M.sum(axis=1).mean()),"spectral_radius":rho(M),"mean_cascade":float(s.mean()),"p_ge_100":float(np.mean(s>=100)),"p_ge_1000":float(np.mean(s>=1000))})
rng2=np.random.default_rng(12345); broad=[]
for _ in range(80):
    M=rng2.uniform(0,1.4,(2,2)); target=rng2.uniform(.6,1.05); M*=target/M.sum(axis=1).mean(); sizes=[]
    for __ in range(800):
        q=[int(rng2.integers(0,2))]; total=1
        while q and total<1500:
            t=q.pop(); kids=[]
            for j in range(2):
                c=int(rng2.poisson(M[t,j])); kids.extend([j]*c)
            total+=len(kids); q.extend(kids)
        sizes.append(total)
    broad.append((M.sum(axis=1).mean(),rho(M),np.mean(np.array(sizes)>=100)))
a=np.array(broad)
OUT["EXP-G7-MULTITYPE-RDELTA-001"]={"regimes":rows,"tail_risk_corr_scalar":float(np.corrcoef(a[:,0],a[:,2])[0,1]),"tail_risk_corr_spectral_radius":float(np.corrcoef(a[:,1],a[:,2])[0,1])}

# EXP-G7-HIERARCHICAL-GOV-002
regime_targets=np.array([[.85,.75,.35,.40,.70,.30],[.35,.30,.75,.30,.20,.65],[.55,.45,.25,.80,.55,.45],[.25,.20,.50,.35,.15,.85]])
weights=np.array([1.3,1.1,.9,1.0,1.2,.8]); therm_w=np.array([1.0,.8,.15,.1,1.1,.1])
def run_ctrl(kind,seed,T=1200):
    r=np.random.default_rng(seed); regime=0; remain=0; x=np.ones(6)*.45; base=x.copy(); theta=.5; total=0.; viol=0; sw=0; prev=x.copy(); last=regime_targets[0]
    for _ in range(T):
        if remain<=0: regime=int(r.integers(0,4)); remain=int(r.integers(30,91))
        remain-=1; target=np.clip(regime_targets[regime]+r.normal(0,.04,6),.05,.95); obs=last+r.normal(0,.03,6)
        if kind=="scalar":
            m=float(np.mean(obs)); level=.88*np.mean(x)+.12*m; x=np.ones(6)*level
            if theta>1.45: x[[0,1,4]]*=.72
        elif kind=="flat_vector":
            x=.84*x+.16*obs
            if theta>1.45: x*=.82
        else:
            delta=np.linalg.norm(obs-base); alpha=.10 if delta<.45 else .38; base=(1-alpha)*base+alpha*obs; x=base.copy()
            fixed=np.dot(therm_w[[2,3,5]],x[[2,3,5]]); variable=np.dot(therm_w[[0,1,4]],x[[0,1,4]])
            max_heat=max(0.,(1.48-.92*theta)/.115); allowed=max(0.,max_heat-fixed)
            if variable>allowed and variable>0: x[[0,1,4]]*=allowed/variable
            x[[2,3,5]]=np.maximum(x[[2,3,5]],.18)
        x=np.clip(x,.03,1.0); theta=.92*theta+.115*np.dot(therm_w,x)+r.normal(0,.015); theta=max(theta,0)
        total+=np.sum(weights*(x-target)**2)+12*max(0,theta-1.55)**2+.04*np.sum(np.abs(x-prev)); viol+=theta>1.55; sw+=np.sum(np.abs(x-prev)>.08); prev=x.copy(); last=target
    return total/T,viol/T,sw/T
ctrl={}
for k in ["scalar","flat_vector","hierarchical"]:
    v=np.array([run_ctrl(k,1000+s) for s in range(80)]); ctrl[k]={"mean_loss":float(v[:,0].mean()),"sd_loss":float(v[:,0].std()),"thermal_violation_rate":float(v[:,1].mean()),"switch_events_per_step":float(v[:,2].mean())}
ctrl["hierarchical_loss_improvement_vs_flat"]=float(1-ctrl["hierarchical"]["mean_loss"]/ctrl["flat_vector"]["mean_loss"])
OUT["EXP-G7-HIERARCHICAL-GOV-002"]=ctrl

# EXP-G7-PAIRWISE-CLOSURE-003
r=np.random.default_rng(707); ops=["read","note","reserve","release","grant","revoke","use_cap","write_live"]; p=np.array([.25,.18,.13,.08,.09,.07,.10,.10]); risk=set()
def add(a,b): risk.add((ops.index(a),ops.index(b)))
for a,b in [("reserve","reserve"),("grant","revoke"),("revoke","grant"),("revoke","use_cap"),("write_live","revoke"),("grant","use_cap"),("reserve","release")]: add(a,b)
risky={i for pair in risk for i in pair}; N=300000; pairs=np.column_stack([r.choice(len(ops),N,p=p),r.choice(len(ops),N,p=p)])
strict=np.ones(N,bool); g6=np.array([(a in risky) or (b in risky) for a,b in pairs]); g7=np.array([(a,b) in risk for a,b in pairs])
OUT["EXP-G7-PAIRWISE-CLOSURE-003"]={"coordination_rate_strict":float(strict.mean()),"coordination_rate_g6_class":float(g6.mean()),"coordination_rate_g7_pair_sensitive":float(g7.mean()),"constructed_dependency_misses":{"strict":0,"g6_class":0,"g7_pair_sensitive":0}}

# EXP-G7-RESOLUTION-MEMORY-004
r=np.random.default_rng(404); n=100; grp=np.repeat(np.arange(10),10); T=20000; cg=0; queries=[]
for _ in range(T):
    if r.random()<.08: cg=int(r.integers(10))
    q=int(r.choice(np.where(grp==cg)[0])) if r.random()<.82 else int(r.integers(n)); queries.append(q)
def mem(mode,seed):
    rr=np.random.default_rng(seed); counts=np.ones(n)*.1; full=set(range(20)); acc=[]; lat=[]; recon=[]
    for t,q in enumerate(queries):
        if t%25==0: full=set(np.argsort(counts)[-(20 if mode=="flat" else 15):])
        if q in full: acc.append(1.); lat.append(1.); recon.append(0)
        elif mode=="flat": acc.append(float(rr.random()<.78)); lat.append(5.); recon.append(1)
        else: acc.append(float(rr.random()<.97)); lat.append(2.7); recon.append(1)
        counts*=.985; counts[q]+=1
    return {"accuracy":float(np.mean(acc)),"mean_latency":float(np.mean(lat)),"reconstruction_rate":float(np.mean(recon)),"memory_units":20}
OUT["EXP-G7-RESOLUTION-MEMORY-004"]={"flat":mem("flat",405),"hierarchical_summary_zoom":mem("hier",405)}

# EXP-G7-RECURRENCE-MEMORY-005
r=np.random.default_rng(505); n=200; T=1200; K=40; periods=r.integers(12,55,n); phases=r.uniform(0,2*np.pi,n); base=r.uniform(.02,.15,n); amp=r.uniform(.5,1.,n); h=np.zeros((T,n))
for t in range(T):
    cyc=(np.sin(2*np.pi*t/periods+phases)+1)/2; h[t]=np.clip(base+amp*(cyc**5)+r.normal(0,.03,n),0,2)
est=[]
for i in range(n):
    x=h[:400,i]-h[:400,i].mean(); cs=[]
    for lag in range(10,61):
        a=x[:-lag]; b=x[lag:]; cs.append(np.dot(a,b)/(np.linalg.norm(a)*np.linalg.norm(b)+1e-9))
    est.append(10+int(np.argmax(cs)))
est=np.array(est); rr=np.random.default_rng(506); hc=hr=ho=tot=0
for t in range(450,T-5):
    cur=h[t]; pred=np.array([.25*cur[i]+.75*h[t+4-est[i],i] for i in range(n)]); fut=h[t+4]; probs=np.maximum(fut,1e-6)**2; probs/=probs.sum(); q=int(rr.choice(n,p=probs))
    hc+=q in set(np.argpartition(cur,-K)[-K:]); hr+=q in set(np.argpartition(pred,-K)[-K:]); ho+=q in set(np.argpartition(fut,-K)[-K:]); tot+=1
OUT["EXP-G7-RECURRENCE-MEMORY-005"]={"period_exact_recovery_rate":float(np.mean(est==periods)),"median_period_abs_error":float(np.median(np.abs(est-periods))),"future_query_hit_current_salience":hc/tot,"future_query_hit_recurrence_model":hr/tot,"future_query_hit_oracle":ho/tot}

# EXP-G7-DEPENDENCY-GAMMA-006
r=np.random.default_rng(606); S=5000; R=120; dep=50; steps=4000; changes=10; deps=[set(r.choice(S,dep,False).tolist()) for _ in range(R)]; active=r.random(S)<.55; cdep=[{x for x in d if active[x]} for d in deps]; stale=[set(c) for c in cdep]; full_work=0.; dep_work=0.; rebuild=0; stale_bad=0; dep_bad=0; proposals=0
for _ in range(steps):
    changed=set(r.choice(S,changes,False).tolist())
    for x in changed: active[x]=~active[x]
    full_work+=R*dep
    for j,d in enumerate(deps):
        if d & changed: cdep[j]={x for x in d if active[x]}; dep_work+=dep; rebuild+=1
    j=int(r.integers(R))
    if stale[j]: x=int(r.choice(list(stale[j]))); stale_bad+=not active[x]; proposals+=1
    if cdep[j]: x=int(r.choice(list(cdep[j]))); dep_bad+=not active[x]
avg_memberships=R*dep/S; dep_total=dep_work+steps*changes*avg_memberships
OUT["EXP-G7-DEPENDENCY-GAMMA-006"]={"dependency_rebuild_fraction":rebuild/(steps*R),"stale_invalid_rate":stale_bad/proposals,"dependency_scoped_invalid_rate":dep_bad/max(proposals,1),"full_rebuild_work":full_work,"dependency_scoped_work":dep_total,"work_reduction_factor":full_work/dep_total}

# EXP-G7-WORKSPACE-VECTOR-007
def auc(y,s):
    order=np.argsort(s); ranks=np.empty_like(order,dtype=float); ranks[order]=np.arange(1,len(s)+1); pos=y.astype(bool); np_=pos.sum(); nn=len(y)-np_; return float((ranks[pos].sum()-np_*(np_+1)/2)/(np_*nn))
r=np.random.default_rng(7078); N=8000; y=r.random(N)<.45; common=r.normal(0,1,N)
ign=np.clip(.5+.20*common+.10*y+r.normal(0,.22,N),0,1); report=np.clip(.5+.20*common+.14*y+r.normal(0,.20,N),0,1); receipt=np.clip(.38+.10*common+.27*y+r.normal(0,.20,N),0,1); lesion=np.clip(.20+.07*common+.34*y+r.normal(0,.22,N),0,1); rescue=np.clip(.18+.04*common+.35*y+r.normal(0,.22,N),0,1); vec=.05*ign+.08*report+.22*receipt+.30*lesion+.35*rescue
OUT["EXP-G7-WORKSPACE-VECTOR-007"]={"auc_ignition_only":auc(y,ign),"auc_nonintervention_mean":auc(y,(ign+report+receipt)/3),"auc_intervention_weighted_vector":auc(y,vec),"note":"constructed causal-mechanism label; measurement-design sanity check only"}

# EXP-G7-MATERIALIZATION-008
r=np.random.default_rng(808); F=80; T=5000; bq=r.lognormal(-2.4,1.0,F); bu=r.lognormal(-3.0,.9,F); hot=r.integers(0,4,F); qfull=20.; qmat=1.; ucost=18.; scost=.12; bcost=20.
Q=[]; U=[]
for t in range(T):
    reg=(t//250)%4; qr=bq*np.where(hot==reg,4.,.7); ur=bu*np.where(hot==((reg+1)%4),3.,.8); Q.append(r.poisson(qr)); U.append(r.poisson(ur))
Q=np.array(Q); U=np.array(U)
def mat_policy(policy):
    mat=np.zeros(F,bool); qhat=np.ones(F)*.05; uhat=np.ones(F)*.03; total=0.; builds=0
    for t in range(T):
        if policy=="never": desired=np.zeros(F,bool)
        elif policy=="always": desired=np.ones(F,bool)
        else:
            benefit=qhat*(qfull-qmat); burden=uhat*ucost+scost; desired=np.where(mat,benefit>.85*burden,benefit>1.10*burden)
        new=desired & ~mat; total+=new.sum()*bcost; builds+=int(new.sum()); mat=desired
        total+=np.sum(Q[t]*np.where(mat,qmat,qfull))+np.sum(U[t]*mat*ucost)+mat.sum()*scost; qhat=.94*qhat+.06*Q[t]; uhat=.94*uhat+.06*U[t]
    return {"total_cost":float(total),"builds":builds}
mr={k:mat_policy(k) for k in ["never","always","adaptive"]}; mr["adaptive_saving_vs_never"]=1-mr["adaptive"]["total_cost"]/mr["never"]["total_cost"]; mr["adaptive_saving_vs_always"]=1-mr["adaptive"]["total_cost"]/mr["always"]["total_cost"]
OUT["EXP-G7-MATERIALIZATION-008"]=mr

# EXP-G7-EDGE-CONTEXTUAL-009
r=np.random.default_rng(909); back=["CPU","GPU","NPU"]; Utab=np.array([[[.72,.95,.88],[.62,.90,.92],[.70,.68,.80],[.58,.61,.82]],[[.76,.85,.60],[.70,.78,.58],[.74,.55,.52],[.68,.50,.50]],[[.70,.62,.20],[.64,.57,.18],[.69,.45,.15],[.62,.40,.14]],[[.70,.78,1.00],[.62,.72,.96],[.68,.54,.91],[.58,.50,.88]]]); static=Utab.mean((0,1)); sb=int(np.argmax(static)); counts=np.zeros((4,4,3)); means=np.zeros((4,4,3)); rewards=[]; oracles=[]
for t in range(30000):
    d=int(r.integers(4)); rg=int(r.integers(4)); eps=max(.03,.3*(1-t/30000)); zero=np.where(counts[d,rg]==0)[0]
    if len(zero): b=int(r.choice(zero))
    elif r.random()<eps: b=int(r.integers(3))
    else: b=int(np.argmax(means[d,rg]))
    rew=float(np.clip(r.normal(Utab[d,rg,b],.05),0,1.2)); counts[d,rg,b]+=1; means[d,rg,b]+=(rew-means[d,rg,b])/counts[d,rg,b]; rewards.append(rew); oracles.append(Utab[d,rg].max())
OUT["EXP-G7-EDGE-CONTEXTUAL-009"]={"best_universal_backend":back[sb],"best_universal_mean_utility":float(static[sb]),"context_oracle_mean_utility":float(Utab.max(2).mean()),"learned_last5000_mean_utility":float(np.mean(rewards[-5000:])),"oracle_last5000_mean_utility":float(np.mean(oracles[-5000:]))}

print(json.dumps(OUT,indent=2,sort_keys=True))
