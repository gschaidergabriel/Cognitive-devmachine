#!/usr/bin/env python3
from __future__ import annotations
import collections, json, random, statistics

SEED=20260811

def material_pairs(labels):
    return {(i,j) for i in range(len(labels)) for j in range(i+1,len(labels)) if labels[i]!=labels[j]}

def item_coverage(item,pairs):
    p=item['pattern']; return {x for x in pairs if p[x[0]]!=p[x[1]]}

def gen_decision_case(rng):
    n=rng.randint(4,12); k=rng.randint(2,min(4,n))
    labels=[i%k for i in range(n)]; rng.shuffle(labels)
    items=[]; m=rng.randint(max(12,n*2),max(20,n*4))
    for j in range(m):
        patt=[rng.randint(0,1) for _ in range(n)]
        if all(x==patt[0] for x in patt): patt[rng.randrange(n)]^=1
        cost=rng.randint(1,12); ones=sum(patt)
        rel=.45*rng.random()+.35*(max(ones,n-ones)/n)+.20*(1/cost)
        items.append({'id':j,'pattern':patt,'cost':cost,'rel':rel})
    nextid=m
    for a in range(n):
        for b in range(a+1,n):
            if labels[a]==labels[b]: continue
            if not any(x['pattern'][a]!=x['pattern'][b] for x in items):
                patt=[0]*n; patt[b]=1
                items.append({'id':nextid,'pattern':patt,'cost':rng.randint(2,8),'rel':.15*rng.random()}); nextid+=1
    mandatory=[{'id':'identity','pattern':[0]*n,'cost':3,'rel':1.0},{'id':'intent','pattern':[0]*n,'cost':3,'rel':1.0}]
    true=rng.randrange(n); total=sum(x['cost'] for x in items)
    budget=max(12,int(total*rng.uniform(.12,.25)))
    return labels,items,mandatory,true,budget

def topk(items,budget,mandatory):
    used=list(mandatory); cost=sum(x['cost'] for x in used)
    for it in sorted(items,key=lambda x:x['rel']/max(1,x['cost']),reverse=True):
        if cost+it['cost']<=budget: used.append(it); cost+=it['cost']
    return used,cost

def cover(items,budget,pairs,mandatory):
    used=list(mandatory); cost=sum(x['cost'] for x in used); uncovered=set(pairs); remaining=list(items)
    while uncovered:
        best=None; score=0.0
        for it in remaining:
            if cost+it['cost']>budget: continue
            gain=len(item_coverage(it,uncovered)); s=gain/it['cost']
            if s>score: score=s; best=it
        if best is None or score<=0: break
        used.append(best); cost+=best['cost']; uncovered-=item_coverage(best,uncovered); remaining.remove(best)
    return used,cost,uncovered

def certified_action(selected,true,labels):
    possible=[]
    for h in range(len(labels)):
        if all(isinstance(it['id'],str) or it['pattern'][h]==it['pattern'][true] for it in selected): possible.append(h)
    return len({labels[h] for h in possible})==1

def decision_benchmark():
    rng=random.Random(SEED); rows=[]
    for case in range(3000):
        labels,items,mandatory,true,budget=gen_decision_case(rng); pairs=material_pairs(labels)
        full=items+mandatory; top,c_top=topk(items,budget,mandatory); safe,c_safe,_=cover(items,budget,pairs,mandatory)
        for name,sel,cost in [('FULL',full,sum(x['cost'] for x in full)),('TOPK_SAFE',top,c_top),('SAFE_DECISION_COVER',safe,c_safe),('DCA_SELECTION',safe,c_safe+2)]:
            covered=set()
            for it in sel:
                if not isinstance(it['id'],str): covered|=item_coverage(it,pairs)
            rows.append({'method':name,'cost':cost,'full_cost':sum(x['cost'] for x in full),'certified':certified_action(sel,true,labels),'uncovered':len(pairs-covered)})
    out={}
    for name in ['FULL','TOPK_SAFE','SAFE_DECISION_COVER','DCA_SELECTION']:
        rs=[r for r in rows if r['method']==name]; costs=[r['cost'] for r in rs]
        out[name]={'certification_rate':sum(r['certified'] for r in rs)/len(rs),'mean_cost':statistics.mean(costs),'median_cost':statistics.median(costs),'p95_cost':statistics.quantiles(costs,n=20)[18],'mean_cost_vs_full':statistics.mean(r['cost']/r['full_cost'] for r in rs),'mean_uncovered_pairs':statistics.mean(r['uncovered'] for r in rs)}
    return out

def negative_benchmark():
    rng=random.Random(SEED+2); N=8000; stats=collections.defaultdict(collections.Counter)
    for _ in range(N):
        ideal=0 if rng.random()<.38 else rng.randint(1,5); global_complete=rng.random()<.35; query_complete=global_complete or rng.random()<.38
        available=ideal if query_complete else sum(1 for _ in range(ideal) if rng.random()<.48)
        qsel=1 if available>0 else 0; generic=sum(1 for _ in range(available) if rng.random()<.4); stale=rng.random()<.10
        if stale:
            ideal=max(1,ideal); available=max(1,available); qsel=0; generic=0; query_complete=True
        truth='ABSENT' if ideal==0 else 'PRESENT'
        preds={
          'TOPK_NAIVE':'PRESENT' if generic>0 else 'ABSENT',
          'QUERY_AWARE_NO_CERT':'PRESENT' if qsel>0 else 'ABSENT',
          'GLOBAL_CERT':'PRESENT' if qsel>0 else ('ABSENT' if global_complete else 'UNKNOWN'),
          'DCA_QR_CURRENT':'PRESENT' if qsel>0 else ('UNKNOWN' if stale else ('ABSENT' if query_complete else 'UNKNOWN')),
          'QR_STALE_UNFENCED':'PRESENT' if qsel>0 else ('ABSENT' if query_complete else 'UNKNOWN')}
        for name,pred in preds.items():
            c=stats[name]; c['n']+=1; c['correct']+=pred==truth; c['unknown']+=pred=='UNKNOWN'; c['overclosure']+=pred=='ABSENT' and truth=='PRESENT'; c['stale_overclosure']+=stale and pred=='ABSENT'
    out={}
    for name,c in stats.items():
        answered=c['n']-c['unknown']
        out[name]={'accuracy_total':c['correct']/c['n'],'coverage':answered/c['n'],'selective_accuracy':c['correct']/answered if answered else None,'overclosure_rate':c['overclosure']/c['n'],'stale_overclosure_rate':c['stale_overclosure']/c['n'],'unknown_rate':c['unknown']/c['n']}
    return out

if __name__=='__main__':
    print(json.dumps({'seed':SEED,'decision_benchmark':decision_benchmark(),'negative_benchmark':negative_benchmark()},indent=2,sort_keys=True))
