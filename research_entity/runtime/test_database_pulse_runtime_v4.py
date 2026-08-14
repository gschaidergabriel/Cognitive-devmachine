from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_runtime_v4 import (
    DatabasePulseRuntimeV4,
    PulseRankPolicyV4,
)
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def make_ledger(path=":memory:", low_rows=180, *, policy_provider=None):
    ledger=StateLedger(path)
    ops=[]
    for i in range(low_rows):
        ops.append({
            "op":"SET","domain":"memory","key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT",
        })
    ops.extend([
        {"op":"SET","domain":"memory","key":"zzzz-critical",
         "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
         "epistemic":"KNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"unknown","value":{"priority":1.0},
         "epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"priority":1.0},
         "epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(event_id="seed",idem="seed",base_epoch=ledger.epoch,
                        event_type="PULSE_V4_SEED",writer="test",ops=ops,
                        committed_at="2026-08-10T02:40:00Z")
    runtime=DatabasePulseRuntimeV4(ledger,rank_policy_provider=policy_provider)
    runtime.set_scheduler(enabled=True,event_id="scheduler-on",base_epoch=ledger.epoch,
                          actor="test",reason="test",committed_at="2026-08-10T02:40:01Z")
    return ledger,runtime


def stable_policy(spec: PulseSpec) -> PulseRankPolicyV4:
    return PulseRankPolicyV4(
        economics_without_horizon=CompileEconomics(
            build_cost_us=1000.0,
            online_query_us=100.0,
            compiled_query_us=10.0,
            online_quality=1.0,
            compiled_quality=1.0,
            expected_reads_before_invalidation=0.0,
            safety_factor=1.2,
        ),
        pulse_history=tuple(EpochReadLifetime(i,100,True,False) for i in range(8)),
        provenance_ref="test:measured-stable-policy",
    )


class DatabasePulseRuntimeV4Tests(unittest.TestCase):
    def test_default_unmeasured_policy_stays_online_and_repairs_prelimit(self):
        ledger,runtime=make_ledger()
        try:
            self.assertFalse(runtime.rank_path.index_exists())
            receipt=runtime.run_pulse(
                PulseSpec("v4-zero",basis_epoch=ledger.epoch,source_domains=("memory",),
                          max_candidates=64,max_focus=1),
                committed_at="2026-08-10T02:40:02Z",
            )
            self.assertEqual(receipt.focus_refs,("memory:zzzz-critical",))
            self.assertEqual((receipt.model_call_count,receipt.tool_call_count,receipt.effect_count),(0,0,0))
            self.assertEqual(receipt.state_transition_count,0)
            latest=ledger.get("pulse","latest")["value"]
            self.assertEqual(latest["physical_rank_mode"],"ONLINE_NO_COMPILE")
            self.assertEqual(latest["rank_policy_provenance_ref"],"UNMEASURED_FAIL_ONLINE")
            self.assertEqual(latest["rank_horizon_status"],"INSUFFICIENT_HISTORY")
            self.assertFalse(latest["rank_index_present_before"])
            self.assertFalse(latest["rank_index_present_after"])
            self.assertTrue(latest["query_truncated"])
            self.assertEqual(latest["candidate_universe_count"],181)
            self.assertEqual(latest["unknown_present"],1)
            self.assertEqual(latest["conflicts_present"],1)
            self.assertEqual(latest["effect_authority"],"NONE")
            self.assertFalse(runtime.rank_path.index_exists())
        finally:
            ledger.close()

    def test_measured_stable_policy_can_admit_physical_index_with_provenance(self):
        ledger,runtime=make_ledger(":memory:",40,policy_provider=stable_policy)
        try:
            receipt=runtime.run_pulse(
                PulseSpec("v4-compiled",basis_epoch=ledger.epoch,source_domains=("memory",),
                          max_candidates=32,max_focus=1),
                committed_at="2026-08-10T02:40:02Z",
            )
            self.assertEqual(receipt.focus_refs,("memory:zzzz-critical",))
            latest=ledger.get("pulse","latest")["value"]
            self.assertEqual(latest["physical_rank_mode"],"COMPILED_INDEX")
            self.assertEqual(latest["rank_policy_provenance_ref"],"test:measured-stable-policy")
            self.assertTrue(latest["rank_index_present_after"])
            self.assertGreater(latest["rank_horizon_reads_lower_bound"],latest["rank_guarded_break_even_reads"])
            self.assertTrue(any(INDEX_NAME in p for p in latest["rank_query_plan"]),latest["rank_query_plan"])
            self.assertTrue(runtime.rank_path.index_exists())
        finally:
            ledger.close()

    def test_optional_model_stays_unknown_and_not_state_transition_or_effect(self):
        ledger,runtime=make_ledger(":memory:",8)
        try:
            receipt=runtime.run_pulse(
                PulseSpec("model",basis_epoch=ledger.epoch,source_domains=("memory",),
                          max_candidates=8,max_focus=1),
                model_assistant=lambda ctx:{"kind":"HYPOTHESIS","basis":ctx["assembly_hash"]},
                committed_at="2026-08-10T02:40:02Z",
            )
            self.assertEqual(receipt.model_call_count,1)
            self.assertEqual(receipt.hypothesis_count,1)
            self.assertEqual(receipt.state_transition_count,0)
            self.assertEqual(receipt.effect_count,0)
            candidate=ledger.get("pulse","model_candidate")
            self.assertEqual(candidate["epistemic"],"UNKNOWN")
            self.assertEqual(candidate["value"]["authority"],"CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
            self.assertFalse(runtime.rank_path.index_exists())
        finally:
            ledger.close()

    def test_stale_basis_fails_before_policy_or_index_side_effect(self):
        calls=[]
        def provider(spec):
            calls.append(spec.pulse_id)
            return stable_policy(spec)
        ledger,runtime=make_ledger(":memory:",8,policy_provider=provider)
        try:
            stale=ledger.epoch
            ledger.append_event(event_id="advance",idem="advance",base_epoch=ledger.epoch,
                                event_type="TEST",writer="test",
                                ops=[{"op":"SET","domain":"memory","key":"new","value":1,
                                      "epistemic":"KNOWN","status":"CURRENT"}],
                                committed_at="2026-08-10T02:40:02Z")
            with self.assertRaises(StaleEpoch):
                runtime.run_pulse(PulseSpec("stale",basis_epoch=stale,source_domains=("memory",)))
            self.assertEqual(calls,[])
            self.assertFalse(runtime.rank_path.index_exists())
        finally:
            ledger.close()

    def test_pause_does_not_call_policy_or_build_index_and_survives_reopen(self):
        calls=[]
        def provider(spec):
            calls.append(spec.pulse_id)
            return stable_policy(spec)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"pulse.sqlite"
            ledger,runtime=make_ledger(path,8,policy_provider=provider)
            runtime.set_scheduler(enabled=False,event_id="off",base_epoch=ledger.epoch,
                                  actor="test",reason="pause",committed_at="2026-08-10T02:40:02Z")
            paused_epoch=ledger.epoch
            paused=runtime.run_pulse(PulseSpec("paused",basis_epoch=ledger.epoch,source_domains=("memory",)))
            self.assertEqual(paused.status,"PAUSED")
            self.assertEqual(calls,[])
            self.assertFalse(runtime.rank_path.index_exists())
            self.assertEqual(ledger.epoch,paused_epoch)
            ledger.close()

            reopened=StateLedger(path)
            runtime2=DatabasePulseRuntimeV4(reopened,rank_policy_provider=provider)
            runtime2.set_scheduler(enabled=True,event_id="on2",base_epoch=reopened.epoch,
                                   actor="test",reason="resume",committed_at="2026-08-10T02:40:03Z")
            resumed=runtime2.run_pulse(
                PulseSpec("resumed",basis_epoch=reopened.epoch,source_domains=("memory",),
                          max_candidates=8,max_focus=1),
                committed_at="2026-08-10T02:40:04Z",
            )
            self.assertEqual(resumed.status,"COMMITTED")
            self.assertEqual(calls,["resumed"])
            reopened.close()

    def test_same_pulse_id_is_idempotent_without_second_policy_decision(self):
        calls=[]
        def provider(spec):
            calls.append(spec.pulse_id)
            return stable_policy(spec)
        ledger,runtime=make_ledger(":memory:",8,policy_provider=provider)
        try:
            spec=PulseSpec("idem",basis_epoch=ledger.epoch,source_domains=("memory",),
                           max_candidates=8,max_focus=1)
            first=runtime.run_pulse(spec,committed_at="2026-08-10T02:40:02Z")
            second=runtime.run_pulse(spec,committed_at="2026-08-10T02:40:03Z")
            self.assertEqual(second.status,"ALREADY_COMMITTED")
            self.assertEqual(first.receipt_hash,second.receipt_hash)
            self.assertEqual(calls,["idem"])
        finally:
            ledger.close()

    def test_truthful_reentry_causal_difference_survives_adaptive_online_route(self):
        ledger,runtime=make_ledger(":memory:",0)
        try:
            ledger.append_event(event_id="pair",idem="pair",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"RETRACT","domain":"memory","key":"zzzz-critical","value":None,"epistemic":"KNOWN","status":"CURRENT"},
                ],committed_at="2026-08-10T02:40:02Z")
            ledger.append_event(event_id="boost-prev",idem="boost-prev",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
                committed_at="2026-08-10T02:40:03Z")
            first=runtime.run_pulse(PulseSpec("first",basis_epoch=ledger.epoch,source_domains=("memory",),
                                              max_candidates=2,max_focus=1),
                                    committed_at="2026-08-10T02:40:04Z")
            self.assertEqual(first.focus_refs,("memory:previous",))
            ledger.append_event(event_id="lower-prev",idem="lower-prev",base_epoch=ledger.epoch,event_type="TEST",writer="test",
                ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"}],
                committed_at="2026-08-10T02:40:05Z")
            events=ledger.export_events()
        finally:
            ledger.close()
        truth_ledger=StateLedger.replay(events); lesion_ledger=StateLedger.replay(events)
        try:
            truth=DatabasePulseRuntimeV4(truth_ledger).run_pulse(
                PulseSpec("truth",basis_epoch=truth_ledger.epoch,source_domains=("memory",),
                          max_candidates=2,max_focus=1,reentry_mode="TRUTHFUL"),
                committed_at="2026-08-10T02:40:06Z")
            lesion=DatabasePulseRuntimeV4(lesion_ledger).run_pulse(
                PulseSpec("lesion",basis_epoch=lesion_ledger.epoch,source_domains=("memory",),
                          max_candidates=2,max_focus=1,reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T02:40:06Z")
            self.assertEqual(truth.focus_refs,("memory:previous",))
            self.assertEqual(truth.reentry_count,1)
            self.assertEqual(lesion.focus_refs,("memory:challenger",))
            self.assertEqual(lesion.reentry_count,0)
            self.assertNotEqual(truth.assembly_hash,lesion.assembly_hash)
        finally:
            truth_ledger.close(); lesion_ledger.close()

    def test_output_domains_remain_invalid_sources(self):
        ledger,runtime=make_ledger(":memory:",4)
        try:
            with self.assertRaises(ValueError):
                runtime.run_pulse(PulseSpec("bad",basis_epoch=ledger.epoch,source_domains=("pulse",)))
            with self.assertRaises(ValueError):
                runtime.run_pulse(PulseSpec("bad2",basis_epoch=ledger.epoch,source_domains=("memory","pulse_control")))
            self.assertFalse(runtime.rank_path.index_exists())
        finally:
            ledger.close()


if __name__=="__main__": unittest.main(verbosity=2)
