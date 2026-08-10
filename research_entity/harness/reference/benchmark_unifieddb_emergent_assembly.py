from __future__ import annotations
import hashlib,json,math,random,sqlite3,statistics,time
from .unifieddb_emergent_preprocessor import EmergentAssemblyPreprocessor,PossibilitySpec
N_CLUSTERS=240; CLUSTER_SIZE=50; K=12; MAX_HOPS=3; HOP_DECAY=0.88
BENCHMARK_REVISION='EAP-VPS-1'

def h(v): return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class SyntheticLedger:
    def __init__(self,rows):
        self._rows=rows; self.epoch=1; self.semantic_state_hash=h([(r['domain'],r['key'],r['semantic_hash']) for r in rows])
    def materialized(self): return self._rows

def mkrow(domain,key,value,epistemic='KNOWN',status='CURRENT'):
    sh=h({'domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':status})
    return {'domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':status,'domain_epoch':1,'semantic_hash':sh}
def percentile(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return ys[lo] if lo==hi else ys[lo]*(hi-p)+ys[hi]*(p-lo)
def quality(got,truth):
    got=got[:K]; truth=truth[:K]; ts=set(truth); gs=set(got)
    rec=len(gs&ts)/max(1,len(ts)); prec=len(gs&ts)/max(1,len(gs))
    dcg=sum((1.0 if x in ts else 0.0)/math.log2(i+2) for i,x in enumerate(got)); idcg=sum(1/math.log2(i+2) for i in range(len(truth)))
    return rec,prec,dcg/idcg if idcg else 1.0

def build_dataset():
    rows=[]; con=sqlite3.connect(':memory:')
    con.execute('CREATE TABLE nodes(ref TEXT PRIMARY KEY,domain TEXT,key TEXT,value_json TEXT,epistemic TEXT,status TEXT,domain_epoch INTEGER,semantic_hash TEXT)')
    con.execute('CREATE TABLE edges(src TEXT,dst TEXT,w REAL,relation TEXT,dep_ref TEXT)'); con.execute('CREATE INDEX edge_src ON edges(src)')
    for c in range(N_CLUSTERS):
        refs=[f'semantic:c{c:03d}_n{i:02d}' for i in range(CLUSTER_SIZE)]
        for ref in refs:
            key=ref.split(':',1)[1]; r=mkrow('semantic',key,{'cluster':c,'label':key}); rows.append(r)
            con.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?,?)',(ref,r['domain'],r['key'],json.dumps(r['value'],sort_keys=True,separators=(',',':')),r['epistemic'],r['status'],r['domain_epoch'],r['semantic_hash']))
        depn=0
        for i in range(CLUSTER_SIZE):
            for j,child in enumerate((3*i+1,3*i+2,3*i+3)):
                if child>=CLUSTER_SIZE: continue
                w=(0.97,0.91,0.84)[j]; dk=f'c{c:03d}_e{depn:03d}'; depn+=1; dr='dependency:'+dk
                rows.append(mkrow('dependency',dk,{'source':refs[i],'target':refs[child],'strength':w,'relation_type':'POSSIBILITY'}))
                con.execute('INSERT INTO edges VALUES(?,?,?,?,?)',(refs[i],refs[child],w,'POSSIBILITY',dr))
    con.commit(); return rows,con

def recursive_paths(con,seed):
    sql='''WITH RECURSIVE walk(ref,score,depth,via,relation,dep_ref) AS (SELECT ?,1.0,0,NULL,NULL,NULL UNION ALL SELECT e.dst,walk.score*e.w*?,walk.depth+1,walk.ref,e.relation,e.dep_ref FROM walk JOIN edges e ON e.src=walk.ref WHERE walk.depth<?) SELECT ref,score,depth,via,relation,dep_ref FROM walk ORDER BY score DESC,depth ASC,ref ASC LIMIT ?'''
    return con.execute(sql,(seed,HOP_DECAY,MAX_HOPS,K)).fetchall()
def recursive_refs(con,seed): return [r[0] for r in recursive_paths(con,seed)]
def staged(con,seed):
    paths=recursive_paths(con,seed); refs=[r[0] for r in paths]; qs=','.join('?' for _ in refs)
    nr=con.execute(f'SELECT ref,domain,key,value_json,epistemic,status,domain_epoch,semantic_hash FROM nodes WHERE ref IN ({qs})',refs).fetchall(); by={r[0]:r for r in nr}; selected=[]
    for p in paths:
        n=by[p[0]]; selected.append({'ref':p[0],'domain':n[1],'key':n[2],'value':json.loads(n[3]),'epistemic':n[4],'status':n[5],'source_semantic_hash':n[7],'domain_epoch':n[6],'activation_score':p[1],'hop':p[2],'via_ref':p[3],'relation_type':p[4],'dependency_ref':p[5],'authority':'CONTEXT_ONLY'})
    _=h({'v':'SQL-STAGED','selected':tuple((x['ref'],x['source_semantic_hash'],x['activation_score'],x['hop'],x['dependency_ref']) for x in selected)})
    return [x['ref'] for x in selected]
def key(con,seed):
    r=con.execute('SELECT ref FROM nodes WHERE ref=?',(seed,)).fetchone(); return [] if r is None else [r[0]]
