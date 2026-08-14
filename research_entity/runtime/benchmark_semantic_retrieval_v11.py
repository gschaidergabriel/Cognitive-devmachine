#!/usr/bin/env python3
"""Differential benchmark: SQLite FTS5 vs U10 vs coherent U11 semantic access.

Synthetic deterministic engineering profile only. It measures the semantic fast path used by
Clay; it is not a universal database benchmark and not live-FRANK outcome evidence.
"""
from __future__ import annotations
import json, os, tempfile
from pathlib import Path
import benchmark_semantic_retrieval_v10 as b
from semantic_retrieval_runtime_v10 import SemanticRetrievalFabric
from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11

HERE=Path(__file__).resolve().parent
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text(encoding='utf-8')

def main():
    with tempfile.TemporaryDirectory() as td:
        con,target,queries,rows,storage=b.build_db(os.path.join(td,'bench.sqlite'))
        con.executescript(U11)
        seed_count=con.execute("SELECT count(*) FROM semantic_query_seeds WHERE status='CURRENT'").fetchone()[0]
        path_count=con.execute("SELECT count(*) FROM semantic_access_projection WHERE status='CURRENT'").fetchone()[0]
        con.execute("INSERT INTO semantic_access_generations VALUES('bench-g1',1,1,'bench-v11','bench-hash',?,?, '{}','CURRENT','t','t','t')",(seed_count,path_count))
        con.execute("""INSERT INTO semantic_access_projection_v11
          SELECT 'bench-g1',seed_id,target_record_id,target_logical_id,path_rank,hop_count,path_weight,authority_rank,path_clay
          FROM semantic_access_projection WHERE status='CURRENT'""")
        con.execute("INSERT INTO semantic_access_head VALUES('CURRENT','bench-g1',1,1,'bench-hash','t')")
        con.commit()
        v10=SemanticRetrievalFabric(con); v11=SemanticRetrievalFabricV11(con)
        def q10(q,k):
            r=v10.query_seed(q,source_epoch=1,graph_epoch=1,limit=k)
            return list(r.refs) if r.refs else b.fts_meta(con,q,k)
        def q11(q,k):
            r=v11.query(q,source_epoch=1,graph_epoch=1,limit=k)
            return list(r.refs) if r.refs else b.fts_meta(con,q,k)
        results=[
            b.assess('sqlite_fts5_current_authority',lambda q,k:b.fts_meta(con,q,k),queries,target,repeats=100),
            b.assess('udb_claygraph_v10_materialized',q10,queries,target,repeats=100),
            b.assess('udb_claygraph_v11_coherent_generation',q11,queries,target,repeats=100),
        ]
        print(json.dumps({'schema':'clay.semantic_retrieval_benchmark.v11','scope':'synthetic deterministic Clay semantic-access engineering profile; not universal DB superiority','dataset':{'rows':rows,'queries':len(queries),'topics':len(b.TOPICS)},'projection':storage,'results':results},indent=2,sort_keys=True))
if __name__=='__main__': main()
