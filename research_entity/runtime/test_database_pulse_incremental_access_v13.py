#!/usr/bin/env python3
from __future__ import annotations
import sqlite3, unittest
from pathlib import Path
from database_pulse_v0 import DatabasePulseV0
from pulse_incremental_access_v13 import IncrementalAccessInvariant, PulseIncrementalSemanticAccessV13

HERE=Path(__file__).resolve().parent
U10=(HERE/'RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql').read_text(encoding='utf-8')
U11=(HERE/'RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql').read_text(encoding='utf-8')
U12=(HERE/'RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql').read_text(encoding='utf-8')
U13=(HERE/'RAE_UNIFIEDDB_V13_PULSE_INCREMENTAL_ACCESS.sql').read_text(encoding='utf-8')

def path(ref): return {'target_record_id':ref,'target_logical_id':ref,'path_rank':1,'hop_count':1,'path_weight':1.0,'authority_rank':0.0,'path_clay':'{}'}
def dep(ref): return {'dependency_ref':ref,'dependency_kind':'SEMANTIC','dependency_version_hash':'h','proof_eligible':True}

class DatabasePulseIncrementalAccessV13Tests(unittest.TestCase):
    def make(self):
        con=sqlite3.connect(':memory:'); con.executescript(U10); con.executescript(U11); con.executescript(U12); con.executescript(U13)
        pulse=DatabasePulseV0(con); pulse.bootstrap(entity_id='frank',lineage_id='lineage',source_epoch=1,graph_epoch=1,now='t0')
        con.executemany("""INSERT INTO semantic_query_seeds
          (seed_version_id,seed_id,normalized_key,logical_id,seed_class,confidence,provenance_clay,source_epoch,graph_epoch,status,created_at,updated_at)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",[
          ('va','a','alpha','a','CANONICAL',1.0,'{}',1,1,'CURRENT','t0','t0'),
          ('vb','b','beta','b','CANONICAL',1.0,'{}',1,1,'CURRENT','t0','t0'),
          ('vc','c','gamma','c','CANONICAL',1.0,'{}',1,1,'CURRENT','t0','t0')])
        con.commit(); access=PulseIncrementalSemanticAccessV13(con)
        for seed,ref,capture in [('a','a-old','COMPLETE'),('b','b-stable','COMPLETE'),('c','c-old','PARTIAL')]:
            access.stage_seed_generation(generation_id=f'g-{seed}-1',seed_id=seed,derivation_id='u13-test',derivation_hash=f'h-{seed}-1',paths=[path(ref)],dependencies=[dep(f'semantic:{seed}')],dependency_capture=capture,created_at='t0')
            access.install_seed_head(seed_id=seed,generation_id=f'g-{seed}-1',dependency_capture=capture,now='t0')
        return con,pulse,access

    def test_real_zero_model_pulse_invalidates_only_affected_complete_heads(self):
        con,pulse,access=self.make()
        pulse.admit_delta(delta_id='d-a',changed_ref='semantic:a',reason_class='STATE_UPDATE',payload={'v':2},source_epoch=2,graph_epoch=1,now='a')
        receipt=pulse.pulse(now='p1',model_call_count=0)
        self.assertEqual(receipt.model_call_count,0)
        self.assertEqual(access.query('alpha',source_epoch=2,graph_epoch=1).mode,'MISS')
        self.assertEqual(access.query('beta',source_epoch=2,graph_epoch=1).refs,('b-stable',))
        self.assertEqual(access.query('gamma',source_epoch=2,graph_epoch=1).mode,'MISS')
        self.assertEqual(con.execute("SELECT status FROM semantic_access_seed_heads_v13 WHERE seed_id='b'").fetchone()[0],'CURRENT')

    def test_rebuild_only_affected_seed_restores_fastpath_at_new_epoch(self):
        _,pulse,access=self.make()
        pulse.admit_delta(delta_id='d-a',changed_ref='semantic:a',reason_class='STATE_UPDATE',payload={'v':2},source_epoch=2,graph_epoch=1,now='a'); pulse.pulse(now='p1')
        access.stage_seed_generation(generation_id='g-a-2',seed_id='a',derivation_id='u13-test',derivation_hash='h-a-2',paths=[path('a-new')],dependencies=[dep('semantic:a')],created_at='r')
        access.install_seed_head(seed_id='a',generation_id='g-a-2',dependency_capture='COMPLETE',now='r')
        self.assertEqual(access.query('alpha',source_epoch=2,graph_epoch=1).refs,('a-new',))
        self.assertEqual(access.query('beta',source_epoch=2,graph_epoch=1).refs,('b-stable',))

    def test_injected_pulse_failure_rolls_back_u13_invalidation(self):
        con,pulse,_=self.make()
        pulse.admit_delta(delta_id='fault',changed_ref='semantic:a',reason_class='STATE_UPDATE',payload={'v':2},source_epoch=2,graph_epoch=1,now='a')
        with self.assertRaisesRegex(RuntimeError,'injected fault'):
            pulse.pulse(now='fault',fault_after_apply=True)
        self.assertEqual(con.execute("SELECT status FROM semantic_access_seed_heads_v13 WHERE seed_id='a'").fetchone()[0],'CURRENT')
        self.assertEqual(con.execute("SELECT count(*) FROM semantic_access_seed_invalidations_v13").fetchone()[0],0)

    def test_global_compiler_barrier_stales_all_heads_even_without_ref_prefix(self):
        con,pulse,_=self.make()
        pulse.admit_delta(delta_id='compiler',changed_ref='odd-noncanonical-ref',reason_class='COMPILER_CHANGE',payload={'v':2},source_epoch=2,graph_epoch=1,now='a'); pulse.pulse(now='p')
        self.assertEqual(con.execute("SELECT count(*) FROM semantic_access_seed_heads_v13 WHERE status='STALE'").fetchone()[0],3)
        self.assertEqual(con.execute("SELECT count(*) FROM semantic_access_seed_invalidations_v13 WHERE invalidation_class='GLOBAL_BARRIER'").fetchone()[0],3)

    def test_unprocessed_future_epoch_never_uses_incremental_fastpath(self):
        _,_,access=self.make(); self.assertEqual(access.query('beta',source_epoch=2,graph_epoch=1).mode,'MISS')

    def test_dependency_version_tamper_breaks_head_certificate(self):
        con,_,access=self.make(); self.assertTrue(access.verify_seed_head('a')['verified'])
        con.execute("UPDATE semantic_access_seed_dependencies_v13 SET dependency_version_hash='tampered' WHERE generation_id='g-a-1' AND seed_id='a'"); con.commit()
        with self.assertRaisesRegex(IncrementalAccessInvariant,'certificate hash mismatch'):
            access.verify_seed_head('a')

    def test_stage_inside_outer_transaction_uses_savepoint_not_hidden_commit(self):
        con,_,access=self.make()
        con.execute("CREATE TABLE caller_state(v TEXT)"); con.execute("INSERT INTO caller_state VALUES('must-rollback')")
        self.assertTrue(con.in_transaction)
        access.stage_seed_generation(generation_id='g-a-nested',seed_id='a',derivation_id='nested',derivation_hash='nested-h',paths=[path('nested')],dependencies=[dep('semantic:a')],created_at='nested')
        self.assertTrue(con.in_transaction)
        con.rollback()
        self.assertEqual(con.execute("SELECT count(*) FROM caller_state").fetchone()[0],0)
        self.assertEqual(con.execute("SELECT count(*) FROM semantic_access_generations WHERE generation_id='g-a-nested'").fetchone()[0],0)

if __name__=='__main__': unittest.main(verbosity=2)
