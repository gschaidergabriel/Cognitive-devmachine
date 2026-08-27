#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, math, os, random, sqlite3, statistics, time
from collections import defaultdict
from pathlib import Path
import numpy as np

SEED=20260810
random.seed(SEED); np.random.seed(SEED)
OUT=Path('/mnt/data/unifieddb_u11_deep/EXPERIMENT_RESULTS.json')

def q(xs,p): return float(np.quantile(np.asarray(xs,dtype=np.float64),p))
def stats_us(ns):
    a=np.asarray(ns,dtype=np.float64)/1000.0
    return {'n':int(len(a)),'p50':q(a,.5),'p95':q(a,.95),'p99':q(a,.99),'mean':float(a.mean())}

def receipt_lattice_experiment(n_mut=10000,n_lat=5000):
    con=sqlite3.connect(':memory:')
    con.executescript('''
    PRAGMA foreign_keys=ON;
    CREATE TABLE current_execution(singleton INTEGER PRIMARY KEY CHECK(singleton=1),execution_id TEXT NOT NULL,lease_epoch INTEGER NOT NULL,state TEXT NOT NULL);
    INSERT INTO current_execution VALUES(1,'exec-current',77,'ACTIVE');
    CREATE TABLE receipt(receipt_id TEXT PRIMARY KEY,kind TEXT NOT NULL,state_epoch INTEGER NOT NULL,execution_id TEXT NOT NULL,lease_epoch INTEGER NOT NULL,payload_hash TEXT NOT NULL,verified INTEGER NOT NULL CHECK(verified IN(0,1)));
    CREATE TABLE edge(child_id TEXT NOT NULL,parent_id TEXT NOT NULL,edge_kind TEXT NOT NULL,PRIMARY KEY(child_id,parent_id,edge_kind),FOREIGN KEY(child_id) REFERENCES receipt(receipt_id),FOREIGN KEY(parent_id) REFERENCES receipt(receipt_id));
    ''')
    kinds=['GWT_USE','EFFECT_ATTEMPT','VERIFIED_OUTCOME','CAUSAL_CREDIT','ADMITTED_DELTA','REENTRY']; ids=[]
    for i,k in enumerate(kinds):
        rid=f'r{i}-{k.lower()}'; ids.append(rid); ph=hashlib.sha256(f'{rid}|{k}|payload'.encode()).hexdigest(); con.execute('INSERT INTO receipt VALUES(?,?,?,?,?,?,1)',(rid,k,100+i,'exec-current',77,ph))
    edge_kinds=['CAUSES_ATTEMPT','VERIFIES','CREDITS','ADMITS','REENTERS']
    for child,parent,ek in zip(ids[1:],ids[:-1],edge_kinds): con.execute('INSERT INTO edge VALUES(?,?,?)',(child,parent,ek))
    con.commit(); expected=list(zip(kinds,ids)); expected_edges=list(zip(ids[1:],ids[:-1],edge_kinds))
    def baseline_accept(refs,execution_id,lease_epoch): return bool(execution_id and lease_epoch and all(refs))
    def candidate_accept(refs,execution_id,lease_epoch):
        row=con.execute('SELECT execution_id,lease_epoch,state FROM current_execution WHERE singleton=1').fetchone()
        if not row or row!=(execution_id,lease_epoch,'ACTIVE') or len(refs)!=len(kinds): return False
        for (kind,_),rid in zip(expected,refs):
            r=con.execute('SELECT kind,execution_id,lease_epoch,verified FROM receipt WHERE receipt_id=?',(rid,)).fetchone()
            if r!=(kind,execution_id,lease_epoch,1): return False
        for child,parent,ek in expected_edges:
            if con.execute('SELECT 1 FROM edge WHERE child_id=? AND parent_id=? AND edge_kind=?',(child,parent,ek)).fetchone() is None: return False
        return True
    assert candidate_accept(ids,'exec-current',77)
    mutation_types=['fabricated_ref','stale_lease','wrong_execution','cross_kind','missing_ref','unverified_outcome','missing_edge']; false_accept_base=false_accept_candidate=0; counts=defaultdict(int)
    for j in range(n_mut):
        t=mutation_types[j%len(mutation_types)]; counts[t]+=1; refs=ids.copy(); ex='exec-current'; le=77; cleanup=None
        if t=='fabricated_ref': refs[random.randrange(len(refs))]='fake-'+str(j)
        elif t=='stale_lease': le=76
        elif t=='wrong_execution': ex='exec-other'
        elif t=='cross_kind': refs[0],refs[1]=refs[1],refs[0]
        elif t=='missing_ref': refs[random.randrange(len(refs))]=''
        elif t=='unverified_outcome':
            con.execute("UPDATE receipt SET verified=0 WHERE kind='VERIFIED_OUTCOME'"); cleanup=lambda: con.execute("UPDATE receipt SET verified=1 WHERE kind='VERIFIED_OUTCOME'")
        elif t=='missing_edge':
            e=expected_edges[2]; con.execute('DELETE FROM edge WHERE child_id=? AND parent_id=? AND edge_kind=?',e); cleanup=lambda e=e: con.execute('INSERT INTO edge VALUES(?,?,?)',e)
        if baseline_accept(refs,ex,le): false_accept_base+=1
        if candidate_accept(refs,ex,le): false_accept_candidate+=1
        if cleanup: cleanup()
    con.commit(); lat=[]
    for _ in range(n_lat):
        t0=time.perf_counter_ns(); ok=candidate_accept(ids,'exec-current',77); lat.append(time.perf_counter_ns()-t0)
        if not ok: raise AssertionError('valid chain rejected')
    return {'mutations':n_mut,'mutation_counts':dict(counts),'baseline_false_accept_rate':false_accept_base/n_mut,'candidate_false_accept_rate':false_accept_candidate/n_mut,'valid_chain_accept':True,'candidate_validation_latency_us':stats_us(lat)}

