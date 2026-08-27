#!/usr/bin/env python3
"""G8 deterministic synthetic/analytic falsification harness.

All outputs are proxies/sanity checks. They are not live FRANK measurements.
"""
import json
import numpy as np
from numpy.linalg import eigvals, norm

SEED = 8082026


def max_transient(A, horizon=60):
    M = np.eye(A.shape[0]); best = 1.0; peak = 0
    for t in range(1, horizon + 1):
        M = A @ M
        g = norm(M, 2)
        if g > best: best, peak = g, t
    return float(best), peak


def exp_nonnormal():
    rows = []
    for k in [0, .5, 1, 2, 4, 8]:
        A = np.array([[.88, k], [0, .88]])
        gain, peak = max_transient(A)
        rows.append({"coupling": k, "rho": float(max(abs(eigvals(A)))), "max_transient_gain": gain, "time_of_peak": peak})
    return {"rows": rows}


def sim_governor(policy, seed, T=5000):
    r = np.random.default_rng(seed); modes = np.array([.3, .6, .9]); mode = 1; last_switch = -999
    loss = switches = violations = 0; demand = .55; hist = [demand] * 6
    for t in range(T):
        if t in (1300, 2600, 3900): demand = float(np.clip(demand + r.normal(0, .2), .15, .95))
        demand = float(np.clip(.97*demand + .03*(.55 + .25*np.sin(t/180)) + r.normal(0, .018), .05, .98))
        hist.append(demand); obs = hist[-4] + r.normal(0, .025); err = obs - modes[mode]
        if policy == "threshold":
            if err > .05 and mode < 2: mode += 1; switches += 1
            elif err < -.05 and mode > 0: mode -= 1; switches += 1
        elif policy == "hysteresis":
            if t-last_switch >= 12:
                if err > .10 and mode < 2: mode += 1; switches += 1; last_switch = t
                elif err < -.10 and mode > 0: mode -= 1; switches += 1; last_switch = t
        else:
            if obs > .86 and mode < 2: switches += int(mode != 2); mode = 2; last_switch = t
            elif t-last_switch >= 10:
                if err > .12 and mode < 2: mode += 1; switches += 1; last_switch = t
                elif err < -.12 and mode > 0: mode -= 1; switches += 1; last_switch = t
        cur = modes[mode]; under = max(0, demand-cur); over = max(0, cur-demand)
        loss += 4*under**2 + .6*over**2; violations += cur + .12 < demand
    return loss/T, switches/T, violations/T


def exp_governor():
    out = {}
    for p in ["threshold", "hysteresis", "slowfast"]:
        v = [sim_governor(p, SEED+i) for i in range(40)]
        out[p] = {"mean_loss": float(np.mean([x[0] for x in v])), "switch_rate": float(np.mean([x[1] for x in v])), "underallocation_violation_rate": float(np.mean([x[2] for x in v]))}
    return out


def dep_policy(seed, N, coverage):
    r = np.random.default_rng(seed); s = {p:{"coord":0,"unsafe":0} for p in ["global","narrow","coverage_aware"]}
    for _ in range(N):
        a = set(r.choice(200, size=r.integers(1,4), replace=False).tolist()); b = set(r.choice(200, size=r.integers(1,4), replace=False).tolist()); true = bool(a & b)
        ao = {x for x in a if r.random() < coverage}; bo = {x for x in b if r.random() < coverage}; observed = bool(ao & bo)
        s["global"]["coord"] += 1
        if observed: s["narrow"]["coord"] += 1
        elif true: s["narrow"]["unsafe"] += 1
        complete = len(ao)==len(a) and len(bo)==len(b)
        if observed or not complete: s["coverage_aware"]["coord"] += 1
        elif true: s["coverage_aware"]["unsafe"] += 1
    return {p:{"coordination_rate":v["coord"]/N,"unsafe_rate":v["unsafe"]/N} for p,v in s.items()}


