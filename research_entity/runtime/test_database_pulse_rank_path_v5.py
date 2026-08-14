from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_rank_path_v5 import AdaptiveAuthoritativeRankPathV5
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics():
    return CompileEconomics(
        build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
        online_quality=1.0,compiled_quality=1.0,
        expected_reads_before_invalidation=0.0,safety_factor=1.0)


def seed():
    l=StateLedger()
    ops=[]
    for i in range(100):
        ops.append({"op":"SET","domain":"memory","key":f"k{i:03d}",
                    "value":{"priority":i/100.0},"epistemic":"KNOWN","status":"CURRENT"})
    l.append_event(event_id="seed",idem="seed",base_epoch=0,event_type="SEED",writer="test",ops=ops,
                   committed_at="2026-08-10T02:00:00Z")
    return l,AdaptiveAuthoritativeRankPathV5(l)


def stable_long():
    return [EpochReadLifetime(i+1,200) for i in range(8)]


def sparse():
    return [EpochReadLifetime(1,200),EpochReadLifetime(2,200)]


class RankPathV5Tests(unittest.TestCase):
    def test_select_never_builds_index_even_when_compile_desired(self):
        l,v=seed(); before=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
        self.assertFalse(v.index_exists())
        r=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=32,max_focus=4,
                   economics_without_horizon=economics(),pulse_history=stable_long())
        self.assertEqual(r.desired_mode,"COMPILED_INDEX")
        self.assertEqual(r.maintenance_action,"BUILD_INDEX")
        self.assertEqual(r.physical_read_mode,"ONLINE_PENDING_COMPILE")
        self.assertFalse(v.index_exists())
        self.assertEqual(before,(l.epoch,l.semantic_state_hash,l.trace_root_hash))
        l.close()

    def test_maintenance_build_then_next_read_is_compiled(self):
        l,v=seed()
        p=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        m=v.apply_maintenance(p)
        self.assertEqual(m.status,"BUILT"); self.assertTrue(v.index_exists())
        r=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=32,max_focus=4,
                   economics_without_horizon=economics(),pulse_history=stable_long())
        self.assertEqual(r.physical_read_mode,"COMPILED_INDEX")
        self.assertTrue(any(INDEX_NAME in x for x in r.query_plan))
        l.close()

    def test_churn_or_sparse_history_forces_online_before_drop_maintenance(self):
        l,v=seed()
        build=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        self.assertEqual(v.apply_maintenance(build).status,"BUILT")
        r=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=32,max_focus=4,
                   economics_without_horizon=economics(),pulse_history=sparse())
        self.assertEqual(r.desired_mode,"ONLINE")
        self.assertEqual(r.maintenance_action,"DROP_INDEX")
        self.assertEqual(r.physical_read_mode,"ONLINE_PENDING_DECOMPILE")
        self.assertTrue(v.index_exists())
        # NOT INDEXED must prevent the still-present stale accelerator from being used for the read.
        self.assertFalse(any(INDEX_NAME in x for x in r.query_plan))
        l.close()

    def test_drop_maintenance_stops_future_write_amplification_surface(self):
        l,v=seed()
        build=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        v.apply_maintenance(build); self.assertTrue(v.index_exists())
        drop=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=sparse())
        m=v.apply_maintenance(drop)
        self.assertEqual(m.status,"DROPPED"); self.assertFalse(v.index_exists())
        self.assertEqual(m.semantic_state_hash_before,m.semantic_state_hash_after)
        self.assertEqual(m.trace_root_hash_before,m.trace_root_hash_after)
        l.close()

    def test_stale_maintenance_plan_is_rejected(self):
        l,v=seed()
        p=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        l.append_event(event_id="advance",idem="advance",base_epoch=l.epoch,event_type="UPDATE",writer="test",
                       ops=[{"op":"SET","domain":"memory","key":"new","value":{"priority":1.0},
                             "epistemic":"KNOWN","status":"CURRENT"}],
                       committed_at="2026-08-10T02:00:01Z")
        with self.assertRaises(StaleEpoch): v.apply_maintenance(p)
        self.assertFalse(v.index_exists())
        l.close()

    def test_online_and_prepared_compiled_paths_are_semantically_identical(self):
        l,v=seed()
        online=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=50,max_focus=10,
                        economics_without_horizon=economics(),pulse_history=sparse())
        p=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        v.apply_maintenance(p)
        compiled=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=50,max_focus=10,
                          economics_without_horizon=economics(),pulse_history=stable_long())
        self.assertEqual(online.candidate_refs,compiled.candidate_refs)
        self.assertEqual(online.focus_refs,compiled.focus_refs)
        self.assertEqual(online.candidate_scores,compiled.candidate_scores)
        l.close()

    def test_truthful_reentry_equivalent_online_and_compiled(self):
        l,v=seed(); previous=("memory:k000",)
        online=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=100,max_focus=1,
                        economics_without_horizon=economics(),pulse_history=sparse(),
                        reentry_mode="TRUTHFUL",previous_focus_refs=previous)
        p=v.plan_lifecycle(basis_epoch=l.epoch,economics_without_horizon=economics(),pulse_history=stable_long())
        v.apply_maintenance(p)
        compiled=v.select(source_domains=("memory",),basis_epoch=l.epoch,max_candidates=100,max_focus=1,
                          economics_without_horizon=economics(),pulse_history=stable_long(),
                          reentry_mode="TRUTHFUL",previous_focus_refs=previous)
        self.assertEqual(online.focus_refs,compiled.focus_refs)
        l.close()

    def test_output_and_control_domains_are_rejected(self):
        l,v=seed()
        for domains in (("pulse",),("memory","pulse_control")):
            with self.assertRaises(ValueError):
                v.select(source_domains=domains,basis_epoch=l.epoch,max_candidates=8,max_focus=1,
                         economics_without_horizon=economics(),pulse_history=sparse())
        l.close()

if __name__=="__main__":unittest.main(verbosity=2)
