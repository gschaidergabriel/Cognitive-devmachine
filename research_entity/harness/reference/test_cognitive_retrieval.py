import sqlite3
import unittest

from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .cognitive_retrieval import (
    CognitiveQueryIntent,
    CognitiveRetrievalIndex,
    GraphEdge,
    UnverifiedGraphProjection,
    load_verified_claygraph_edges,
)


class CognitiveRetrievalTests(unittest.TestCase):
    def make(self):
        ledger = StateLedger()
        plane = UnifiedDBQueryPlane(ledger)
        plane.transact(
            event_id='seed', idem='seed', base_epoch=0, event_type='SEED', writer='test',
            provenance={'class': 'FIXTURE'},
            ops=[
                {'op':'SET','domain':'authority','key':'needle','value':{'text':'Needle routing tool selection not effect authority'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'authority','key':'gateway','value':{'text':'Effect gateway commits verified external effects with authority'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'authority','key':'bad','value':{'text':'conflicting gateway speculation'},'epistemic':'CONFLICT','status':'CURRENT'},
            ],
        )
        index = CognitiveRetrievalIndex(
            plane,
            graph_edges=(
                GraphEdge('authority:needle','authority:gateway','routes_to',1.0,1.0,'edge:1'),
                GraphEdge('authority:needle','authority:bad','routes_to',1.0,1.0,'edge:bad'),
            ),
            alias_groups=(('route','routing','routes'),('commit','commits','authority')),
        )
        return ledger, index

    @staticmethod
    def graphdb(*, ambiguous=False, verified=True, source_epoch=1):
        db=sqlite3.connect(':memory:'); db.row_factory=sqlite3.Row
        db.executescript("""
          CREATE TABLE graph_epochs(graph_epoch INTEGER, source_epoch INTEGER, status TEXT);
          CREATE TABLE graph_head_edges(logical_edge_id TEXT, graph_epoch INTEGER);
          CREATE TABLE graph_current_projection_receipts(graph_epoch INTEGER, source_epoch INTEGER, verified_equal INTEGER, created_at TEXT);
          CREATE TABLE amb(logical_edge_id TEXT, graph_epoch INTEGER, version_count INTEGER);
          CREATE VIEW v_graph_projection_ambiguous_edge_epochs AS SELECT * FROM amb;
          CREATE TABLE heads(logical_edge_id TEXT, source_logical_id TEXT, target_logical_id TEXT, relation_type TEXT, weight REAL, confidence REAL, graph_epoch INTEGER);
          CREATE VIEW v_graph_current_edges_fast AS SELECT * FROM heads;
        """)
        db.execute("INSERT INTO graph_epochs VALUES(3,?,'CURRENT')",(source_epoch,))
        if ambiguous: db.execute("INSERT INTO amb VALUES('x',3,2)")
        if verified: db.execute("INSERT INTO graph_current_projection_receipts VALUES(3,?,1,'z')",(source_epoch,))
        db.execute("INSERT INTO graph_head_edges VALUES('e',3)")
        db.execute("INSERT INTO heads VALUES('e','a','b','routes_to',1.0,0.9,3)")
        return db

    def test_direct_retrieval(self):
        ledger,index=self.make()
        r=index.query(CognitiveQueryIntent('q','effect gateway commit',basis_epoch=ledger.epoch))
        self.assertEqual(r.results[0].record_ref,'authority:gateway')
        index.close(); ledger.close()

    def test_connected_target_has_graph_path_and_provenance(self):
        ledger,index=self.make()
        r=index.query(CognitiveQueryIntent(
            query_id='q',text='Needle route then effect commit',semantic_hints=('gateway authority',),
            anchor_refs=('authority:needle',),target_mode='CONNECTED_TARGET',basis_epoch=ledger.epoch))
        self.assertEqual(r.results[0].record_ref,'authority:gateway')
        self.assertEqual(r.results[0].graph_path[0],'authority:needle')
        self.assertTrue(r.graph_used)
        self.assertEqual(r.results[0].provenance['event_id'],'seed')
        index.close(); ledger.close()

    def test_graph_cannot_admit_conflict_by_default(self):
        ledger,index=self.make()
        r=index.query(CognitiveQueryIntent(query_id='q',text='conflicting gateway',anchor_refs=('authority:needle',),target_mode='CONNECTED_TARGET',basis_epoch=ledger.epoch))
        self.assertNotIn('authority:bad',[x.record_ref for x in r.results])
        index.close(); ledger.close()

    def test_stale_basis_rejected(self):
        ledger,index=self.make()
        with self.assertRaises(StaleEpoch): index.query(CognitiveQueryIntent('q','gateway',basis_epoch=0))
        index.close(); ledger.close()

    def test_projection_rebuilds_after_write(self):
        ledger,index=self.make(); index.query(CognitiveQueryIntent('q','gateway',basis_epoch=ledger.epoch))
        ledger.append_event(event_id='fresh',idem='fresh',base_epoch=ledger.epoch,event_type='WRITE',writer='test',ops=[
            {'op':'SET','domain':'state','key':'fresh','value':{'text':'fresh unique semantic'},'epistemic':'KNOWN','status':'CURRENT'}])
        r=index.query(CognitiveQueryIntent('q2','fresh unique',basis_epoch=ledger.epoch))
        self.assertEqual(r.results[0].record_ref,'state:fresh')
        index.close(); ledger.close()

    def test_verified_v3_graph_loader(self):
        db=self.graphdb(); edges=load_verified_claygraph_edges(db,source_epoch=1)
        self.assertEqual(len(edges),1); self.assertEqual((edges[0].source_ref,edges[0].target_ref),('a','b')); db.close()

    def test_v3_graph_loader_fails_closed_on_ambiguity(self):
        db=self.graphdb(ambiguous=True)
        with self.assertRaises(UnverifiedGraphProjection): load_verified_claygraph_edges(db,source_epoch=1)
        db.close()

    def test_v3_graph_loader_fails_closed_without_receipt(self):
        db=self.graphdb(verified=False)
        with self.assertRaises(UnverifiedGraphProjection): load_verified_claygraph_edges(db,source_epoch=1)
        db.close()


if __name__=='__main__': unittest.main()
