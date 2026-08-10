from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_rank_path_v5 import AdaptiveAuthoritativeRankPathV5
from research_entity.runtime.database_pulse_rank_path_v5_1 import AdaptiveAuthoritativeRankPathV51
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics():
    return CompileEconomics(
        build_cost_us=1000.0,
        online_query_us=100.0,
        compiled_query_us=10.0,
        online_quality=1.0,
        compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,
        safety_factor=1.0,
    )


def stable():
    return [EpochReadLifetime(i + 1, 250) for i in range(8)]


def seed(path: str):
    ledger = StateLedger(path)
    ledger.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=0,
        event_type="V51_SEED",
        writer="test",
        ops=[{
            "op": "SET",
            "domain": "memory",
            "key": f"k{i:03d}",
            "value": {"priority": i / 100.0},
            "epistemic": "KNOWN",
            "status": "CURRENT",
        } for i in range(100)],
        committed_at="2026-08-10T03:20:00Z",
    )
    return ledger


def advance(ledger: StateLedger, event_id: str):
    return ledger.append_event(
        event_id=event_id,
        idem=event_id,
        base_epoch=ledger.epoch,
        event_type="CONCURRENT_ADVANCE",
        writer="competitor",
        ops=[{
            "op": "SET",
            "domain": "memory",
            "key": event_id,
            "value": {"priority": 1.0},
            "epistemic": "KNOWN",
            "status": "CURRENT",
        }],
        committed_at="2026-08-10T03:20:01Z",
    )


class RaceInjectCurrentV5(AdaptiveAuthoritativeRankPathV5):
    def arm_after_precheck(self, callback):
        self._race_callback = callback
        self._race_armed = True

    def index_exists(self):
        present = super().index_exists()
        if getattr(self, "_race_armed", False):
            self._race_armed = False
            self._race_callback()
        return present


class RaceInjectV51(AdaptiveAuthoritativeRankPathV51):
    def arm_before_lock(self, callback):
        self._race_callback = callback
        self._race_armed = True

    def _begin_maintenance(self):
        if getattr(self, "_race_armed", False):
            self._race_armed = False
            self._race_callback()
        return super()._begin_maintenance()


class RankPathV51ConcurrencyTests(unittest.TestCase):
    def test_negative_control_current_v5_accepts_plan_that_goes_stale_after_precheck(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "v5-race.sqlite")
            owner = seed(path)
            competitor = StateLedger(path)
            try:
                route = RaceInjectCurrentV5(owner)
                plan = route.plan_lifecycle(
                    basis_epoch=owner.epoch,
                    economics_without_horizon=economics(),
                    pulse_history=stable(),
                )
                self.assertEqual(plan.maintenance_action, "BUILD_INDEX")
                self.assertEqual(plan.basis_epoch, 1)
                route.arm_after_precheck(lambda: advance(competitor, "winner-update"))
                receipt = route.apply_maintenance(plan)
                self.assertEqual(receipt.status, "BUILT")
                self.assertEqual(receipt.basis_epoch, 1)
                self.assertEqual(owner.epoch, 2)
                self.assertTrue(route.index_exists())
                # This is the falsifier: stale plan 1 performed physical maintenance at epoch 2.
                self.assertNotEqual(receipt.basis_epoch, owner.epoch)
            finally:
                competitor.close()
                owner.close()

    def test_v51_revalidates_after_writer_lock_and_rejects_same_stale_plan(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "v51-race.sqlite")
            owner = seed(path)
            competitor = StateLedger(path)
            try:
                route = RaceInjectV51(owner)
                plan = route.plan_lifecycle(
                    basis_epoch=owner.epoch,
                    economics_without_horizon=economics(),
                    pulse_history=stable(),
                )
                route.arm_before_lock(lambda: advance(competitor, "winner-update"))
                with self.assertRaises(StaleEpoch):
                    route.apply_maintenance(plan)
                self.assertEqual(owner.epoch, 2)
                self.assertFalse(route.index_exists())
            finally:
                competitor.close()
                owner.close()

    def test_v51_normal_build_and_drop_preserve_semantic_roots(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "v51-normal.sqlite")
            owner = seed(path)
            try:
                route = AdaptiveAuthoritativeRankPathV51(owner)
                roots = (owner.epoch, owner.semantic_state_hash, owner.trace_root_hash)
                build = route.plan_lifecycle(
                    basis_epoch=owner.epoch,
                    economics_without_horizon=economics(),
                    pulse_history=stable(),
                )
                built = route.apply_maintenance(build)
                self.assertEqual(built.status, "BUILT")
                self.assertTrue(route.index_exists())
                self.assertEqual(roots, (owner.epoch, owner.semantic_state_hash, owner.trace_root_hash))

                sparse = [EpochReadLifetime(1, 20), EpochReadLifetime(2, 20)]
                drop = route.plan_lifecycle(
                    basis_epoch=owner.epoch,
                    economics_without_horizon=economics(),
                    pulse_history=sparse,
                )
                self.assertEqual(drop.maintenance_action, "DROP_INDEX")
                dropped = route.apply_maintenance(drop)
                self.assertEqual(dropped.status, "DROPPED")
                self.assertFalse(route.index_exists())
                self.assertEqual(roots, (owner.epoch, owner.semantic_state_hash, owner.trace_root_hash))
            finally:
                owner.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
