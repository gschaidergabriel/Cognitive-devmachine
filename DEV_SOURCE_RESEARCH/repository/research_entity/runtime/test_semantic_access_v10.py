#!/usr/bin/env python3
import sqlite3
import unittest
from semantic_retrieval_runtime_v10 import SemanticRetrievalFabric, reciprocal_rank_fusion
from semantic_access_builder_v10 import AccessPath, publish_projection

UDB_SCHEMA=open("RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql",encoding="utf-8").read()

class SemanticAccessV10Tests(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(":memory:")
        self.con.executescript(UDB_SCHEMA)
        self.con.execute("""INSERT INTO semantic_query_seeds VALUES
          ('sv1','seed.unifieddb','shared semantic state','unifieddb','ALIAS',1.0,'{}',7,9,'CURRENT','t','t')""")
        self.con.execute("""INSERT INTO semantic_access_projection VALUES
          ('pv0','seed.unifieddb','record.old','unifieddb',1,0,1.0,2.0,7,9,'d0','{}','CURRENT','t')""")
        self.con.commit()
    def tearDown(self): self.con.close()

    def test_fast_path_exact_epoch(self):
        r=SemanticRetrievalFabric(self.con).query_seed("shared semantic state",source_epoch=7,graph_epoch=9)
        self.assertEqual(r.mode,"SEMANTIC_SEED_FASTPATH")
        self.assertEqual(r.refs,("record.old",))

    def test_epoch_mismatch_fails_closed(self):
        r=SemanticRetrievalFabric(self.con).query_seed("shared semantic state",source_epoch=8,graph_epoch=9)
        self.assertEqual(r.mode,"MISS")
        self.assertEqual(r.refs,())

    def test_empty_rebuild_preserves_last_known_good(self):
        with self.assertRaises(ValueError):
            publish_projection(self.con,seed_id="seed.unifieddb",source_epoch=7,graph_epoch=9,
                               derivation_hash="d1",paths=[],created_at="t2")
        row=self.con.execute("SELECT target_record_id FROM semantic_access_projection WHERE status='CURRENT'").fetchone()
        self.assertEqual(row[0],"record.old")

    def test_atomic_rebuild_supersedes_old(self):
        paths=[AccessPath("record.new","unifieddb",1,0,1.0,3.0,'{"why":"new"}')]
        publish_projection(self.con,seed_id="seed.unifieddb",source_epoch=7,graph_epoch=9,
                           derivation_hash="d1",paths=paths,created_at="t2")
        old=self.con.execute("SELECT status FROM semantic_access_projection WHERE target_record_id='record.old'").fetchone()[0]
        cur=self.con.execute("SELECT target_record_id FROM semantic_access_projection WHERE status='CURRENT'").fetchone()[0]
        self.assertEqual(old,"SUPERSEDED"); self.assertEqual(cur,"record.new")

    def test_rrf_does_not_compare_raw_scores(self):
        self.assertEqual(reciprocal_rank_fusion([["a","b"],["b","c"]])[0],"b")

if __name__=="__main__": unittest.main(verbosity=2)
