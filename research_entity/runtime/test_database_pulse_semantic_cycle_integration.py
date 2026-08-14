#!/usr/bin/env python3
from __future__ import annotations
import sqlite3
import unittest
from pathlib import Path

from database_pulse_v0 import DatabasePulseV0
from semantic_retrieval_runtime_v13 import CyclePinnedSemanticAccessV13, norm
from adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest, AdaptiveSemanticReadPlaneV14, VerifiedReadBasis, StaleReadBasis,
)

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text(encoding='utf-8')
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text(encoding='utf-8')
U12P=(HERE/'RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql').read_text(encoding='utf-8')
U13=(HERE/'RAE_UNIFIEDDB_V13_CYCLE_PINNED_FLAT_ACCESS.sql').read_text(encoding='utf-8')

class DatabasePulseSemanticCycleIntegrationTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:')
  self.c.executescript(U10); self.c.executescript(U11); self.c.executescript(U13); self.c.executescript(U12P)
  for g,se,ge,status,dh,target in [
      ('g1',1,1,'CURRENT','h1','record.v1'),
      ('g2',2,2,'VERIFIED','h2','record.v2'),
  ]:
   self.c.execute(
    """INSERT INTO semantic_access_generations
       (generation_id,source_epoch,graph_epoch,derivation_id,derivation_hash,seed_count,
        path_count,verification_clay,status,created_at,verified_at,published_at)
       VALUES(?,?,?,'d',?,1,1,'{}',?,'t','t',?)""",
    (g,se,ge,dh,status,'t' if status=='CURRENT' else None))
   self.c.execute(
    """INSERT INTO semantic_access_flat_v13
       VALUES(?, 'shared semantic state', ?, 'unifieddb', 1, 1.0, 3.0, '{}')""",
    (g,target))
  self.c.execute("INSERT INTO semantic_access_head VALUES('CURRENT','g1',1,1,'h1','t')")
  self.c.commit()
  self.pulse=DatabasePulseV0(self.c)
  self.pulse.bootstrap(entity_id='frank-test',lineage_id='lineage-constant',
                       source_epoch=1,graph_epoch=1,now='boot')
  self.access=CyclePinnedSemanticAccessV13(self.c)

 def tearDown(self): self.c.close()

 def plane_for_pin(self,pin):
  basis=VerifiedReadBasis(pin.generation_id,pin.source_epoch,pin.graph_epoch,pin.derivation_hash)
  def verify(_request): return basis
  def exact(_key,_basis,_limit): return ()
  def semantic(text,b,limit):
   rows=self.c.execute(
    """SELECT target_record_id FROM semantic_access_flat_v13
       WHERE generation_id=? AND normalized_key=?
       ORDER BY path_rank,path_weight DESC,authority_rank DESC,target_record_id LIMIT ?""",
    (b.basis_id,norm(text),limit)).fetchall()
   return tuple(r[0] for r in rows)
  def resolve(_text,_basis): return None
  def graph(_logical,_text,_basis,_limit): return ()
  def comp(_text,_basis,_limit): return ()
  def fallback(_text,_basis,_limit): return ()
  return AdaptiveSemanticReadPlaneV14(
   verify_read_basis=verify,exact_lookup=exact,compiled_semantic_lookup=semantic,
   resolve_entity=resolve,graph_lookup=graph,compositional_lookup=comp,fallback_lookup=fallback)

 def publish_g2(self):
  with self.c:
   self.c.execute("UPDATE semantic_access_generations SET status='SUPERSEDED' WHERE generation_id='g1'")
   self.c.execute("UPDATE semantic_access_generations SET status='CURRENT',published_at='t2' WHERE generation_id='g2'")
   self.c.execute(
    """UPDATE semantic_access_head SET generation_id='g2',source_epoch=2,graph_epoch=2,
       derivation_hash='h2',published_at='t2' WHERE head_key='CURRENT'""")

 def test_pulse_epoch_change_invalidates_old_cognitive_read_until_matching_generation_exists(self):
  before=self.pulse.pulse(now='p1',expected_source_epoch=1,expected_graph_epoch=1)
  self.assertEqual((before.semantic_generation_id,before.applied_delta_count),('g1',0))
  pin1=self.access.pin('cycle-1',source_epoch=before.source_epoch,graph_epoch=before.graph_epoch,pinned_at='p1')
  read1=self.plane_for_pin(pin1).query(
   AdaptiveReadRequest('read-1','shared semantic state',before.source_epoch,before.graph_epoch))
  self.assertEqual((read1.refs,read1.read_basis_id),(('record.v1',),'g1'))

  self.pulse.admit_delta(
   delta_id='world-update-2',changed_ref='world:environment',reason_class='WORLD_UPDATE',
   payload={'changed':True},source_epoch=2,graph_epoch=2,now='d2')
  changed=self.pulse.pulse(now='p2')
  self.assertEqual(changed.applied_delta_count,1)
  self.assertIsNone(changed.semantic_generation_id)
  state=self.c.execute("SELECT state_clay,lineage_id,state_transition_count FROM frank_database_pulse_state").fetchone()
  self.assertIn('STALE_FAIL_CLOSED',state[0])
  self.assertEqual((state[1],state[2]),('lineage-constant',1))

  with self.assertRaises(StaleReadBasis):
   self.plane_for_pin(pin1).query(
    AdaptiveReadRequest('stale-read','shared semantic state',changed.source_epoch,changed.graph_epoch))
  with self.assertRaises(RuntimeError):
   self.access.pin('cycle-stale',source_epoch=2,graph_epoch=2,pinned_at='p2')

  self.publish_g2()
  coherent=self.pulse.pulse(now='p3',expected_source_epoch=2,expected_graph_epoch=2)
  self.assertEqual((coherent.semantic_generation_id,coherent.applied_delta_count),('g2',0))
  pin2=self.access.pin('cycle-2',source_epoch=coherent.source_epoch,graph_epoch=coherent.graph_epoch,pinned_at='p3')
  read2=self.plane_for_pin(pin2).query(
   AdaptiveReadRequest('read-2','shared semantic state',coherent.source_epoch,coherent.graph_epoch))
  self.assertEqual((read2.refs,read2.read_basis_id),(('record.v2',),'g2'))
  self.assertNotEqual(read1.refs,read2.refs)
  self.assertEqual(self.c.execute("SELECT lineage_id FROM frank_database_pulse_state").fetchone()[0],'lineage-constant')

 def test_head_swap_does_not_retroactively_change_pinned_cycle(self):
  self.pulse.pulse(now='p1',expected_source_epoch=1,expected_graph_epoch=1)
  pin1=self.access.pin('cycle-1',source_epoch=1,graph_epoch=1,pinned_at='p1')
  plane1=self.plane_for_pin(pin1)
  self.publish_g2()
  old=plane1.query(AdaptiveReadRequest('old','shared semantic state',1,1))
  self.assertEqual((old.refs,old.read_basis_id),(('record.v1',),'g1'))

if __name__=='__main__': unittest.main(verbosity=2)
