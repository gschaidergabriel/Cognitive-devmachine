from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.runtime.database_pulse_candidate_v1 import (
    DatabasePulseRuntime,
    PulseControlError,
    PulseIntegrityError,
    PulseSpec,
)


class DatabasePulseCandidateV1Tests(unittest.TestCase):
    def seed(self, path=":memory:"):
        ledger = StateLedger(path)
        ledger.append_event(
            event_id="seed-state",
            idem="seed-state",
            base_epoch=ledger.epoch,
            event_type="TEST_SEED",
            writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"a","value":{"fact":"A"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"z","value":{"fact":"Z"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"unknown","value":{"fact":"U"},"epistemic":"UNKNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"conflict","value":{"fact":"C"},"epistemic":"CONFLICT","status":"CURRENT"},
            ],
            committed_at="2026-08-10T00:00:00Z",
        )
        runtime = DatabasePulseRuntime(ledger)
        runtime.set_scheduler(
            enabled=True,
            event_id="scheduler-on",
            base_epoch=ledger.epoch,
            actor="test",
            reason="test enable",
            committed_at="2026-08-10T00:00:01Z",
        )
        return ledger, runtime

    def test_zero_model_pulse_has_distinct_observables_and_no_effect_authority(self):
        ledger, runtime = self.seed()
        receipt = runtime.run_pulse(
            PulseSpec("p0", basis_epoch=ledger.epoch, max_focus=1),
            committed_at="2026-08-10T00:00:02Z",
        )
        self.assertEqual(receipt.status, "COMMITTED")
        self.assertEqual(receipt.pulse_count, 1)
        self.assertEqual(receipt.model_call_count, 0)
        self.assertEqual(receipt.tool_call_count, 0)
        self.assertEqual(receipt.effect_count, 0)
        self.assertEqual(receipt.graph_change, 0)
        self.assertEqual(receipt.hypothesis_count, 0)
        self.assertEqual(receipt.state_transition_count, 2)
        self.assertEqual(receipt.focus_refs, ("memory:a",))
        latest = ledger.get("pulse", "latest")
        self.assertEqual(latest["value"]["effect_authority"], "NONE")
        self.assertEqual(latest["value"]["authority"], "ASSEMBLY_CONTEXT_ONLY")
        self.assertEqual(latest["value"]["conflicts_present"], 1)
        self.assertEqual(latest["value"]["unknown_present"], 1)
        ledger.close()

    def test_same_pulse_id_is_idempotent_even_after_epoch_advance(self):
        ledger, runtime = self.seed()
        spec = PulseSpec("idem", basis_epoch=ledger.epoch, max_focus=1)
        first = runtime.run_pulse(spec, committed_at="2026-08-10T00:00:02Z")
        second = runtime.run_pulse(spec, committed_at="2026-08-10T00:00:03Z")
        self.assertEqual(second.status, "ALREADY_COMMITTED")
        self.assertEqual(first.receipt_hash, second.receipt_hash)
        self.assertEqual(first.output_semantic_state_hash, second.output_semantic_state_hash)
        ledger.close()

    def test_pause_resume_survives_process_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "pulse.sqlite"
            ledger, runtime = self.seed(path)
            runtime.set_scheduler(
                enabled=False,
                event_id="scheduler-off",
                base_epoch=ledger.epoch,
                actor="test",
                reason="pause",
                committed_at="2026-08-10T00:00:02Z",
            )
            paused_epoch = ledger.epoch
            ledger.close()

            reopened = StateLedger(path)
            runtime2 = DatabasePulseRuntime(reopened)
            paused = runtime2.run_pulse(PulseSpec("paused", basis_epoch=reopened.epoch))
            self.assertEqual(paused.status, "PAUSED")
            self.assertEqual(reopened.epoch, paused_epoch)
            runtime2.set_scheduler(
                enabled=True,
                event_id="scheduler-resume",
                base_epoch=reopened.epoch,
                actor="test",
                reason="resume",
                committed_at="2026-08-10T00:00:03Z",
            )
            resumed = runtime2.run_pulse(
                PulseSpec("resumed", basis_epoch=reopened.epoch),
                committed_at="2026-08-10T00:00:04Z",
            )
            self.assertEqual(resumed.status, "COMMITTED")
            reopened.close()

    def test_event_replay_reconstructs_exact_state_and_trace_roots(self):
        ledger, runtime = self.seed()
        for i in range(5):
            runtime.run_pulse(
                PulseSpec(f"replay-{i}", basis_epoch=ledger.epoch, max_focus=2),
                committed_at=f"2026-08-10T00:00:{10+i:02d}Z",
            )
        events = ledger.export_events()
        expected_state = ledger.semantic_state_hash
        expected_trace = ledger.trace_root_hash
        replayed = StateLedger.replay(events)
        self.assertEqual(replayed.semantic_state_hash, expected_state)
        self.assertEqual(replayed.trace_root_hash, expected_trace)
        self.assertEqual(replayed.epoch, ledger.epoch)
        replayed.close()
        ledger.close()

    def test_stale_basis_fails_closed(self):
        ledger, runtime = self.seed()
        stale = ledger.epoch
        ledger.append_event(
            event_id="advance",
            idem="advance",
            base_epoch=ledger.epoch,
            event_type="TEST_ADVANCE",
            writer="test",
            ops=[{"op":"SET","domain":"memory","key":"new","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T00:00:02Z",
        )
        with self.assertRaises(StaleEpoch):
            runtime.run_pulse(PulseSpec("stale", basis_epoch=stale))
        ledger.close()

    def test_direct_state_corruption_fails_closed_before_pulse(self):
        ledger, runtime = self.seed()
        ledger.conn.execute("UPDATE state SET value_json='999' WHERE domain='memory' AND k='a'")
        ledger.conn.commit()
        with self.assertRaises(PulseIntegrityError):
            runtime.run_pulse(PulseSpec("corrupt", basis_epoch=ledger.epoch))
        ledger.close()

    def test_missing_schema_surface_fails_closed(self):
        ledger, runtime = self.seed()
        ledger.conn.execute("DROP TABLE snapshots")
        ledger.conn.commit()
        with self.assertRaises(PulseIntegrityError):
            runtime.run_pulse(PulseSpec("schema", basis_epoch=ledger.epoch))
        ledger.close()

    def test_scheduler_unknown_is_not_treated_as_enabled(self):
        ledger, runtime = self.seed()
        ledger.append_event(
            event_id="scheduler-unknown",
            idem="scheduler-unknown",
            base_epoch=ledger.epoch,
            event_type="TEST_CONTROL_CORRUPTION",
            writer="test",
            ops=[{
                "op":"SET","domain":"pulse_control","key":"scheduler",
                "value":{"enabled":True},"epistemic":"UNKNOWN","status":"CURRENT",
            }],
            committed_at="2026-08-10T00:00:02Z",
        )
        with self.assertRaises(PulseControlError):
            runtime.run_pulse(PulseSpec("unknown-control", basis_epoch=ledger.epoch))
        ledger.close()

    def test_truthful_reentry_has_causal_selection_effect_vs_no_reentry_lesion(self):
        ledger, runtime = self.seed()
        first = runtime.run_pulse(
            PulseSpec("first", basis_epoch=ledger.epoch, max_focus=1, reentry_mode="TRUTHFUL"),
            committed_at="2026-08-10T00:00:02Z",
        )
        self.assertEqual(first.focus_refs, ("memory:a",))
        ledger.append_event(
            event_id="insert-lexically-earlier",
            idem="insert-lexically-earlier",
            base_epoch=ledger.epoch,
            event_type="TEST_NEW_MEMORY",
            writer="test",
            ops=[{
                "op":"SET","domain":"memory","key":"0-new","value":{"fact":"N"},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
            committed_at="2026-08-10T00:00:03Z",
        )
        common = ledger.export_events()
        truthful_ledger = StateLedger.replay(common)
        lesion_ledger = StateLedger.replay(common)
        truthful = DatabasePulseRuntime(truthful_ledger).run_pulse(
            PulseSpec("truthful-next", basis_epoch=truthful_ledger.epoch, max_focus=1, reentry_mode="TRUTHFUL"),
            committed_at="2026-08-10T00:00:04Z",
        )
        lesion = DatabasePulseRuntime(lesion_ledger).run_pulse(
            PulseSpec("lesion-next", basis_epoch=lesion_ledger.epoch, max_focus=1, reentry_mode="NO_REENTRY"),
            committed_at="2026-08-10T00:00:04Z",
        )
        self.assertEqual(truthful.focus_refs, ("memory:a",))
        self.assertEqual(truthful.reentry_count, 1)
        self.assertEqual(lesion.focus_refs, ("memory:0-new",))
        self.assertEqual(lesion.reentry_count, 0)
        self.assertNotEqual(truthful.assembly_hash, lesion.assembly_hash)
        truthful_ledger.close()
        lesion_ledger.close()
        ledger.close()

    def test_model_assist_is_optional_unknown_context_not_effect_authority(self):
        ledger, runtime = self.seed()
        receipt = runtime.run_pulse(
            PulseSpec("model", basis_epoch=ledger.epoch, max_focus=1),
            model_assistant=lambda ctx: {"kind":"HYPOTHESIS","text":"candidate only","basis":ctx["assembly_hash"]},
            committed_at="2026-08-10T00:00:02Z",
        )
        self.assertEqual(receipt.model_call_count, 1)
        self.assertEqual(receipt.hypothesis_count, 1)
        self.assertEqual(receipt.tool_call_count, 0)
        self.assertEqual(receipt.effect_count, 0)
        candidate = ledger.get("pulse", "model_candidate")
        self.assertEqual(candidate["epistemic"], "UNKNOWN")
        self.assertEqual(candidate["value"]["authority"], "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
        ledger.close()

    def test_unbounded_or_self_referential_source_requests_are_rejected(self):
        ledger, runtime = self.seed()
        with self.assertRaises(ValueError):
            runtime.run_pulse(PulseSpec("empty-domains", basis_epoch=ledger.epoch, source_domains=()))
        with self.assertRaises(ValueError):
            runtime.run_pulse(PulseSpec("self-loop", basis_epoch=ledger.epoch, source_domains=("memory","pulse")))
        with self.assertRaises(ValueError):
            runtime.run_pulse(PulseSpec("too-wide", basis_epoch=ledger.epoch, max_candidates=513))
        ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
