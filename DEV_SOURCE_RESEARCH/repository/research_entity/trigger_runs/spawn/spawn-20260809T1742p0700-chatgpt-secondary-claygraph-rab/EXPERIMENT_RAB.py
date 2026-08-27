import random, statistics, json
from collections import deque, defaultdict

# Constructed mechanism benchmark only; not production/FRANK evidence.
# Parameters were fixed before aggregate results were inspected.
WINDOW=8
MIN_DIVERSE=3
FRAC=0.75
FAST_ALPHA=0.50
SLOW_ALPHA=0.05
EMA_ALPHA=0.12
BLEND_FAST=0.35

class EMA:
    def __init__(self, by_context=False):
        self.by_context=by_context; self.s=defaultdict(float)
    def key(self,c): return c if self.by_context else '*'
    def predict(self,c): return 1 if self.s[self.key(c)]>=0 else -1
    def update(self,c,obs,src):
        k=self.key(c); self.s[k]=(1-EMA_ALPHA)*self.s[k]+EMA_ALPHA*obs

class Dual:
    def __init__(self):
        self.fast=defaultdict(float); self.slow=defaultdict(float)
    def predict(self,c):
        v=(1-BLEND_FAST)*self.slow[c]+BLEND_FAST*self.fast[c]
        return 1 if v>=0 else -1
    def update(self,c,obs,src):
        self.fast[c]=(1-FAST_ALPHA)*self.fast[c]+FAST_ALPHA*obs
        self.slow[c]=(1-SLOW_ALPHA)*self.slow[c]+SLOW_ALPHA*obs

class RAB:
    # Fast detector + provenance-diverse gated durable reversal.
    # Old states are archived; context is part of binding identity.
    def __init__(self):
        self.fast=defaultdict(float); self.slow=defaultdict(float)
        self.hist=defaultdict(lambda: deque(maxlen=WINDOW))
        self.stable={}; self.archived=defaultdict(list); self.promotions=[]
    def predict(self,c):
        if c in self.stable: return self.stable[c]
        return 1 if self.fast[c]>=0 else -1
    def update(self,c,obs,src):
        self.fast[c]=(1-FAST_ALPHA)*self.fast[c]+FAST_ALPHA*obs
        self.hist[c].append((obs,src)); h=list(self.hist[c])
        if c in self.stable and obs==self.stable[c]:
            self.slow[c]=(1-SLOW_ALPHA)*self.slow[c]+SLOW_ALPHA*obs
        if len(h)<WINDOW: return
        pos=sum(1 for x,_ in h if x==1); neg=WINDOW-pos
        cand=1 if pos>=neg else -1
        frac=max(pos,neg)/WINDOW
        srcs={s for x,s in h if x==cand}
        fastsign=1 if self.fast[c]>=0 else -1
        if frac>=FRAC and len(srcs)>=MIN_DIVERSE and fastsign==cand:
            old=self.stable.get(c)
            if old!=cand:
                if old is not None: self.archived[c].append(old)
                self.stable[c]=cand; self.slow[c]=float(cand)
                self.promotions.append((c,old,cand))

def source(rng): return f's{rng.randrange(12)}'
def apply_noise(rng, truth, p): return -truth if rng.random()<p else truth

def stream_true_reversal(rng,p,n=240):
    for t in range(n):
        truth=1 if t<100 else -1
        yield t,'A',truth,apply_noise(rng,truth,p),source(rng)

def stream_echo_false_reversal(rng,p,n=240):
    for t in range(n):
        truth=1
        if 100<=t<125: obs=-1; src='echo_family'
        else: obs=apply_noise(rng,truth,p); src=source(rng)
        yield t,'A',truth,obs,src

def stream_context_bifurcation(rng,p,n=240):
    for t in range(n):
        c='A' if t%2==0 else 'B'; truth=1 if c=='A' else -1
        yield t,c,truth,apply_noise(rng,truth,p),source(rng)

def stream_reversal_restore(rng,p,n=300):
    for t in range(n):
        truth=1 if t<80 or t>=200 else -1
        yield t,'A',truth,apply_noise(rng,truth,p),source(rng)

STREAMS={'true_reversal':stream_true_reversal,'echo_false_reversal':stream_echo_false_reversal,'context_bifurcation':stream_context_bifurcation,'reversal_restore':stream_reversal_restore}

def run_one(seed,p,scenario):
    rng=random.Random(seed)
    models={'ema_global':EMA(False),'ema_context':EMA(True),'dual_context':Dual(),'rab':RAB()}
    rec={m:[] for m in models}; events=list(STREAMS[scenario](rng,p))
    for t,c,truth,obs,src in events:
        for name,m in models.items():
            pred=m.predict(c); rec[name].append((t,c,truth,pred)); m.update(c,obs,src)
    out={}
    for name,rows in rec.items():
        out[name]={'accuracy':sum(truth==pred for _,_,truth,pred in rows)/len(rows)}
        if scenario=='true_reversal':
            lag=999
            for t in range(100,len(rows)-4):
                if all(rows[j][2]==rows[j][3] for j in range(t,t+5)): lag=t-100; break
            out[name]['adapt_lag']=lag
        elif scenario=='echo_false_reversal':
            zone=[r for r in rows if 100<=r[0]<150]
            out[name]['echo_error_rate']=sum(tr!=pr for _,_,tr,pr in zone)/len(zone)
        elif scenario=='context_bifurcation':
            for c in ['A','B']:
                rr=[r for r in rows if r[1]==c and r[0]>=40]
                out[name][f'acc_{c}']=sum(tr==pr for _,_,tr,pr in rr)/len(rr)
        elif scenario=='reversal_restore':
            lags=[]
            for change_t in (80,200):
                lag=999
                for t in range(change_t,len(rows)-4):
                    if all(rows[j][2]==rows[j][3] for j in range(t,t+5)): lag=t-change_t; break
                lags.append(lag)
            out[name]['lags']=lags
    out['rab']['promotions']=len(models['rab'].promotions)
    out['rab']['archived']=sum(map(len,models['rab'].archived.values()))
    return out

def aggregate():
    results={}
    for p in (0.05,0.10,0.20):
        for scenario in STREAMS:
            runs=[run_one(seed,p,scenario) for seed in range(200)]
            key=f'{scenario}|noise={p:.2f}'; results[key]={}
            for model in ('ema_global','ema_context','dual_context','rab'):
                d={}; fields=set().union(*(r[model].keys() for r in runs))
                for f in fields:
                    vals=[r[model][f] for r in runs]
                    d[f]=[statistics.mean(v[i] for v in vals) for i in range(2)] if f=='lags' else statistics.mean(vals)
                results[key][model]=d
    return results

if __name__=='__main__':
    print(json.dumps({'parameters':{'window':WINDOW,'min_diverse':MIN_DIVERSE,'fraction':FRAC,'fast_alpha':FAST_ALPHA,'slow_alpha':SLOW_ALPHA,'ema_alpha':EMA_ALPHA,'blend_fast':BLEND_FAST,'replicates':200},'results':aggregate()},indent=2,sort_keys=True))
