#!/usr/bin/env python3
import sqlite3
import unittest
from pathlib import Path
from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11
from semantic_access_generation_builder_v11 import Path, stage_generation, verify_generation, publish_generation

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text(encoding='utf-8')
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text(encoding='utf-8')

class SemanticAccessV11Tests(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(':memory:')
        self.con.executescript(U10); self.con.executescript(U11)
        self.con.execute("INSERT INTO semantic_query_seeds VALUES('sv','s','shared semantic state','u','ALIAS',1,'{}',7,9,'CURRENT','t','t')")
        p=[Path('s','r1','u',1,0,1,3,'{}')]
        stage_generation(self.con,generation_id='g1',source_epoch=7,graph_epoch=9,derivation_id='d',derivation_hash='h1',paths=p,created_at='t')
        verify_generation(self.con,'g1',verification_clay='{}',verified_at='t')
        publish_generation(self.con,'g1',published_at='t')
    def tearDown(self): self.con.close()
    def test_fast_path(self):
        r=SemanticRetrievalFabricV11(self.con).query('shared semantic state',source_epoch=7,graph_epoch=9)
        self.assertEqual((r.mode,r.refs,r.generation_id),('COHERENT_SEMANTIC_FASTPATH',('r1',),'g1'))
    def test_stale_epoch_fails_closed(self):
        self.assertEqual(SemanticRetrievalFabricV11(self.con).query('shared semantic state',source_epoch=8,graph_epoch=9).mode,'MISS')
    def test_empty_generation_preserves_lkg(self):
        with self.assertRaises(ValueError):
            stage_generation(self.con,generation_id='bad',source_epoch=7,graph_epoch=9,derivation_id='d',derivation_hash='x',paths=[],created_at='t')
        self.assertEqual(self.con.execute("SELECT generation_id FROM semantic_access_head").fetchone()[0],'g1')
    def test_unverified_generation_cannot_publish(self):
        p=[Path('s','r2','u',1,0,1,3,'{}')]
        stage_generation(self.con,generation_id='g2',source_epoch=7,graph_epoch=9,derivation_id='d',derivation_hash='h2',paths=p,created_at='t')
        with self.assertRaises(ValueError): publish_generation(self.con,'g2',published_at='t')
        self.assertEqual(self.con.execute("SELECT generation_id FROM semantic_access_head").fetchone()[0],'g1')
    def test_atomic_generation_swap(self):
        p=[Path('s','r2','u',1,0,1,3,'{}')]
        stage_generation(self.con,generation_id='g2',source_epoch=7,graph_epoch=9,derivation_id='d',derivation_hash='h2',paths=p,created_at='t')
        verify_generation(self.con,'g2',verification_clay='{}',verified_at='t')
        publish_generation(self.con,'g2',published_at='t2')
        r=SemanticRetrievalFabricV11(self.con).query('shared semantic state',source_epoch=7,graph_epoch=9)
        self.assertEqual((r.refs,r.generation_id),(('r2',),'g2'))
        self.assertEqual(self.con.execute("SELECT status FROM semantic_access_generations WHERE generation_id='g1'").fetchone()[0],'SUPERSEDED')

if __name__=='__main__': unittest.main(verbosity=2)
