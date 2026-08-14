from __future__ import annotations

"""V2.1 fair SQL adversaries for the real-claim Evidence Coalition compiler.

V2's first matched-SQL implementation used repeated scalar overlap queries. That is preserved
as historical evidence but is NOT a fair speed adversary. V2.1 adds two stronger SQLite paths:

A) SQLITE_SET_JOIN: no additional adjacency materialization. For the two lexical seeds it uses
   indexed set-based self-joins over claim_topic and claim_domain, grouped per seed/neighbor.
B) SQLITE_MATERIALIZED_NEIGHBOR: an indexed precomputed seed->neighbor relation with binary
   topic/domain overlap, then one grouped lookup per query.
C) COMPILED_COALITION: disposable in-memory topic/domain maps.

All three use exactly the same deterministic lexical scores and V2 facet/coalition policy.
Every ordered Top-K must therefore be identical. This benchmark compares physical execution
cost only after semantic equivalence is proven. Build/materialization time is reported
separately so a hot-query win cannot hide preparation cost.
"""

import argparse
import json
import os
import platform
import random
import sqlite3
import statistics
import sys
import time
from pathlib import Path

from . import benchmark_real_claim_topology_preprocessor_v1 as base
from .benchmark_real_claim_topology_preprocessor_v1_1 import topology_scores_compiled
from . import benchmark_real_claim_evidence_coalition_v2 as v2


def pct(values, p):
    ys=sorted(values); pos=(len(ys)-1)*p; lo=int(pos); hi=min(len(ys)-1,lo+1)
    return ys[lo] if lo==hi else ys[lo]*(hi-pos)+ys[hi]*(pos-lo)


def summary(samples):
    return {"n":len(samples),"min_us":min(samples),"p50_us":pct(samples,.5),"p95_us":pct(samples,.95),"p99_us":pct(samples,.99),"max_us":max(samples),"mean_us":statistics.mean(samples)}


