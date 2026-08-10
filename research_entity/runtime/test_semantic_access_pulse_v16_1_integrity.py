from __future__ import annotations
import unittest

from semantic_access_pulse_v12 import AccessPath, PulsePlan
from semantic_access_pulse_v16_1_integrity import (
    IntegrityGuardedSegmentedPulseProjection,
    SegmentIntegrityError,
)

SEEDS=[f"seed:{c}:{i}" for c in range(5) for i in range(4)]
VERSIONS={seed:0 for seed in SEEDS}

def paths_for(seed:str):
    _,cluster,_=seed.split(':')
    v=VERSIONS[seed]
    service=f"service:{cluster}"; resource=f"resource:{cluster}"
    deps=(seed,f"cluster:{cluster}",service,resource)
    return [
        AccessPath(f"rec:{seed}:svc:v{v}",service,1,1,1.0+v/1000,dependencies=deps),
        AccessPath(f"rec:{seed}:res:v{v}",resource,2,2,0.8+v/1000,dependencies=deps),
    ]

def all_seeds(): return list(SEEDS)

class V16IntegrityTests(unittest.TestCase):
    def setUp(self):
        for seed in VERSIONS: VERSIONS[seed]=0

    def make(self):
        x=IntegrityGuardedSegmentedPulseProjection()
        x.bootstrap(event_id='boot',source_epoch=1,graph_epoch=1,seeds=SEEDS,recompute_seed=paths_for)
        self.assertEqual(x.integrity_state()['status'],'CLEAN')
        return x

    def current_segment(self,x,seed):
        head=x._head()
        return x.con.execute(
            "SELECT segment_id FROM access_generation_seed WHERE generation_id=? AND seed_id=?",
            (head['generation_id'],seed),
        ).fetchone()[0]

    def repair_pulse(self,x,event='repair'):
        return x.apply_pulse(
            PulsePlan(event,'VALUE_UPDATE',('cluster:4',),tuple(f'seed:4:{i}' for i in range(4)),True,2,1),
            recompute_seed=paths_for,recompute_all_seeds=all_seeds,incremental_fraction_limit=.25,
        )

    def test_clean_bootstrap_has_manifest_for_every_current_segment(self):
        x=self.make()
        audit=x.deep_verify_current()
        self.assertTrue(audit['verified']); self.assertEqual(audit['segment_count'],20)
        self.assertIn(':v0',x.query('seed:2:0')[0])
        x.close()

    def test_deleted_reverse_dependency_trips_dirty_and_forces_full_repair(self):
        x=self.make(); seed='seed:1:0'; seg=self.current_segment(x,seed)
        x.con.execute(
            "DELETE FROM access_segment_dependency WHERE segment_id=? AND dependency_logical_id='cluster:1'",
            (seg,),
        ); x.con.commit()
        self.assertEqual(x.integrity_state()['status'],'DIRTY')
        self.assertEqual(x.integrity_state()['dirty_reason'],'DEPENDENCY_DELETE_AFTER_PUBLISH')
        with self.assertRaisesRegex(SegmentIntegrityError,'projection DIRTY'):
            x.query(seed)
        receipt=self.repair_pulse(x)
        self.assertEqual(receipt.mode,'FULL_FALLBACK')
        self.assertEqual(x.integrity_state()['status'],'CLEAN')
        new_seg=self.current_segment(x,seed)
        self.assertNotEqual(new_seg,seg)
        self.assertIn('-repair-',new_seg)
        self.assertIn(':v0',x.query(seed)[0])
        repair=x.con.execute("SELECT repair_mode FROM access_integrity_repair_receipt_v16_1 WHERE event_id='repair'").fetchone()
        self.assertEqual(repair[0],'FULL_FALLBACK')
        x.close()

    def test_path_update_trips_dirty_and_never_serves_tampered_rank(self):
        x=self.make(); seed='seed:2:0'; seg=self.current_segment(x,seed)
        x.con.execute("UPDATE access_segment_path SET path_weight=999 WHERE segment_id=? AND path_rank=2",(seg,)); x.con.commit()
        with self.assertRaises(SegmentIntegrityError): x.query(seed)
        receipt=self.repair_pulse(x,'repair-path')
        self.assertEqual(receipt.mode,'FULL_FALLBACK')
        self.assertEqual(x.integrity_state()['status'],'CLEAN')
        self.assertTrue(x.deep_verify_current()['verified'])
        x.close()

    def test_post_publish_path_insert_trips_dirty(self):
        x=self.make(); seed='seed:0:0'; seg=self.current_segment(x,seed)
        x.con.execute("INSERT INTO access_segment_path VALUES(?,?,?,?,?,?,?,?)",
                      (seg,'malicious','malicious',99,9,999.0,0.0,'{}')); x.con.commit()
        state=x.integrity_state(); self.assertEqual(state['status'],'DIRTY')
        self.assertEqual(state['dirty_reason'],'PATH_INSERT_AFTER_PUBLISH')
        with self.assertRaises(SegmentIntegrityError): x.query(seed)
        x.close()

    def test_current_generation_map_mutation_trips_dirty(self):
        x=self.make(); head=x._head(); replacement=self.current_segment(x,'seed:0:1')
        x.con.execute("UPDATE access_generation_seed SET segment_id=? WHERE generation_id=? AND seed_id='seed:0:0'",
                      (replacement,head['generation_id'])); x.con.commit()
        self.assertEqual(x.integrity_state()['dirty_reason'],'CURRENT_GENERATION_MAP_UPDATE')
        with self.assertRaises(SegmentIntegrityError): x.query('seed:0:0')
        receipt=self.repair_pulse(x,'repair-map'); self.assertEqual(receipt.mode,'FULL_FALLBACK')
        self.assertEqual(x.integrity_state()['status'],'CLEAN')
        self.assertTrue(x.deep_verify_current()['verified'])
        x.close()

    def test_clean_local_update_remains_incremental_and_exact(self):
        x=self.make(); impacted=tuple(f'seed:3:{i}' for i in range(4))
        for seed in impacted: VERSIONS[seed]=3
        receipt=x.apply_pulse(
            PulsePlan('local','STATUS_UPDATE',('cluster:3',),impacted,True,2,1),
            recompute_seed=paths_for,recompute_all_seeds=all_seeds,incremental_fraction_limit=.25,
        )
        self.assertEqual(receipt.mode,'SEGMENTED_INCREMENTAL_PULSE')
        self.assertEqual(receipt.reused_segment_count,16)
        self.assertEqual(x.integrity_state()['status'],'CLEAN')
        self.assertTrue(x.deep_verify_current()['verified'])
        self.assertIn(':v3',x.query('seed:3:0')[0])
        x.close()

    def test_manifest_row_tamper_is_caught_even_without_tripwire(self):
        x=self.make(); seed='seed:4:0'; seg=self.current_segment(x,seed)
        # Manifests are not part of the mutation trigger because they are the independent
        # certificate itself. A forged certificate therefore must fail direct verification.
        x.con.execute("UPDATE access_segment_manifest_v16_1 SET manifest_hash='forged' WHERE segment_id=?",(seg,)); x.con.commit()
        with self.assertRaisesRegex(SegmentIntegrityError,'manifest hash mismatch'):
            x.query(seed)
        self.assertEqual(x.integrity_state()['status'],'DIRTY')
        x.close()

if __name__=='__main__': unittest.main(verbosity=2)
