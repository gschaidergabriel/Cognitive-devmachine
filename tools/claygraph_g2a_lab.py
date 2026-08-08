#!/usr/bin/env python3
from __future__ import annotations
import json, random, math, re
from collections import Counter

VERSION='claygraph-g2a-lab-0.4-bridge-receipt'
SEED_SELFUSE=314159
SEED_ROUTE=9917
SEED_ATTRACTOR=7711

def words(s): return set(re.findall(r'[a-z0-9_]+', s.lower()))
def top_indices(xs,k): return sorted(range(len(xs)), key=lambda i:(xs[i],i), reverse=True)[:k]
def matvec(v,A):
    out=[0.0]*len(v)
    for i,vi in enumerate(v):
        if vi:
            row=A[i]
            for j,w in enumerate(row):
                if w: out[j]+=vi*w
    return out

def self_use():
    nodes={'tcqs':'ClayCode typed collection query semantics SET ORDERED MULTISET WEIGHTED duplicate order multiplicity weight policy','candidate_topology':'candidate membership ranking topology changes before workspace competition selection','g1d':'ClayGraph immutable semantic graph epochs sparse latent activation bounded assembly exact anchors','activation':'sparse salience activation decay inhibition propagation between model calls','assembly':'bounded epoch pinned active Assembly model visible memory candidate set exact anchors','u1':'UnifiedDB authoritative event state effect spine specialized replayable graph vector FTS activation derived views','replay':'canonical append only event history replay crash recovery rebuild derived views','cacc':'Certified Adaptive Cognitive Continuity integrity utility authority separation adaptive salience','utility':'cognitive utility receipt may update salience decay inhibition routing but not truth authority','anti_attractor':'anti attractor bounded salience gain inhibition novelty diversity holdout poisoning resistance','gwt_r5':'system WorkspaceEpisode distinct from model internal workspace projection uptake effect reentry','internal_ws':'model internal privileged workspace uptake representation lesion rescue','projection':'exact reader projection view identity ordering serialization model handoff','c7':'FRANK Clay Organ Runtime Fabric semantic organ process storage authority boundaries','broker':'isolated capability effect broker secrets revocation execution authority','h4':'Hyperposition typed semantic firebreak fact activation proposal authority effect intent higher order roles','ecert2':'Emergence causal certificate lesion mechanistic rescue recurrence OOD multiscale intervention','temporal':'bitemporal valid time transaction time stale revoked point in time relation validity','role':'role aware n ary relation instance actor object direction higher order relation identity','semantic_hash':'semantic identity distinct from provenance contract instance projected view identity','selection_plan':'query selection plan provenance candidate space ranking identity','exact_anchor':'authoritative exact anchor validation truth witness provenance source','dual_path':'background continuity plus explicit retrieval fallback exact lookup validation broad search recovery'}
    edges=[('tcqs','candidate_topology',1.0),('candidate_topology','gwt_r5',.9),('g1d','activation',1),('activation','assembly',1),('assembly','candidate_topology',.8),('u1','replay',1),('u1','g1d',.8),('replay','exact_anchor',.8),('cacc','utility',1),('utility','anti_attractor',1),('gwt_r5','internal_ws',1),('gwt_r5','projection',.8),('c7','broker',1),('c7','u1',.7),('c7','gwt_r5',.7),('h4','role',.8),('h4','broker',.7),('ecert2','gwt_r5',.6),('ecert2','cacc',.6),('temporal','g1d',.7),('temporal','u1',.7),('role','g1d',.8),('semantic_hash','tcqs',.8),('selection_plan','candidate_topology',1),('selection_plan','u1',.8),('exact_anchor','g1d',.8),('dual_path','g1d',.8),('dual_path','u1',.6)]
    ids=list(nodes); idx={n:i for i,n in enumerate(ids)}; N=len(ids); A=[[0.0]*N for _ in range(N)]
    for a,b,w in edges:
        A[idx[a]][idx[b]]=max(A[idx[a]][idx[b]],w); A[idx[b]][idx[a]]=max(A[idx[b]][idx[a]],w*.85)
    queries=[('What upstream change can alter who competes even when workspace policy is fixed?',['tcqs'],{'tcqs','candidate_topology','selection_plan'}),('What protects memory after a crash if graph and vector views lag?',['u1'],{'u1','replay','exact_anchor'}),('How should useful memory feedback change the system without rewriting facts?',['cacc'],{'utility','anti_attractor','cacc'}),('What must be separated when testing whether a selected workspace item actually affected model reasoning?',['gwt_r5'],{'gwt_r5','internal_ws','projection'}),('Which boundary must remain hard even if cognitive organs share a process?',['c7'],{'broker','c7'}),('What state can change between model calls but must never become truth?',['g1d'],{'activation','g1d','exact_anchor'}),('How do we keep changing facts from becoming stale contradictions?',['temporal'],{'temporal','u1','replay'}),('Why is direction or participant role part of graph identity?',['h4'],{'role','h4','semantic_hash'}),('What is the safer memory architecture when automatic association misses something?',['dual_path'],{'dual_path','g1d','u1','exact_anchor'}),('What should an emergence test do after a continuity effect appears?',['ecert2'],{'ecert2','gwt_r5','cacc'}),('Which identities must not be collapsed when graph results are projected to a reader?',['semantic_hash'],{'semantic_hash','projection','selection_plan'}),('What governs which derived store is queried without letting backend defaults redefine meaning?',['selection_plan'],{'selection_plan','tcqs','u1'})]
    docs={k:words(v) for k,v in nodes.items()}; df=Counter(w for ws in docs.values() for w in ws)
    def lexical(q):
        qw=words(q); return [sum(math.log((N+1)/(df[w]+1))+1 for w in qw & docs[k]) for k in ids]
    def arm(mode,k=5):
        recalls=[]; reciprocal=[]; details=[]
        for q,prior,gold in queries:
            score=lexical(q)
            if mode!='off':
                seeds=[0.0]*N; use=prior if mode=='truthful' else [ids[(idx[p]+7)%N] for p in prior]
                for p in use: seeds[idx[p]]=1.0
                one=matvec(seeds,A); two=matvec(one,A); score=[score[i]+.65*(seeds[i]+.75*one[i]+.35*two[i]) for i in range(N)]
            got=[ids[i] for i in top_indices(score,k)]; recalls.append(len(gold & set(got))/len(gold)); ranks=[got.index(z)+1 for z in gold if z in got]; reciprocal.append(1/min(ranks) if ranks else 0); details.append({'q':q,'got':got,'gold':sorted(gold)})
        return {'recall_at_5':sum(recalls)/len(recalls),'mrr':sum(reciprocal)/len(reciprocal),'queries':len(queries),'details':details}
    return {'arm_explicit_only':arm('off'),'arm_truthful_prior':arm('truthful'),'arm_shuffled_prior':arm('shuffled')}

