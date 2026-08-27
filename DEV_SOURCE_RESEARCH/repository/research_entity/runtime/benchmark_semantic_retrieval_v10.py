#!/usr/bin/env python3
"""Deterministic benchmark for Clay UnifiedDB + ClayGraph semantic access candidate.

Scope:
- Representative assistant semantic-retrieval workload, NOT a universal DB benchmark.
- Baseline: SQLite FTS5 + CURRENT filter + metadata authority ordering.
- V1: query-time alias/graph expansion.
- V2: typed semantic seed -> materialized access path fast path, FTS/RRF fallback.
"""
from __future__ import annotations
import json, os, platform, random, re, sqlite3, statistics, tempfile, time
from semantic_retrieval_runtime_v10 import SemanticRetrievalFabric

SEED=42
random.seed(SEED)
TOPICS = {
"unifieddb":(["shared semantic state","canonical state plane","semantic database","state ledger","persistent semantic memory"],"unifieddb semantic state epochs provenance transaction replay canonical persistence query"),
"claygraph":(["derived sparse topology","association graph","semantic dependency graph","coupling topology","graph projection"],"claygraph derived sparse topology dependency edges graph epoch projection activation"),
"gwt":(["workspace broadcast","global workspace","broadcast causal loop","ignition workspace","receiver broadcast"],"gwt global workspace ignition broadcast receiver reconstruction use outcome reentry"),
"needle":(["reflex router","tool selector","routing organ","fast routing","open set router"],"needle routing reflex tool selection confidence abstention open set latency authority"),
"hyperposition":(["unresolved alternatives","alternative relation","higher order codependency","competing routes","phase alternatives"],"hyperposition alternatives higher order codependencies phase timescale unresolved competing routes"),
"retina":(["vision pipeline","visual percept path","digital vision front end","pixel semantic bridge","visual field"],"digital retina visual percept perceptual field pixels embeddings provenance attention"),
"classifier":(["micro visual learner","personal visual classifier","adaptive familiarity learner","prototype learner","known unknown visual"],"adaptive micro visual classifier prototype learner gold silver bronze calibration open set rollback"),
"provenance":(["source lineage","evidence ancestry","origin tracking","causal identity","source receipt"],"provenance source lineage evidence ancestry origin actor ingested adjudicated receipt hash"),
"work":(["dynamic queue","revisioned work","system possibility table","worker lease","capability scheduler"],"dynamic work queue revision lease scheduler capability possibility table priority collision"),
"recovery":(["last known good","rollback health","continuity contract","fail closed recovery","restart rebuild"],"recovery continuity health liveness readiness rollback restart rebuild quarantine last known good"),
"claycode":(["native semantic language","typed cognitive ir","clay compiler","semantic authority language","machine cognition syntax"],"claycode parser typed ir compiler runtime ffi semantic authority clay native"),
"loopcore":(["one cognitive module","recurrent loop core","single executable cognition","loop of loops","whole causal cycle"],"loop core recurrent cognition one module causal cycle appraisal gating workspace needle outcome learning reentry"),
"reentry":(["closed loop return","outcome feedback","provenance bound feedback","causal return path","learning return"],"reentry provenance outcome causal credit learning semantic delta truthful shuffled no reentry"),
"identity":(["researcher subject separation","frank clay boundary","temporary worker identity","andreas interface boundary","proposal only harness"],"identity research entity clay frank separate andreas proposal only harness authority worker"),
"ubuntu":(["target developer system","linux target host","andreas pc target","release operating system","ubuntu developer host"],"ubuntu linux developer system target host andreas pc release v0.1"),
"training":(["paid model gate","owner training authorization","final lora wait","frozen corpus gate","training decision"],"training lora owner authorization frozen corpus wait paid final model")
}
RELATED=[("unifieddb","provenance"),("unifieddb","recovery"),("claygraph","gwt"),("claygraph","hyperposition"),("gwt","reentry"),("needle","loopcore"),("retina","classifier"),("classifier","recovery"),("work","provenance"),("claycode","loopcore"),("loopcore","reentry"),("identity","loopcore"),("ubuntu","recovery")]
TOKEN_RE=re.compile(r"[a-z0-9]+",re.I)
def norm(s): return " ".join(x.group(0).lower() for x in TOKEN_RE.finditer(s))
def pct(vals,p):
    vals=sorted(vals); return vals[min(len(vals)-1,max(0,int((len(vals)-1)*p)))]
