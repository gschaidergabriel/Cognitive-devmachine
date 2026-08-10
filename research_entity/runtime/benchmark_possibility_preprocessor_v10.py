from __future__ import annotations
import sqlite3, random, time, statistics, platform, sys
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
HERE=Path(__file__).resolve().parent
runtime=HERE/'possibility_preprocessor_v10.py'; schema_path=HERE/'RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql'
if not runtime.exists(): runtime=Path('/tmp/possibility_preprocessor_v10.py')
if not schema_path.exists(): schema_path=Path('/tmp/RAE_UNIFIEDDB_V10_POSSIBILITY_COMPILER.sql')
spec=spec_from_file_location('u10',str(runtime)); m=module_from_spec(spec); sys.modules['u10']=m; spec.loader.exec_module(m)
N=6000; DEG=7; CONTEXTS=120; DEPTH=3; K=20; SEED=73419
rng=random.Random(SEED)
conn=sqlite3.connect(':memory:')
conn.execute('pragma foreign_keys=on'); conn.execute('pragma journal_mode=memory'); conn.execute('pragma synchronous=off')
conn.executescript(schema_path.read_text())
conn.executescript('''
CREATE TABLE edges(src TEXT, dst TEXT, w REAL, PRIMARY KEY(src,dst));
CREATE INDEX edges_src ON edges(src);
CREATE TABLE cand(ref TEXT PRIMARY KEY, utility REAL, available TEXT, authority TEXT, modality TEXT);
''')
nodes=[f'n{i}' for i in range(N)]; meta={}
for n in nodes:
    cm=m.CandidateMeta(utility=0.35+rng.random()*0.65, facets={
        'available':'yes' if rng.random()<.82 else 'no',
        'authority':'ok' if rng.random()<.88 else 'blocked',
        'modality':rng.choice(['text','code','tool'])})
    meta[n]=cm
    conn.execute('insert into cand values(?,?,?,?,?)',(n,cm.utility,cm.facets['available'],cm.facets['authority'],cm.facets['modality']))
edges=[]
for i,src in enumerate(nodes):
    for _ in range(DEG):
        j=rng.randrange(N)
        if j==i: continue
        dst=nodes[j]; w=0.55+rng.random()*0.45
        try:
            conn.execute('insert into edges values(?,?,?)',(src,dst,w)); edges.append(m.GraphEdge(src,dst,w,f'e:{src}:{dst}'))
        except sqlite3.IntegrityError: pass
conn.commit()

def sql_query(anchor, modality):
    return conn.execute('''
    WITH RECURSIVE walk(node, depth, pscore) AS (
      SELECT ?,0,1.0
      UNION ALL
      SELECT e.dst,w.depth+1,w.pscore*e.w FROM walk w JOIN edges e ON e.src=w.node WHERE w.depth<?
    ), best AS (SELECT node,MAX(pscore) p FROM walk GROUP BY node)
    SELECT c.ref, MAX(best.p*c.utility) s FROM best JOIN cand c ON c.ref=best.node
    WHERE c.available='yes' AND c.authority='ok' AND c.modality=?
    GROUP BY c.ref ORDER BY s DESC,c.ref LIMIT ?
    ''',(anchor,DEPTH,modality,K)).fetchall()

compiler=m.PossibilityCompiler(conn,m.CompilerConfig(max_depth=DEPTH,max_witnesses_per_candidate=4,max_path_states=250000))
now='2026-08-10T00:00:00Z'; compiler.install_spec(now)
compiler.start_field_epoch(field_epoch=1,source_epoch=101,graph_epoch=77,input_hash='bench',built_at=now,metadata={'seed':SEED,'N':N,'degree':DEG})
compiler.build_facets(field_epoch=1,candidate_meta=meta,source_epoch=101,created_at=now)
anchors=rng.sample(nodes, CONTEXTS); compile_ms=[]
for a in anchors:
    r=compiler.compile_anchor(field_epoch=1,source_epoch=101,graph_epoch=77,anchor_ref=a,edges=edges,candidate_meta=meta,created_at=now)
    compile_ms.append(r['compile_ms'])
compiler.complete_field_epoch(1,now); conn.commit()
for a in anchors[:10]:
    mod=rng.choice(['text','code','tool']); sql_query(a,mod); compiler.query(anchor_ref=a,required_facets={'available':'yes','authority':'ok','modality':mod},limit=K,expected_source_epoch=101,expected_graph_epoch=77)
lat_sql=[]; lat_u10=[]; exact=0; recalls=[]
for idx,a in enumerate(anchors):
    mod=['text','code','tool'][idx%3]
    t=time.perf_counter_ns(); b=sql_query(a,mod); lat_sql.append((time.perf_counter_ns()-t)/1e6)
    t=time.perf_counter_ns(); q=compiler.query(anchor_ref=a,required_facets={'available':'yes','authority':'ok','modality':mod},limit=K,expected_source_epoch=101,expected_graph_epoch=77); lat_u10.append((time.perf_counter_ns()-t)/1e6)
    br=[x[0] for x in b]; qr=[x[0] for x in q]; exact += br==qr
    recalls.append(len(set(br)&set(qr))/max(1,len(br)))
def pct(a,p): return sorted(a)[min(len(a)-1,int((len(a)-1)*p))]
summary={
 'nodes':N,'edges':len(edges),'contexts':CONTEXTS,'depth':DEPTH,'k':K,'seed':SEED,
 'compile_total_ms':round(sum(compile_ms),3),'compile_median_ms':round(statistics.median(compile_ms),4),
 'recursive_sql_p50_ms':round(statistics.median(lat_sql),4),'recursive_sql_p95_ms':round(pct(lat_sql,.95),4),
 'u10_p50_ms':round(statistics.median(lat_u10),4),'u10_p95_ms':round(pct(lat_u10,.95),4),
 'speedup_p50':round(statistics.median(lat_sql)/statistics.median(lat_u10),2),
 'speedup_p95':round(pct(lat_sql,.95)/pct(lat_u10,.95),2),
 'exact_top20_fraction':round(exact/CONTEXTS,4),'recall_at_20':round(statistics.mean(recalls),4),
 'sqlite':sqlite3.sqlite_version,'python':sys.version.split()[0],'platform':platform.platform(),
}
print(summary)
compiler.start_field_epoch(field_epoch=2,source_epoch=102,graph_epoch=78,input_hash='incomplete',built_at=now)
assert conn.execute('select field_epoch from v_clay_current_possibility_field_epoch').fetchone()[0]==1
try:
    compiler.query(anchor_ref=anchors[0],required_facets={'available':'yes'},expected_source_epoch=102)
except m.TruncatedField:
    print('epoch_guard_ok', True)
else:
    print('epoch_guard_ok', False)
print('lkg_shadow_build_ok', conn.execute('select field_epoch from v_clay_current_possibility_field_epoch').fetchone()[0]==1)
receipt={'schema_version':'1.0','benchmark_id':'U10-POSSIBILITY-PREPROCESSOR-SYNTH-001','truth_class':'LOCAL_EXECUTION_PRIMARY_SYNTHETIC_SCOPE_ONLY','summary':summary,'raw':{'compile_ms':compile_ms,'recursive_sql_ms':lat_sql,'u10_ms':lat_u10,'recall_at_20':recalls},'controls':{'matched_anchor_and_facets':True,'recursive_sql_is_ground_truth_for_this_fixture':True,'real_frank_replay':False,'vps':False}}
import json
out=Path('/tmp/U10_POSSIBILITY_COMPILER_BENCHMARK_RECEIPT.json'); out.write_text(json.dumps(receipt,indent=2,sort_keys=True)); print('receipt',out)