def onehop(con,seed): return [seed]+[r[0] for r in con.execute('SELECT dst FROM edges WHERE src=? ORDER BY w DESC,dst LIMIT 11',(seed,))]

def negative_space():
    rows=[mkrow('semantic','anchor','anchor'),mkrow('semantic','real','real'),mkrow('semantic','conflict','uncertain','CONFLICT'),mkrow('semantic','decoy','decoy'),mkrow('dependency','ar',{'source':'semantic:anchor','target':'semantic:real','strength':.60}),mkrow('dependency','ac',{'source':'semantic:anchor','target':'semantic:conflict','strength':1.0}),mkrow('dependency','cd',{'source':'semantic:conflict','target':'semantic:decoy','strength':1.0})]
    p=EmergentAssemblyPreprocessor(SyntheticLedger(rows)); out=p.compile_active_assembly(PossibilitySpec('neg',seed_refs=('semantic:anchor',),basis_epoch=1,max_items=2,max_hops=2,hop_decay=HOP_DECAY,min_edge_weight=0.0)); gated=[x['ref'] for x in out['selected']]
    scores={'semantic:anchor':1.0,'semantic:real':.60*HOP_DECAY,'semantic:conflict':HOP_DECAY,'semantic:decoy':HOP_DECAY*HOP_DECAY}; ung=[r for r,_ in sorted(((r,s) for r,s in scores.items() if r!='semantic:conflict'),key=lambda z:(-z[1],z[0]))[:2]]; truth={'semantic:anchor','semantic:real'}
    return {'experiment_id':'EXP-GO-EAP-NEGATIVE-SPACE-001','gated_selected':gated,'ungated_counterfactual_selected':ung,'gated_precision_at_2':len(set(gated)&truth)/2,'ungated_precision_at_2':len(set(ung)&truth)/2,'blocked_propagation_refs':out['blocked_propagation_refs']}

def main():
    rows,con=build_dataset(); ledger=SyntheticLedger(rows); p=EmergentAssemblyPreprocessor(ledger); seeds=[f'semantic:c{c:03d}_n00' for c in range(N_CLUSTERS)]; truth={s:recursive_refs(con,s) for s in seeds}
    t=time.perf_counter_ns(); first=p.compile_active_assembly(PossibilitySpec('cold',seed_refs=(seeds[0],),basis_epoch=1,max_items=K,max_hops=MAX_HOPS,frontier_budget=256,hop_decay=HOP_DECAY,min_edge_weight=0.0)); cold=(time.perf_counter_ns()-t)/1000
    methods=(('indexed_key',lambda s:key(con,s)),('indexed_onehop',lambda s:onehop(con,s)),('recursive_sql_refs_only',lambda s:recursive_refs(con,s)),('recursive_sql_staged_assembly',lambda s:staged(con,s)),('eap_hot_assembly',lambda s:[x['ref'] for x in p.compile_active_assembly(PossibilitySpec('b-'+s,seed_refs=(s,),basis_epoch=1,max_items=K,max_hops=MAX_HOPS,frontier_budget=256,hop_decay=HOP_DECAY,min_edge_weight=0.0))['selected']]))
    res={}; order=seeds[:]; random.Random(17).shuffle(order)
    for name,fn in methods:
        ts=[]; qs=[]
        for s in order:
            t=time.perf_counter_ns(); got=fn(s); ts.append((time.perf_counter_ns()-t)/1000); qs.append(quality(got,truth[s]))
        res[name]={'recall_at_12':statistics.mean(x[0] for x in qs),'precision_at_12':statistics.mean(x[1] for x in qs),'ndcg_at_12':statistics.mean(x[2] for x in qs),'latency_us':{'p50':percentile(ts,.5),'p95':percentile(ts,.95),'p99':percentile(ts,.99),'mean':statistics.mean(ts),'min':min(ts),'max':max(ts)}}
    e=res['eap_hot_assembly']['latency_us']['p50']; st=res['recursive_sql_staged_assembly']['latency_us']['p50']; rr=res['recursive_sql_refs_only']['latency_us']['p50']; res['eap_hot_assembly']['speedup_vs_recursive_sql_staged_p50']=st/e; res['eap_hot_assembly']['relative_to_sql_refs_only_p50']=rr/e
    print(json.dumps({'schema_version':'1.0','benchmark':'EAP_SYNTHETIC_MULTI_HOP_MODEL_INPUT','benchmark_revision':BENCHMARK_REVISION,'evidence_class':'SYNTHETIC_EXECUTED_TEST','scope_guard':'Bounded model-facing multi-hop semantic retrieval mechanics only; not universal database superiority.','dataset':{'semantic_nodes':N_CLUSTERS*CLUSTER_SIZE,'dependency_edges':N_CLUSTERS*(CLUSTER_SIZE-1),'queries':len(seeds),'k':K,'max_hops':MAX_HOPS},'preprocessor':{'version':first['preprocessor_version'],'cold_build_plus_first_query_us':cold,'compiled_index_hash':first['compiled_index_hash'],'lexical_index_policy':'LAZY_ON_QUERY_TEXT'},'methods':res,'out_of_box_experiment':negative_space()},indent=2,sort_keys=True))
if __name__=='__main__': main()
