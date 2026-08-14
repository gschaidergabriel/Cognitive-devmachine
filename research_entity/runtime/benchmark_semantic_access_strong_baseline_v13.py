#!/usr/bin/env python3
"""Strong exact-key counterbaseline for semantic access candidates.

Purpose: prevent false superiority claims. A plain SQLite WITHOUT ROWID B-tree map is the
correct comparator when the normalized semantic key is already known. U11/U13 must justify
extra latency with coherence/replay/provenance, not pretend FTS5 is the only baseline.
"""
from __future__ import annotations
import os,tempfile
from pathlib import Path
import benchmark_semantic_retrieval_v10 as b
from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11
from semantic_retrieval_runtime_v13 import CyclePinnedSemanticAccessV13
H=Path(__file__).resolve().parent

def main():
 with tempfile.TemporaryDirectory() as td:
  c,target,queries,_,_=b.build_db(os.path.join(td,'x.db'))
  c.execute('CREATE TABLE normal_alias_map(normalized_key TEXT PRIMARY KEY,target_record_id TEXT NOT NULL) WITHOUT ROWID')
  for q,topic in queries:c.execute('INSERT OR REPLACE INTO normal_alias_map VALUES(?,?)',(b.norm(q),target[topic]))
  c.executescript((H/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text())
  c.executescript((H/'RAE_UNIFIEDDB_V13_CYCLE_PINNED_FLAT_ACCESS.sql').read_text())
  sc=c.execute("SELECT count(*) FROM semantic_query_seeds WHERE status='CURRENT'").fetchone()[0];pc=c.execute("SELECT count(*) FROM semantic_access_projection WHERE status='CURRENT'").fetchone()[0]
  c.execute("INSERT INTO semantic_access_generations VALUES('g',1,1,'b','h',?,?,'{}','CURRENT','t','t','t')",(sc,pc))
  c.execute("INSERT INTO semantic_access_projection_v11 SELECT 'g',seed_id,target_record_id,target_logical_id,path_rank,hop_count,path_weight,authority_rank,path_clay FROM semantic_access_projection WHERE status='CURRENT'")
  c.execute("INSERT INTO semantic_access_head VALUES('CURRENT','g',1,1,'h','t')")
  c.execute("""INSERT INTO semantic_access_flat_v13
    SELECT 'g',s.normalized_key,p.target_record_id,p.target_logical_id,p.path_rank,p.path_weight,p.authority_rank,p.path_clay
    FROM semantic_query_seeds s JOIN semantic_access_projection p ON p.seed_id=s.seed_id WHERE s.status='CURRENT' AND p.status='CURRENT'""")
  c.commit();u11=SemanticRetrievalFabricV11(c);u13=CyclePinnedSemanticAccessV13(c);pin=u13.pin('bench',source_epoch=1,graph_epoch=1,pinned_at='t')
  def normal(q,k):
   r=c.execute('SELECT target_record_id FROM normal_alias_map WHERE normalized_key=?',(b.norm(q),)).fetchone();return [r[0]] if r else []
  def q11(q,k):return list(u11.query(q,source_epoch=1,graph_epoch=1,limit=k).refs)
  def q13(q,k):return list(u13.query(pin,q,k)[0])
  for name,fn in [('normal_btree_alias_map',normal),('u11_coherent_semantic_access',q11),('u13_cycle_pinned_flat_access',q13)]:print(b.assess(name,fn,queries,target,repeats=200))
if __name__=='__main__':main()
