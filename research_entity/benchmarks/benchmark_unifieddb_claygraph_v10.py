#!/usr/bin/env python3
"""Deterministic candidate benchmark for UnifiedDB V10 + ClayGraph V3.

Compares three things without conflating them:
1) lexical SQLite FTS5 context retrieval,
2) optimized structured SQLite over authoritative source tables,
3) rebuildable Clay current projections.

Synthetic data is deliberately adversarial for stale/low-authority retrieval. Results are
candidate evidence only; they do not establish superiority on real FRANK workloads.
"""
from __future__ import annotations
from collections import defaultdict
import json, math, os, platform, random, sqlite3, statistics, time

SEED = 20260810
K = 5


def pct(xs, p):
    ys = sorted(xs)
    return ys[math.ceil(p * len(ys)) - 1]


def metadata():
    return {
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
    }


def build_mixed(n=600):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    c = con.cursor()
    c.executescript("""
    CREATE TABLE records(record_id TEXT PRIMARY KEY,logical_key TEXT,title TEXT,body TEXT,status TEXT,
      authority_rank INT,valid_from INT,valid_to INT,epoch INT);
    CREATE VIRTUAL TABLE records_fts USING fts5(record_id UNINDEXED,title,body,tokenize='unicode61');
    CREATE TABLE edges(source_key TEXT,target_key TEXT,relation_type TEXT,status TEXT,confidence REAL,authority_rank INT,epoch INT);
    CREATE INDEX idx_r_key_epoch ON records(logical_key,epoch DESC);
    CREATE INDEX idx_e_src ON edges(source_key,relation_type,epoch,status,authority_rank,confidence);
    CREATE TABLE retrieval_current(logical_key TEXT PRIMARY KEY,record_id TEXT NOT NULL,epoch INT NOT NULL) WITHOUT ROWID;
    CREATE TABLE graph_current_adjacency(source_key TEXT,relation_type TEXT,target_key TEXT,epoch INT,
      PRIMARY KEY(source_key,relation_type,target_key)) WITHOUT ROWID;
    """)
    current = {}
    aliases = {}
    for i in range(n):
        key = f"C{i:04d}"; alias = f"nebula{i:04d}"; token = f"conceptword{i:04d}"
        aliases[alias] = key; current[key] = f"{key}:current"
        rows = [
            (f"{key}:current", key, f"{alias} current", f"{alias} {token} authoritative current", "CURRENT", 3, 200, None, 10),
            (f"{key}:stale", key, f"{alias} {alias} legacy", f"{alias} {alias} {token} obsolete", "SUPERSEDED", 3, 0, 199, 5),
        ]
        if i % 3 == 0:
            rows.append((f"{key}:conflict", key, f"{alias} disputed", f"{alias} {alias} {alias} {token} model proposed", "CURRENT", 0, 200, None, 10))
        for row in rows:
            c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?,?,?)", row)
            c.execute("INSERT INTO records_fts VALUES (?,?,?)", (row[0], row[2], row[3]))
        c.execute("INSERT INTO retrieval_current VALUES (?,?,?)", (key, current[key], 10))
        for d, rel in ((1, "NEXT"), (7, "SUPPORTS")):
            target = f"C{(i+d)%n:04d}"
            c.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?)", (key,target,rel,"CURRENT",.98,3,10))
            c.execute("INSERT INTO graph_current_adjacency VALUES (?,?,?,?)", (key,rel,target,10))
        if i % 4 == 0:
            c.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?)", (key,f"C{(i+113)%n:04d}","SUPPORTS","CURRENT",.95,0,10))
    con.commit()
    return con, aliases, current


def mixed_benchmark():
    random.seed(SEED)
    con, aliases, current = build_mixed(); c = con.cursor()
    queries = []
    for _ in range(120):
        i = random.randrange(600); a=f"nebula{i:04d}"; key=f"C{i:04d}"
        queries.append(("record", a, current[key], None, 0))
    for _ in range(120):
        i = random.randrange(600); a=f"nebula{i:04d}"; target=f"C{(i+7)%600:04d}"
        queries.append(("graph1", a, current[target], "SUPPORTS", 1))
    for _ in range(120):
        i = random.randrange(600); a=f"nebula{i:04d}"; target=f"C{(i+2)%600:04d}"
        queries.append(("graph2", a, current[target], "NEXT", 2))
    random.shuffle(queries)

    def base(alias, typ, rel, hops):
        rows = c.execute("SELECT record_id FROM records_fts WHERE records_fts MATCH ? ORDER BY bm25(records_fts) LIMIT ?", (alias,K)).fetchall()
        return [x[0] for x in rows]

    graph_sql = """WITH RECURSIVE walk(node,depth) AS (
      SELECT ?,0 UNION ALL SELECT a.target_key,w.depth+1 FROM walk w
      JOIN graph_current_adjacency a ON a.source_key=w.node AND a.relation_type=? WHERE w.depth<?)
      SELECT r.record_id FROM walk w JOIN retrieval_current r ON r.logical_key=w.node WHERE w.depth=? LIMIT ?"""
    def clay(alias, typ, rel, hops):
        key = aliases[alias]
        if typ == "record":
            return [c.execute("SELECT record_id FROM retrieval_current WHERE logical_key=?", (key,)).fetchone()[0]]
        return [x[0] for x in c.execute(graph_sql, (key,rel,hops,hops,K)).fetchall()]

    def evaluate(fn):
        hit=0; rr=0.0; bad=0; lat=[]; by=defaultdict(lambda:[0,0])
        for typ,alias,truth,rel,hops in queries:
            t=time.perf_counter_ns(); out=fn(alias,typ,rel,hops); lat.append((time.perf_counter_ns()-t)/1e6)
            by[typ][1]+=1
            if truth in out:
                rank=out.index(truth)+1; hit+=1; rr+=1/rank; by[typ][0]+=1
            for rid in out:
                row=c.execute("SELECT status,authority_rank,valid_from,valid_to FROM records WHERE record_id=?",(rid,)).fetchone()
                if row and (row[0] != "CURRENT" or row[1] < 2 or row[2] > 250 or (row[3] is not None and row[3] < 250)):
                    bad += 1
        return {"hit_at_5":hit/len(queries),"mrr":rr/len(queries),"p50_ms":statistics.median(lat),
                "p95_ms":pct(lat,.95),"p99_ms":pct(lat,.99),"inadmissible_results":bad,
                "by_type":{k:v[0]/v[1] for k,v in by.items()}}
    return {"queries":len(queries),"sqlite_fts5":evaluate(base),"clay_projection":evaluate(clay)}


