from __future__ import annotations

import tempfile
from pathlib import Path
import unittest

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec
from research_entity.runtime.database_pulse_candidate_v2 import (
    DatabasePulseRuntimeV2,
    PulseSpecV2,
    PulseV2JournalCorrupt,
)


class DatabasePulseCandidateV2Tests(unittest.TestCase):
    def seed(self, path=":memory:", *, runtime_cls=DatabasePulseRuntimeV2):
        ledger = StateLedger(path)
        ledger.append_event(
            event_id="seed-v2",
            idem="seed-v2",
            base_epoch=ledger.epoch,
            event_type="TEST_SEED",
            writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"a","value":{"fact":"A","priority":0.2},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"b","value":{"fact":"B"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"c","value":{"fact":"C"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"d","value":{"fact":"D"},"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"unknown","value":{"fact":"U"},"epistemic":"UNKNOWN","status":"CURRENT"},
                {"op":"SET","domain":"memory","key":"conflict","value":{"fact":"C?"},"epistemic":"CONFLICT","status":"CURRENT"},
            ],
            committed_at="2026-08-10T00:00:00Z",
        )
        runtime = runtime_cls(ledger)
        runtime.set_scheduler(
            enabled=True,
            event_id="scheduler-on-v2",
            base_epoch=ledger.epoch,
            actor="test",
            reason="test enable",
            committed_at="2026-08-10T00:00:01Z",
        )
        return ledger, runtime

    def test_zero_model_v2_pulse_advances_execution_clock_not_semantic_clock(self):
        ledger, runtime = self.seed()
        epoch = ledger.epoch
        semantic_hash = ledger.semantic_state_hash
        trace_root = ledger.trace_root_hash
        receipt = runtime.run_pulse_v2(
            PulseSpecV2("p0", basis_epoch=epoch, source_domains=("memory",), max_focus=2),
            committed_at="2026-08-10T00:00:02Z",
        )
        self.assertEqual(receipt.status, "RECORDED")
        self.assertEqual(receipt.pulse_sequence, 1)
        self.assertEqual(receipt.model_call_count, 0)
        self.assertEqual(receipt.tool_call_count, 0)
        self.assertEqual(receipt.effect_count, 0)
        self.assertEqual(receipt.pulse_state_transition_count, 1)
        self.assertEqual(receipt.semantic_state_transition_count, 0)
        self.assertEqual(ledger.epoch, epoch)
        self.assertEqual(ledger.semantic_state_hash, semantic_hash)
        self.assertEqual(ledger.trace_root_hash, trace_root)
        self.assertEqual(runtime.journal.verify_all()["pulse_sequence"], 1)
        ledger.close()

    def test_v2_removes_v1_unrelated_query_receipt_invalidation(self):
        v1_ledger, v1 = self.seed(runtime_cls=DatabasePulseRuntime)
        v1_plane = UnifiedDBQueryPlane(v1_ledger)
        v1_receipt = v1_plane.query(QuerySpec(
            "v1-before", domains=("memory",), basis_epoch=v1_ledger.epoch
        ))
        v1.run_pulse(PulseSpec("v1-pulse", basis_epoch=v1_ledger.epoch, source_domains=("memory",)))
        with self.assertRaises(StaleEpoch):
            v1_plane.select_for_assembly(v1_receipt)
        v1_ledger.close()

        v2_ledger, v2 = self.seed()
        v2_plane = UnifiedDBQueryPlane(v2_ledger)
        v2_receipt = v2_plane.query(QuerySpec(
            "v2-before", domains=("memory",), basis_epoch=v2_ledger.epoch
        ))
        epoch = v2_ledger.epoch
        v2.run_pulse_v2(PulseSpecV2(
            "v2-pulse", basis_epoch=epoch, source_domains=("memory",)
        ))
        selected = v2_plane.select_for_assembly(v2_receipt)
        self.assertEqual(v2_ledger.epoch, epoch)
        self.assertTrue(selected["selected"])
        v2_ledger.close()

    def test_idle_fast_pulse_has_no_source_delta_and_keeps_focus_carry(self):
        ledger, runtime = self.seed()
        first = runtime.run_pulse_v2(PulseSpecV2(
            "p1", basis_epoch=ledger.epoch, source_domains=("memory",),
            max_candidates=6, max_focus=2, refresh_every_pulses=100,
        ))
        second = runtime.run_pulse_v2(PulseSpecV2(
            "p2", basis_epoch=ledger.epoch, source_domains=("memory",),
            max_candidates=6, max_focus=2, refresh_every_pulses=100,
        ))
        self.assertEqual(second.changed_refs, ())
        head = runtime.journal.head()["body"]
        self.assertEqual(head["scanned_event_count"], 0)
        self.assertFalse(head["refresh_due"])
        self.assertEqual(set(second.focus_refs), set(first.focus_refs))
        self.assertIn("memory:unknown", second.carry_refs)
        self.assertIn("memory:conflict", second.carry_refs)
        ledger.close()

    def test_single_semantic_event_is_processed_as_delta_without_full_refresh(self):
        ledger, runtime = self.seed()
        runtime.run_pulse_v2(PulseSpecV2(
            "p1", basis_epoch=ledger.epoch, source_domains=("memory",),
            max_candidates=6, max_focus=1, refresh_every_pulses=100,
        ))
        ledger.append_event(
            event_id="new-hot",
            idem="new-hot",
            base_epoch=ledger.epoch,
            event_type="TEST_MEMORY_DELTA",
            writer="test",
            ops=[{
                "op":"SET","domain":"memory","key":"0-hot","value":{"fact":"N"},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
            committed_at="2026-08-10T00:00:03Z",
        )
        receipt = runtime.run_pulse_v2(PulseSpecV2(
            "p2", basis_epoch=ledger.epoch, source_domains=("memory",),
            max_candidates=6, max_focus=1, refresh_every_pulses=100,
        ))
        head = runtime.journal.head()["body"]
        self.assertEqual(receipt.changed_refs, ("memory:0-hot",))
        self.assertEqual(head["relevant_event_count"], 1)
        self.assertEqual(head["scanned_event_count"], 1)
        self.assertFalse(head["refresh_due"])
        ledger.close()

    def test_bounded_cyclic_scan_eventually_exposes_tail_instead_of_first_page_forever(self):
        ledger, runtime = self.seed()
        seen: set[str] = set()
        for i in range(1, 5):
            receipt = runtime.run_pulse_v2(PulseSpecV2(
                f"scan-{i}", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=2, max_focus=1, refresh_every_pulses=1,
            ))
            seen.update(receipt.scan_refs)
        self.assertTrue({
            "memory:a", "memory:b", "memory:c", "memory:d", "memory:unknown", "memory:conflict"
        }.issubset(seen))
        self.assertTrue(runtime.journal.head()["body"]["scan_wrapped"] or len(seen) == 6)
        ledger.close()

    def test_truthful_reentry_can_outweigh_small_new_delta_vs_no_reentry_lesion(self):
        def prepare(mode: str):
            ledger, runtime = self.seed()
            first = runtime.run_pulse_v2(PulseSpecV2(
                "first", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=6, max_focus=1, refresh_every_pulses=100,
            ))
            self.assertEqual(first.focus_refs, ("memory:a",))
            ledger.append_event(
                event_id="new",
                idem="new",
                base_epoch=ledger.epoch,
                event_type="TEST_NEW",
                writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"0-new","value":{"fact":"N"},
                    "epistemic":"KNOWN","status":"CURRENT",
                }],
                committed_at="2026-08-10T00:00:03Z",
            )
            out = runtime.run_pulse_v2(PulseSpecV2(
                "next", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=6, max_focus=1, refresh_every_pulses=100, reentry_mode=mode,
            ))
            return ledger, out

        truthful_ledger, truthful = prepare("TRUTHFUL")
        lesion_ledger, lesion = prepare("NO_REENTRY")
        self.assertEqual(truthful.focus_refs, ("memory:a",))
        self.assertEqual(truthful.reentry_count, 1)
        self.assertEqual(lesion.focus_refs, ("memory:0-new",))
        self.assertEqual(lesion.reentry_count, 0)
        self.assertNotEqual(truthful.assembly_hash, lesion.assembly_hash)
        truthful_ledger.close()
        lesion_ledger.close()

    def test_model_assist_is_persisted_unknown_in_execution_receipt_not_semantic_state(self):
        ledger, runtime = self.seed()
        epoch = ledger.epoch
        semantic_hash = ledger.semantic_state_hash
        out = runtime.run_pulse_v2(
            PulseSpecV2("model", basis_epoch=epoch, source_domains=("memory",), max_focus=1),
            model_assistant=lambda ctx: {
                "kind":"HYPOTHESIS", "text":"candidate only", "basis":ctx["assembly_hash"]
            },
            committed_at="2026-08-10T00:00:02Z",
        )
        self.assertEqual(out.model_call_count, 1)
        self.assertEqual(out.hypothesis_count, 1)
        self.assertEqual(out.effect_count, 0)
        body = runtime.journal.head()["body"]
        self.assertEqual(body["model_candidate"]["epistemic"], "UNKNOWN")
        self.assertEqual(
            body["model_candidate"]["authority"],
            "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
        )
        self.assertIsNone(ledger.get("pulse", "model_candidate"))
        self.assertEqual(ledger.epoch, epoch)
        self.assertEqual(ledger.semantic_state_hash, semantic_hash)
        ledger.close()

    def test_pause_resume_remains_explicit_and_persistent(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "v2.sqlite"
            ledger, runtime = self.seed(path)
            runtime.set_scheduler(
                enabled=False,
                event_id="off-v2",
                base_epoch=ledger.epoch,
                actor="test",
                reason="pause",
                committed_at="2026-08-10T00:00:02Z",
            )
            paused = runtime.run_pulse_v2(PulseSpecV2(
                "paused", basis_epoch=ledger.epoch, source_domains=("memory",)
            ))
            self.assertEqual(paused.status, "PAUSED")
            self.assertEqual(runtime.journal.verify_all()["pulse_sequence"], 0)
            ledger.close()

            reopened = StateLedger(path)
            runtime2 = DatabasePulseRuntimeV2(reopened)
            runtime2.set_scheduler(
                enabled=True,
                event_id="on-v2",
                base_epoch=reopened.epoch,
                actor="test",
                reason="resume",
                committed_at="2026-08-10T00:00:03Z",
            )
            resumed = runtime2.run_pulse_v2(PulseSpecV2(
                "resumed", basis_epoch=reopened.epoch, source_domains=("memory",)
            ))
            self.assertEqual(resumed.status, "RECORDED")
            self.assertEqual(resumed.pulse_sequence, 1)
            reopened.close()

    def test_journal_corruption_fails_closed_before_next_pulse(self):
        ledger, runtime = self.seed()
        runtime.run_pulse_v2(PulseSpecV2(
            "p1", basis_epoch=ledger.epoch, source_domains=("memory",)
        ))
        ledger.conn.execute(
            "UPDATE database_pulse_v2_receipts SET receipt_json='{}' WHERE pulse_id='p1'"
        )
        ledger.conn.commit()
        epoch = ledger.epoch
        with self.assertRaises(PulseV2JournalCorrupt):
            runtime.run_pulse_v2(PulseSpecV2(
                "p2", basis_epoch=ledger.epoch, source_domains=("memory",)
            ))
        self.assertEqual(ledger.epoch, epoch)
        self.assertIsNone(ledger.conn.execute(
            "SELECT 1 FROM database_pulse_v2_receipts WHERE pulse_id='p2'"
        ).fetchone())
        ledger.close()

    def test_same_semantic_history_and_pulse_schedule_reproduce_receipt_chain(self):
        def run_once():
            ledger, runtime = self.seed()
            a = runtime.run_pulse_v2(PulseSpecV2(
                "a", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=2, max_focus=1, refresh_every_pulses=2,
            ), committed_at="2026-08-10T00:00:02Z")
            ledger.append_event(
                event_id="delta-replay",
                idem="delta-replay",
                base_epoch=ledger.epoch,
                event_type="TEST_DELTA",
                writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"x","value":{"fact":"X"},
                    "epistemic":"KNOWN","status":"CURRENT",
                }],
                committed_at="2026-08-10T00:00:03Z",
            )
            b = runtime.run_pulse_v2(PulseSpecV2(
                "b", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=2, max_focus=1, refresh_every_pulses=2,
            ), committed_at="2026-08-10T00:00:04Z")
            result = (
                ledger.semantic_state_hash,
                a.receipt_hash, a.pulse_chain_hash,
                b.receipt_hash, b.pulse_chain_hash,
            )
            ledger.close()
            return result

        self.assertEqual(run_once(), run_once())

    def test_direct_semantic_corruption_still_uses_v1_integrity_fail_closed(self):
        ledger, runtime = self.seed()
        ledger.conn.execute(
            "UPDATE state SET value_json='999' WHERE domain='memory' AND k='a'"
        )
        ledger.conn.commit()
        with self.assertRaises(PulseIntegrityError):
            runtime.run_pulse_v2(PulseSpecV2(
                "corrupt", basis_epoch=ledger.epoch, source_domains=("memory",)
            ))
        ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
