#!/usr/bin/env python3
from __future__ import annotations
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import argparse, hashlib, json, math, random, statistics, time

KINDS = ('verified','prototype','echo','stale')
PROV = {'verified':1.0,'prototype':0.55,'echo':0.05,'stale':-0.4}
INITCAP = {'verified':0.2,'prototype':0.0,'echo':-0.5,'stale':-1.0}

@dataclass
class Memory:
    mid:int
    ctx:int
    cluster:int
    action:int
    kind:str
    created:int
    reward_ema:float=0.5
    capital:float=0.0
    truth_class:str='NOT_A_TRUTH_CLAIM'
    authority_class:str='NO_EFFECT_AUTHORITY'

@dataclass
class Config:
    T:int=1600
    nctx:int=80
    clusters:int=8
    capacity:int=120
    echo_rate:float=.80
    proto_rate:float=.07
    stale_rate:float=.04
    verified_write_rate:float=.35
    drift_frac_1:float=.40
    drift_frac_2:float=.70
    drift_context_fraction:float=.20
    rent:float=.005
    coupon:float=.25
    fixed_k:int=5
    cmx_margin:float=.45


def relevance(m, ctx, cluster):
    return 1.0 if m.ctx == ctx else (0.55 if m.cluster == cluster else 0.05)


def score(m, ctx, cluster, t, algo):
    r = relevance(m,ctx,cluster)
    rec = math.exp(-max(0,t-m.created)/250.0)
    if algo == 'similarity': return 2.0*r + .30*rec
    if algo == 'provenance': return 1.5*r + PROV[m.kind] + .10*rec
    if algo == 'reward': return 1.6*r + .75*m.reward_ema + .15*rec + .15*max(0.0,PROV[m.kind])
    if algo.startswith('cmx'):
        capital = max(-2.0,min(4.0,m.capital))
        prov = 0.0 if algo == 'cmx_no_provenance' else PROV[m.kind]
        return 1.5*r + prov + .25*capital + .10*rec
    raise ValueError(algo)


def choose_general(mem, ctx, cluster, t, algo, cfg):
    ss=sorted(((score(m,ctx,cluster,t,algo),i,m) for i,m in enumerate(mem)),key=lambda z:z[0],reverse=True)
    if not ss: return 0,[],{}
    if algo.startswith('cmx') and algo != 'cmx_fixed_k':
        top=[ss[0]]
        m0=ss[0][2]; margin=ss[0][0]-(ss[1][0] if len(ss)>1 else -999)
        if not (m0.kind=='verified' and m0.ctx==ctx and margin>cfg.cmx_margin):
            top=ss[:cfg.fixed_k]
    else:
        top=ss[:cfg.fixed_k]
    votes=defaultdict(float); weights={}
    for sc,i,m in top:
        w=max(.01,sc+.60); votes[m.action]+=w; weights[i]=w
    action=max(votes.items(),key=lambda kv:(kv[1],-kv[0]))[0]
    return action,top,weights


def choose_latest_verified(mem,ctx,cluster,t):
    exact=[m for m in mem if m.kind=='verified' and m.ctx==ctx]
    if exact:
        m=max(exact,key=lambda x:x.created)
        return m.action,1
    cluster_mem=[m for m in mem if m.kind=='verified' and m.cluster==cluster]
    if cluster_mem:
        votes=defaultdict(float)
        for m in cluster_mem[-20:]: votes[m.action]+=math.exp(-(t-m.created)/300.0)
        return max(votes.items(),key=lambda kv:(kv[1],-kv[0]))[0],min(20,len(cluster_mem))
    return 0,0


def retention_score(m,t,algo):
    rec=math.exp(-max(0,t-m.created)/300.0)
    if algo=='latest': return (10.0 if m.kind=='verified' else -10.0) + m.created/1e6
    if algo=='similarity': return .30*rec + .05*PROV[m.kind]
    if algo=='provenance': return PROV[m.kind]+.05*rec
    if algo=='reward': return .90*m.reward_ema + {'verified':.30,'prototype':.10,'echo':0.0,'stale':-.20}[m.kind]+.10*rec
    if algo.startswith('cmx'):
        prov=0.0 if algo=='cmx_no_provenance' else PROV[m.kind]
        cap=m.capital if algo!='cmx_no_coupon' else INITCAP[m.kind]
        return prov + .35*cap + .05*rec
    raise ValueError(algo)


