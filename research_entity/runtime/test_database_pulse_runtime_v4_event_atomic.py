from __future__ import annotations

import json
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_runtime_v4_event_atomic import (
    DatabasePulseRuntimeV4EventAtomic,
)
from research_entity.runtime.database_pulse_v0 import PulseIntegrityError, PulseStateError


def seeded_runtime() -> tuple[StateLedger, DatabasePulseRuntimeV4EventAtomic]:
    ledger = StateLedger()
    ledger.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=ledger.epoch,
        event_type="EVENT_ATOMIC_SEED",
        writer="test",
        ops=[
            {
                "op":"SET","domain":"memory","key":"baseline",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"memory","key":"zzzz-critical",
                "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            },
        ],
        committed_at="2026-08-10T01:55:00Z",
    )
    runtime = DatabasePulseRuntimeV4EventAtomic(
        ledger, now="2026-08-10T01:55:01Z"
    )
    return ledger, runtime


class DatabasePulseRuntimeV4EventAtomicTests(unittest.TestCase):
    def test_one_180_op_stateledger_event_is_exactly_one_u12_delta(self):
        ledger, runtime = seeded_runtime()
        try:
            ops = [
                {
                    "op":"SET","domain":"memory","key":f"bulk-{i:04d}",
                    "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
                }
                for i in range(180)
            ]
            ledger.append_event(
                event_id="one-big-transaction",
                idem="one-big-transaction",
                base_epoch=ledger.epoch,
                event_type="BIG_ATOMIC_TRANSACTION",
                writer="test",
                ops=ops,
                committed_at="2026-08-10T01:55:02Z",
            )
            target_epoch = ledger.epoch
            bridge = runtime.bridge_stateledger_events(now="bridge-big")
            self.assertEqual(bridge["events_consumed"], 1)
            self.assertEqual(bridge["admitted_deltas"], 1)
            self.assertEqual(len(bridge["changed_refs"]), 180)
            self.assertEqual(runtime.backlog_count(), 1)

            queued = runtime.con.execute(
                "SELECT * FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL ORDER BY seq"
            ).fetchall()
            self.assertEqual(len(queued), 1)
            payload = json.loads(queued[0]["payload_clay"])
            self.assertEqual(payload["atomicity"], "ONE_STATELEDGER_EVENT_ONE_U12_DELTA")
            self.assertEqual(payload["event_epoch"], target_epoch)
            self.assertEqual(len(payload["changes"]), 180)
            self.assertEqual(len(payload["changed_refs"]), 180)

            out = runtime.run_pulse(
                basis_epoch=target_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=1,
                reentry_mode="NO_REENTRY",
                now="apply-big",
            )
            self.assertEqual(out.applied_delta_count, 1)
            self.assertEqual(out.memory_update_observed_count, 180)
            self.assertEqual(runtime.backlog_count(), 0)
            self.assertEqual(int(runtime._state()["source_epoch"]), target_epoch)
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(ledger.epoch, target_epoch)
        finally:
            ledger.close()

    def test_many_events_catch_up_only_at_complete_event_boundaries(self):
        ledger, runtime = seeded_runtime()
        try:
            event_epochs: list[int] = []
            for i in range(75):
                ledger.append_event(
                    event_id=f"e-{i:03d}",
                    idem=f"e-{i:03d}",
                    base_epoch=ledger.epoch,
                    event_type="ONE_EVENT",
                    writer="test",
                    ops=[{
                        "op":"SET","domain":"memory","key":f"event-{i:03d}",
                        "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
                    }],
                    committed_at=f"event-{i:03d}",
                )
                event_epochs.append(ledger.epoch)
            final_semantic_epoch = ledger.epoch
            runtime.bridge_stateledger_events(now="bridge-many")
            self.assertEqual(runtime.backlog_count(), 75)

            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    basis_epoch=final_semantic_epoch,
                    source_domains=("memory",),
                    max_candidates=64,
                    max_focus=1,
                    max_deltas=16,
                    reentry_mode="NO_REENTRY",
                    now="blocked-before-catchup",
                )
            self.assertEqual(int(runtime._state()["source_epoch"]), event_epochs[0] - 1)

            applied = 0
            observed_source_epochs: list[int] = []
            while runtime.backlog_count() > 16:
                receipt = runtime.drain_backlog(
                    basis_epoch=final_semantic_epoch,
                    max_deltas=16,
                    now=f"catchup-{len(observed_source_epochs)}",
                )
                applied += receipt.applied_delta_count
                source_epoch = int(runtime._state()["source_epoch"])
                observed_source_epochs.append(source_epoch)
                self.assertIn(source_epoch, event_epochs)
                self.assertEqual(source_epoch, event_epochs[applied - 1])
                self.assertLessEqual(source_epoch, final_semantic_epoch)
                self.assertEqual(receipt.model_call_count, 0)
                self.assertEqual(receipt.tool_call_count, 0)
                self.assertEqual(receipt.effect_count, 0)

            final = runtime.run_pulse(
                basis_epoch=final_semantic_epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                max_deltas=16,
                reentry_mode="NO_REENTRY",
                now="final-cognition",
            )
            self.assertEqual(runtime.backlog_count(), 0)
            self.assertEqual(int(runtime._state()["source_epoch"]), final_semantic_epoch)
            self.assertEqual(applied + final.applied_delta_count, 75)
            self.assertEqual(final.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(ledger.epoch, final_semantic_epoch)
        finally:
            ledger.close()

    def test_one_cross_domain_transaction_remains_one_delta_with_all_refs(self):
        ledger, runtime = seeded_runtime()
        try:
            ledger.append_event(
                event_id="cross-domain",
                idem="cross-domain",
                base_epoch=ledger.epoch,
                event_type="CROSS_DOMAIN",
                writer="test",
                ops=[
                    {
                        "op":"SET","domain":"memory","key":"m2","value":1,
                        "epistemic":"KNOWN","status":"CURRENT",
                    },
                    {
                        "op":"SET","domain":"goal","key":"g2","value":{"priority":0.8},
                        "epistemic":"KNOWN","status":"CURRENT",
                    },
                    {
                        "op":"SET","domain":"world","key":"w2","value":2,
                        "epistemic":"KNOWN","status":"CURRENT",
                    },
                ],
                committed_at="2026-08-10T01:55:02Z",
            )
            bridge = runtime.bridge_stateledger_events(now="cross-bridge")
            self.assertEqual(bridge["admitted_deltas"], 1)
            self.assertEqual(
                set(bridge["changed_refs"]), {"memory:m2", "goal:g2", "world:w2"}
            )
            row = runtime.con.execute(
                "SELECT payload_clay FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL"
            ).fetchone()
            payload = json.loads(row[0])
            self.assertEqual(
                set(payload["changed_refs"]), {"memory:m2", "goal:g2", "world:w2"}
            )
            out = runtime.run_pulse(
                basis_epoch=ledger.epoch,
                source_domains=("goal",),
                max_candidates=8,
                max_focus=1,
                max_deltas=1,
                reentry_mode="NO_REENTRY",
                now="cross-pulse",
            )
            self.assertEqual(out.applied_delta_count, 1)
            self.assertEqual(out.memory_update_observed_count, 1)
            self.assertEqual(out.focus_refs, ("goal:g2",))
        finally:
            ledger.close()

    def test_idle_event_atomic_pulse_preserves_prepared_query_and_semantic_roots(self):
        ledger, runtime = seeded_runtime()
        try:
            plane = UnifiedDBQueryPlane(ledger)
            prepared = plane.query(QuerySpec(
                "before-idle", domains=("memory",), basis_epoch=ledger.epoch
            ))
            before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            for i in range(4):
                out = runtime.run_pulse(
                    basis_epoch=ledger.epoch,
                    source_domains=("memory",),
                    max_candidates=8,
                    max_focus=1,
                    max_deltas=4,
                    reentry_mode="NO_REENTRY",
                    now=f"idle-{i}",
                )
                self.assertEqual(out.applied_delta_count, 0)
                self.assertEqual(out.model_call_count, 0)
                self.assertEqual(out.tool_call_count, 0)
                self.assertEqual(out.effect_count, 0)
            selected = plane.select_for_assembly(prepared)
            self.assertTrue(selected["selected"])
            self.assertEqual(before, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
        finally:
            ledger.close()

    def test_event_payload_hash_tamper_fails_closed_without_ack_or_pulse(self):
        ledger, runtime = seeded_runtime()
        try:
            ledger.append_event(
                event_id="tamper-target",
                idem="tamper-target",
                base_epoch=ledger.epoch,
                event_type="TEST",
                writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"tamper","value":1,
                    "epistemic":"KNOWN","status":"CURRENT",
                }],
                committed_at="2026-08-10T01:55:02Z",
            )
            runtime.bridge_stateledger_events(now="bridge-tamper")
            row = runtime.con.execute(
                "SELECT seq,payload_hash FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL"
            ).fetchone()
            runtime.con.execute(
                "UPDATE frank_database_pulse_delta_queue SET payload_clay='{}' WHERE seq=?",
                (row["seq"],),
            )
            runtime.con.commit()
            pulse_count = int(runtime._state()["pulse_count"])
            with self.assertRaises(PulseIntegrityError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch,
                    source_domains=("memory",),
                    max_deltas=4,
                    now="tamper-pulse",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), pulse_count)
            self.assertIsNone(runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue WHERE seq=?",
                (row["seq"],),
            ).fetchone()[0])
        finally:
            ledger.close()

    def test_fault_after_event_ack_rolls_back_entire_event_delta_and_receipt(self):
        ledger, runtime = seeded_runtime()
        try:
            ledger.append_event(
                event_id="fault-event",
                idem="fault-event",
                base_epoch=ledger.epoch,
                event_type="FAULT_EVENT",
                writer="test",
                ops=[
                    {
                        "op":"SET","domain":"memory","key":"f1","value":1,
                        "epistemic":"KNOWN","status":"CURRENT",
                    },
                    {
                        "op":"SET","domain":"memory","key":"f2","value":2,
                        "epistemic":"KNOWN","status":"CURRENT",
                    },
                ],
                committed_at="2026-08-10T01:55:02Z",
            )
            before_receipts = int(runtime.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_receipts"
            ).fetchone()[0])
            before_state = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,source_epoch,state_hash "
                "FROM frank_database_pulse_state"
            ).fetchone())
            with self.assertRaises(RuntimeError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch,
                    source_domains=("memory",),
                    max_deltas=1,
                    fault_after_apply=True,
                    now="fault-injected",
                )
            after_state = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,source_epoch,state_hash "
                "FROM frank_database_pulse_state"
            ).fetchone())
            self.assertEqual(before_state, after_state)
            self.assertEqual(int(runtime.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_receipts"
            ).fetchone()[0]), before_receipts)
            self.assertEqual(runtime.backlog_count(), 1)
            self.assertIsNone(runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL"
            ).fetchone()[0])
            retry = runtime.run_pulse(
                basis_epoch=ledger.epoch,
                source_domains=("memory",),
                max_deltas=1,
                now="fault-retry",
            )
            self.assertEqual(retry.applied_delta_count, 1)
            self.assertEqual(retry.memory_update_observed_count, 2)
            self.assertEqual(runtime.backlog_count(), 0)
        finally:
            ledger.close()

    def test_legacy_op_level_delta_can_still_be_drained_for_migration_compatibility(self):
        ledger, runtime = seeded_runtime()
        try:
            admitted = runtime.admit_delta(
                delta_id="legacy-op",
                changed_ref="memory:legacy",
                reason_class="MEMORY_UPDATE",
                payload={"legacy": True},
                source_epoch=ledger.epoch,
                graph_epoch=0,
                now="legacy-admit",
            )
            self.assertTrue(admitted)
            receipt = runtime.drain_backlog(
                basis_epoch=ledger.epoch,
                max_deltas=1,
                now="legacy-drain",
            )
            self.assertEqual(receipt.applied_delta_count, 1)
            self.assertEqual(receipt.model_call_count, 0)
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
            self.assertEqual(runtime.backlog_count(), 0)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