def pkm_experiment(m=256,dhalf=16,nq=180,topk=4,noises=(.06,.12,.18,.28)):
    rng=np.random.default_rng(SEED+1); a=rng.normal(size=(m,dhalf)).astype(np.float32); a/=np.linalg.norm(a,axis=1,keepdims=True); b=rng.normal(size=(m,dhalf)).astype(np.float32); b/=np.linalg.norm(b,axis=1,keepdims=True)
    full=np.concatenate([np.repeat(a,m,axis=0),np.tile(b,(m,1))],axis=1)/math.sqrt(2); rows=[]
    for noise in noises:
        targets=rng.integers(0,m*m,size=nq); queries=full[targets]+rng.normal(scale=noise,size=(nq,2*dhalf)).astype(np.float32); queries/=np.linalg.norm(queries,axis=1,keepdims=True); brute_lat=[]; pkm_lat=[]; brute_correct=pkm_correct=parity=0
        for qi,target in zip(queries,targets):
            t0=time.perf_counter_ns(); idx=int(np.argmax(full@qi)); brute_lat.append(time.perf_counter_ns()-t0); brute_correct+=(idx==target); q1=qi[:dhalf]*math.sqrt(2); q2=qi[dhalf:]*math.sqrt(2); t0=time.perf_counter_ns(); s1=a@q1; s2=b@q2; i1=np.argpartition(s1,-topk)[-topk:]; i2=np.argpartition(s2,-topk)[-topk:]; best_score=-1e9; best=-1
            for x in i1:
                for y in i2:
                    score=(s1[x]+s2[y])/math.sqrt(2)
                    if score>best_score: best_score=score; best=int(x*m+y)
            pkm_lat.append(time.perf_counter_ns()-t0); pkm_correct+=(best==target); parity+=(best==idx)
        rows.append({'noise_std':noise,'queries':nq,'bruteforce_recall_at_1_to_planted_target':brute_correct/nq,'pkm_recall_at_1_to_planted_target':pkm_correct/nq,'pkm_parity_with_bruteforce_top1':parity/nq,'latency_us':{'bruteforce':stats_us(brute_lat),'pkm':stats_us(pkm_lat)}})
    randkeys=rng.normal(size=full.shape).astype(np.float32); randkeys/=np.linalg.norm(randkeys,axis=1,keepdims=True); targets=rng.integers(0,m*m,size=200); qs=randkeys[targets]+rng.normal(scale=.06,size=(len(targets),2*dhalf)).astype(np.float32); qs/=np.linalg.norm(qs,axis=1,keepdims=True); pkm_hit=brute_hit=0
    for qi,target in zip(qs,targets):
        brute=int(np.argmax(randkeys@qi)); brute_hit+=(brute==target); q1=qi[:dhalf]*math.sqrt(2); q2=qi[dhalf:]*math.sqrt(2); s1=a@q1; s2=b@q2; i1=np.argpartition(s1,-topk)[-topk:]; i2=np.argpartition(s2,-topk)[-topk:]; best=max(((s1[x]+s2[y])/math.sqrt(2),int(x*m+y)) for x in i1 for y in i2)[1]; pkm_hit+=(best==target)
    return {'slots':m*m,'dimension':2*dhalf,'subkeys_per_half':m,'candidate_slots_per_query':topk*topk,'index_float_count':{'full_keys':int(full.size),'product_subkeys':int(a.size+b.size)},'index_compression_ratio_full_to_product':float(full.size/(a.size+b.size)),'structured_manifold':rows,'nonproduct_control':{'queries':len(targets),'bruteforce_recall_at_1':brute_hit/len(targets),'pkm_recall_at_1':pkm_hit/len(targets)}}

