from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from .benchmark_colocation_v1 import GRAPH_SCHEMA_PATH, GRAPH_V3_PATH, pragmas, seed_graph
from .build_colocated_database_v2 import build


class CoLocationMigrationV2Tests(unittest.TestCase):
    def _sources(self,td:Path):
        state=td/'state.sqlite'; graph=td/'graph.sqlite'
        with StateLedger(state) as l:
            l.append_event(event_id='seed',idem='seed',base_epoch=0,event_type='SEED',writer='test',ops=[
                {'op':'SET','domain':'semantic','key':'a','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'}])
        g=sqlite3.connect(graph); pragmas(g); g.executescript(GRAPH_SCHEMA_PATH.read_text()); g.executescript(GRAPH_V3_PATH.read_text())
        g.execute("INSERT INTO meta VALUES('graph-version','v1')"); seed_graph(g,nodes=16)
        g.execute("INSERT INTO graph_epochs VALUES(2,1,'edge','t','CURRENT')")
        g.execute("INSERT INTO graph_edges VALUES('e@2','e',2,'n0','n1','LINK',.9,1,'{}','{}',NULL,'CURRENT','t')")
        g.commit(); g.close(); return state,graph

    def test_v2_build_pins_and_revalidates_sources(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); out=td/'combined.sqlite'
            receipt=build(state,graph,out)
            self.assertTrue(out.exists())
            self.assertEqual(receipt['source_snapshot'],receipt['fresh_source_head'])
            self.assertEqual(receipt['source_snapshot']['state_epoch'],1)
            self.assertEqual(receipt['source_snapshot']['graph_source_epoch'],1)
            self.assertTrue(receipt['projection']['pass'])
            c=sqlite3.connect(out)
            self.assertEqual(c.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(c.execute('SELECT COUNT(*) FROM graph_current_projection_receipts').fetchone()[0],1)
            c.close()

    def test_state_advance_before_publish_rejects_stale_output(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); out=td/'combined.sqlite'
            def advance_state():
                with StateLedger(state) as l:
                    l.append_event(event_id='advance',idem='advance',base_epoch=l.epoch,event_type='ADVANCE',writer='test',ops=[
                        {'op':'SET','domain':'semantic','key':'b','value':2,'epistemic':'KNOWN','status':'CURRENT'}])
            with self.assertRaisesRegex(RuntimeError,'source advanced during migration'):
                build(state,graph,out,before_publish_hook=advance_state)
            self.assertFalse(out.exists())

    def test_graph_advance_before_publish_rejects_stale_output(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); out=td/'combined.sqlite'
            def advance_graph():
                g=sqlite3.connect(graph); g.execute("INSERT INTO graph_epochs VALUES(3,1,'advance','t','CURRENT')")
                g.execute("INSERT INTO graph_edges VALUES('e2@3','e2',3,'n1','n2','LINK',.8,1,'{}','{}',NULL,'CURRENT','t')")
                g.commit(); g.close()
            with self.assertRaisesRegex(RuntimeError,'source advanced during migration'):
                build(state,graph,out,before_publish_hook=advance_graph)
            self.assertFalse(out.exists())

    def test_coherent_both_sources_advance_still_rejects_stale_snapshot(self):
        with tempfile.TemporaryDirectory() as raw:
            td=Path(raw); state,graph=self._sources(td); out=td/'combined.sqlite'
            def advance_both():
                with StateLedger(state) as l:
                    l.append_event(event_id='advance',idem='advance',base_epoch=l.epoch,event_type='ADVANCE',writer='test',ops=[
                        {'op':'SET','domain':'semantic','key':'b','value':2,'epistemic':'KNOWN','status':'CURRENT'}])
                g=sqlite3.connect(graph); g.execute("INSERT INTO graph_epochs VALUES(3,2,'advance','t','CURRENT')")
                g.execute("INSERT INTO graph_edges VALUES('e2@3','e2',3,'n1','n2','LINK',.8,1,'{}','{}',NULL,'CURRENT','t')")
                g.commit(); g.close()
            with self.assertRaisesRegex(RuntimeError,'source advanced during migration'):
                build(state,graph,out,before_publish_hook=advance_both)
            self.assertFalse(out.exists())


if __name__=='__main__': unittest.main(verbosity=2)
