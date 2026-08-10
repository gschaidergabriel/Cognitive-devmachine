"""CQC-001 synthetic reference discriminator.
Evidence class: LOCAL_SYNTHETIC_REFERENCE_MODEL_ONLY.
No Frank runtime/effect/database mutation.
"""
from collections import defaultdict
import itertools, random, statistics, time

SEED=20260811
G,M,D=6,4,4
NORMAL=[f"n{i}" for i in range(4)]
INTERVENTIONS=["LESION","REENTRY_SHUFFLE","STALE_EPOCH","AUTHORITY_BREAK"]
ACTIONS=NORMAL+INTERVENTIONS
STATES=[(g,m,d) for g in range(G) for m in range(M) for d in range(D)]
IDX={s:i for i,s in enumerate(STATES)}
LABEL={IDX[s]:s[0] for s in STATES}

def canon_next(g,m,a):
    if a.startswith("n"):
        i=int(a[1:]); return ((g+i+1)%G,m)
    if a=="LESION": return ((g+(m%2)+1)%G,(m+1)%M)
    if a=="REENTRY_SHUFFLE": return ((g+(m//2)+2)%G,(m+2)%M)
    if a=="STALE_EPOCH": return ((g+m+3)%G,(m+3)%M)
    if a=="AUTHORITY_BREAK": return ((g+(3-m)+1)%G,3-m)
    raise KeyError(a)

TRANS={}
for s in STATES:
    g,m,d=s
    for a in ACTIONS:
        ng,nm=canon_next(g,m,a)
        nd=(d+(hash(a)%D))%D
        TRANS[(IDX[s],a)]=IDX[(ng,nm,nd)]

def refine(action_subset):
    p=[]
    for lab in range(G): p.append([s for s,l in LABEL.items() if l==lab])
    changed=True
    while changed:
        changed=False
        block={s:i for i,b in enumerate(p) for s in b}
        nxt=[]
        for b in p:
            groups=defaultdict(list)
            for s in b:
                sig=(LABEL[s],tuple(block[TRANS[(s,a)]] for a in action_subset))
                groups[sig].append(s)
            nxt.extend(groups.values())
            changed |= len(groups)>1
        p=nxt
    return p

def quotient(partition):
    block={s:i for i,b in enumerate(partition) for s in b}
    qlabel={i:LABEL[b[0]] if len({LABEL[s] for s in b})==1 else -1 for i,b in enumerate(partition)}
    qtrans={}; inconsistent=0
    for i,b in enumerate(partition):
        for a in ACTIONS:
            targets={block[TRANS[(s,a)]] for s in b}
            inconsistent += len(targets)!=1
            qtrans[(i,a)]=min(targets)
    return block,qlabel,qtrans,inconsistent

def original_trace(s,seq):
    out=[LABEL[s]]
    for a in seq:
        s=TRANS[(s,a)]; out.append(LABEL[s])
    return tuple(out)

def evaluate(partition,seqs):
    block,qlabel,qtrans,inconsistent=quotient(partition)
    violations=0; total=0
    for s in range(len(STATES)):
        for seq in seqs:
            expected=original_trace(s,seq)
            q=block[s]; got=[qlabel[q]]
            for a in seq:
                q=qtrans[(q,a)]; got.append(qlabel[q])
            total+=1; violations += tuple(got)!=expected
    return dict(classes=len(partition),compression=len(STATES)/len(partition),
                transition_table_entries=len(partition)*len(ACTIONS),
                transition_table_reduction=1-len(partition)/len(STATES),
                inconsistent_block_actions=inconsistent,trace_cases=total,
                trace_violations=violations,trace_violation_rate=violations/total)

def main():
    rng=random.Random(SEED)
    full=[[s] for s in range(len(STATES))]
    output=[[s for s,l in LABEL.items() if l==lab] for lab in range(G)]
    normal=refine(NORMAL)
    cqc=refine(ACTIONS)
    shuffled=list(range(len(STATES))); rng.shuffle(shuffled)
    random24=[[] for _ in range(len(cqc))]
    for i,s in enumerate(shuffled): random24[i%len(cqc)].append(s)
    seqs=[]
    for length in (1,2,3): seqs.extend(itertools.product(ACTIONS,repeat=length))
    for _ in range(500): seqs.append(tuple(rng.choice(ACTIONS) for _ in range(4)))
    results={name:evaluate(part,seqs) for name,part in [
        ("FULL_NO_FUSION",full),("OUTPUT_ONLY",output),("NORMAL_PATH_BISIM",normal),
        ("RANDOM_24_CLASS_FUSION",random24),("CQC_INTERVENTIONAL_QUOTIENT",cqc)]}
    timings=[]
    for _ in range(200):
        t=time.perf_counter_ns(); refine(ACTIONS); timings.append((time.perf_counter_ns()-t)/1e6)
    timings.sort()
    print({"seed":SEED,"states":len(STATES),"actions":ACTIONS,"results":results,
           "refinement_ms":{"n":200,"p50":statistics.median(timings),
                            "p95":timings[189],"min":timings[0],"max":timings[-1]}})

if __name__=="__main__": main()
