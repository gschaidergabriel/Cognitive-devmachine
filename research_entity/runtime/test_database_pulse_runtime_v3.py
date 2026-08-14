from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_runtime_v3 import DatabasePulseRuntimeV3


def make_ledger(path=":memory:", low_rows=180):
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
                        event_type="PULSE_V3_SEED",writer="test",ops=ops,
                        committed_at="2026-08-10T01:40:00Z")
    runtime=DatabasePulseRuntimeV3(ledger)
    runtime.set_scheduler(enabled=True,event_id="scheduler-on",base_epoch=ledger.epoch,
                          actor="test",reason="test",committed_at="2026-08-10T01:40:01Z")
    return ledger,runtime


class DatabasePulseRuntimeV3Tests(unittest.TestCase):
    def test_zero_model_repairs_prelimit_with_no_second_candidate_table(self):
        ledger,runtime=make_ledger()
        root_before=(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash)
        receipt=runtime.run_pulse(
            PulseSpec("v3-zero",basis_epoch=ledger.epoch,source_domains=("memory",),max_candidates=64,max_focus=1),
            committed_at="2026-08-10T01:40:02Z",
        )
        self.assertEqual(receipt.focus_refs,("memory:zzzz-critical",))
        self.assertEqual(receipt.model_call_count,0)
        self.assertEqual(receipt.tool_call_count,0)
        self.assertEqual(receipt.effect_count,0)
        self.assertEqual(receipt.state_transition_count,0)
        latest=ledger.get("pulse","latest")["value"]
        self.assertTrue(latest["query_truncated"])
        self.assertEqual(latest["candidate_universe_count"],181)
        self.assertEqual(latest["unknown_present"],1)
        self.assertEqual(latest["conflicts_present"],1)
        self.assertEqual(latest["effect_authority"],"NONE")
        self.assertTrue(any(INDEX_NAME in x for x in latest["rank_index_query_plan"]))
        tables={r[0] for r in ledger.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertNotIn("pulse_active_field",tables)
        self.assertGreater(ledger.epoch,root_before[0])  # only Pulse receipt/metrics event advances ledger
        ledger.close()

    def test_physical_index_creation_does_not_change_semantic_roots(self):
        ledger,runtime=make_ledger(8)
        before=(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash)
        runtime.rank_index.ensure_index()
        after=(ledger.epoch,ledger.semantic_state_hash,ledger.trace_root_hash)
        self.assertEqual(before,after)
        self.assertTrue(runtime.rank_index.verify_index_semantics(domains=("memory",))["pass"])
        ledger.close()

    def test_optional_model_is_unknown_hypothesis_not_state_transition_or_effect(self):
        ledger,runtime=make_ledger(8)
        receipt=runtime.run_pulse(
            PulseSpec("v3-model",basis_epoch=ledger.epoch,source_domains=("memory",),max_candidates=8,max_focus=1),
            model_assistant=lambda ctx:{"kind":"HYPOTHESIS","basis":ctx["assembly_hash"],"claim":"candidate only"},
            committed_at="2026-08-10T01:40:02Z",
        )
        self.assertEqual(receipt.model_call_count,1)
        self.assertEqual(receipt.hypothesis_count,1)
        self.assertEqual(receipt.state_transition_count,0)
        self.assertEqual(receipt.effect_count,0)
        candidate=ledger.get("pulse","model_candidate")
        self.assertEqual(candidate["epistemic"],"UNKNOWN")
        self.assertEqual(candidate["value"]["authority"],"CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
        ledger.close()

    def test_pause_resume_survives_process_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"pulse.sqlite"
            ledger,runtime=make_ledger(path,8)
            runtime.set_scheduler(enabled=False,event_id="off",base_epoch=ledger.epoch,
                                  actor="test",reason="pause",committed_at="2026-08-10T01:40:02Z")
            paused_epoch=ledger.epoch
            ledger.close()
            reopened=StateLedger(path); runtime2=DatabasePulseRuntimeV3(reopened)
            paused=runtime2.run_pulse(PulseSpec("paused",basis_epoch=reopened.epoch,source_domains=("memory",)))
            self.assertEqual(paused.status,"PAUSED")
            self.assertEqual(reopened.epoch,paused_epoch)
            runtime2.set_scheduler(enabled=True,event_id="on2",base_epoch=reopened.epoch,
                                   actor="test",reason="resume",committed_at="2026-08-10T01:40:03Z")
            resumed=runtime2.run_pulse(PulseSpec("resumed",basis_epoch=reopened.epoch,source_domains=("memory",),max_candidates=8,max_focus=1),
                                       committed_at="2026-08-10T01:40:04Z")
            self.assertEqual(resumed.status,"COMMITTED")
            reopened.close()

    def test_stale_basis_fails_before_index_selection(self):
        ledger,runtime=make_ledger(8)
        stale=ledger.epoch
        ledger.append_event(event_id="advance",idem="advance",base_epoch=ledger.epoch,event_type="TEST",
                            writer="test",ops=[{"op":"SET","domain":"memory","key":"new","value":1,
                                                "epistemic":"KNOWN","status":"CURRENT"}],
                            committed_at="2026-08-10T01:40:02Z")
        with self.assertRaises(StaleEpoch):
            runtime.run_pulse(PulseSpec("stale",basis_epoch=stale,source_domains=("memory",)))
        ledger.close()

    def test_truthful_reentry_has_causal_lesion_difference(self):
        ledger,runtime=make_ledger(0)
        # Replace the critical seed with a controlled pair.
        ledger.append_event(event_id="pair",idem="pair",base_epoch=ledger.epoch,event_type="TEST",writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"RETRACT","domain":"memory","key":"zzzz-critical","value":None,"epistemic":"KNOWN","status":"CURRENT"},
            ],committed_at="2026-08-10T01:40:02Z")
        # Seed prior focus explicitly through a first Pulse where previous is made highest.
        ledger.append_event(event_id="boost-prev",idem="boost-prev",base_epoch=ledger.epoch,event_type="TEST",writer="test",
            ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:40:03Z")
        first=runtime.run_pulse(PulseSpec("first",basis_epoch=ledger.epoch,source_domains=("memory",),max_candidates=2,max_focus=1),
                                committed_at="2026-08-10T01:40:04Z")
        self.assertEqual(first.focus_refs,("memory:previous",))
        ledger.append_event(event_id="lower-prev",idem="lower-prev",base_epoch=ledger.epoch,event_type="TEST",writer="test",
            ops=[{"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:40:05Z")
        events=ledger.export_events()
        truth_ledger=StateLedger.replay(events); lesion_ledger=StateLedger.replay(events)
        truth=DatabasePulseRuntimeV3(truth_ledger).run_pulse(
            PulseSpec("truth",basis_epoch=truth_ledger.epoch,source_domains=("memory",),max_candidates=2,max_focus=1,reentry_mode="TRUTHFUL"),
            committed_at="2026-08-10T01:40:06Z")
        lesion=DatabasePulseRuntimeV3(lesion_ledger).run_pulse(
            PulseSpec("lesion",basis_epoch=lesion_ledger.epoch,source_domains=("memory",),max_candidates=2,max_focus=1,reentry_mode="NO_REENTRY"),
            committed_at="2026-08-10T01:40:06Z")
        self.assertEqual(truth.focus_refs,("memory:previous",))
        self.assertEqual(truth.reentry_count,1)
        self.assertEqual(lesion.focus_refs,("memory:challenger",))
        self.assertEqual(lesion.reentry_count,0)
        self.assertNotEqual(truth.assembly_hash,lesion.assembly_hash)
        truth_ledger.close();lesion_ledger.close();ledger.close()

    def test_same_pulse_id_remains_idempotent(self):
        ledger,runtime=make_ledger(8)
        spec=PulseSpec("idem",basis_epoch=ledger.epoch,source_domains=("memory",),max_candidates=8,max_focus=1)
        first=runtime.run_pulse(spec,committed_at="2026-08-10T01:40:02Z")
        second=runtime.run_pulse(spec,committed_at="2026-08-10T01:40:03Z")
        self.assertEqual(second.status,"ALREADY_COMMITTED")
        self.assertEqual(first.receipt_hash,second.receipt_hash)
        ledger.close()


if __name__=="__main__": unittest.main(verbosity=2)
