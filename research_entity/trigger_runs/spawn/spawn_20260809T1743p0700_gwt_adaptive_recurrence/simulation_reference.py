import random, statistics, math, json

REGIMES=['easy','hard','cycle','stalled','diverging']
PROBS=[0.28,0.30,0.18,0.14,0.10]
MAX_STEPS=12
SUCCESS_P=0.15
COST=0.025


def next_pressure(reg, p, t, rng):
    if reg=='easy':
        q=0.48*p + rng.gauss(0,0.015)
    elif reg=='hard':
        q=0.80*p + rng.gauss(0,0.018)
    elif reg=='cycle':
        # productive 2-step oscillation: a small uphill integration step then larger downhill gain
        if t % 2 == 1:
            q=p + 0.045 + rng.gauss(0,0.012)
        else:
            q=0.72*p - 0.015 + rng.gauss(0,0.015)
    elif reg=='stalled':
        q=p + rng.gauss(0,0.008)
    elif reg=='diverging':
        q=1.10*p + 0.015 + rng.gauss(0,0.015)
    return max(0.0,min(1.5,q))


def run_episode(reg, policy, rng):
    p=rng.uniform(0.75,1.05)
    hist=[p]
    stop_reason='budget'
    for t in range(1,MAX_STEPS+1):
        p=next_pressure(reg,p,t,rng)
        hist.append(p)
        if policy.startswith('fixed'):
            k=int(policy[5:])
            if t>=k:
                stop_reason='fixed_budget'; break
        elif policy=='delta_only':
            if p<=SUCCESS_P:
                stop_reason='resolved'; break
            if t>=2 and abs(hist[-1]-hist[-2]) < 0.03:
                stop_reason='low_delta'; break
        elif policy=='pressure_trend':
            if p<=SUCCESS_P:
                stop_reason='resolved'; break
            if t>=2 and hist[-1] > hist[-3] + 0.12:
                stop_reason='diverging'; break
            if t>=4:
                improvement=(hist[-5]-hist[-1])/4.0
                local_var=statistics.pstdev(hist[-5:])
                if p>SUCCESS_P and improvement < 0.008 and local_var < 0.025:
                    stop_reason='stalled'; break
        else:
            raise ValueError(policy)
    steps=len(hist)-1
    success=p<=SUCCESS_P
    quality=max(0.0,1.0-min(p,1.0))
    utility=0.75*quality + 0.25*(1.0 if success else 0.0) - COST*steps
    return dict(regime=reg,steps=steps,pressure=p,success=success,utility=utility,stop=stop_reason)


def one_seed(seed,n=3000):
    rng=random.Random(seed)
    policies=['fixed4','fixed8','fixed12','delta_only','pressure_trend']
    rows={p:[] for p in policies}
    for _ in range(n):
        x=rng.random(); acc=0
        for reg,pr in zip(REGIMES,PROBS):
            acc+=pr
            if x<=acc:
                break
        ep_seed=rng.getrandbits(64)
        for pol in policies:
            rows[pol].append(run_episode(reg,pol,random.Random(ep_seed)))
    out={}
    for pol,rs in rows.items():
        out[pol]={
            'success_rate':sum(r['success'] for r in rs)/n,
            'mean_steps':sum(r['steps'] for r in rs)/n,
            'mean_pressure':sum(r['pressure'] for r in rs)/n,
            'mean_utility':sum(r['utility'] for r in rs)/n,
            'by_regime':{}
        }
        for reg in REGIMES:
            q=[r for r in rs if r['regime']==reg]
            out[pol]['by_regime'][reg]={
                'n':len(q),'success_rate':sum(r['success'] for r in q)/len(q),
                'mean_steps':sum(r['steps'] for r in q)/len(q),
                'mean_pressure':sum(r['pressure'] for r in q)/len(q)
            }
    return out

seeds=list(range(20))
allr=[one_seed(s) for s in seeds]
policies=list(allr[0])
summary={}
for pol in policies:
    summary[pol]={}
    for metric in ['success_rate','mean_steps','mean_pressure','mean_utility']:
        vals=[r[pol][metric] for r in allr]
        m=statistics.mean(vals); sd=statistics.stdev(vals)
        se=sd/math.sqrt(len(vals)); ci=1.96*se
        summary[pol][metric]={'mean':m,'ci95':ci}
    summary[pol]['by_regime']={}
    for reg in REGIMES:
        summary[pol]['by_regime'][reg]={}
        for metric in ['success_rate','mean_steps','mean_pressure']:
            vals=[r[pol]['by_regime'][reg][metric] for r in allr]
            m=statistics.mean(vals); sd=statistics.stdev(vals); ci=1.96*sd/math.sqrt(len(vals))
            summary[pol]['by_regime'][reg][metric]={'mean':m,'ci95':ci}
print(json.dumps(summary,indent=2))