def adaptive_manifold_router_experiment(m=128,dhalf=16,cal_each=180,test_each=300,topk=4,noise=.10,safety_margin=.0):
    rng=np.random.default_rng(SEED+5); a=rng.normal(size=(m,dhalf)).astype(np.float32); a/=np.linalg.norm(a,axis=1,keepdims=True); b=rng.normal(size=(m,dhalf)).astype(np.float32); b/=np.linalg.norm(b,axis=1,keepdims=True); prod=np.concatenate([np.repeat(a,m,axis=0),np.tile(b,(m,1))],axis=1)/math.sqrt(2); rand=rng.normal(size=prod.shape).astype(np.float32); rand/=np.linalg.norm(rand,axis=1,keepdims=True); allkeys=np.concatenate([prod,rand],axis=0)
    def make(kind,n):
        if kind=='product': t=rng.integers(0,len(prod),size=n); q=prod[t]+rng.normal(scale=noise,size=(n,2*dhalf)).astype(np.float32); true=t
        else: t=rng.integers(0,len(rand),size=n); q=rand[t]+rng.normal(scale=noise,size=(n,2*dhalf)).astype(np.float32); true=t+len(prod)
        q/=np.linalg.norm(q,axis=1,keepdims=True); return q,true
    def gate_score(qi): q1=qi[:dhalf]*math.sqrt(2); q2=qi[dhalf:]*math.sqrt(2); return float(np.max(a@q1)+np.max(b@q2))
    cp,_=make('product',cal_each); cr,_=make('random',cal_each); sp=np.array([gate_score(x) for x in cp]); sr=np.array([gate_score(x) for x in cr]); threshold=float(sr.max()+safety_margin+1e-6); cal_product_route=float(np.mean(sp>threshold)); cal_random_false_route=float(np.mean(sr>threshold)); qp,tp=make('product',test_each); qr,tr=make('random',test_each); Q=np.concatenate([qp,qr]); T=np.concatenate([tp,tr]); K=np.array([1]*test_each+[0]*test_each); order=rng.permutation(len(Q)); Q=Q[order]; T=T[order]; K=K[order]; brute_lat=[]; hybrid_lat=[]; brute_ok=hybrid_ok=pkm_routes=false_routes=0
    for qi,target,isprod in zip(Q,T,K):
        t0=time.perf_counter_ns(); brute=int(np.argmax(allkeys@qi)); brute_lat.append(time.perf_counter_ns()-t0); brute_ok+=int(brute==target); t0=time.perf_counter_ns(); q1=qi[:dhalf]*math.sqrt(2); q2=qi[dhalf:]*math.sqrt(2); s1=a@q1; s2=b@q2; score=float(np.max(s1)+np.max(s2))
        if score>threshold: pkm_routes+=1; false_routes+=int(not bool(isprod)); i1=np.argpartition(s1,-topk)[-topk:]; i2=np.argpartition(s2,-topk)[-topk:]; pred=max(((s1[x]+s2[y])/math.sqrt(2),int(x*m+y)) for x in i1 for y in i2)[1]
        else: pred=int(np.argmax(allkeys@qi))
        hybrid_lat.append(time.perf_counter_ns()-t0); hybrid_ok+=int(pred==target)
    return {'safety_margin':safety_margin,'product_slots':len(prod),'random_slots':len(rand),'total_slots':len(allkeys),'noise_std':noise,'calibration':{'threshold':threshold,'product_route_rate':cal_product_route,'random_false_route_rate':cal_random_false_route,'product_score_p05':float(np.quantile(sp,.05)),'random_score_max':float(sr.max())},'heldout':{'queries':len(Q),'product_fraction':.5,'pkm_route_rate':pkm_routes/len(Q),'false_pkm_route_rate':false_routes/len(Q),'bruteforce_recall_to_planted_target':brute_ok/len(Q),'hybrid_recall_to_planted_target':hybrid_ok/len(Q),'hybrid_parity_with_bruteforce_recall':bool(hybrid_ok==brute_ok),'latency_us':{'bruteforce':stats_us(brute_lat),'hybrid':stats_us(hybrid_lat)}}}

