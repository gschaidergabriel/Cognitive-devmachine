from __future__ import annotations
import argparse, hashlib, importlib.util, json, pathlib, random, sqlite3, statistics, time, sys

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pp', HERE/'possibility_preprocessor_v1.py')
pp=importlib.util.module_from_spec(spec); sys.modules['pp']=pp; spec.loader.exec_module(pp)
MIG=(HERE/'RAE_UNIFIEDDB_V10_POSSIBILITY_PREPROCESSOR.sql').read_text()
RESOURCE_KINDS=[f"rk{i}" for i in range(16)]; CAP_CLASSES=[f"cap{i}" for i in range(32)]
GOALS=[f"goal{i}" for i in range(12)]; CONSTRAINTS=[f"constraint{i}" for i in range(10)]; OUTCOMES=[f"outcome{i}" for i in range(20)]
SOURCE_SCHEMA='''
CREATE TABLE resources(resource_id TEXT PRIMARY KEY, kind TEXT, status TEXT, reliability REAL);
CREATE TABLE capabilities(cap_id TEXT PRIMARY KEY, resource_id TEXT, cap_class TEXT, status TEXT, reliability REAL);
CREATE INDEX idx_cap_res ON capabilities(resource_id,status,cap_class);
CREATE TABLE rules(rule_id TEXT PRIMARY KEY, cap_a TEXT, cap_b TEXT, resource_kind TEXT, goal_class TEXT,
 constraint_class TEXT, outcome_kind TEXT, base_utility REAL, risk REAL, evidence REAL);
CREATE INDEX idx_rule_sig ON rules(goal_class,constraint_class,resource_kind,cap_a,cap_b);
CREATE VIRTUAL TABLE rule_fts USING fts5(rule_id UNINDEXED,text);
'''

def make_dataset(seed,n_resources=2500,caps_per_resource=4,n_rules=420):
    rng=random.Random(seed); resources=[]; caps=[]; rules=[]; seen=set()
    for i in range(n_resources):
        rid=f'r{i}'; rk=rng.choice(RESOURCE_KINDS); rr=round(rng.uniform(.72,.999),6); resources.append([rid,rk,'CURRENT',rr])
        for j,cc in enumerate(rng.sample(CAP_CLASSES,caps_per_resource)): caps.append([f'c{i}_{j}',rid,cc,'CURRENT',round(rng.uniform(.65,.999),6)])
    while len(rules)<n_rules:
        a,b=sorted(rng.sample(CAP_CLASSES,2)); key=(a,b,rng.choice(RESOURCE_KINDS),rng.choice(GOALS),rng.choice(CONSTRAINTS))
        if key in seen: continue
        seen.add(key); a,b,rk,g,k=key
        rules.append([f'rule{len(rules)}',a,b,rk,g,k,rng.choice(OUTCOMES),round(rng.uniform(.35,1),6),round(rng.uniform(0,.65),6),round(rng.uniform(.45,1),6)])
    return {'resources':resources,'caps':caps,'rules':rules}

def open_db(data):
    con=sqlite3.connect(':memory:'); con.executescript(MIG); con.executescript(SOURCE_SCHEMA)
    con.executemany('INSERT INTO resources VALUES(?,?,?,?)',data['resources']); con.executemany('INSERT INTO capabilities VALUES(?,?,?,?,?)',data['caps']); con.executemany('INSERT INTO rules VALUES(?,?,?,?,?,?,?,?,?,?)',data['rules'])
    con.executemany('INSERT INTO rule_fts(rule_id,text) VALUES(?,?)',[(r[0],f'{r[4]} {r[5]} {r[3]} {r[1]} {r[2]} {r[6]}') for r in data['rules']]); con.commit(); return con

def sig(g,k): return pp.canonical_context_signature([f'goal:{g}',f'constraint:{k}'])
def relational_score_sql():
    w=pp.DEFAULT_SELECTOR
    return f'''(r.base_utility*{w['utility']} + (((res.reliability + ((ca.reliability+cb.reliability)/2.0))/2.0))*{w['coherence']} + 0.5*{w['urgency']} + r.evidence*{w['evidence']} + r.risk*{w['risk']} + 0.2*{w['cost']})'''
def source_rows(con,g=None,k=None,resource_id=None):
    where=[]; args=[]
    if g is not None: where.append('r.goal_class=?'); args.append(g)
    if k is not None: where.append('r.constraint_class=?'); args.append(k)
    if resource_id is not None: where.append('res.resource_id=?'); args.append(resource_id)
    ws=('WHERE '+' AND '.join(where)) if where else ''
    q=f'''SELECT r.rule_id,res.resource_id,ca.cap_id,cb.cap_id,r.goal_class,r.constraint_class,r.outcome_kind,
    r.base_utility,((res.reliability+((ca.reliability+cb.reliability)/2.0))/2.0) coherence,r.evidence,r.risk
    FROM rules r JOIN resources res ON res.kind=r.resource_kind AND res.status='CURRENT'
    JOIN capabilities ca ON ca.resource_id=res.resource_id AND ca.cap_class=r.cap_a AND ca.status='CURRENT'
    JOIN capabilities cb ON cb.resource_id=res.resource_id AND cb.cap_class=r.cap_b AND cb.status='CURRENT' {ws}'''
    return con.execute(q,args).fetchall()
