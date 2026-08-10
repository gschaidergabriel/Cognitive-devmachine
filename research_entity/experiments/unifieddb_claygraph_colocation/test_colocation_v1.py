from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import SCHEMA as STATE_SCHEMA, StateLedger
from .benchmark_colocation_v1 import (
    GRAPH_SCHEMA_PATH, GRAPH_V3_PATH, graph_schema_colocated, inject_rollback,
    pragmas, seed_graph, seed_state, tx_single,
)
from .build_colocated_database_v1 import build


class UnifiedDBClayGraphColocationTests(unittest.TestCase):
    def test_naive_colocation_has_incompatible_generic_meta_schema(self):
        con=sqlite3.connect(':memory:'); con.executescript(STATE_SCHEMA); con.executescript(GRAPH_SCHEMA_PATH.read_text())
        self.assertEqual([r[1] for r in con.execute('PRAGMA table_info(meta)')],['k','v'])
        with self.assertRaises(sqlite3.OperationalError): con.execute("INSERT INTO meta(key,value) VALUES('graph','x')")
        con.close()

    def test_namespaced_colocation_preserves_both_meta_contracts(self):
        con=sqlite3.connect(':memory:'); con.executescript(STATE_SCHEMA); con.executescript(graph_schema_colocated())
        self.assertEqual([r[1] for r in con.execute('PRAGMA table_info(meta)')],['k','v'])
        self.assertEqual([r[1] for r in con.execute('PRAGMA table_info(claygraph_meta)')],['key','value'])
        con.execute("INSERT INTO meta VALUES('state-key','state-value')"); con.execute("INSERT INTO claygraph_meta VALUES('graph-key','graph-value')")
        self.assertEqual(con.execute("SELECT v FROM meta WHERE k='state-key'").fetchone()[0],'state-value')
        self.assertEqual(con.execute("SELECT value FROM claygraph_meta WHERE key='graph-key'").fetchone()[0],'graph-value'); con.close()

    def test_current_graph_v3_projection_and_rollback_survive_colocation(self):
        with tempfile.TemporaryDirectory() as td:
            con=sqlite3.connect(str(Path(td)/'unified.sqlite')); pragmas(con); con.executescript(STATE_SCHEMA); con.executescript(graph_schema_colocated()); con.executescript(GRAPH_V3_PATH.read_text())
            seed_state(con,n=128); seed_graph(con,nodes=32)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_nodes').fetchone()[0],32)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM v_graph_current_nodes_fast').fetchone()[0],32)
            tx_single(con,0); self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_edges').fetchone()[0],1); self.assertTrue(inject_rollback(con,False)); self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_edges').fetchone()[0],1); con.close()

    def _sources(self,td:Path):
        state=td/'state.sqlite'; graph=td/'graph.sqlite'
        with StateLedger(state) as l:
            l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='test',ops=[{'op':'SET','domain':'semantic','key':'a','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'}])
        g=sqlite3.connect(graph); pragmas(g); g.executescript(GRAPH_SCHEMA_PATH.read_text()); g.executescript(GRAPH_V3_PATH.read_text()); g.execute("INSERT INTO meta VALUES('graph-version','v1')"); seed_graph(g,nodes=16)
        g.execute("INSERT INTO graph_epochs VALUES(2,1,'edge','t','CURRENT')"); g.execute("INSERT INTO graph_edges VALUES('e@2','e',2,'n0','n1','LINK',.9,1,'{}','{}',NULL,'CURRENT','t')"); g.commit(); g.close(); return state,graph

    def test_reversible_builder_preserves_state_roots_and_rebuilds_graph_heads(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); out=td/'combined.sqlite'; receipt=build(state,graph,out)
            self.assertTrue(out.exists()); self.assertTrue(receipt['projection']['pass']); self.assertEqual(receipt['copied_rows']['graph_nodes'],16); self.assertEqual(receipt['copied_rows']['graph_edges'],1)
            c=sqlite3.connect(out)
            self.assertEqual(c.execute("SELECT value FROM claygraph_meta WHERE key='graph-version'").fetchone()[0],'v1')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM graph_head_nodes').fetchone()[0],16); self.assertEqual(c.execute('SELECT COUNT(*) FROM graph_head_edges').fetchone()[0],1)
            self.assertEqual(c.execute("SELECT v FROM meta WHERE k='semantic_state_hash'").fetchone()[0],receipt['semantic_state_hash']); self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok'); c.close()
            with StateLedger(out) as l: self.assertEqual(l.semantic_state_hash,receipt['semantic_state_hash'])

    def test_unknown_graph_table_fails_closed_without_output(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); g=sqlite3.connect(graph); g.execute('CREATE TABLE surprise_future_semantics(x TEXT)'); g.commit(); g.close(); out=td/'combined.sqlite'
            with self.assertRaisesRegex(RuntimeError,'unknown ClayGraph tables'): build(state,graph,out)
            self.assertFalse(out.exists())

    def test_ambiguous_same_epoch_graph_versions_fail_closed(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); g=sqlite3.connect(graph)
            g.execute("INSERT INTO graph_nodes VALUES('n0-z@1','n0',1,'STATE','ambiguous','{}',.2,.2,1,'bench','DERIVED','CURRENT','t')"); g.commit(); g.close(); out=td/'combined.sqlite'
            with self.assertRaisesRegex(RuntimeError,'projection differs'): build(state,graph,out)
            self.assertFalse(out.exists())


if __name__=='__main__': unittest.main()
