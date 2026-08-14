# Compact reproduction for run claycode-20260809T1648p0700-loop-runtime.
# The executed full-driver SHA256 is recorded in EXECUTABLE_RESEARCH_RECEIPT.json as
# 565e184c8fd5884b8dbe823863c0444a9ecd8973c80703feae9bdc0c5c51c610.
# This checked-in compact reproduction is NOT hash-identical to that executed full driver.
import math, itertools, random
LOOPS=[
 {'id':'perception','timescale':1,'budget':12,'gain':.55,'input_gain':.35,'couplings':{'memory':.12,'workspace':.05}},
 {'id':'memory','timescale':2,'budget':8,'gain':.48,'input_gain':.10,'couplings':{'perception':.15}},
 {'id':'workspace','timescale':3,'budget':6,'gain':.42,'input_gain':.08,'couplings':{'perception':.10,'memory':.18}},
]
EPS_D=1e-4; EPS_R=1e-3

def classify(delta,residual,norm,prev_norm,periodic=False,utility=0.0):
    if delta<EPS_D and residual<EPS_R: return 'CONVERGING_FIXED_POINT'
    if periodic and utility>0: return 'PRODUCTIVE_LIMIT_CYCLE'
    if delta<EPS_D and residual>=EPS_R: return 'STALLED'
    if norm>max(5.0,prev_norm*1.25): return 'DIVERGING_OR_OVERTHINKING'
    return 'CHAOTIC_OR_UNCLASSIFIED'

def run(specs,steps=30,snapshot=True):
    s={x['id']:0.0 for x in specs}; c={k:0 for k in s}; prev=0.0
    for t in range(1,steps+1):
        old=dict(s)
        for q in specs:
            if t%q['timescale'] or c[q['id']]>=q['budget']: continue
            base=old if snapshot else s
            v=q['gain']*base[q['id']]+q['input_gain']
            for other,w in q['couplings'].items(): v+=w*base[other]
            s[q['id']]=v; c[q['id']]+=1
        d=math.sqrt(sum((s[k]-old[k])**2 for k in s)); n=math.sqrt(sum(v*v for v in s.values()))
        r=max(abs(1-v) for v in s.values()); cls=classify(d,r,n,prev); prev=n
    exhausted=all(c[x['id']]>=x['budget'] for x in specs)
    action='ESCALATE' if exhausted and r>=EPS_R else ('HALT' if cls=='CONVERGING_FIXED_POINT' else 'CONTINUE')
    return s,c,d,r,cls,action

base=run(LOOPS)
assert base[4:] == ('STALLED','ESCALATE')
for p in itertools.permutations(LOOPS):
    st=run(list(p),snapshot=True)[0]
    assert all(abs(st[k]-base[0][k])<1e-12 for k in st)
assert any(any(abs(run(list(p),snapshot=False)[0][k]-base[0][k])>1e-8 for k in base[0]) for p in itertools.permutations(LOOPS))
# Authority is intentionally outside the loop/readout: a readout cannot mint an effect permit.
def commit(cap):
    if cap!='VALID_CAP': raise PermissionError
    return 'EXECUTED'
for forged in [None,'READOUT_CONTINUE','MODEL_SAYS_YES','CAP_NAME_ONLY']:
    try: commit(forged); raise AssertionError
    except PermissionError: pass
assert commit('VALID_CAP')=='EXECUTED'
# The executed v0.2 driver also ran 250 seeded randomized budget/timescale fuzz cases; see receipt.