def build_materialized_neighbors(con: sqlite3.Connection, rows) -> float:
    t0=time.perf_counter_ns()
    con.executescript(
        """
        DROP TABLE IF EXISTS claim_neighbor;
        CREATE TABLE claim_neighbor(
          seed_id TEXT NOT NULL,
          neighbor_id TEXT NOT NULL,
          topic_shared INTEGER NOT NULL,
          domain_shared INTEGER NOT NULL,
          PRIMARY KEY(seed_id,neighbor_id)
        ) WITHOUT ROWID;
        CREATE INDEX idx_claim_neighbor_seed ON claim_neighbor(seed_id,neighbor_id);
        """
    )
    topics={r["claim_id"]:set(str(x) for x in r.get("topic_packets",())) for r in rows}
    domains={r["claim_id"]:set(str(x) for x in r.get("domains",())) for r in rows}
    for a in rows:
        aid=a["claim_id"]
        for b in rows:
            bid=b["claim_id"]
            if aid==bid: continue
            ts=int(bool(topics[aid]&topics[bid])); ds=int(bool(domains[aid]&domains[bid]))
            if ts or ds:
                con.execute("INSERT INTO claim_neighbor VALUES(?,?,?,?)",(aid,bid,ts,ds))
    con.commit()
    return (time.perf_counter_ns()-t0)/1000.0


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--iterations",type=int,default=5000); ap.add_argument("--output")
    args=ap.parse_args(); iterations=max(100,min(args.iterations,100000))

    rows=base.current_rows(); rows_by_id={r["claim_id"]:r for r in rows}
    doc_tokens,postings,idf=base.compiled_lexical_index(rows)
    t0=time.perf_counter_ns(); topology=base.compile_topology(rows); compiled_topology_build_us=(time.perf_counter_ns()-t0)/1000.0
    con=base.make_sqlite(rows); materialized_neighbor_build_us=build_materialized_neighbors(con,rows)

    def lexical(q): return base.lexical_scores(q,rows_by_id,postings,doc_tokens,idf)

    def set_join_scores(q):
        lex=lexical(q); seeds=base.ranked(lex,2); scores=dict(lex)
        if seeds:
            ph=','.join('?' for _ in seeds)
            tq=f"""
            SELECT a.claim_id,b.claim_id
            FROM claim_topic a JOIN claim_topic b ON a.topic=b.topic
            WHERE a.claim_id IN ({ph}) AND b.claim_id<>a.claim_id
            GROUP BY a.claim_id,b.claim_id
            """
            for _seed,cid in con.execute(tq,seeds): scores[cid]=scores.get(cid,0.0)+4.0
            dq=f"""
            SELECT a.claim_id,b.claim_id
            FROM claim_domain a JOIN claim_domain b ON a.domain=b.domain
            WHERE a.claim_id IN ({ph}) AND b.claim_id<>a.claim_id
            GROUP BY a.claim_id,b.claim_id
            """
            for _seed,cid in con.execute(dq,seeds): scores[cid]=scores.get(cid,0.0)+0.75
        statuses=base.query_statuses(q)
        if statuses:
            for cid in list(scores):
                if str(rows_by_id[cid].get('current_status','')).upper() in statuses: scores[cid]+=3.0
        return scores

    def materialized_scores(q):
        lex=lexical(q); seeds=base.ranked(lex,2); scores=dict(lex)
        if seeds:
            ph=','.join('?' for _ in seeds)
            sql=f"""
            SELECT neighbor_id,SUM(4.0*topic_shared+0.75*domain_shared)
            FROM claim_neighbor WHERE seed_id IN ({ph}) GROUP BY neighbor_id
            """
            for cid,boost in con.execute(sql,seeds): scores[cid]=scores.get(cid,0.0)+float(boost)
        statuses=base.query_statuses(q)
        if statuses:
            for cid in list(scores):
                if str(rows_by_id[cid].get('current_status','')).upper() in statuses: scores[cid]+=3.0
        return scores

    def compiled_scores(q): return topology_scores_compiled(q,lexical(q),rows_by_id,topology)
    methods={
        'sqlite_set_join_coalition':lambda q:v2.coalition_rank(set_join_scores(q),rows_by_id,q,v2.K),
        'sqlite_materialized_neighbor_coalition':lambda q:v2.coalition_rank(materialized_scores(q),rows_by_id,q,v2.K),
        'compiled_coalition':lambda q:v2.coalition_rank(compiled_scores(q),rows_by_id,q,v2.K),
    }
    sets={
        'development_8':base.FROZEN_QUERIES,
        'paraphrase_stress_16':v2.PARAPHRASE_STRESS,
        'new_topic_holdout_7':v2.NEW_TOPIC_HOLDOUT,
    }
    per_set={}
    equivalent=True
    for sname,cases in sets.items():
        rows_out=[]; metric_rows={name:[] for name in methods}
        for case in cases:
            item={'id':case['id'],'query':case['query'],'expected':case['expected'],'methods':{}}
            outputs={}
            for name,fn in methods.items():
                got=fn(case['query']); outputs[name]=got; metric=base.retrieval_metrics(got,case['expected'],v2.K)
                metric_rows[name].append(metric); item['methods'][name]={'got':got,'metrics':metric}
            if len({tuple(x) for x in outputs.values()})!=1: equivalent=False
            rows_out.append(item)
        per_set[sname]={'summary':{name:base.aggregate(vals) for name,vals in metric_rows.items()},'per_query':rows_out}

    timing_cases=base.FROZEN_QUERIES+v2.PARAPHRASE_STRESS+v2.NEW_TOPIC_HOLDOUT
    rng=random.Random(313); schedule=[timing_cases[rng.randrange(len(timing_cases))]['query'] for _ in range(iterations)]
    for _ in range(10):
        for case in timing_cases:
            for fn in methods.values(): fn(case['query'])
    latency={name:[] for name in methods}
    for q in schedule:
        for name,fn in methods.items():
            t=time.perf_counter_ns(); fn(q); latency[name].append((time.perf_counter_ns()-t)/1000.0)
    lat={name:summary(xs) for name,xs in latency.items()}
    comp=lat['compiled_coalition']['p50_us']; setj=lat['sqlite_set_join_coalition']['p50_us']; mat=lat['sqlite_materialized_neighbor_coalition']['p50_us']
    gate={
        'all_three_ordered_top3_equivalent_all_31_queries':equivalent,
        'compiled_p50_ratio_vs_sqlite_set_join':comp/setj,
        'compiled_p50_ratio_vs_sqlite_materialized_neighbor':comp/mat,
        'compiled_strictly_faster_than_set_join_p50':comp<setj,
        'compiled_strictly_faster_than_materialized_neighbor_p50':comp<mat,
    }
    # Fair promotion requires semantic equivalence first. Speed alone never promotes truth.
    gate['advance_to_larger_cross_engine_falsifier']=equivalent and comp<setj and comp<mat
    output={
        'schema_version':'2.1',
        'benchmark':'REAL_CLAY_CLAIM_COALITION_FAIR_SQL_V2_1',
        'evidence_class':'REAL_REPOSITORY_LEDGER_FAIR_SQL_PHYSICAL_DIFFERENTIAL',
        'corpus_claims':len(rows),'queries':sum(len(v) for v in sets.values()),'k':v2.K,
        'preparation_cost_us':{'compiled_topology_build':compiled_topology_build_us,'sqlite_materialized_neighbor_build':materialized_neighbor_build_us},
        'sets':per_set,'latency':lat,'candidate_gate':gate,
        'execution_metadata':{'git_sha':os.environ.get('GITHUB_SHA','UNKNOWN_LOCAL'),'python':sys.version,'sqlite':sqlite3.sqlite_version,'platform':platform.platform(),'iterations':iterations,'timing_seed':313,'warmup_rounds':10},
        'fairness_note':'V2 repeated-scalar SQL is not used for speed claims. Set-join requires no extra adjacency materialization; materialized-neighbor is the stronger prepared-SQL baseline. All three methods must produce identical ordered Top-K before latency is interpreted.',
        'scope_guard':'Tiny 17-claim real Clay corpus and model-authored queries. No universal database superiority. Next competitors must include PostgreSQL/pgvector and graph-native systems under matched semantics.',
    }
    text=json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if args.output:
        p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8')
    print(text,end=''); con.close()

if __name__=='__main__': main()
