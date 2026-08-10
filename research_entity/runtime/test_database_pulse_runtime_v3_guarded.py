from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_runtime_v3_guarded import (
    DatabasePulseRuntimeV3Guarded,
)
from research_entity.runtime.database_pulse_v0 import PulseStateError


class DatabasePulseRuntimeV3GuardedTests(unittest.TestCase):
    def test_large_semantic_burst_cannot_publish_future_focus_ahead_of_u12_epoch(self):
        ledger = StateLedger()
        ops = [
            {
                "op":"SET","domain":"memory","key":f"k{i:04d}",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            }
            for i in range(180)
        ]
        ops.append({
            "op":"SET","domain":"memory","key":"zzzz-critical",
            "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
            "epistemic":"KNOWN","status":"CURRENT",
        })
        ledger.append_event(
            event_id="burst", idem="burst", base_epoch=ledger.epoch,
            event_type="BURST", writer="test", ops=ops,
            committed_at="2026-08-10T01:20:00Z",
        )
        runtime = DatabasePulseRuntimeV3Guarded(ledger, now="2026-08-10T01:20:01Z")
        epoch = ledger.epoch
        try:
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    basis_epoch=epoch, source_domains=("memory",),
                    max_candidates=64, max_focus=1, max_deltas=32,
                    reentry_mode="NO_REENTRY", now="2026-08-10T01:20:02Z",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), 0)
            self.assertGreater(runtime.backlog_count(), 32)
            while runtime.backlog_count() > 32:
                runtime.drain_backlog(
                    basis_epoch=epoch, max_deltas=32, now="2026-08-10T01:20:03Z"
                )
            out = runtime.run_pulse(
                basis_epoch=epoch, source_domains=("memory",),
                max_candidates=64, max_focus=1, max_deltas=32,
                reentry_mode="NO_REENTRY", now="2026-08-10T01:20:04Z",
            )
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(runtime.backlog_count(), 0)
            self.assertEqual(ledger.epoch, epoch)
        finally:
            ledger.close()

    def test_global_bridge_does_not_lose_domain_events_when_first_cognitive_view_is_narrow(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=ledger.epoch,
            event_type="SEED", writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":"m","value":1,"epistemic":"KNOWN","status":"CURRENT"},
                {"op":"SET","domain":"goal","key":"g","value":2,"epistemic":"KNOWN","status":"CURRENT"},
            ], committed_at="2026-08-10T01:20:00Z",
        )
        runtime = DatabasePulseRuntimeV3Guarded(ledger, now="2026-08-10T01:20:01Z")
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_deltas=32, now="2026-08-10T01:20:02Z",
            )
            refs = {
                str(r[0])
                for r in runtime.con.execute(
                    "SELECT changed_ref FROM frank_database_pulse_delta_queue"
                )
            }
            self.assertIn("memory:m", refs)
            self.assertIn("goal:g", refs)
            self.assertEqual(runtime.backlog_count(), 0)

            # No old goal event can be skipped just because the first cognitive selection was memory.
            goal = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("goal",),
                max_deltas=32, max_focus=1, now="2026-08-10T01:20:03Z",
            )
            self.assertEqual(goal.focus_refs, ("goal:g",))
        finally:
            ledger.close()

    def test_catchup_is_zero_model_tool_effect_and_semantically_non_mutating(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=ledger.epoch,
            event_type="SEED", writer="test",
            ops=[
                {"op":"SET","domain":"memory","key":f"k{i}","value":i,"epistemic":"KNOWN","status":"CURRENT"}
                for i in range(10)
            ], committed_at="2026-08-10T01:20:00Z",
        )
        runtime = DatabasePulseRuntimeV3Guarded(ledger, now="2026-08-10T01:20:01Z")
        epoch = ledger.epoch
        semantic_hash = ledger.semantic_state_hash
        trace_hash = ledger.trace_root_hash
        try:
            receipt = runtime.drain_backlog(
                basis_epoch=epoch, max_deltas=4, now="2026-08-10T01:20:02Z"
            )
            self.assertEqual(receipt.model_call_count, 0)
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
            self.assertEqual(receipt.applied_delta_count, 4)
            self.assertEqual(ledger.epoch, epoch)
            self.assertEqual(ledger.semantic_state_hash, semantic_hash)
            self.assertEqual(ledger.trace_root_hash, trace_hash)
        finally:
            ledger.close()

    def test_direct_corruption_still_recomputes_full_root_each_new_guarded_operation(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=ledger.epoch,
            event_type="SEED", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"x","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:20:00Z",
        )
        runtime = DatabasePulseRuntimeV3Guarded(ledger, now="2026-08-10T01:20:01Z")
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_deltas=32, now="2026-08-10T01:20:02Z",
            )
            ledger.conn.execute(
                "UPDATE state SET value_json='999' WHERE domain='memory' AND k='x'"
            )
            ledger.conn.commit()
            with self.assertRaises(Exception) as caught:
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_deltas=32, now="2026-08-10T01:20:03Z",
                )
            self.assertIn("root mismatch", str(caught.exception))
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
