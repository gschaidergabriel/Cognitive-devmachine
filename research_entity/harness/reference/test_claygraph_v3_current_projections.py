import random
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'research_entity/runtime/RAE_CLAYGRAPH_SCHEMA.sql'
V3 = ROOT / 'research_entity/runtime/RAE_CLAYGRAPH_V3_CURRENT_PROJECTIONS.sql'

class ClayGraphV3ProjectionTests(unittest.TestCase):
    def make(self):
        db=sqlite3.connect(':memory:')
        db.row_factory=sqlite3.Row
        db.executescript(BASE.read_text())
        db.executescript(V3.read_text())
        for epoch in range(1,8):
            db.execute('INSERT INTO graph_epochs VALUES(?,?,?,?,?)',(epoch,epoch,f't{epoch}',f'2026-08-10T00:00:0{epoch}Z','CURRENT'))
        return db

    def edge(self,db,logical,version,epoch,status='CURRENT',src='a',dst='b',rel='depends'):
        db.execute(
            'INSERT INTO graph_edges(edge_version_id,logical_edge_id,graph_epoch,source_logical_id,target_logical_id,relation_type,weight,confidence,provenance_clay,admissibility_clay,causal_class,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (version,logical,epoch,src,dst,rel,1.0,0.9,'{}','{}','ASSOCIATIVE',status,f'2026-08-10T00:00:0{epoch}Z'))

    @staticmethod
    def legacy(db):
        return [tuple(r) for r in db.execute('SELECT logical_edge_id,edge_version_id,graph_epoch,source_logical_id,target_logical_id,relation_type,status FROM v_latest_graph_edges ORDER BY logical_edge_id,edge_version_id')]

    @staticmethod
    def fast(db):
        return [tuple(r) for r in db.execute("SELECT logical_edge_id,edge_version_id,graph_epoch,source_logical_id,target_logical_id,relation_type,source_status FROM v_graph_current_edges_fast ORDER BY logical_edge_id,edge_version_id")]

    @staticmethod
    def rebuild_edges(db):
        db.execute('DELETE FROM graph_head_edges')
        db.execute('''
          INSERT INTO graph_head_edges(
            logical_edge_id,edge_version_id,graph_epoch,source_epoch,source_logical_id,target_logical_id,
            relation_type,weight,confidence,provenance_clay,admissibility_clay,causal_class,source_status,created_at)
          SELECT e.logical_edge_id,e.edge_version_id,e.graph_epoch,g.source_epoch,e.source_logical_id,e.target_logical_id,
                 e.relation_type,e.weight,e.confidence,e.provenance_clay,e.admissibility_clay,e.causal_class,e.status,e.created_at
          FROM graph_edges e JOIN graph_epochs g ON g.graph_epoch=e.graph_epoch
          WHERE NOT EXISTS (
            SELECT 1 FROM graph_edges newer
            WHERE newer.logical_edge_id=e.logical_edge_id
              AND (newer.graph_epoch>e.graph_epoch OR
                   (newer.graph_epoch=e.graph_epoch AND newer.edge_version_id>e.edge_version_id))
          )
        ''')

    def test_newer_tombstone_cannot_be_resurrected_by_late_old_current(self):
        db=self.make()
        self.edge(db,'x','x-v5',5,'RETRACTED')
        self.edge(db,'x','x-v2',2,'CURRENT')
        head=db.execute('SELECT graph_epoch,source_status FROM graph_head_edges WHERE logical_edge_id=?',('x',)).fetchone()
        self.assertEqual((head['graph_epoch'],head['source_status']),(5,'RETRACTED'))
        self.assertEqual(db.execute("SELECT COUNT(*) FROM v_graph_current_edges_fast WHERE logical_edge_id='x'").fetchone()[0],0)
        db.close()

    def test_out_of_order_incremental_projection_matches_legacy_when_epoch_heads_are_unique(self):
        db=self.make(); rows=[]
        for i in range(120):
            logical=f'e{i:03d}'
            for epoch in (1,3,6):
                status='RETRACTED' if epoch==6 and i%7==0 else 'CURRENT'
                rows.append((logical,f'{logical}-v{epoch}',epoch,status,f'n{i%13}',f'n{(i+1)%13}',f'r{i%5}'))
        random.Random(731).shuffle(rows)
        for row in rows: self.edge(db,*row)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs').fetchone()[0],0)
        self.assertEqual(self.fast(db),self.legacy(db))
        db.close()

    def test_rebuild_from_history_matches_legacy(self):
        db=self.make(); rows=[]
        for i in range(80):
            logical=f'r{i:03d}'
            for epoch in (2,4,7):
                status='SUPERSEDED' if epoch==7 and i%9==0 else 'CURRENT'
                rows.append((logical,f'{logical}-v{epoch}',epoch,status,f's{i%11}',f't{(i+3)%11}',f'k{i%4}'))
        random.Random(991).shuffle(rows)
        for row in rows: self.edge(db,*row)
        expected=self.legacy(db)
        self.rebuild_edges(db)
        self.assertEqual(self.fast(db),expected)
        db.close()

    def test_same_logical_same_epoch_ambiguity_is_visible_and_blocks_verified_promotion(self):
        db=self.make()
        self.edge(db,'amb','amb-a',3,'CURRENT')
        self.edge(db,'amb','amb-b',3,'CURRENT')
        row=db.execute('SELECT logical_edge_id,graph_epoch,version_count FROM v_graph_projection_ambiguous_edge_epochs').fetchone()
        self.assertEqual(tuple(row),('amb',3,2))
        self.assertNotEqual(self.fast(db),self.legacy(db))
        db.close()

if __name__=='__main__': unittest.main()