def make_candidates(rows,epoch=1,graph_epoch=1):
    out=[]
    for rule_id,res,c1,c2,g,k,outcome,utility,coherence,evidence,risk in rows:
        cid=hashlib.sha1(f'{rule_id}|{res}|{c1}|{c2}'.encode()).hexdigest()[:20]; deriv=pp.sha256_text(f'{rule_id}|{res}|{c1}|{c2}|{utility}|{coherence}|{evidence}|{risk}')
        out.append(pp.Candidate(candidate_id=cid,context_signature=sig(g,k),source_epoch=epoch,graph_epoch=graph_epoch,candidate_kind='AFFORDANCE',semantic_refs=[f'goal:{g}',f'constraint:{k}',f'outcome:{outcome}'],graph_refs=[f'claygraph:resource:{res}',f'claygraph:rule:{rule_id}'],hyperposition_refs=[f'hyperposition:goal:{g}:constraint:{k}'],evidence_refs=[f'evidence:{rule_id}'],conflict_refs=[],uncertainty_refs=[],authority_refs=['PROPOSAL_ONLY'],dependency_refs=[rule_id,res,c1,c2],utility=utility,coherence=coherence,urgency=.5,evidence_score=evidence,risk=risk,cost=.2,provenance={'rule':rule_id,'resource':res,'caps':[c1,c2]},derivation_hash=deriv,family_id=f'rule:{rule_id}'))
    return out
def compile_all(con,epoch=1,graph_epoch=1):
    cands=make_candidates(source_rows(con),epoch,graph_epoch); pp.upsert_candidates(con,cands); signatures=sorted(set(c.context_signature for c in cands))
    for s in signatures: pp.compile_packet(con,s,epoch,graph_epoch,top_k=3)
    con.commit(); return len(cands),signatures
def relational(con,g,k,limit=3):
    q=f'''SELECT r.rule_id,res.resource_id,ca.cap_id,cb.cap_id,{relational_score_sql()} score FROM rules r JOIN resources res ON res.kind=r.resource_kind AND res.status='CURRENT' JOIN capabilities ca ON ca.resource_id=res.resource_id AND ca.cap_class=r.cap_a AND ca.status='CURRENT' JOIN capabilities cb ON cb.resource_id=res.resource_id AND cb.cap_class=r.cap_b AND cb.status='CURRENT' WHERE r.goal_class=? AND r.constraint_class=? ORDER BY score DESC,r.evidence DESC,r.risk ASC,r.rule_id ASC LIMIT ?'''
    return con.execute(q,(g,k,limit)).fetchall()
def packet(con,g,k):
    p=pp.read_current_packet(con,sig(g,k));
    if p is None: return []
    return [(x['provenance']['rule'],x['provenance']['resource'],x['provenance']['caps'][0],x['provenance']['caps'][1],x['score']) for x in p['selected']]
def fts(con,g,k,limit=3):
    ruleids=[r[0] for r in con.execute('SELECT rule_id FROM rule_fts WHERE rule_fts MATCH ? LIMIT 12',(f'"{g}" "{k}"',)).fetchall()]; out=[]
    for rule_id in ruleids:
        r=con.execute('SELECT cap_a,cap_b,resource_kind,base_utility FROM rules WHERE rule_id=?',(rule_id,)).fetchone()
        if not r: continue
        a,b,rk,sc=r; x=con.execute('''SELECT res.resource_id,ca.cap_id,cb.cap_id FROM resources res JOIN capabilities ca ON ca.resource_id=res.resource_id AND ca.cap_class=? AND ca.status='CURRENT' JOIN capabilities cb ON cb.resource_id=res.resource_id AND cb.cap_class=? AND cb.status='CURRENT' WHERE res.kind=? AND res.status='CURRENT' LIMIT 1''',(a,b,rk)).fetchone()
        if x: out.append((rule_id,*x,sc))
        if len(out)>=limit: break
    return out
def topkey(rows): return None if not rows else tuple(rows[0][:4])
def stats(xs):
    ys=sorted(xs); idx=lambda p: ys[min(len(ys)-1,int((len(ys)-1)*p))]
    return {'p50_ms':statistics.median(ys),'p95_ms':idx(.95),'p99_ms':idx(.99),'mean_ms':statistics.mean(ys)}
def timed(fn,qs,reps):
    ts=[]; outs=[]
    for _ in range(reps):
        for q in qs:
            t=time.perf_counter_ns(); o=fn(*q); ts.append((time.perf_counter_ns()-t)/1e6); outs.append(o)
    return ts,outs