def authority(ep): return {"PROJECT_OWNER_FIXED":3,"VALIDATED_RESEARCH":1}.get(ep,0)

def build_db(path: str):
    con=sqlite3.connect(path); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=NORMAL"); con.execute("PRAGMA temp_store=MEMORY")
    con.executescript("""
    CREATE TABLE records(record_id TEXT PRIMARY KEY,topic TEXT,status TEXT,epistemic_class TEXT,updated_seq INTEGER,text TEXT);
    CREATE INDEX idx_records_topic_status ON records(topic,status);
    CREATE TABLE aliases(alias TEXT PRIMARY KEY,topic TEXT,weight REAL);
    CREATE TABLE edges(source_topic TEXT,target_record_id TEXT,relation TEXT,weight REAL,PRIMARY KEY(source_topic,target_record_id,relation));
    CREATE VIRTUAL TABLE fts USING fts5(record_id UNINDEXED,text,tokenize='unicode61',prefix='2 3');
    CREATE TABLE semantic_query_seeds(seed_version_id TEXT PRIMARY KEY,seed_id TEXT NOT NULL,normalized_key TEXT NOT NULL,logical_id TEXT NOT NULL,seed_class TEXT NOT NULL,confidence REAL NOT NULL,provenance_clay TEXT NOT NULL,source_epoch INTEGER NOT NULL,graph_epoch INTEGER,status TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
    CREATE UNIQUE INDEX idx_semantic_query_seed_id_current ON semantic_query_seeds(seed_id) WHERE status='CURRENT';
    CREATE UNIQUE INDEX idx_semantic_query_key_current ON semantic_query_seeds(normalized_key) WHERE status='CURRENT';
    CREATE INDEX idx_semantic_query_seed_lookup ON semantic_query_seeds(normalized_key,logical_id,confidence DESC,seed_id) WHERE status='CURRENT';
    CREATE TABLE semantic_access_projection(projection_version_id TEXT PRIMARY KEY,seed_id TEXT NOT NULL,target_record_id TEXT NOT NULL,target_logical_id TEXT NOT NULL,path_rank INTEGER NOT NULL,hop_count INTEGER NOT NULL,path_weight REAL NOT NULL,authority_rank REAL NOT NULL DEFAULT 0.0,source_epoch INTEGER NOT NULL,graph_epoch INTEGER NOT NULL,derivation_hash TEXT NOT NULL,path_clay TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE UNIQUE INDEX idx_semantic_access_unique_current ON semantic_access_projection(seed_id,target_record_id) WHERE status='CURRENT';
    CREATE INDEX idx_semantic_access_hot ON semantic_access_projection(seed_id,path_rank,path_weight DESC,authority_rank DESC,target_record_id) WHERE status='CURRENT';
    """)
    target={}; rid=0
    for topic,(aliases,keywords) in TOPICS.items():
        rid+=1; t=f"R{rid:05d}"; target[topic]=t; text=f"{topic} current canonical contract {keywords} verified current semantics"; con.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",(t,topic,"CURRENT","PROJECT_OWNER_FIXED",100,text)); con.execute("INSERT INTO fts VALUES(?,?)",(t,text))
        rid+=1; s=f"R{rid:05d}"; st=f"{topic} historical superseded contract {keywords} old archived semantics"; con.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",(s,topic,"SUPERSEDED","HISTORICAL",10,st)); con.execute("INSERT INTO fts VALUES(?,?)",(s,st))
        toks=keywords.split()
        for j in range(18):
            rid+=1; r=f"R{rid:05d}"; sample=" ".join(random.sample(toks,min(len(toks),random.randint(3,6)))); tx=f"{topic} research note {j} {sample} evidence candidate"; ep="VALIDATED_RESEARCH" if j<5 else "DERIVED"; con.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",(r,topic,"CURRENT",ep,50-j,tx)); con.execute("INSERT INTO fts VALUES(?,?)",(r,tx))
        for a in aliases: con.execute("INSERT INTO aliases VALUES(?,?,?)",(norm(a),topic,1.0))
        con.execute("INSERT INTO edges VALUES(?,?,?,?)",(topic,t,"CANONICAL_OF",1.0))
    for a,b in RELATED: con.execute("INSERT INTO edges VALUES(?,?,?,?)",(a,target[b],"RELATED",0.45))
    vocab="state graph memory loop tool model evidence current runtime semantic context work event signal task system archive branch result candidate source causal latency accuracy recovery query".split()
    for _ in range(4000):
        rid+=1; r=f"N{rid:05d}"; tx=" ".join(random.choices(vocab,k=18)); con.execute("INSERT INTO records VALUES(?,?,?,?,?,?)",(r,"noise","CURRENT","DERIVED",random.randint(1,99),tx)); con.execute("INSERT INTO fts VALUES(?,?)",(r,tx))
    con.commit(); baseline_bytes=con.execute("PRAGMA page_count").fetchone()[0]*con.execute("PRAGMA page_size").fetchone()[0]; build_started=time.perf_counter_ns()
    for topic,(aliases,keywords) in TOPICS.items():
        seeds=[topic]+aliases+[" ".join(keywords.split()[:2])]
        for n,seed in enumerate(seeds):
            key=norm(seed); sid=f"S:{topic}:{n}"; con.execute("INSERT INTO semantic_query_seeds VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(f"SV:{topic}:{n}",sid,key,topic,"CANONICAL" if n==0 else "ALIAS",1.0,'{"source":"benchmark"}',1,1,"CURRENT","2026-08-10T00:00:00Z","2026-08-10T00:00:00Z")); con.execute("INSERT INTO semantic_access_projection VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(f"PV:{topic}:{n}:1",sid,target[topic],topic,1,0,1.0,3.0,1,1,"bench",f'{{"seed":"{key}"}}',"CURRENT","2026-08-10T00:00:00Z")); rank=2
            for rr,w in con.execute("SELECT target_record_id,weight FROM edges WHERE source_topic=? AND relation='RELATED' ORDER BY weight DESC",(topic,)).fetchall():
                con.execute("INSERT OR IGNORE INTO semantic_access_projection VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(f"PV:{topic}:{n}:{rank}",sid,rr,topic,rank,1,w,1.0,1,1,"bench",f'{{"seed":"{key}","relation":"RELATED"}}',"CURRENT","2026-08-10T00:00:00Z")); rank+=1
    con.commit(); projection_build_ns=time.perf_counter_ns()-build_started; materialized_bytes=con.execute("PRAGMA page_count").fetchone()[0]*con.execute("PRAGMA page_size").fetchone()[0]; semantic_seed_rows=con.execute("SELECT count(*) FROM semantic_query_seeds").fetchone()[0]; projection_rows=con.execute("SELECT count(*) FROM semantic_access_projection").fetchone()[0]
    queries=[]
    for topic,(aliases,keywords) in TOPICS.items(): queries.append((topic,topic)); queries.append((" ".join(keywords.split()[:2]),topic)); queries.extend((a,topic) for a in aliases)
    random.shuffle(queries)
    return con,target,queries,rid,{"baseline_bytes":baseline_bytes,"materialized_bytes":materialized_bytes,"overhead_bytes":materialized_bytes-baseline_bytes,"projection_build_ns":projection_build_ns,"semantic_seed_rows":semantic_seed_rows,"projection_rows":projection_rows}

def fts_meta(con,q,k=5):
    toks=norm(q).split()
    if not toks:return []
    rows=con.execute("SELECT f.record_id,bm25(fts),r.epistemic_class,r.updated_seq FROM fts f JOIN records r ON r.record_id=f.record_id WHERE fts MATCH ? AND r.status='CURRENT'",(" OR ".join(toks),)).fetchall(); rows.sort(key=lambda r:(-authority(r[2]),r[1],-r[3],r[0])); return [r[0] for r in rows[:k]]

def hybrid_v1(con,q,k=5):
    lex=fts_meta(con,q,12); scores={}
    for rank,r in enumerate(lex): scores[r]=scores.get(r,0)+1/(rank+1)
    a=con.execute("SELECT topic FROM aliases WHERE alias=?",(norm(q),)).fetchone(); topic=a[0] if a else (q if q in TOPICS else None)
    if topic:
        for r,w,_ in con.execute("SELECT target_record_id,weight,relation FROM edges WHERE source_topic=?",(topic,)): scores[r]=scores.get(r,0)+4*w
    if scores:
        ids=list(scores); ph=",".join("?"*len(ids))
        for r,ep,upd in con.execute(f"SELECT record_id,epistemic_class,updated_seq FROM records WHERE record_id IN ({ph})",ids): scores[r]+=2.2 if ep=="PROJECT_OWNER_FIXED" else (0.5 if ep=="VALIDATED_RESEARCH" else 0); scores[r]+=upd*0.001
    return [r for r,_ in sorted(scores.items(),key=lambda kv:(-kv[1],kv[0]))[:k]]

def assess(name,fn,queries,target,repeats=30):
    hit1=hit5=0; rr=[]
    for q,topic in queries:
        res=fn(q,5); gt=target[topic]; hit1+=bool(res and res[0]==gt); hit5+=gt in res; rr.append(1/(res.index(gt)+1) if gt in res else 0)
    for q,_ in queries: fn(q,5)
    lat=[]
    for _ in range(repeats):
        for q,_ in queries:
            t=time.perf_counter_ns(); fn(q,5); lat.append(time.perf_counter_ns()-t)
    return {"name":name,"queries":len(queries),"operations_timed":len(lat),"hit_at_1":hit1/len(queries),"recall_at_5":hit5/len(queries),"mrr":sum(rr)/len(rr),"latency_ns":{"p50":int(statistics.median(lat)),"p95":int(pct(lat,.95)),"p99":int(pct(lat,.99)),"max":int(max(lat))}}

def main():
    with tempfile.TemporaryDirectory() as td:
        db=os.path.join(td,"bench.sqlite"); con,target,queries,rows,storage=build_db(db); fabric=SemanticRetrievalFabric(con)
        def v2(q,k):
            fast=fabric.query_seed(q,source_epoch=1,graph_epoch=1,limit=k)
            return list(fast.refs) if fast.refs else fts_meta(con,q,k)
        results=[assess("sqlite_fts5_current_authority",lambda q,k:fts_meta(con,q,k),queries,target),assess("udb_claygraph_v1_query_time",lambda q,k:hybrid_v1(con,q,k),queries,target),assess("udb_claygraph_v2_materialized",v2,queries,target)]
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)"); con.close()
        out={"schema":"clay.semantic_retrieval_benchmark.v1","seed":SEED,"scope":"assistant semantic retrieval; synthetic deterministic workload; not universal database superiority","dataset":{"rows":rows,"queries":len(queries),"topics":len(TOPICS),"noise_rows":4000},"projection":storage,"environment":{"python":platform.python_version(),"sqlite":sqlite3.sqlite_version,"platform":platform.platform(),"machine":platform.machine(),"processor":platform.processor() or "UNKNOWN"},"database_bytes":os.path.getsize(db),"results":results}; print(json.dumps(out,indent=2,sort_keys=True))
if __name__=="__main__": main()
