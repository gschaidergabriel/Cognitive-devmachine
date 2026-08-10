from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_path_v4 import AdaptiveAuthoritativeRankPathV4
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def ledger_with_state():
    ledger = StateLedger()
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=ledger.epoch,
        event_type="RETENTION_TEST", writer="test",
        ops=[{
            "op": "SET", "domain": "memory", "key": f"k{i:03d}",
            "value": {"priority": (i % 10) / 10.0, "salience": (i % 7) / 7.0},
            "epistemic": "KNOWN", "status": "CURRENT",
        } for i in range(200)],
        committed_at="2026-08-10T03:10:00Z",
    )
    return ledger


def econ():
    return CompileEconomics(
        build_cost_us=1000.0, online_query_us=100.0, compiled_query_us=1.0,
        online_quality=1.0, compiled_quality=1.0,
        expected_reads_before_invalidation=0.0, safety_factor=1.2,
    )


class RankRetentionV4FalsifierTests(unittest.TestCase):
    def test_stable_compile_then_churn_routes_online_but_retains_existing_index(self):
        ledger = ledger_with_state()
        try:
            route = AdaptiveAuthoritativeRankPathV4(ledger)
            stable = [EpochReadLifetime(i, 1000) for i in range(8)]
            first = route.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=32, max_focus=4,
                economics_without_horizon=econ(), pulse_history=stable,
            )
            self.assertEqual(first.physical_mode, "COMPILED_INDEX")
            self.assertTrue(route.index_exists())

            churn = [EpochReadLifetime(i, 1000) for i in range(5)] + [
                EpochReadLifetime(5, 2), EpochReadLifetime(6, 1), EpochReadLifetime(7, 1)
            ]
            second = route.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=32, max_focus=4,
                economics_without_horizon=econ(), pulse_history=churn,
            )
            self.assertEqual(second.horizon_status, "CHURN_SHOCK_BOUND")
            self.assertEqual(second.physical_mode, "ONLINE_NO_COMPILE")
            self.assertTrue(second.index_present_before)
            self.assertTrue(second.index_present_after)
            self.assertTrue(route.index_exists())
        finally:
            ledger.close()

    def test_explicit_drop_is_semantically_non_authoritative(self):
        ledger = ledger_with_state()
        try:
            route = AdaptiveAuthoritativeRankPathV4(ledger)
            roots = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            route.v3.ensure_index()
            self.assertTrue(route.index_exists())
            route.v3.drop_index()
            self.assertFalse(route.index_exists())
            self.assertEqual(roots, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
            sparse = [EpochReadLifetime(1, 50), EpochReadLifetime(2, 50)]
            got = route.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=32, max_focus=4,
                economics_without_horizon=econ(), pulse_history=sparse,
            )
            self.assertEqual(got.physical_mode, "ONLINE_NO_COMPILE")
            self.assertFalse(got.index_present_after)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