def scale_benchmark(n=20000, qn=1200):
    random.seed(SEED)
    con=sqlite3.connect(":memory:"); c=con.cursor()
    c.executescript("""
    CREATE TABLE records(record_id TEXT PRIMARY KEY,logical_key TEXT,status TEXT,authority_rank INT,valid_from INT,valid_to INT,epoch INT);
    CREATE INDEX idx_r_key_epoch ON records(logical_key,epoch DESC);
    CREATE TABLE edges(source_key TEXT,target_key TEXT,relation_type TEXT,status TEXT,confidence REAL,authority_rank INT,epoch INT);
    CREATE INDEX idx_e_src ON edges(source_key,relation_type,epoch,status,authority_rank,confidence);
    CREATE TABLE retrieval_current(logical_key TEXT PRIMARY KEY,record_id TEXT NOT NULL,epoch INT NOT NULL) WITHOUT ROWID;
    CREATE TABLE graph_current_adjacency(source_key TEXT,relation_type TEXT,target_key TEXT,epoch INT,
      PRIMARY KEY(source_key,relation_type,target_key)) WITHOUT ROWID;
    """)
    for i in range(n):
        key=f"C{i:06d}"
        c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",(f"{key}:cur",key,"CURRENT",3,200,None,10))
        c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",(f"{key}:old",key,"SUPERSEDED",3,0,199,5))
        if i%3==0: c.execute("INSERT INTO records VALUES (?,?,?,?,?,?,?)",(f"{key}:low",key,"CURRENT",0,200,None,10))
        c.execute("INSERT INTO retrieval_current VALUES (?,?,?)",(key,f"{key}:cur",10))
        for d,rel in ((1,"NEXT"),(7,"SUPPORTS")):
            target=f"C{(i+d)%n:06d}"
            c.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?)",(key,target,rel,"CURRENT",.98,3,10))
            c.execute("INSERT INTO graph_current_adjacency VALUES (?,?,?,?)",(key,rel,target,10))
        if i%4==0: c.execute("INSERT INTO edges VALUES (?,?,?,?,?,?,?)",(key,f"C{(i+113)%n:06d}","SUPPORTS","CURRENT",.95,0,10))
    con.commit()
    cases=[]
    for _ in range(qn):
        i=random.randrange(n); rel,hops=random.choice([("NEXT",2),("SUPPORTS",1)]); target=(i+(2 if rel=="NEXT" else 7))%n
        cases.append((f"C{i:06d}",rel,hops,f"C{target:06d}:cur"))

    raw_sql="""WITH RECURSIVE walk(node,depth) AS (
      SELECT ?,0 UNION ALL SELECT e.target_key,w.depth+1 FROM walk w JOIN edges e ON e.source_key=w.node
      WHERE e.relation_type=? AND e.status='CURRENT' AND e.authority_rank>=2 AND e.confidence>=.8 AND e.epoch=10 AND w.depth<?)
      SELECT (SELECT r.record_id FROM records r INDEXED BY idx_r_key_epoch WHERE r.logical_key=w.node
        AND r.status='CURRENT' AND r.authority_rank>=2 AND r.valid_from<=250 AND (r.valid_to IS NULL OR r.valid_to>=250)
        ORDER BY r.epoch DESC LIMIT 1) FROM walk w WHERE w.depth=? LIMIT ?"""
    clay_sql="""WITH RECURSIVE walk(node,depth) AS (
      SELECT ?,0 UNION ALL SELECT a.target_key,w.depth+1 FROM walk w JOIN graph_current_adjacency a
      ON a.source_key=w.node AND a.relation_type=? WHERE w.depth<?)
      SELECT r.record_id FROM walk w JOIN retrieval_current r ON r.logical_key=w.node WHERE w.depth=? LIMIT ?"""
    def run(sql):
        lat=[]; ok=0
        for key,rel,hops,truth in cases:
            t=time.perf_counter_ns(); out=[x[0] for x in c.execute(sql,(key,rel,hops,hops,K)).fetchall() if x[0]]
            lat.append((time.perf_counter_ns()-t)/1e6); ok += truth in out
        return {"accuracy":ok/qn,"p50_ms":statistics.median(lat),"p95_ms":pct(lat,.95),"p99_ms":pct(lat,.99)}
    ordinary=run(raw_sql); clay=run(clay_sql)
    return {"concepts":n,"queries":qn,"ordinary_structured_sqlite":ordinary,"clay_projection":clay,
            "projection_speedup_x":{"p50":ordinary["p50_ms"]/clay["p50_ms"],"p95":ordinary["p95_ms"]/clay["p95_ms"]}}


if __name__ == "__main__":
    result={"seed":SEED,"metadata":metadata(),"mixed":mixed_benchmark(),"scale":scale_benchmark()}
    print(json.dumps(result,indent=2,sort_keys=True))
