import json, math, random, statistics, time
from collections import defaultdict
from pathlib import Path

SEED=20260810
N=5000
D=8
MAX_ORDER=2
rng=random.Random(SEED)

class Poly:
    def __init__(self, terms=None, truncated=False, dropped_abs=0.0):
        self.terms=defaultdict(float)
        if terms:
            for k,v in terms.items():
                if abs(v)>1e-15:
                    self.terms[frozenset(k)] += float(v)
        self.truncated=bool(truncated)
        self.dropped_abs=float(dropped_abs)
    @staticmethod
    def const(v): return Poly({frozenset():float(v)})
    @staticmethod
    def tag(use, scale=1.0): return Poly({frozenset([use]):float(scale)})
    def __add__(self, other):
        if not isinstance(other, Poly): other=Poly.const(other)
        out=Poly(self.terms, self.truncated or other.truncated, self.dropped_abs+other.dropped_abs)
        for k,v in other.terms.items(): out.terms[k]+=v
        return out
    __radd__=__add__
    def __mul__(self, other):
        if not isinstance(other, Poly): other=Poly.const(other)
        out=Poly(truncated=self.truncated or other.truncated, dropped_abs=self.dropped_abs+other.dropped_abs)
        for ka,va in self.terms.items():
            for kb,vb in other.terms.items():
                k=ka|kb; val=va*vb
                if len(k)<=MAX_ORDER: out.terms[k]+=val
                else: out.truncated=True; out.dropped_abs += abs(val)
        return out
    __rmul__=__mul__
    def eval(self, disabled=frozenset()):
        return sum(v for k,v in self.terms.items() if not (k and any(u in disabled for u in k)))
    def lesion_delta(self, use):
        return sum(v for k,v in self.terms.items() if use in k)
    def pair_synergy(self, a,b):
        return sum(v for k,v in self.terms.items() if a in k and b in k)

def truth_value(active, x, context, eps, triple=False):
    y=1.8*context+eps
    for i in active: y += (0.45+0.17*i)*x[i]
    if 0 in active and 2 in active: y += 1.35*x[0]*x[2]
    if 4 in active and 5 in active: y += -0.8*x[4]*x[5]
    if triple and 0 in active and 2 in active and 5 in active: y += 0.9*x[0]*x[2]*x[5]
    return y

def truth_credit(active, x, context, eps, triple=False):
    y=truth_value(active,x,context,eps,triple); out={}
    for i in active:
        aa=set(active); aa.remove(i); out[i]=y-truth_value(aa,x,context,eps,triple)
    return out

def build_poly(active,x,context,eps,triple=False):
    p=Poly.const(1.8*context+eps); tags={i:Poly.tag(i) for i in active}
    for i in active: p += (0.45+0.17*i)*x[i]*tags[i]
    if 0 in active and 2 in active: p += 1.35*x[0]*x[2]*tags[0]*tags[2]
    if 4 in active and 5 in active: p += -0.8*x[4]*x[5]*tags[4]*tags[5]
    if triple and 0 in active and 2 in active and 5 in active: p += 0.9*x[0]*x[2]*x[5]*tags[0]*tags[2]*tags[5]
    return p

def mae(pred,true): return sum(abs(pred[k]-true[k]) for k in true)/max(1,len(true))
def rmse(pred,true): return math.sqrt(sum((pred[k]-true[k])**2 for k in true)/max(1,len(true)))
def signacc(pred,true): return 1.0 if not true else sum((pred[k]>=0)==(true[k]>=0) for k in true)/len(true)