def run_seed(seed,algo,noise,cfg):
    rng=random.Random(seed)
    cc=[i%cfg.clusters for i in range(cfg.nctx)]
    base=[rng.randrange(2) for _ in range(cfg.clusters)]
    labels=[base[cc[i]] ^ int(rng.random()<.20) for i in range(cfg.nctx)]
    weights=[1/(1+i/8) for i in range(cfg.nctx)]; z=sum(weights); weights=[w/z for w in weights]
    cum=[]; z=0.0
    for w in weights: z+=w; cum.append(z)
    mem=[]; mid=0
    for _ in range(12):
        c=rng.randrange(cfg.nctx); observed=labels[c]^int(rng.random()<noise)
        mem.append(Memory(mid,c,cc[c],observed,'verified',0,capital=INITCAP['verified'])); mid+=1
    correct=avoidable=available=retrieved=0
    seg_correct=[0,0,0]; seg_total=[0,0,0]
    drift1=int(cfg.T*cfg.drift_frac_1); drift2=int(cfg.T*cfg.drift_frac_2)
    for t in range(cfg.T):
        if t in (drift1,drift2):
            for c in rng.sample(range(cfg.nctx),max(1,int(cfg.nctx*cfg.drift_context_fraction))): labels[c]^=1
        q=rng.random(); c=0
        while cum[c] < q: c+=1
        cl=cc[c]; y=labels[c]
        if algo=='latest':
            action,k=choose_latest_verified(mem,c,cl,t); top=[]; wmap={}; retrieved+=k
        else:
            action,top,wmap=choose_general(mem,c,cl,t,algo,cfg); retrieved+=len(top)
        reward=int(action==y); correct+=reward
        seg=0 if t<drift1 else (1 if t<drift2 else 2); seg_correct[seg]+=reward; seg_total[seg]+=1
        has_correct=any(m.ctx==c and m.kind=='verified' and m.action==y for m in mem)
        if has_correct: available+=1; avoidable += int(not reward)
        if algo=='reward':
            for _,_,m in top:
                if m.action==action: m.reward_ema=.9*m.reward_ema+.1*reward
        if algo.startswith('cmx'):
            use_rent=0.0 if algo=='cmx_no_rent' else cfg.rent
            use_coupon=0.0 if algo=='cmx_no_coupon' else cfg.coupon
            for _,_,m in top: m.capital-=use_rent
            if use_coupon:
                for _,ti,target in top:
                    votes=defaultdict(float)
                    for _,i,m in top:
                        if i!=ti: votes[m.action]+=wmap[i]
                    shadow=max(votes.items(),key=lambda kv:(kv[1],-kv[0]))[0] if votes else 0
                    delta=reward-int(shadow==y)
                    if target.action==action: target.capital += use_coupon*delta
        if rng.random()<cfg.verified_write_rate:
            observed=y^int(rng.random()<noise)
            mem.append(Memory(mid,c,cl,observed,'verified',t,capital=INITCAP['verified'])); mid+=1
        if rng.random()<cfg.echo_rate:
            mem.append(Memory(mid,c,cl,action,'echo',t,capital=INITCAP['echo'])); mid+=1
        if rng.random()<cfg.proto_rate:
            vals=[m.action for m in mem[-250:] if m.cluster==cl and m.kind=='verified']
            if vals:
                p=int(sum(vals)>=len(vals)/2)
                mem.append(Memory(mid,c,cl,p,'prototype',t,capital=INITCAP['prototype'])); mid+=1
        if rng.random()<cfg.stale_rate:
            mem.append(Memory(mid,c,cl,1-y,'stale',t,capital=INITCAP['stale'])); mid+=1
        if len(mem)>cfg.capacity:
            mem=sorted(mem,key=lambda m:retention_score(m,t,algo),reverse=True)[:cfg.capacity]
    return {
      'accuracy':correct/cfg.T,
      'avoidable_error_rate':avoidable/available if available else 0.0,
      'retrieved_per_turn':retrieved/cfg.T,
      'segments':[seg_correct[i]/seg_total[i] for i in range(3)],
      'final_kinds':dict(Counter(m.kind for m in mem)),
    }


def aggregate(rows):
    return {
      'accuracy_mean':statistics.mean(x['accuracy'] for x in rows),
      'accuracy_sd':statistics.stdev(x['accuracy'] for x in rows) if len(rows)>1 else 0.0,
      'avoidable_error_mean':statistics.mean(x['avoidable_error_rate'] for x in rows),
      'retrieved_per_turn_mean':statistics.mean(x['retrieved_per_turn'] for x in rows),
      'segment_accuracy_mean':[statistics.mean(x['segments'][i] for x in rows) for i in range(3)],
      'final_kinds_total':{k:sum(x['final_kinds'].get(k,0) for x in rows) for k in KINDS},
    }


