#!/usr/bin/env python3
"""Seeded Clay G9 synthetic/analytic experiment harness. Requires numpy.
Mechanism/economics proxies only; never interpret as live FRANK performance.
"""
import json,argparse
from collections import defaultdict
import numpy as np

def clean(x):
    if isinstance(x,dict): return {k:clean(v) for k,v in x.items()}
    if isinstance(x,list): return [clean(v) for v in x]
    if isinstance(x,np.integer): return int(x)
    if isinstance(x,np.floating): return float(x)
    return x

def run():
    R={}
    # ClayGraph C4 measured costs are used only as interpolation seeds.
    frac=np.array([.0001,.001,.005,.01,.025,.05,.10,.20])
    ob0=np.array([.014,.119,.700,1.469,4.517,8.971,15.459,32.971]); rb0=np.array([25.831,26.512,24.675,24.722,24.877,27.644,25.674,26.875])
    oq0=np.array([5.423,5.938,7.312,8.708,11.225,13.037,14.635,16.178])/1000; rq0=np.array([3.142,3.228,3.386,3.467,3.716,3.870,4.150,4.479])/1000
    r=np.random.default_rng(90808); N=20000; f=np.exp(r.uniform(np.log(.0001),np.log(.20),N)); reads=np.maximum(0,np.rint(r.lognormal(np.log(1200),1.35,N))).astype(int)
    I=lambda a:np.interp(f,frac,a); ob,rb,oq,rq=I(ob0),I(rb0),I(oq0),I(rq0); co,cr=ob+reads*oq,rb+reads*rq; oracle=np.minimum(co,cr)
    pr=np.maximum(0,np.rint(reads*r.lognormal(0,.6,N))).astype(int); choose=ob+pr*oq<=rb+pr*rq; ra=np.where(choose,co,cr); f5=np.where(f<=.05,co,cr); f10=np.where(f<=.10,co,cr)
    R['EXP-G9-COMPACTION-POLICY-001']={'mean_ms':{'overlay':co.mean(),'rebuild':cr.mean(),'fixed5':f5.mean(),'fixed10':f10.mean(),'read_aware':ra.mean(),'oracle':oracle.mean()},'read_aware_regret_pct':(ra.mean()/oracle.mean()-1)*100,'wrong_mode_rate':np.mean(choose!=(co<=cr))}

    r=np.random.default_rng(90809); n=12000; T=800; d=.94; nbr={i:r.choice(n,8,replace=False).tolist() for i in range(n)}; val={}; last={}; log=[]; ops=0
    for t in range(T):
        ups=defaultdict(float)
        for s in r.choice(n,3,replace=False):
            ups[int(s)]+=1
            for q in nbr[int(s)]: ups[int(q)]+=.35
        log.append(dict(ups))
        for q,inc in ups.items(): val[q]=val.get(q,0)*(d**(t-last.get(q,t)))+inc; last[q]=t; ops+=1
    sample=r.choice(n,1000,replace=False); lazy=np.array([val.get(int(q),0)*(d**((T-1)-last.get(int(q),T-1))) for q in sample]); dense=np.zeros(n)
    for ups in log:
        dense*=d; ix=np.fromiter(ups,dtype=int); dense[ix]+=np.fromiter(ups.values(),dtype=float)
    R['EXP-G9-LAZY-FIELD-002']={'dense_ops':n*T,'lazy_updates':ops,'operation_reduction_x':n*T/ops,'max_sample_error':np.max(np.abs(lazy-dense[sample])),'materialized':len(val),'active_gt_0_02':np.sum(dense>.02)}

    r=np.random.default_rng(90810); N=200000; fields=6; ts=r.random(N); num=np.sum(ts[:,None]>=np.arange(fields)/fields,axis=1)
    R['EXP-G9-EPOCH-CONSISTENCY-003']={'inplace_mixed_rate':np.mean((num>0)&(num<fields)),'atomic_epoch_mixed_rate':0.0}

    r=np.random.default_rng(90811); N=50000; rel=r.random(N)<.35; lex=r.random(N)<np.where(rel,.56,.90); graph=r.random(N)<np.where(rel,.95,.89); score=np.where(rel,r.normal(.75,.18,N),r.normal(.23,.17,N)); gate=score>.52; gated=np.where(gate,graph,lex)
    R['EXP-G9-RETRIEVAL-ESCALATION-004']={'accuracy':{'lexical':lex.mean(),'graph':graph.mean(),'gated':gated.mean()},'escalation_rate':gate.mean(),'cost_proxy_ms':np.mean(np.where(gate,86.,1.))}

    r=np.random.default_rng(90812); N=100000; c=r.choice(['clean','stale_basis','payload_mutation','wrong_reader_version','trusted_miscompile'],N,p=[.75,.08,.07,.05,.05]); bad=c!='clean'; meta=np.isin(c,['stale_basis','payload_mutation','wrong_reader_version']); sem=meta|((c=='trusted_miscompile')&(r.random(N)<.85))
    R['EXP-G9-PROJECTION-INTEGRITY-005']={'invalid_rate':bad.mean(),'metadata_recall':meta[bad].mean(),'metadata_plus_semantic_recall':sem[bad].mean()}

    r=np.random.default_rng(90813); N=50000; need=r.random(N)<.28; summary=r.random(N)<np.where(need,.20,.96); exact=r.random(N)<.985; zoom=np.where(need,r.random(N)<.88,r.random(N)<.12); adaptive=np.where(zoom,exact,summary); chars=np.where(zoom,1000,160)
    R['EXP-G9-SEMANTIC-ZOOM-006']={'accuracy':{'summary':summary.mean(),'exact':exact.mean(),'adaptive':adaptive.mean()},'adaptive_chars':chars.mean(),'zoom_rate':zoom.mean()}

    r=np.random.default_rng(90814); N=20000; perms=np.array([r.permutation(3) for _ in range(N)])
    R['EXP-G9-ROLE-BINDING-007']={'unlabelled_pairwise_exact':np.mean(np.all(perms==[0,1,2],axis=1)),'labelled_nary':1.0,'reified_roles':1.0}

    r=np.random.default_rng(90815); T=5000; df=sf=dd=sd=0.; fc=[]; dc=[]; fr=dr=0
    for t in range(T):
        inc=float(r.lognormal(-3.7,.8)); q=float(r.lognormal(5.0,.8)); df+=inc; sf+=inc*.7; rp=(df*1.8+sf*.6)*q*.0007; m=0
        if (t+1)%50==0: m=25+df*50; df=sf=0; fr+=1
        fc.append(rp+m); dd+=inc; sd+=inc*.7; rp=(dd*1.8+sd*.6)*q*.0007; rc=25+dd*50; m=0
        if rp*20>rc or dd>.75: m=rc; dd=sd=0; dr+=1
        dc.append(rp+m)
    R['EXP-G9-MAINTENANCE-DEBT-008']={'fixed':{'mean':np.mean(fc),'p95':np.quantile(fc,.95),'rebuilds':fr},'debt':{'mean':np.mean(dc),'p95':np.quantile(dc,.95),'rebuilds':dr}}

    r=np.random.default_rng(90816); T=30000; x=np.zeros(T); e=np.zeros(T); u=r.normal(size=T)
    for t in range(1,T): x[t]=.92*x[t-1]+.28*u[t-1]+r.normal(scale=.08); e[t]=.92*e[t-1]+r.normal(scale=.29)
    y=.55*x+r.normal(scale=.30,size=T); base=np.mean((y-.55*x)**2); lesion=np.mean(y*y); ac=lambda a:np.corrcoef(a[:-1],a[1:])[0,1]
    R['EXP-G9-RECURRENCE-CAUSAL-009']={'autocorr1':{'functional':ac(x),'echo':ac(e)},'base_mse':base,'functional_lesion_mse':lesion,'functional_delta':lesion-base,'echo_delta':0.0}
    return clean(R)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output'); a=p.parse_args(); out={'schema_version':'1.0','class':'SYNTHETIC_ANALYTIC_PROXY','seed_family':'90808..90816','experiments':run()}; text=json.dumps(out,indent=2)
    if a.output: open(a.output,'w',encoding='utf-8').write(text+'\n')
    print(text)