def packet_selection_map(con,contexts): return {f'{g}|{k}':[x['candidate_id'] for x in (pp.read_current_packet(con,sig(g,k)) or {}).get('selected',[])] for g,k in contexts}
def family_recall_at_3(con,contexts):
    flat_scores=[]; packet_scores=[]; packet_unique=[]
    for g,k in contexts:
        rows=relational(con,g,k,200); gold=[]
        for r in rows:
            if r[0] not in gold: gold.append(r[0])
            if len(gold)>=3: break
        if not gold: continue
        flat=[]
        for r in rows[:3]:
            if r[0] not in flat: flat.append(r[0])
        p=pp.read_current_packet(con,sig(g,k)) or {}; pf=[str(x.get('family_id','')).removeprefix('rule:') for x in p.get('selected',[])]; denom=len(gold)
        flat_scores.append(len(set(flat)&set(gold))/denom); packet_scores.append(len(set(pf)&set(gold))/denom); packet_unique.append(len(set(pf)))
    return {'flat_relational_top3_family_recall':statistics.mean(flat_scores) if flat_scores else None,'possibility_packet_family_recall_at_3':statistics.mean(packet_scores) if packet_scores else None,'possibility_packet_unique_families_mean':statistics.mean(packet_unique) if packet_unique else None}
def run(seed=20260810,n_resources=2500,reps=5):
    data=make_dataset(seed,n_resources=n_resources); con=open_db(data); t=time.perf_counter_ns(); nposs,_=compile_all(con); compile_ms=(time.perf_counter_ns()-t)/1e6
    contexts=[(g,k) for g in GOALS for k in CONSTRAINTS if relational(con,g,k,1)][:120]; gold=[topkey(relational(con,*q,1)) for q in contexts]
    for q in contexts[:10]: relational(con,*q); packet(con,*q); fts(con,*q)
    rt,ro=timed(lambda g,k: relational(con,g,k,3),contexts,reps); pt,po=timed(lambda g,k: packet(con,g,k),contexts,reps); ft,fo=timed(lambda g,k: fts(con,g,k,3),contexts,max(1,reps//2)); acc=lambda outs: sum(topkey(o)==gold[i%len(gold)] for i,o in enumerate(outs))/len(outs)
    family_metrics=family_recall_at_3(con,contexts); total_candidates=con.execute("SELECT count(*) FROM possibility_candidates WHERE status='CURRENT'").fetchone()[0]
    cap_id=con.execute("""SELECT m.member_ref,count(*) n FROM possibility_candidate_members m JOIN capabilities c ON c.cap_id=m.member_ref GROUP BY m.member_ref ORDER BY n DESC LIMIT 1""").fetchone()[0]
    res_id,old_rel=con.execute('SELECT resource_id,reliability FROM capabilities WHERE cap_id=?',(cap_id,)).fetchone(); con.execute('UPDATE capabilities SET reliability=? WHERE cap_id=?',(old_rel*.51,cap_id)); con.commit()
    for row in data['caps']:
        if row[0]==cap_id: row[4]=old_rel*.51; break
    t=time.perf_counter_ns(); packet_sigs=pp.invalidate_ref(con,cap_id,2,'CAPABILITY_DELTA'); cand_sigs=pp.retire_candidates_by_ref(con,cap_id); refreshed=make_candidates(source_rows(con,resource_id=res_id),2,2); pp.upsert_candidates(con,refreshed); touched=sorted(set(packet_sigs)|set(cand_sigs)|set(c.context_signature for c in refreshed))
    for s in touched: pp.compile_packet(con,s,2,2,top_k=3)
    con.commit(); targeted_ms=(time.perf_counter_ns()-t)/1e6; targeted_map=packet_selection_map(con,contexts)
    con2=open_db(data); t=time.perf_counter_ns(); compile_all(con2,2,2); full_ms=(time.perf_counter_ns()-t)/1e6; full_map=packet_selection_map(con2,contexts)
    return {'seed':seed,'resources':n_resources,'capabilities':n_resources*4,'rules':len(data['rules']),'prepared_candidates':nposs,'contexts':len(contexts),'initial_compile_ms':compile_ms,'family_retrieval':family_metrics,'methods':{'fts5_document_retrieval':{'accuracy_at_1':acc(fo[:len(contexts)]),**stats(ft)},'relational_query_time_derivation':{'accuracy_at_1':acc(ro[:len(contexts)]),**stats(rt)},'possibility_packet_hot_read':{'accuracy_at_1':acc(po[:len(contexts)]),**stats(pt)}},'update':{'changed_capability':cap_id,'affected_signatures':len(touched),'targeted_refresh_ms':targeted_ms,'full_rebuild_ms':full_ms,'selection_equivalent_to_full_rebuild':targeted_map==full_map,'retired_candidate_fraction':len(con.execute("SELECT candidate_id FROM possibility_candidates WHERE status='STALE'").fetchall())/max(1,total_candidates)}}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--seed',type=int,default=20260810); ap.add_argument('--resources',type=int,default=2500); ap.add_argument('--reps',type=int,default=5); a=ap.parse_args(); print(json.dumps(run(a.seed,a.resources,a.reps),indent=2,sort_keys=True))