def replay_control():
    rng=random.Random(99173)
    events=[]
    for i in range(1000):
        events.append({'receipt_id':f'r{i}','epoch':7,'mid':rng.randrange(40),'delta':rng.choice([-1,0,1])*.25,'rent':.005})
    stale=[{'receipt_id':f's{i}','epoch':6,'mid':rng.randrange(40),'delta':1.0,'rent':0.0} for i in range(100)]
    duplicated=events + events[:200] + stale
    rng.shuffle(duplicated)
    def apply(seq):
        capital=[0.0]*40; seen=set(); stale_reject=duplicate_reject=0
        for e in seq:
            if e['epoch']!=7: stale_reject+=1; continue
            if e['receipt_id'] in seen: duplicate_reject+=1; continue
            seen.add(e['receipt_id']); capital[e['mid']]+=e['delta']-e['rent']
        raw=json.dumps([round(x,9) for x in capital],separators=(',',':')).encode()
        return hashlib.sha256(raw).hexdigest(),stale_reject,duplicate_reject,len(seen)
    a=apply(duplicated); b=apply(list(reversed(duplicated)))
    return {'forward':a,'reverse':b,'same_digest':a[0]==b[0],'expected_unique':1000}


def authority_control():
    m=Memory(1,1,1,1,'echo',0,capital=1000.0,truth_class='UNVERIFIED_PROCEDURAL_HINT',authority_class='NO_EFFECT_AUTHORITY')
    before=(m.truth_class,m.authority_class); _=max(-2,min(4,m.capital)); after=(m.truth_class,m.authority_class)
    return {'classes_unchanged':before==after,'truth_class':m.truth_class,'authority_class':m.authority_class}


def microbench(cfg):
    rng=random.Random(1234); mem=[]
    for i in range(cfg.capacity):
        kind=KINDS[i%4]; mem.append(Memory(i,i%cfg.nctx,i%cfg.clusters,i%2,kind,i,capital=INITCAP[kind]))
    queries=[(rng.randrange(cfg.nctx),rng.randrange(cfg.clusters),1000+i) for i in range(6000)]
    out={}
    for algo in ('latest','provenance','cmx'):
        start=time.perf_counter_ns(); count=0
        for c,cl,t in queries:
            if algo=='latest': _,k=choose_latest_verified(mem,c,cl,t); count+=k
            else: _,top,_=choose_general(mem,c,cl,t,algo,cfg); count+=len(top)
        elapsed=time.perf_counter_ns()-start
        out[algo]={'ns_per_query':elapsed/len(queries),'retrieved_total':count}
    conventional={'mid':1,'ctx':1,'cluster':1,'action':1,'kind':'verified','created':1,'reward_ema':.5}
    cmx={**conventional,'capital':.2,'truth_class':'NOT_A_TRUTH_CLAIM','authority_class':'NO_EFFECT_AUTHORITY'}
    out['representative_json_bytes']={'conventional':len(json.dumps(conventional,separators=(',',':')).encode()),'cmx':len(json.dumps(cmx,separators=(',',':')).encode())}
    return out


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--seeds',type=int,default=10); ap.add_argument('--output'); args=ap.parse_args()
    cfg=Config(); noises=[0.0,.02,.05,.10,.15]
    algorithms=['similarity','provenance','reward','latest','cmx']
    matrix={}
    started=time.perf_counter()
    for noise in noises:
        matrix[str(noise)]={}
        for algo in algorithms:
            rows=[run_seed(seed,algo,noise,cfg) for seed in range(args.seeds)]
            matrix[str(noise)][algo]=aggregate(rows)
    ablations={}
    for algo in ['cmx','cmx_no_coupon','cmx_no_rent','cmx_fixed_k','cmx_no_provenance']:
        rows=[run_seed(seed,algo,.10,cfg) for seed in range(args.seeds)]
        ablations[algo]=aggregate(rows)
    result={
      'schema_version':'1.0','candidate':'ATOMIC-CMX-001','evidence_class':'LOCAL_SYNTHETIC_EXECUTABLE_PROXY',
      'config':asdict(cfg),'seeds':args.seeds,'noise_sweep':matrix,'ablations_at_noise_0_10':ablations,
      'replay_control':replay_control(),'authority_control':authority_control(),'microbench':microbench(cfg),
      'runtime_seconds':time.perf_counter()-started,
      'claims_guard':['not target-VPS performance','not factual-memory truth benchmark','not whole-Frank acceptance']
    }
    text=json.dumps(result,indent=2,sort_keys=True)+'\n'
    if args.output: open(args.output,'w',encoding='utf-8').write(text)
    print(text,end='')

if __name__=='__main__': main()
