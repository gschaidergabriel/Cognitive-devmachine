#!/usr/bin/env python3
import sqlite3,unittest
from pathlib import Path
from semantic_retrieval_runtime_v13 import CyclePinnedSemanticAccessV13
H=Path(__file__).resolve().parent
class SemanticAccessV13Tests(unittest.TestCase):
 def setUp(self):
  c=self.c=sqlite3.connect(':memory:'); c.executescript((H/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text()); c.executescript((H/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text()); c.executescript((H/'RAE_UNIFIEDDB_V13_CYCLE_PINNED_FLAT_ACCESS.sql').read_text())
  for g,status,h,target in [('g1','CURRENT','h1','r1'),('g2','VERIFIED','h2','r2')]:
   c.execute("insert into semantic_access_generations values(?,1,1,'d',?,1,1,'{}',?,'t','t',?)",(g,h,status,'t' if status=='CURRENT' else None)); c.execute("insert into semantic_access_flat_v13 values(?, 'shared semantic state',?,'u',1,1,3,'{}')",(g,target))
  c.execute("insert into semantic_access_head values('CURRENT','g1',1,1,'h1','t')");c.commit();self.r=CyclePinnedSemanticAccessV13(c)
 def tearDown(self):self.c.close()
 def test_pin_and_read(self):
  p=self.r.pin('c1',source_epoch=1,graph_epoch=1,pinned_at='t');self.assertEqual(self.r.query(p,'shared semantic state')[0],('r1',))
 def test_old_cycle_keeps_snapshot_after_head_swap(self):
  p1=self.r.pin('c1',source_epoch=1,graph_epoch=1,pinned_at='t')
  with self.c:
   self.c.execute("update semantic_access_generations set status='SUPERSEDED' where generation_id='g1'");self.c.execute("update semantic_access_generations set status='CURRENT',published_at='t2' where generation_id='g2'");self.c.execute("update semantic_access_head set generation_id='g2',derivation_hash='h2',published_at='t2' where head_key='CURRENT'")
  self.assertEqual(self.r.query(p1,'shared semantic state')[0],('r1',));p2=self.r.pin('c2',source_epoch=1,graph_epoch=1,pinned_at='t2');self.assertEqual(self.r.query(p2,'shared semantic state')[0],('r2',))
 def test_wrong_epoch_refused(self):
  with self.assertRaises(RuntimeError):self.r.pin('bad',source_epoch=2,graph_epoch=1,pinned_at='t')
if __name__=='__main__':unittest.main(verbosity=2)
