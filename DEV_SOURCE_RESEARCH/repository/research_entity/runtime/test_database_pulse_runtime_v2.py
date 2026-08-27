from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec
from research_entity.runtime.database_pulse_runtime_v2 import DatabasePulseRuntimeV2


def seed_many(n: int = 180):
    ledger = StateLedger()
    ops = []
    for i in range(n):
        ops.append({
            "op":"SET","domain":"memory","key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT",
        })
    ops.extend([
        {
            "op":"SET","domain":"memory","key":"zzzz-critical",
            "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
            "epistemic":"KNOWN","status":"CURRENT",
        },
        {"op":"SET","domain":"memory","key":"unknown","value":{"u":1},"epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"c":1},"epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(
        event_id="seed", idem="seed", base_epoch=ledger.epoch,
        event_type="PULSE_V2_TEST_SEED", writer="test", ops=ops,
        committed_at="2026-08-10T00:50:00Z",
    )
    runtime = DatabasePulseRuntimeV2(ledger)
    runtime.set_scheduler(
        enabled=True, event_id="scheduler", base_epoch=ledger.epoch,
        actor="test", reason="test", committed_at="2026-08-10T00:50:01Z",
    )
    return ledger, runtime


class DatabasePulseRuntimeV2Tests(unittest.TestCase):
    def test_v2_repairs_v1_pre_ranking_truncation_on_matched_state(self):
        ledger, _ = seed_many()
        events = ledger.export_events(); ledger.close()
        left = StateLedger.replay(events)
        right = StateLedger.replay(events)
        try:
            v1 = DatabasePulseRuntime(left).run_pulse(
                PulseSpec("v1", basis_epoch=left.epoch, source_domains=("memory",),
                          max_candidates=64, max_focus=1, reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T00:50:02Z",
            )
            v2 = DatabasePulseRuntimeV2(right).run_pulse(
                PulseSpec("v2", basis_epoch=right.epoch, source_domains=("memory",),
                          max_candidates=64, max_focus=1, reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T00:50:02Z",
            )
            self.assertNotEqual(v1.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(v2.focus_refs, ("memory:zzzz-critical",))
            latest = right.get("pulse", "latest")["value"]
            self.assertEqual(latest["candidate_generation"], "PULSE_ACTIVE_FIELD_V2")
            self.assertEqual(latest["effect_authority"], "NONE")
            self.assertEqual(v2.conflicts_present, 1)
            self.assertEqual(v2.unknown_present, 1)
        finally:
            left.close(); right.close()

    def test_zero_model_v2_remains_zero_tool_zero_effect(self):
        ledger, runtime = seed_many(8)
        try:
            r = runtime.run_pulse(
                PulseSpec("zero", basis_epoch=ledger.epoch, source_domains=("memory",), max_focus=2),
                committed_at="2026-08-10T00:50:02Z",
            )
            self.assertEqual((r.model_call_count, r.tool_call_count, r.effect_count), (0,0,0))
            self.assertEqual(r.pulse_count, 1)
            self.assertGreaterEqual(r.state_transition_count, 2)
        finally:
            ledger.close()

    def test_v2_is_idempotent_by_pulse_id(self):
        ledger, runtime = seed_many(8)
        try:
            spec = PulseSpec("idem", basis_epoch=ledger.epoch, source_domains=("memory",), max_focus=1)
            first = runtime.run_pulse(spec, committed_at="2026-08-10T00:50:02Z")
            second = runtime.run_pulse(spec, committed_at="2026-08-10T00:50:03Z")
            self.assertEqual(second.status, "ALREADY_COMMITTED")
            self.assertEqual(first.receipt_hash, second.receipt_hash)
            self.assertEqual(first.output_semantic_state_hash, second.output_semantic_state_hash)
        finally:
            ledger.close()

    def test_incremental_state_change_reenters_active_field_before_next_pulse(self):
        ledger, runtime = seed_many(8)
        try:
            first = runtime.run_pulse(
                PulseSpec("first", basis_epoch=ledger.epoch, source_domains=("memory",), max_focus=1),
                committed_at="2026-08-10T00:50:02Z",
            )
            self.assertEqual(first.focus_refs, ("memory:zzzz-critical",))
            ledger.append_event(
                event_id="new-critical", idem="new-critical", base_epoch=ledger.epoch,
                event_type="TEST_UPDATE", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"000-new-critical",
                    "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                    "epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T00:50:03Z",
            )
            second = runtime.run_pulse(
                PulseSpec("second", basis_epoch=ledger.epoch, source_domains=("memory",),
                          max_focus=2, reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T00:50:04Z",
            )
            self.assertIn("memory:000-new-critical", second.focus_refs)
            latest = ledger.get("pulse", "latest")["value"]
            self.assertEqual(latest["projection_refresh_mode"], "DELTA_REFRESH")
            self.assertTrue(runtime.active_field.verify_projection()["pass"])
        finally:
            ledger.close()

    def test_truthful_reentry_remains_causally_lesionable_in_v2(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=ledger.epoch,
            event_type="TEST", writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"a","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"b","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
            ], committed_at="2026-08-10T00:50:00Z",
        )
        runtime = DatabasePulseRuntimeV2(ledger)
        runtime.set_scheduler(enabled=True,event_id="scheduler",base_epoch=ledger.epoch,
                              actor="test",reason="test",committed_at="2026-08-10T00:50:01Z")
        first = runtime.run_pulse(
            PulseSpec("first",basis_epoch=ledger.epoch,source_domains=("memory",),max_focus=1,reentry_mode="TRUTHFUL"),
            committed_at="2026-08-10T00:50:02Z",
        )
        self.assertEqual(first.focus_refs,("memory:a",))
        ledger.append_event(
            event_id="challenge", idem="challenge", base_epoch=ledger.epoch,
            event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"0-challenger","value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T00:50:03Z",
        )
        events=ledger.export_events(); ledger.close()
        truthful_ledger=StateLedger.replay(events); lesion_ledger=StateLedger.replay(events)
        try:
            truthful=DatabasePulseRuntimeV2(truthful_ledger).run_pulse(
                PulseSpec("truthful",basis_epoch=truthful_ledger.epoch,source_domains=("memory",),
                          max_candidates=2,max_focus=1,reentry_mode="TRUTHFUL"),
                committed_at="2026-08-10T00:50:04Z",
            )
            lesion=DatabasePulseRuntimeV2(lesion_ledger).run_pulse(
                PulseSpec("lesion",basis_epoch=lesion_ledger.epoch,source_domains=("memory",),
                          max_candidates=2,max_focus=1,reentry_mode="NO_REENTRY"),
                committed_at="2026-08-10T00:50:04Z",
            )
            self.assertEqual(truthful.focus_refs,("memory:a",))
            self.assertEqual(truthful.reentry_count,1)
            self.assertEqual(lesion.focus_refs,("memory:0-challenger",))
            self.assertEqual(lesion.reentry_count,0)
        finally:
            truthful_ledger.close(); lesion_ledger.close()

    def test_optional_model_output_stays_unknown_and_no_effect_authority(self):
        ledger, runtime = seed_many(8)
        try:
            r=runtime.run_pulse(
                PulseSpec("model",basis_epoch=ledger.epoch,source_domains=("memory",),max_focus=1),
                model_assistant=lambda ctx:{"kind":"HYPOTHESIS","basis":ctx["assembly_hash"]},
                committed_at="2026-08-10T00:50:02Z",
            )
            self.assertEqual(r.model_call_count,1)
            self.assertEqual(r.effect_count,0)
            candidate=ledger.get("pulse","model_candidate")
            self.assertEqual(candidate["epistemic"],"UNKNOWN")
            self.assertEqual(candidate["value"]["authority"],"CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
