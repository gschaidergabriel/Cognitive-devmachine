from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    LEGACY_MAINTENANCE_PROVENANCE,
    MAINTENANCE_LOG_TABLE,
    RankPhysicalStateStale,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def stable_econ():
    return CompileEconomics(build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
                            online_quality=1.0,compiled_quality=1.0,
                            expected_reads_before_invalidation=0.0,safety_factor=1.0)
def stable_history():
    return tuple(EpochReadLifetime(i+1,200) for i in range(8))
def sparse_history():
    return (EpochReadLifetime(1,2),EpochReadLifetime(2,2))
def seed():
    l=StateLedger()
    l.append_event(event_id="seed",idem="seed",base_epoch=0,event_type="SEED",writer="test",
                   ops=[{"op":"SET","domain":"memory","key":"x","value":{"priority":1.0},
                         "epistemic":"KNOWN","status":"CURRENT"}],
                   committed_at="2026-08-10T03:10:00Z")
    return l,AdaptiveAuthoritativeRankPathV5(l)


def create_legacy_v5_log(l):
    l.conn.execute(f"""CREATE TABLE {MAINTENANCE_LOG_TABLE}(
        receipt_id TEXT PRIMARY KEY,
        plan_hash TEXT NOT NULL UNIQUE,
        basis_epoch INTEGER NOT NULL,
        action TEXT NOT NULL,
        status TEXT NOT NULL,
        index_present_before INTEGER NOT NULL,
        index_present_after INTEGER NOT NULL,
        semantic_state_hash_before TEXT NOT NULL,
        semantic_state_hash_after TEXT NOT NULL,
        trace_root_hash_before TEXT NOT NULL,
        trace_root_hash_after TEXT NOT NULL,
        executed_at TEXT NOT NULL,
        authority TEXT NOT NULL
    )""")
    l.conn.execute(f"""INSERT INTO {MAINTENANCE_LOG_TABLE}(
        receipt_id,plan_hash,basis_epoch,action,status,index_present_before,index_present_after,
        semantic_state_hash_before,semantic_state_hash_after,trace_root_hash_before,
        trace_root_hash_after,executed_at,authority
    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        ("legacy-receipt","legacy-plan",l.epoch,"NONE","NO_CHANGE",0,0,
         l.semantic_state_hash,l.semantic_state_hash,l.trace_root_hash,l.trace_root_hash,
         "2026-08-10T03:10:00Z","PHYSICAL_INDEX_MAINTENANCE_ONLY_NO_SEMANTIC_AUTHORITY"))
    l.conn.commit()


class RankPathV5AtomicMaintenanceTests(unittest.TestCase):
    def test_successful_build_is_durably_receipted_in_same_physical_state(self):
        l,r=seed()
        try:
            roots=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            receipt=r.apply_maintenance(plan,actor="atomic-test",policy_provenance_ref="policy:stable")
            self.assertEqual(receipt.status,"BUILT")
            self.assertTrue(receipt.persisted)
            self.assertIsNotNone(receipt.receipt_id)
            self.assertEqual(receipt.actor,"atomic-test")
            self.assertEqual(receipt.policy_provenance_ref,"policy:stable")
            self.assertTrue(r.index_exists())
            rows=r.maintenance_receipts()
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0]["receipt_id"],receipt.receipt_id)
            self.assertEqual(rows[0]["plan_hash"],plan.plan_hash)
            self.assertEqual(rows[0]["status"],"BUILT")
            self.assertEqual(rows[0]["actor"],"atomic-test")
            self.assertEqual(rows[0]["policy_provenance_ref"],"policy:stable")
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_legacy_v5_log_migrates_in_same_transaction_without_inventing_old_provenance(self):
        l,r=seed()
        try:
            create_legacy_v5_log(l)
            roots=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            receipt=r.apply_maintenance(plan,actor="migration-test",policy_provenance_ref="policy:migration")
            self.assertEqual(receipt.status,"BUILT")
            self.assertTrue(receipt.persisted)
            rows=r.maintenance_receipts()
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]["actor"],LEGACY_MAINTENANCE_PROVENANCE)
            self.assertEqual(rows[0]["policy_provenance_ref"],LEGACY_MAINTENANCE_PROVENANCE)
            self.assertEqual(rows[1]["actor"],"migration-test")
            self.assertEqual(rows[1]["policy_provenance_ref"],"policy:migration")
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_reapplying_same_build_plan_is_physical_cas_rejected_not_false_built(self):
        l,r=seed()
        try:
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            first=r.apply_maintenance(plan)
            self.assertEqual(first.status,"BUILT")
            with self.assertRaises(RankPhysicalStateStale):r.apply_maintenance(plan)
            self.assertEqual(len(r.maintenance_receipts()),1)
            self.assertTrue(r.index_exists())
        finally:l.close()

    def test_receipt_insert_failure_rolls_back_build(self):
        l,r=seed()
        try:
            # Deliberately incompatible pre-existing audit table: migration can add provenance
            # columns inside the transaction, but receipt INSERT still fails on the missing base
            # columns. The ALTERs and CREATE INDEX must roll back together.
            l.conn.execute(f"CREATE TABLE {MAINTENANCE_LOG_TABLE}(wrong TEXT)");l.conn.commit()
            roots=(l.semantic_state_hash,l.trace_root_hash)
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            receipt=r.apply_maintenance(plan)
            self.assertEqual(receipt.status,"FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
            self.assertFalse(receipt.persisted)
            self.assertFalse(r.index_exists(),"CREATE INDEX must roll back when receipt write fails")
            self.assertEqual({str(x[1]) for x in l.conn.execute(f"PRAGMA table_info({MAINTENANCE_LOG_TABLE})")},{"wrong"})
            self.assertEqual((l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_receipt_insert_failure_rolls_back_drop(self):
        l,r=seed()
        try:
            r.v3.ensure_index();self.assertTrue(r.index_exists())
            l.conn.execute(f"CREATE TABLE {MAINTENANCE_LOG_TABLE}(wrong TEXT)");l.conn.commit()
            roots=(l.semantic_state_hash,l.trace_root_hash)
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=sparse_history())
            self.assertEqual(plan.maintenance_action,"DROP_INDEX")
            receipt=r.apply_maintenance(plan)
            self.assertEqual(receipt.status,"FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
            self.assertTrue(r.index_exists(),"DROP INDEX must roll back when receipt write fails")
            self.assertEqual({str(x[1]) for x in l.conn.execute(f"PRAGMA table_info({MAINTENANCE_LOG_TABLE})")},{"wrong"})
            self.assertEqual((l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_external_physical_change_invalidates_plan_even_when_semantic_epoch_matches(self):
        l,r=seed()
        try:
            plan=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            self.assertFalse(plan.actual_index_present)
            r.v3.ensure_index()
            roots=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
            with self.assertRaises(RankPhysicalStateStale):r.apply_maintenance(plan)
            self.assertTrue(r.index_exists())
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_successful_drop_is_durably_receipted_and_roots_stay_fixed(self):
        l,r=seed()
        try:
            build=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=stable_history())
            self.assertEqual(r.apply_maintenance(build).status,"BUILT")
            roots=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
            drop=r.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=stable_econ(),pulse_history=sparse_history())
            receipt=r.apply_maintenance(drop)
            self.assertEqual(receipt.status,"DROPPED")
            self.assertTrue(receipt.persisted)
            self.assertFalse(r.index_exists())
            self.assertEqual(len(r.maintenance_receipts()),2)
            self.assertEqual([x["status"] for x in r.maintenance_receipts()],["BUILT","DROPPED"])
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()


if __name__=="__main__":unittest.main(verbosity=2)
