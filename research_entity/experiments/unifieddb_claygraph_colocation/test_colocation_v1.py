from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import SCHEMA as STATE_SCHEMA
from .benchmark_colocation_v1 import (
    GRAPH_SCHEMA_PATH,
    GRAPH_V3_PATH,
    graph_schema_colocated,
    inject_rollback,
    pragmas,
    seed_graph,
    seed_state,
    tx_single,
)


class UnifiedDBClayGraphColocationTests(unittest.TestCase):
    def test_naive_colocation_has_incompatible_generic_meta_schema(self):
        con=sqlite3.connect(':memory:')
        con.executescript(STATE_SCHEMA)
        con.executescript(GRAPH_SCHEMA_PATH.read_text())
        cols=[r[1] for r in con.execute('PRAGMA table_info(meta)')]
        self.assertEqual(cols,['k','v'])
        with self.assertRaises(sqlite3.OperationalError):
            con.execute("INSERT INTO meta(key,value) VALUES('graph','x')")
        con.close()

    def test_namespaced_colocation_preserves_both_meta_contracts(self):
        con=sqlite3.connect(':memory:')
        con.executescript(STATE_SCHEMA)
        con.executescript(graph_schema_colocated())
        self.assertEqual([r[1] for r in con.execute('PRAGMA table_info(meta)')],['k','v'])
        self.assertEqual([r[1] for r in con.execute('PRAGMA table_info(claygraph_meta)')],['key','value'])
        con.execute("INSERT INTO meta VALUES('state-key','state-value')")
        con.execute("INSERT INTO claygraph_meta VALUES('graph-key','graph-value')")
        self.assertEqual(con.execute("SELECT v FROM meta WHERE k='state-key'").fetchone()[0],'state-value')
        self.assertEqual(con.execute("SELECT value FROM claygraph_meta WHERE key='graph-key'").fetchone()[0],'graph-value')
        con.close()

    def test_current_graph_v3_projection_and_rollback_survive_colocation(self):
        with tempfile.TemporaryDirectory() as td:
            con=sqlite3.connect(str(Path(td)/'unified.sqlite'))
            pragmas(con); con.executescript(STATE_SCHEMA); con.executescript(graph_schema_colocated()); con.executescript(GRAPH_V3_PATH.read_text())
            seed_state(con,n=128); seed_graph(con,nodes=32)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_nodes').fetchone()[0],32)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM v_graph_current_nodes_fast').fetchone()[0],32)
            tx_single(con,0)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_edges').fetchone()[0],1)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM v_graph_current_edges_fast').fetchone()[0],1)
            self.assertTrue(inject_rollback(con,False))
            self.assertEqual(con.execute('SELECT COUNT(*) FROM graph_head_edges').fetchone()[0],1)
            con.close()

    def test_graph_and_state_objects_share_one_transactional_catalog_without_name_overlap(self):
        con=sqlite3.connect(':memory:')
        con.executescript(STATE_SCHEMA); con.executescript(graph_schema_colocated()); con.executescript(GRAPH_V3_PATH.read_text())
        names={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        required={'meta','domain_epochs','state','events','snapshots','claygraph_meta','graph_epochs','graph_nodes','graph_edges','graph_head_nodes','graph_head_edges','v_graph_current_nodes_fast','v_graph_current_edges_fast'}
        self.assertTrue(required.issubset(names))
        con.close()


if __name__=='__main__': unittest.main()