def exp_coverage():
    out = {}
    for c in [.7,.85,.95]:
        v = [dep_policy(SEED+i, 30000, c) for i in range(8)]
        out[str(c)] = {p:{k:float(np.mean([x[p][k] for x in v])) for k in ["coordination_rate","unsafe_rate"]} for p in ["global","narrow","coverage_aware"]}
    return out


def freshness_sim(policy, seed, T=100000):
    r=np.random.default_rng(seed); x=sent=0.; last=0; sends=queries=0; loss=0.; pending=False
    for t in range(T):
        pchange=.025 if (t//10000)%2==0 else .12
        if r.random()<pchange: x += r.normal(); pending=True
        query=r.random()<.06
        if policy=="periodic" and t-last>=20: sent=x; last=t; sends+=1; pending=False
        elif policy=="dirty_immediate" and pending: sent=x; last=t; sends+=1; pending=False
        elif policy=="coalesced_query_voi":
            dev=abs(x-sent)
            if (query and dev>.25) or dev>2.2 or (pending and t-last>=60): sent=x; last=t; sends+=1; pending=False
        if query: queries+=1; loss += min((x-sent)**2,25)
    return {"mean_query_error": loss/max(queries,1), "send_rate": sends/T}


def exp_freshness():
    out={}
    for p in ["periodic","dirty_immediate","coalesced_query_voi"]:
        v=[freshness_sim(p,SEED+i) for i in range(30)]; out[p]={k:float(np.mean([x[k] for x in v])) for k in v[0]}
    return out


def tcc(seed,N=150000,hidden=.03):
    r=np.random.default_rng(seed); s={p:{"accepted":0,"unsafe":0,"reject":0} for p in ["global_root","scoped","coverage_escalate"]}
    for _ in range(N):
        root_changed=r.random()<.65; conflict=root_changed and r.random()<.035; dep_known=not(conflict and r.random()<hidden); scoped=conflict and dep_known
        if root_changed: s["global_root"]["reject"]+=1
        else: s["global_root"]["accepted"]+=1
        if scoped: s["scoped"]["reject"]+=1
        else: s["scoped"]["accepted"]+=1; s["scoped"]["unsafe"]+=int(conflict)
        incomplete=conflict and not dep_known; flagged=(incomplete and r.random()<.985) or ((not incomplete) and r.random()<.03)
        if scoped or flagged: s["coverage_escalate"]["reject"]+=1
        else: s["coverage_escalate"]["accepted"]+=1; s["coverage_escalate"]["unsafe"]+=int(conflict)
    return {p:{k:v/N for k,v in x.items()} for p,x in s.items()}


def exp_tcc():
    v=[tcc(SEED+i) for i in range(20)]; return {p:{k:float(np.mean([x[p][k] for x in v])) for k in v[0][p]} for p in v[0]}


def drift(policy, seed, T=1000):
    r=np.random.default_rng(seed); exact=np.zeros(16); summary=np.zeros(16); errs=[]
    for t in range(T):
        exact=.995*exact+r.normal(0,.03,16); summary=.995*summary+r.normal(0,.03,16)+r.normal(0,.006,16)
        if policy=="periodic_rebase" and t%50==0: summary=exact+r.normal(0,.002,16)
        elif policy=="error_triggered_rebase" and np.linalg.norm(summary-exact)+r.normal(0,.01)>.22: summary=exact+r.normal(0,.002,16)
        errs.append(np.linalg.norm(summary-exact))
    return np.mean(errs), np.percentile(errs,95), errs[-1]


def exp_drift():
    out={}
    for p in ["no_rebase","periodic_rebase","error_triggered_rebase"]:
        v=[drift(p,SEED+i) for i in range(50)]; out[p]={"mean_error":float(np.mean([x[0] for x in v])),"p95_error":float(np.mean([x[1] for x in v])),"final_error":float(np.mean([x[2] for x in v]))}
    return out


def emerg_one(seed, typ, N=50000):
    r=np.random.default_rng(seed); active=np.zeros(N); sig=r.normal(size=N); y=np.zeros(N); st=0
    for t in range(N):
        st=1 if r.random() < (.08 if st==0 else .72) else 0; active[t]=st; y[t]=(.8*st*sig[t] if typ=="useful" else 0)+r.normal()
    X=active*sig; beta=(X@y)/(X@X+1e-9); mse_full=np.mean((y-beta*X)**2); mse_lesion=np.mean(y**2)
    sh=r.permutation(active)*sig; b=(sh@y)/(sh@sh+1e-9); mse_sh=np.mean((y-b*sh)**2)
    return {"recurrence":float(active.mean()),"lesion_delta_mse":float(mse_lesion-mse_full),"shuffled_rescue_delta_mse":float(mse_lesion-mse_sh)}


def exp_emergence():
    out={}
    for p in ["useful","oscillator"]:
        v=[emerg_one(SEED+i,p) for i in range(30)]; out[p]={k:float(np.mean([x[k] for x in v])) for k in v[0]}
    return out


def rebuild(seed,N=120000):
    r=np.random.default_rng(seed); c={"always_incremental":0.,"always_rebuild":0.,"adaptive":0.}; wrong=0
    for _ in range(N):
        touched=r.beta(1.4,3.); tail=r.lognormal(mean=-1.2+2.2*touched,sigma=.55); inc=2+55*touched+12*tail; reb=20+12*touched
        pi=inc*np.exp(r.normal(0,.12)); pr=reb*np.exp(r.normal(0,.08)); c["always_incremental"]+=inc; c["always_rebuild"]+=reb
        if pi<pr: c["adaptive"]+=inc+.35; wrong+=inc>reb
        else: c["adaptive"]+=reb+.35; wrong+=reb>inc
    return {k:v/N for k,v in c.items()}|{"selector_wrong_rate":wrong/N}


def exp_rebuild():
    v=[rebuild(SEED+i) for i in range(20)]; return {k:float(np.mean([x[k] for x in v])) for k in v[0]}


def broadcast(seed,N=30000):
    r=np.random.default_rng(seed); s={p:{"miss":0,"deliveries":0,"rel":0} for p in ["full","fixed_sparse","confidence_fallback"]}
    for t in range(N):
        sep=2.0 if (t//10000)%3!=2 else .6; relevant=set(r.choice(20,5,replace=False).tolist()); scores=r.normal(0,1,20)
        for i in relevant: scores[i]+=sep
        ranked=np.argsort(scores)[::-1]; gap=scores[ranked[4]]-scores[ranked[5]]
        s["full"]["deliveries"]+=20; s["full"]["rel"]+=5
        for p in ["fixed_sparse","confidence_fallback"]:
            if p=="confidence_fallback" and (gap<.18 or sep<.8): delivered=set(range(20))
            else:
                delivered=set(ranked[:5].tolist())
                for i in relevant-delivered:
                    if r.random()<.95: delivered.add(i)
            s[p]["deliveries"]+=len(delivered); s[p]["rel"]+=5; s[p]["miss"]+=len(relevant-delivered)
    return {p:{"miss_rate":x["miss"]/x["rel"],"mean_fanout":x["deliveries"]/N} for p,x in s.items()}


def exp_broadcast():
    v=[broadcast(SEED+i) for i in range(20)]; return {p:{k:float(np.mean([x[p][k] for x in v])) for k in v[0][p]} for p in v[0]}


def main():
    out={"schema_version":"1.0","class":"synthetic_analytic_proxy","seed_family":"G8-20260808",
         "EXP-G8-NONNORMAL-001":exp_nonnormal(),"EXP-G8-GOV-STABILITY-002":exp_governor(),"EXP-G8-COVERAGE-003":exp_coverage(),
         "EXP-G8-VOI-FRESHNESS-004":exp_freshness(),"EXP-G8-TCC-REBASE-005":exp_tcc(),"EXP-G8-DRIFT-006":exp_drift(),
         "EXP-G8-EMERGENCE-007":exp_emergence(),"EXP-G8-REBUILD-008":exp_rebuild(),"EXP-G8-BROADCAST-009":exp_broadcast()}
    print(json.dumps(out,indent=2))

if __name__ == "__main__": main()