rows=[]; start=time.perf_counter()
for ep in range(N):
    active={i for i in range(D) if rng.random()<0.36}
    if not active: active={rng.randrange(D)}
    x=[rng.gauss(0,1) for _ in range(D)]; context=rng.gauss(0,1); eps=rng.gauss(0,0.2)
    true=truth_credit(active,x,context,eps,False); p=build_poly(active,x,context,eps,False)
    cpd={i:p.lesion_delta(i) for i in active}
    p1=Poly({k:v for k,v in p.terms.items() if len(k)<=1}); first={i:p1.lesion_delta(i) for i in active}
    perm=list(active); rng.shuffle(perm); mp=dict(zip(sorted(active),perm)); shuffled={i:cpd.get(mp.get(i,i),0.0) for i in active}
    base=1.8*context+eps; share=(p.eval()-base)/len(active); broadcast={i:share for i in active}
    rows.append({'ep':ep,'k':len(active),'terms':len(p.terms),'cpd_mae':mae(cpd,true),'cpd_rmse':rmse(cpd,true),'cpd_sign':signacc(cpd,true),'first_mae':mae(first,true),'first_rmse':rmse(first,true),'first_sign':signacc(first,true),'shuffle_mae':mae(shuffled,true),'shuffle_rmse':rmse(shuffled,true),'shuffle_sign':signacc(shuffled,true),'broadcast_mae':mae(broadcast,true),'broadcast_rmse':rmse(broadcast,true),'broadcast_sign':signacc(broadcast,true),'gold_evals':1+len(active),'cpd_forward_evals':1,'truncated':p.truncated,'dropped_abs':p.dropped_abs})
elapsed=time.perf_counter()-start

triple_rows=[]
for ep in range(2000):
    active={i for i in range(D) if rng.random()<0.45}
    if not active: active={0}
    x=[rng.gauss(0,1) for _ in range(D)]; context=rng.gauss(0,1); eps=rng.gauss(0,0.2); p=build_poly(active,x,context,eps,True)
    triple_active=(0 in active and 2 in active and 5 in active)
    triple_rows.append({'triple_active':triple_active,'truncated':p.truncated,'dropped_abs':p.dropped_abs})

syn_err=[]
for _ in range(2000):
    active={0,2,4,5}; x=[rng.gauss(0,1) for _ in range(D)]; context=rng.gauss(0,1); eps=rng.gauss(0,0.2); p=build_poly(active,x,context,eps,False)
    syn_err.append(abs(p.pair_synergy(0,2)-1.35*x[0]*x[2])); syn_err.append(abs(p.pair_synergy(4,5)-(-0.8*x[4]*x[5])))

def avg(field): return statistics.fmean(r[field] for r in rows)
def p95(field):
    a=sorted(r[field] for r in rows); return a[int(.95*(len(a)-1))]
summary={'run':{'seed':SEED,'episodes':N,'dimensions':D,'max_order':MAX_ORDER,'elapsed_python_seconds':elapsed,'evidence_class':'SYNTHETIC_PROXY'},'candidate_cpd':{'mae_mean':avg('cpd_mae'),'mae_p95':p95('cpd_mae'),'rmse_mean':avg('cpd_rmse'),'sign_accuracy_mean':avg('cpd_sign'),'forward_evaluations_mean':avg('cpd_forward_evals'),'terms_mean':avg('terms')},'gold_leave_one_out':{'credit_error':0.0,'forward_evaluations_mean':avg('gold_evals')},'first_order_ablation':{'mae_mean':avg('first_mae'),'rmse_mean':avg('first_rmse'),'sign_accuracy_mean':avg('first_sign')},'shuffled_provenance_control':{'mae_mean':avg('shuffle_mae'),'rmse_mean':avg('shuffle_rmse'),'sign_accuracy_mean':avg('shuffle_sign')},'broadcast_only_control':{'mae_mean':avg('broadcast_mae'),'rmse_mean':avg('broadcast_rmse'),'sign_accuracy_mean':avg('broadcast_sign')},'pair_synergy':{'mae_mean':statistics.fmean(syn_err),'tests':len(syn_err)},'order3_containment':{'triple_active_n':sum(r['triple_active'] for r in triple_rows),'triple_active_flagged_truncated_n':sum(r['triple_active'] and r['truncated'] for r in triple_rows),'false_truncation_n':sum((not r['triple_active']) and r['truncated'] for r in triple_rows),'policy':'truncated => exact=false; material_reward_credit_for_affected_terms=UNKNOWN/BLOCKED'}}
print(json.dumps(summary,indent=2))