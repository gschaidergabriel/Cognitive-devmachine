from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v4 import AdaptiveAuthoritativeRankPathV4
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def seed(n=180):
    ledger=StateLedger()
    ops=[]
    for i in range(n):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:04d}",
                    "value":{"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0,"fact":i},
                    "epistemic":"KNOWN","status":"CURRENT"})
    ops.append({"op":"SET","domain":"memory","key":"zzzz-critical",
                "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN","status":"CURRENT"})
    ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="V4_TEST_SEED",
                        writer="test",ops=ops,committed_at="2026-08-10T02:10:00Z")
    return ledger


def econ(build=1000.0, online=100.0, compiled=10.0):
    return CompileEconomics(build_cost_us=build,online_query_us=online,compiled_query_us=compiled,
                            online_quality=1.0,compiled_quality=1.0,expected_reads_before_invalidation=0.0,
                            safety_factor=1.2)


def history(reads, n=8):
    return [EpochReadLifetime(i,reads,True,False) for i in range(n)]


class AdaptiveAuthoritativeRankPathV4Tests(unittest.TestCase):
    def test_sparse_history_stays_online_without_hidden_index_build_but_is_correct(self):
        ledger=seed()
        try:
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            before=(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash)
            got=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1,
                             economics_without_horizon=econ(),pulse_history=history(100,2))
            self.assertEqual(got.focus_refs,("memory:zzzz-critical",))
            self.assertEqual(got.physical_mode,"ONLINE_NO_COMPILE")
            self.assertEqual(got.horizon_status,"INSUFFICIENT_HISTORY")
            self.assertFalse(got.index_present_before)
            self.assertFalse(got.index_present_after)
            self.assertFalse(route.index_exists())
            self.assertEqual(before,(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash))
        finally:
            ledger.close()

    def test_long_stable_horizon_builds_index_and_query_remains_correct(self):
        ledger=seed()
        try:
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            got=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1,
                             economics_without_horizon=econ(build=1000,online=100,compiled=10),
                             pulse_history=history(100,8))
            self.assertEqual(got.focus_refs,("memory:zzzz-critical",))
            self.assertEqual(got.physical_mode,"COMPILED_INDEX")
            self.assertFalse(got.index_present_before)
            self.assertTrue(got.index_present_after)
            self.assertTrue(any(INDEX_NAME in p for p in got.query_plan),got.query_plan)
            self.assertGreater(got.horizon_reads_lower_bound,got.guarded_break_even_reads)
        finally:
            ledger.close()

    def test_short_horizon_remains_online_by_economics_not_epistemics(self):
        ledger=seed()
        try:
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            got=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1,
                             economics_without_horizon=econ(build=10000,online=100,compiled=90),
                             pulse_history=history(20,8))
            self.assertEqual(got.focus_refs,("memory:zzzz-critical",))
            self.assertEqual(got.physical_mode,"ONLINE_NO_COMPILE")
            self.assertEqual(got.compile_reason,"EXPECTED_LIFETIME_BELOW_GUARDED_BREAK_EVEN")
            self.assertFalse(route.index_exists())
        finally:
            ledger.close()

    def test_churn_shock_uses_recent_floor_and_can_cancel_compile(self):
        ledger=seed()
        try:
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            samples=[EpochReadLifetime(i,1000) for i in range(5)] + [
                EpochReadLifetime(5,5),EpochReadLifetime(6,4),EpochReadLifetime(7,3)
            ]
            got=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1,
                             economics_without_horizon=econ(build=1000,online=100,compiled=10),pulse_history=samples)
            self.assertEqual(got.horizon_status,"CHURN_SHOCK_BOUND")
            self.assertEqual(got.horizon_reads_lower_bound,3.0)
            self.assertEqual(got.physical_mode,"ONLINE_NO_COMPILE")
            self.assertFalse(route.index_exists())
        finally:
            ledger.close()

    def test_compile_failure_falls_back_to_correct_online_path(self):
        ledger=seed()
        try:
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            route.v3.ensure_index=lambda: (_ for _ in ()).throw(RuntimeError("injected build failure"))
            got=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=64,max_focus=1,
                             economics_without_horizon=econ(),pulse_history=history(100,8))
            self.assertEqual(got.focus_refs,("memory:zzzz-critical",))
            self.assertEqual(got.physical_mode,"ONLINE_COMPILE_FAILED_FALLBACK")
            self.assertFalse(got.index_present_after)
        finally:
            ledger.close()

    def test_truthful_reentry_is_semantically_same_online_and_compiled(self):
        ledger=StateLedger()
        try:
            ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
                ],committed_at="2026-08-10T02:10:00Z")
            route=AdaptiveAuthoritativeRankPathV4(ledger)
            online=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=1,max_focus=1,
                                economics_without_horizon=econ(),pulse_history=history(100,2),
                                reentry_mode="TRUTHFUL",previous_focus_refs=("memory:previous",))
            self.assertEqual(online.focus_refs,("memory:previous",))
            compiled=route.select(source_domains=("memory",),basis_epoch=ledger.epoch,max_candidates=1,max_focus=1,
                                  economics_without_horizon=econ(),pulse_history=history(100,8),
                                  reentry_mode="TRUTHFUL",previous_focus_refs=("memory:previous",))
            self.assertEqual(compiled.focus_refs,online.focus_refs)
            self.assertEqual(compiled.candidate_scores,online.candidate_scores)
        finally:
            ledger.close()


if __name__=='__main__': unittest.main(verbosity=2)
