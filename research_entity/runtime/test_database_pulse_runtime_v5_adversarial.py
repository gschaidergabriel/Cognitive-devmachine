from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_runtime_v4 import PulseRankPolicyV4
from research_entity.runtime.database_pulse_runtime_v5 import DatabasePulseRuntimeV5
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def stable_policy():
    return PulseRankPolicyV4(
        economics_without_horizon=CompileEconomics(
            build_cost_us=1000.0,online_query_us=100.0,compiled_query_us=10.0,
            online_quality=1.0,compiled_quality=1.0,
            expected_reads_before_invalidation=0.0,safety_factor=1.0),
        pulse_history=tuple(EpochReadLifetime(i+1,200) for i in range(8)),
        provenance_ref="adversarial:stable")


def seed(provider=None):
    l=StateLedger()
    l.append_event(
        event_id="seed",idem="seed",base_epoch=l.epoch,event_type="SEED",writer="adversarial",
        ops=[
            {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
            {"op":"SET","domain":"memory","key":"challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
        ],committed_at="2026-08-10T03:00:00Z")
    r=DatabasePulseRuntimeV5(l,rank_policy_provider=provider)
    r.set_scheduler(enabled=True,event_id="on",base_epoch=l.epoch,actor="adversarial",reason="test",
                    committed_at="2026-08-10T03:00:01Z")
    return l,r


class DatabasePulseRuntimeV5AdversarialTests(unittest.TestCase):
    def test_default_unmeasured_policy_never_creates_index(self):
        l,r=seed()
        try:
            out=r.run_pulse(PulseSpec("default",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=2,max_focus=1),
                            committed_at="2026-08-10T03:00:02Z")
            latest=l.get("pulse","latest")["value"]
            self.assertEqual(out.focus_refs,("memory:challenger",))
            self.assertEqual(latest["physical_rank_mode"],"ONLINE")
            self.assertEqual(latest["rank_maintenance_recommendation"],"NONE")
            self.assertEqual(latest["rank_policy_provenance_ref"],"UNMEASURED_FAIL_ONLINE")
            self.assertFalse(r.rank_path.index_exists())
        finally:l.close()

    def test_idempotent_retry_does_not_reconsult_policy_or_change_epoch(self):
        calls=[]
        def provider(spec):calls.append(spec.pulse_id);return stable_policy()
        l,r=seed(provider)
        try:
            spec=PulseSpec("idem",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=2,max_focus=1)
            first=r.run_pulse(spec,committed_at="2026-08-10T03:00:02Z");epoch=l.epoch
            second=r.run_pulse(spec,committed_at="2026-08-10T03:00:03Z")
            self.assertEqual(second.status,"ALREADY_COMMITTED")
            self.assertEqual(first.receipt_hash,second.receipt_hash)
            self.assertEqual(l.epoch,epoch)
            self.assertEqual(calls,["idem"])
            self.assertFalse(r.rank_path.index_exists())
        finally:l.close()

    def test_stale_pulse_fails_before_policy_invocation(self):
        calls=[]
        def provider(spec):calls.append(spec.pulse_id);return stable_policy()
        l,r=seed(provider)
        try:
            stale=l.epoch
            l.append_event(event_id="advance",idem="advance",base_epoch=l.epoch,event_type="UPDATE",writer="adversarial",
                           ops=[{"op":"SET","domain":"memory","key":"other","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
                           committed_at="2026-08-10T03:00:02Z")
            with self.assertRaises(StaleEpoch):
                r.run_pulse(PulseSpec("stale",basis_epoch=stale,source_domains=("memory",)))
            self.assertEqual(calls,[])
            self.assertFalse(r.rank_path.index_exists())
        finally:l.close()

    def test_maintenance_build_and_drop_leave_semantic_and_trace_roots_unchanged(self):
        l,r=seed(lambda spec:stable_policy())
        try:
            roots=(l.epoch,l.semantic_state_hash,l.trace_root_hash)
            built=r.maintain_rank_index(basis_epoch=l.epoch,policy=stable_policy(),actor="adversarial-maintainer")
            self.assertEqual(built.receipt.status,"BUILT")
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
            sparse=PulseRankPolicyV4(
                economics_without_horizon=stable_policy().economics_without_horizon,
                pulse_history=(EpochReadLifetime(1,2),EpochReadLifetime(2,2)),
                provenance_ref="adversarial:sparse")
            dropped=r.maintain_rank_index(basis_epoch=l.epoch,policy=sparse,actor="adversarial-maintainer")
            self.assertEqual(dropped.receipt.status,"DROPPED")
            self.assertEqual((l.epoch,l.semantic_state_hash,l.trace_root_hash),roots)
        finally:l.close()

    def test_truthful_reentry_lesion_changes_focus_without_effect_authority(self):
        l,r=seed()
        try:
            l.append_event(event_id="raise-prev",idem="raise-prev",base_epoch=l.epoch,event_type="UPDATE",writer="adversarial",
                           ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
                           committed_at="2026-08-10T03:00:02Z")
            first=r.run_pulse(PulseSpec("first",basis_epoch=l.epoch,source_domains=("memory",),max_candidates=2,max_focus=1),
                              committed_at="2026-08-10T03:00:03Z")
            self.assertEqual(first.focus_refs,("memory:previous",))
            l.append_event(event_id="lower-prev",idem="lower-prev",base_epoch=l.epoch,event_type="UPDATE",writer="adversarial",
                           ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"}],
                           committed_at="2026-08-10T03:00:04Z")
            events=l.export_events()
        finally:l.close()
        truth_l=StateLedger.replay(events);lesion_l=StateLedger.replay(events)
        try:
            truth=DatabasePulseRuntimeV5(truth_l).run_pulse(
                PulseSpec("truth",basis_epoch=truth_l.epoch,source_domains=("memory",),max_candidates=2,max_focus=1,reentry_mode="TRUTHFUL"),
                committed_at="2026-08-10T03:00:05Z")
            lesion=DatabasePulseRuntimeV5(lesion_l).run_pulse(
                PulseSpec("lesion",basis_epoch=lesion_l.epoch,source_domains=("memory",),max_candidates=2,max_focus=1,reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T03:00:05Z")
            self.assertEqual(truth.focus_refs,("memory:previous",));self.assertEqual(truth.reentry_count,1)
            self.assertEqual(lesion.focus_refs,("memory:challenger",));self.assertEqual(lesion.reentry_count,0)
            self.assertEqual((truth.effect_count,lesion.effect_count),(0,0))
            self.assertNotEqual(truth.assembly_hash,lesion.assembly_hash)
        finally:truth_l.close();lesion_l.close()


if __name__=="__main__":unittest.main(verbosity=2)
