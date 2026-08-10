from __future__ import annotations

import os
import tempfile
import time
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    RankPhysicalStateStale,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def stable_econ():
    return CompileEconomics(
        build_cost_us=1000.0,
        online_query_us=100.0,
        compiled_query_us=10.0,
        online_quality=1.0,
        compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,
        safety_factor=1.0,
    )


def stable_history():
    return tuple(EpochReadLifetime(i + 1, 200) for i in range(8))


def seed_file(path: str):
    writer = StateLedger(path)
    writer.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=0,
        event_type="SEED",
        writer="test",
        ops=[{
            "op": "SET",
            "domain": "memory",
            "key": "x",
            "value": {"priority": 1.0},
            "epistemic": "KNOWN",
            "status": "CURRENT",
        }],
        committed_at="2026-08-10T01:01:00Z",
    )
    maintenance_ledger = StateLedger(path)
    return writer, maintenance_ledger, AdaptiveAuthoritativeRankPathV5(maintenance_ledger)


class RankPathV5TwoConnectionTests(unittest.TestCase):
    def temp_path(self):
        fd, path = tempfile.mkstemp(prefix="clay-v5-concurrency-", suffix=".sqlite3")
        os.close(fd)
        return path

    def cleanup(self, path):
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(path + suffix)
            except FileNotFoundError:
                pass

    def test_foreign_writer_lock_fails_retryably_then_replan_recovers(self):
        path = self.temp_path()
        a = b = None
        try:
            a, b, rank_b = seed_file(path)
            # Keep the contention falsifier bounded; the production default stays 10s.
            b.conn.execute("PRAGMA busy_timeout=50")
            plan = rank_b.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=stable_econ(),
                pulse_history=stable_history(),
            )
            self.assertEqual(plan.maintenance_action, "BUILD_INDEX")
            roots = (b.epoch, b.semantic_state_hash, b.trace_root_hash)

            a.conn.execute("BEGIN IMMEDIATE")
            started = time.perf_counter()
            receipt = rank_b.apply_maintenance(plan)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self.assertEqual(receipt.status, "FAILED_RETRYABLE_PHYSICAL_MAINTENANCE")
            self.assertFalse(receipt.persisted)
            self.assertFalse(rank_b.index_exists())
            self.assertEqual(rank_b.maintenance_receipts(), [])
            self.assertEqual((b.epoch, b.semantic_state_hash, b.trace_root_hash), roots)
            # Do not silently block for the StateLedger production 10s busy timeout.
            self.assertLess(elapsed_ms, 1000.0)
            a.conn.rollback()

            # Recovery is a fresh observation/plan, never replaying the failed plan.
            recovered_plan = rank_b.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=stable_econ(),
                pulse_history=stable_history(),
            )
            recovered = rank_b.apply_maintenance(recovered_plan)
            self.assertEqual(recovered.status, "BUILT")
            self.assertTrue(recovered.persisted)
            self.assertTrue(rank_b.index_exists())
            self.assertEqual(len(rank_b.maintenance_receipts()), 1)
            self.assertEqual((b.epoch, b.semantic_state_hash, b.trace_root_hash), roots)
        finally:
            if a is not None:
                try: a.conn.rollback()
                except Exception: pass
                a.close()
            if b is not None:
                b.close()
            self.cleanup(path)

    def test_foreign_semantic_commit_invalidates_old_maintenance_plan(self):
        path = self.temp_path()
        a = b = None
        try:
            a, b, rank_b = seed_file(path)
            plan = rank_b.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=stable_econ(),
                pulse_history=stable_history(),
            )
            a.append_event(
                event_id="writer-a-update",
                idem="writer-a-update",
                base_epoch=a.epoch,
                event_type="UPDATE",
                writer="writer-a",
                ops=[{
                    "op": "SET",
                    "domain": "memory",
                    "key": "y",
                    "value": {"priority": 0.9},
                    "epistemic": "KNOWN",
                    "status": "CURRENT",
                }],
                committed_at="2026-08-10T01:02:00Z",
            )
            new_roots = (b.epoch, b.semantic_state_hash, b.trace_root_hash)
            self.assertNotEqual(plan.basis_epoch, new_roots[0])
            with self.assertRaises(StaleEpoch):
                rank_b.apply_maintenance(plan)
            self.assertFalse(rank_b.index_exists())
            self.assertEqual(rank_b.maintenance_receipts(), [])
            self.assertEqual((b.epoch, b.semantic_state_hash, b.trace_root_hash), new_roots)
        finally:
            if a is not None: a.close()
            if b is not None: b.close()
            self.cleanup(path)

    def test_foreign_physical_change_invalidates_plan_without_semantic_drift(self):
        path = self.temp_path()
        a = b = None
        try:
            a, b, rank_b = seed_file(path)
            rank_a = AdaptiveAuthoritativeRankPathV5(a)
            plan = rank_b.plan_lifecycle(
                basis_epoch=b.epoch,
                economics_without_horizon=stable_econ(),
                pulse_history=stable_history(),
            )
            roots = (b.epoch, b.semantic_state_hash, b.trace_root_hash)
            self.assertFalse(plan.actual_index_present)
            rank_a.v3.ensure_index()
            self.assertTrue(rank_b.index_exists())
            with self.assertRaises(RankPhysicalStateStale):
                rank_b.apply_maintenance(plan)
            self.assertTrue(rank_b.index_exists())
            self.assertEqual(rank_b.maintenance_receipts(), [])
            self.assertEqual((b.epoch, b.semantic_state_hash, b.trace_root_hash), roots)
        finally:
            if a is not None: a.close()
            if b is not None: b.close()
            self.cleanup(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
