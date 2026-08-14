import random, statistics, json
from collections import deque, defaultdict

WINDOW=8
FRAC=0.75
FAST_ALPHA=0.5

class RAB:
    def __init__(self,min_diverse):
        self.min_diverse=min_diverse
        self.fast=defaultdict(float)
        self.hist=defaultdict(lambda:deque(maxlen=WINDOW))
        self.stable={}
        self.promotions=0
    def predict(self,c):
        return self.stable.get(c,1 if self.fast[c]>=0 else -1)
    def update(self,c,obs,src):
        self.fast[c]=(1-FAST_ALPHA)*self.fast[c]+FAST_ALPHA*obs
        self.hist[c].append((obs,src)); h=list(self.hist[c])
        if len(h)<WINDOW: return
        pos=sum(x==1 for x,_ in h); neg=WINDOW-pos
        cand=1 if pos>=neg else -1
        frac=max(pos,neg)/WINDOW
        srcs={s for x,s in h if x==cand}
        fastsign=1 if self.fast[c]>=0 else -1
        if frac>=FRAC and len(srcs)>=self.min_diverse and fastsign==cand and self.stable.get(c)!=cand:
            self.stable[c]=cand; self.promotions+=1

def src(rng): return f's{rng.randrange(12)}'
def noisy(rng,t,p): return -t if rng.random()<p else t

def run(seed,p,scenario,k):
    rng=random.Random(seed); m=RAB(k); rows=[]; n=240
    for t in range(n):
        truth=1 if scenario=='echo' else (1 if t<100 else -1)
        if scenario=='echo' and 100<=t<125: obs=-1; s='echo_family'
        else: obs=noisy(rng,truth,p); s=src(rng)
        pred=m.predict('A'); rows.append((truth,pred)); m.update('A',obs,s)
    acc=sum(a==b for a,b in rows)/n
    if scenario=='echo':
        err=sum(rows[t][0]!=rows[t][1] for t in range(100,150))/50
        return acc,err,m.promotions
    lag=999
    for t in range(100,n-4):
        if all(rows[j][0]==rows[j][1] for j in range(t,t+5)): lag=t-100; break
    return acc,lag,m.promotions

out={}
for p in (.05,.1,.2):
    for k in (1,2,3,4,5):
        for scenario in ('true','echo'):
            vals=[run(seed,p,scenario,k) for seed in range(500)]
            out[f'{scenario}|p={p}|k={k}']=[statistics.mean(x[i] for x in vals) for i in range(3)]
print(json.dumps(out,indent=2,sort_keys=True))