def hdc_experiment(D=4096,entity_count=900,loads=(25,50,100,200,300),trials=3):
    rng=np.random.default_rng(SEED+2); src=rng.choice(np.array([-1,1],dtype=np.int8),size=(entity_count,D)); tgt=rng.choice(np.array([-1,1],dtype=np.int8),size=(entity_count,D)); rel=rng.choice(np.array([-1,1],dtype=np.int8),size=D); results=[]
    for load in loads:
        recalls=[]; query_lat=[]
        for rep in range(trials):
            ids=rng.choice(entity_count,size=load,replace=False); target_ids=rng.choice(entity_count,size=load,replace=False); memory=np.zeros(D,dtype=np.int32)
            for s,t in zip(ids,target_ids): memory += src[s].astype(np.int32)*rel.astype(np.int32)*tgt[t].astype(np.int32)
            correct=0
            for s,t in list(zip(ids,target_ids))[:min(load,80)]:
                t0=time.perf_counter_ns(); probe=memory*src[s].astype(np.int32)*rel.astype(np.int32); scores=tgt[target_ids].astype(np.int32)@probe; pred=int(target_ids[int(np.argmax(scores))]); query_lat.append(time.perf_counter_ns()-t0); correct+=(pred==t)
            recalls.append(correct/min(load,80))
        results.append({'load':load,'recall_at_1_mean':float(np.mean(recalls)),'recall_at_1_min':float(np.min(recalls)),'latency_us':stats_us(query_lat)})
    return {'dimension':D,'entity_pool':entity_count,'trials_per_load':trials,'results':results,'memory_bytes_int32_accumulator':D*4}

def incremental_projection_experiment(n=30000,tags=512,tags_per=4,batch=300,rounds=10):
    rng=np.random.default_rng(SEED+3); records=[set(map(int,rng.choice(tags,size=tags_per,replace=False))) for _ in range(n)]
    def rebuild(rs):
        idx=[set() for _ in range(tags)]
        for rid,ts in enumerate(rs):
            for t in ts: idx[t].add(rid)
        return idx
    t0=time.perf_counter_ns(); idx=rebuild(records); initial=time.perf_counter_ns()-t0; full=[]; inc=[]; equal=[]
    for _ in range(rounds):
        changed=list(map(int,rng.choice(n,size=batch,replace=False))); newvals={rid:set(map(int,rng.choice(tags,size=tags_per,replace=False))) for rid in changed}; t0=time.perf_counter_ns()
        for rid,new in newvals.items():
            old=records[rid]
            for t in old-new: idx[t].discard(rid)
            for t in new-old: idx[t].add(rid)
            records[rid]=new
        inc.append(time.perf_counter_ns()-t0); t0=time.perf_counter_ns(); rebuilt=rebuild(records); full.append(time.perf_counter_ns()-t0); equal.append(all(idx[t]==rebuilt[t] for t in range(tags)))
    return {'records':n,'tags':tags,'batch_updates':batch,'rounds':rounds,'initial_rebuild_ms':initial/1e6,'incremental_latency_us':stats_us(inc),'full_rebuild_latency_us':stats_us(full),'median_speedup_full_over_incremental':float(np.median(np.asarray(full)/np.asarray(inc))),'all_projection_equivalence_checks_passed':bool(all(equal))}

def merkle_segment_experiment(n=20000,segment=512):
    rng=np.random.default_rng(SEED+4); payloads=[rng.bytes(48) for _ in range(n)]
    def H(x): return hashlib.sha256(x).digest()
    chain=[]; root=b'\x00'*32; t=[]
    for p in payloads: t0=time.perf_counter_ns(); root=H(root+H(p)); t.append(time.perf_counter_ns()-t0); chain.append(root)
    def tree_root(leaves):
        level=[H(b'\x00'+x) for x in leaves]
        while len(level)>1:
            if len(level)%2: level.append(level[-1])
            level=[H(b'\x01'+level[i]+level[i+1]) for i in range(0,len(level),2)]
        return level[0] if level else H(b'')
    seg_lat=[]; roots=[]
    for i in range(0,n,segment): leaves=payloads[i:i+segment]; t0=time.perf_counter_ns(); roots.append(tree_root(leaves)); seg_lat.append(time.perf_counter_ns()-t0)
    j=n//2; si=j//segment; altered=list(payloads[si*segment:(si+1)*segment]); k=j-si*segment; altered[k]=b'X'+altered[k][1:]; tamper_detected=tree_root(altered)!=roots[si]
    return {'events':n,'segment_size':segment,'hash_chain_append_latency_us':stats_us(t),'merkle_segment_build_latency_us':stats_us(seg_lat),'segments':len(roots),'inclusion_proof_sibling_hashes_per_full_segment':int(math.log2(segment)),'inclusion_proof_bytes_per_full_segment':int(math.log2(segment))*32,'tamper_detected':tamper_detected}

def main():
    result={'schema_version':'1.0','run_seed':SEED,'evidence_class':'LOCAL_SYNTHETIC_EXECUTION_NOT_TARGET_VPS','receipt_lattice':receipt_lattice_experiment(),'product_key_memory':pkm_experiment(),'adaptive_manifold_router':adaptive_manifold_router_experiment(),'hyperdimensional_relation_field':hdc_experiment(),'incremental_projection':incremental_projection_experiment(),'merkle_segment_spine':merkle_segment_experiment()}
    OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2,sort_keys=True))
if __name__=='__main__': main()