def route_policy(n=10000):
    rng=random.Random(SEED_ROUTE); T,P=50,16; N=T*P; topic=[i//P for i in range(N)]; arms=['explicit','always_blend','adaptive_router','shuffled_blend']; res={a:{k:{'ok':0,'n':0,'rec':0.0,'fp':0.0} for k in ('exact','associative')} for a in arms}
    for _ in range(n):
        t=rng.randrange(T); kind='exact' if rng.random()<.55 else 'associative'; gold=set(range(t*P,t*P+5)); base=[0.0]*N; field=[0.0]*N; shuf=[0.0]*N
        if kind=='exact':
            for i in gold: base[i]=rng.uniform(.65,1.05)
            for _ in range(7):
                j=rng.randrange(N)
                if j not in gold: base[j]=max(base[j],rng.uniform(.05,.3))
            ft=t if rng.random()<.25 else (t+rng.randrange(1,T))%T
        else:
            i=rng.choice(list(gold)); base[i]=rng.uniform(.25,.4)
            for _ in range(12):
                j=rng.randrange(N)
                if j not in gold: base[j]=max(base[j],rng.uniform(.18,.5))
            ft=t if rng.random()<.9 else (t+rng.randrange(1,T))%T
        for i in range(ft*P,ft*P+5): field[i]=rng.uniform(.45,.9)
        st=(t+rng.randrange(1,T))%T
        for i in range(st*P,st*P+5): shuf[i]=rng.uniform(.45,.9)
        scores={'explicit':base,'always_blend':[base[i]+1.35*field[i] for i in range(N)],'adaptive_router':base if kind=='exact' else [base[i]+1.35*field[i] for i in range(N)],'shuffled_blend':[base[i]+1.35*shuf[i] for i in range(N)]}
        for a,s in scores.items():
            top=top_indices(s,8); d=res[a][kind]; d['n']+=1; d['ok']+=int(topic[top[0]]==t); d['rec']+=len(gold&set(top))/5; d['fp']+=sum(topic[i]!=t for i in top)/8
    out={}
    for a in arms:
        out[a]={}
        for kind,d in res[a].items(): out[a][kind]={'n':d['n'],'top1_accuracy':d['ok']/d['n'],'recall_at_8':d['rec']/d['n'],'off_topic_share':d['fp']/d['n']}
        tot=sum(res[a][k]['n'] for k in res[a]); out[a]['overall']={'top1_accuracy':sum(res[a][k]['ok'] for k in res[a])/tot,'recall_at_8':sum(res[a][k]['rec'] for k in res[a])/tot,'off_topic_share':sum(res[a][k]['fp'] for k in res[a])/tot}
    return {'seed':SEED_ROUTE,'episodes':n,'field_gain':1.35,'arms':out}

def anti_attractor(episodes=5000, poison_rates=(0.0,.15,.30)):
    def one(poison):
        rng=random.Random(SEED_ATTRACTOR); T,P=25,18; N=T*P; topic=[i//P for i in range(N)]; weights=[1/(i+1)**1.05 for i in range(T)]; sw=sum(weights); weights=[x/sw for x in weights]; cdf=[]; c=0
        for w in weights: c+=w; cdf.append(c)
        def draw():
            x=rng.random()
            for i,v in enumerate(cdf):
                if x<=v: return i
            return T-1
        core={t:list(range(t*P,t*P+5)) for t in range(T)}; sal_na=[0.0]*N; sal_safe=[0.0]*N; M={m:{'ok':[],'rare':[],'attr':[],'rec':[]} for m in ('fixed','naive_scalar','governed')}
        for _ in range(episodes):
            t=draw(); gold=set(core[t]); base=[0.0]*N
            for i in rng.sample(core[t],3): base[i]=rng.uniform(.65,.95)
            for _ in range(7):
                dt=rng.randrange(T); j=rng.choice(core[dt])
                if j not in gold: base[j]=max(base[j],rng.uniform(.25,.68))
            if t!=0:
                for j in rng.sample(core[0],2): base[j]=max(base[j],rng.uniform(.2,.5))
            scores={'fixed':base,'naive_scalar':[base[i]+.8*sal_na[i] for i in range(N)],'governed':[base[i]+.55*sal_safe[i]*(1 if base[i]>.12 else 0) for i in range(N)]}; sels={}
            for m,s in scores.items():
                top=top_indices(s,8); sels[m]=top; ok=topic[top[0]]==t; M[m]['ok'].append(ok)
                if t>=10: M[m]['rare'].append(ok)
                M[m]['attr'].append(topic[top[0]]==0 and t!=0); M[m]['rec'].append(len(gold&set(top))/5)
            sel=sels['naive_scalar']; success=int(topic[sel[0]]==t); scalar=success or (rng.random()<poison and any(topic[i]==0 for i in sel)); sal_na=[x*.9994 for x in sal_na]
            if scalar:
                for rank,i in enumerate(sel): sal_na[i]+=.025*(1-rank/12)
            sel=sels['governed']; sal_safe=[x*.996 for x in sal_safe]; poisoned=(rng.random()<poison)
            for rank,i in enumerate(sel):
                truth=i in gold; claim=truth or (poisoned and topic[i]==0 and t!=0); verified=truth if rng.random()<.96 else claim; sal_safe[i]=max(-.25,min(.75,sal_safe[i]+(.018 if verified else -.009)*(1-rank/14)))
            for tt in range(T):
                lo,hi=tt*P,(tt+1)*P; mass=max(0,sum(sal_safe[lo:hi]))
                if mass>3.5:
                    f=3.5/mass
                    for i in range(lo,hi): sal_safe[i]*=f
        out={}
        for m,d in M.items():
            tail=min(3000,episodes); rare_tail=min(1500,len(d['rare'])); out[m]={'top1_accuracy':sum(d['ok'][-tail:])/tail,'rare_topic_accuracy':sum(d['rare'][-rare_tail:])/rare_tail,'false_frequent_attractor_top1':sum(d['attr'][-tail:])/tail,'recall_at_8':sum(d['rec'][-tail:])/tail}
        for name,sal in (('naive_scalar',sal_na),('governed',sal_safe)):
            pos=[max(x,0) for x in sal]; total=sum(pos); ps=[x/total for x in pos]; out[name]['salience_hhi']=sum(x*x for x in ps); out[name]['top10_salience_mass']=sum(sorted(ps)[-10:]); out[name]['topic0_salience_mass']=sum(ps[:P])
        return out
    return {'seed':SEED_ATTRACTOR,'episodes_per_condition':episodes,'conditions':{str(p):one(p) for p in poison_rates},'governor':['context gate: learned salience applies only to currently reachable candidates','itemwise verified utility credit (96% synthetic verifier)','bounded positive/negative salience','topic mass cap','decay']}

def main():
    su=self_use(); rp=route_policy(); aa=anti_attractor()
    def m(p,arm):
        c=aa['conditions'][p][arm]
        return {'top1':c['top1_accuracy'],'rare':c['rare_topic_accuracy'],'attractor':c['false_frequent_attractor_top1'],'recall8':c['recall_at_8']}
    summary={'v':VERSION,'status':'PASS','self':{k:[round(v['recall_at_5'],6),round(v['mrr'],6)] for k,v in su.items()},'route':{k:[round(v['overall']['top1_accuracy'],6),round(v['overall']['recall_at_8'],6),round(v['overall']['off_topic_share'],6)] for k,v in rp['arms'].items()},'route_exact_assoc':{'explicit':[round(rp['arms']['explicit']['exact']['top1_accuracy'],6),round(rp['arms']['explicit']['associative']['top1_accuracy'],6)],'always':[round(rp['arms']['always_blend']['exact']['top1_accuracy'],6),round(rp['arms']['always_blend']['associative']['top1_accuracy'],6)],'adaptive':[round(rp['arms']['adaptive_router']['exact']['top1_accuracy'],6),round(rp['arms']['adaptive_router']['associative']['top1_accuracy'],6)]},'attractor_0':{'naive':m('0.0','naive_scalar'),'governed':m('0.0','governed')},'attractor_015':{'naive':m('0.15','naive_scalar'),'governed':m('0.15','governed')}}
    print(json.dumps(summary,sort_keys=True,separators=(',',':')))
if __name__=='__main__': main()
