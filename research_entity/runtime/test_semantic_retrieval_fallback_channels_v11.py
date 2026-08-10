#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text(encoding='utf-8')
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text(encoding='utf-8')


class FallbackChannelReceiptTests(unittest.TestCase):
    def setUp(self):
        self.con=sqlite3.connect(':memory:')
        self.con.executescript(U10); self.con.executescript(U11)
        self.fabric=SemanticRetrievalFabricV11(self.con)

    def tearDown(self): self.con.close()

    def test_lexical_only_is_labelled_lexical(self):
        r=self.fabric.query('unseen',source_epoch=1,graph_epoch=1,lexical_ranking=['l1','l2'])
        self.assertEqual((r.mode,r.refs,r.fallback_channels),('LEXICAL_FALLBACK',('l1','l2'),('LEXICAL',)))

    def test_graph_only_is_not_mislabelled_as_lexical(self):
        r=self.fabric.query('unseen',source_epoch=1,graph_epoch=1,graph_fallback_ranking=['g1','g2'])
        self.assertEqual((r.mode,r.refs,r.fallback_channels),('GRAPH_FALLBACK',('g1','g2'),('GRAPH',)))

    def test_hybrid_receipt_identifies_both_channels(self):
        r=self.fabric.query('unseen',source_epoch=1,graph_epoch=1,lexical_ranking=['a','b'],graph_fallback_ranking=['b','c'])
        self.assertEqual(r.mode,'HYBRID_RRF_FALLBACK')
        self.assertEqual(r.fallback_channels,('LEXICAL','GRAPH'))
        self.assertEqual(set(r.refs),{'a','b','c'})

    def test_miss_has_no_fallback_channels(self):
        r=self.fabric.query('unseen',source_epoch=1,graph_epoch=1)
        self.assertEqual((r.mode,r.refs,r.fallback_channels),('MISS',(),()))

    def test_coherent_fastpath_has_no_fallback_channels(self):
        self.con.execute("INSERT INTO semantic_query_seeds VALUES('sv','s','known query','u','ALIAS',1,'{}',7,9,'CURRENT','t','t')")
        self.con.execute("INSERT INTO semantic_access_generations VALUES('g',7,9,'d','h',1,1,'{}','CURRENT','t','t','t')")
        self.con.execute("INSERT INTO semantic_access_projection_v11 VALUES('g','s','r','u',1,0,1,3,'{}')")
        self.con.execute("INSERT INTO semantic_access_head VALUES('CURRENT','g',7,9,'h','t')")
        self.con.commit()
        r=self.fabric.query('known query',source_epoch=7,graph_epoch=9)
        self.assertEqual((r.mode,r.refs,r.fallback_channels),('COHERENT_SEMANTIC_FASTPATH',('r',),()))


if __name__=='__main__': unittest.main(verbosity=2)
