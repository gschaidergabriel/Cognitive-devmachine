from __future__ import annotations

import json
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.auth_shadow_v1 import AuthShadowIntegrityError
from research_entity.runtime.database_pulse_execution_plane_v5 import (
    DatabasePulseExecutionPlaneV5,
    PulseSpecV5,
)
from research_entity.runtime.database_pulse_v0 import PulseIntegrityError, PulseStateError


def seed() -> tuple[StateLedger, DatabasePulseExecutionPlaneV5]:
    ledger = StateLedger()
    ledger.append_event(
        event_id="seed",
        idem="seed",
        base_epoch=ledger.epoch,
        event_type="V5_TEST_SEED",
        writer="test",
        ops=[
            {
                "op":"SET","domain":"memory","key":"a",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"memory","key":"b",
                "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"memory","key":"zzzz-critical",
                "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
                "epistemic":"KNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"goal","key":"g",
                "value":{"priority":0.7},"epistemic":"KNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"memory","key":"unknown",
                "value":{"priority":1.0},"epistemic":"UNKNOWN","status":"CURRENT",
            },
            {
                "op":"SET","domain":"memory","key":"conflict",
                "value":{"priority":1.0},"epistemic":"CONFLICT","status":"CURRENT",
            },
        ],
        committed_at="2026-08-10T02:10:00Z",
    )
    runtime = DatabasePulseExecutionPlaneV5(
        ledger, now="2026-08-10T02:10:01Z"
    )
    return ledger, runtime


class DatabasePulseExecutionPlaneV5Tests(unittest.TestCase):
    def test_fresh_bootstrap_adopts_current_snapshot_without_duplicate_delta_log(self):
        ledger, runtime = seed()
        try:
            state = runtime._verify_state()
            body = runtime._decode_state_clay(state)
            self.assertEqual(body["implementation"], "database_pulse_execution_plane_v5_direct_stateledger_events")
            self.assertEqual(body["mode"], "CURRENT_STATELEDGER_SNAPSHOT_BOOTSTRAP")
            self.assertEqual(body["last_source_event_seq"], runtime._max_event_seq())
            self.assertEqual(int(state["source_epoch"]), ledger.epoch)
            self.assertEqual(runtime._pending_event_count(), 0)
            self.assertEqual(
                int(runtime.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue"
                ).fetchone()[0]),
                0,
            )
            self.assertEqual(int(state["pulse_count"]), 0)
        finally:
            ledger.close()

    def test_idle_pulse_uses_separate_execution_clock_and_preserves_query_receipt(self):
        ledger, runtime = seed()
        try:
            plane = UnifiedDBQueryPlane(ledger)
            prepared = plane.query(QuerySpec(
                "prepared", domains=("memory",), basis_epoch=ledger.epoch
            ))
            before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            out = runtime.run_pulse(
                PulseSpecV5(
                    "idle-1", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=3, max_focus=1, max_source_events=4,
                    reentry_mode="NO_REENTRY",
                ),
                now="2026-08-10T02:10:02Z",
            )
            self.assertEqual(out.status, "RECORDED")
            self.assertEqual(out.source_event_count, 0)
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(out.physical_rank_mode, "ONLINE_STATE_TOPK")
            self.assertTrue(out.focus_guard_passed)
            self.assertEqual(out.model_call_count, 0)
            self.assertEqual(out.tool_call_count, 0)
            self.assertEqual(out.effect_count, 0)
            selected = plane.select_for_assembly(prepared)
            self.assertTrue(selected["selected"])
            self.assertEqual(before, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
            self.assertEqual(int(runtime._state()["pulse_count"]), 1)
            self.assertEqual(runtime._pending_event_count(), 0)
        finally:
            ledger.close()

    def test_one_180_op_semantic_transaction_is_one_direct_source_event_not_180_deltas(self):
        ledger, runtime = seed()
        try:
            ledger.append_event(
                event_id="big-event",
                idem="big-event",
                base_epoch=ledger.epoch,
                event_type="BIG_TRANSACTION",
                writer="test",
                ops=[
                    {
                        "op":"SET","domain":"memory","key":f"bulk-{i:04d}",
                        "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
                    }
                    for i in range(180)
                ],
                committed_at="2026-08-10T02:10:02Z",
            )
            semantic_epoch = ledger.epoch
            self.assertEqual(runtime._pending_event_count(), 1)
            out = runtime.run_pulse(
                PulseSpecV5(
                    "big", basis_epoch=semantic_epoch, source_domains=("memory",),
                    max_candidates=16, max_focus=1, max_source_events=1,
                    reentry_mode="NO_REENTRY",
                ),
                now="2026-08-10T02:10:03Z",
            )
            self.assertEqual(out.source_event_count, 1)
            self.assertEqual(out.memory_update_observed_count, 180)
            self.assertEqual(out.source_epoch_after, semantic_epoch)
            self.assertEqual(out.backlog_events_after, 0)
            self.assertEqual(runtime._pending_event_count(), 0)
            self.assertEqual(
                int(runtime.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue"
                ).fetchone()[0]),
                0,
            )
            self.assertEqual(ledger.epoch, semantic_epoch)
        finally:
            ledger.close()

    def test_many_events_are_cognition_gated_and_catch_up_on_whole_event_boundaries(self):
        ledger, runtime = seed()
        try:
            event_epochs: list[int] = []
            event_seqs: list[int] = []
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
                event_seqs.append(runtime._max_event_seq())
            final_epoch = ledger.epoch
            self.assertEqual(runtime._pending_event_count(), 75)
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    PulseSpecV5(
                        "blocked", basis_epoch=final_epoch, source_domains=("memory",),
                        max_candidates=16, max_focus=1, max_source_events=16,
                        reentry_mode="NO_REENTRY",
                    ),
                    now="blocked",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), 0)

            applied = 0
            batch = 0
            while runtime._pending_event_count() > 16:
                out = runtime.drain_source_events(
                    invocation_id=f"catch-{batch}",
                    basis_epoch=final_epoch,
                    max_source_events=16,
                    now=f"catch-{batch}",
                )
                applied += out.source_event_count
                self.assertEqual(out.source_event_count, 16)
                self.assertEqual(out.source_event_seq_after, event_seqs[applied - 1])
                self.assertEqual(out.source_epoch_after, event_epochs[applied - 1])
                self.assertEqual(out.model_call_count, 0)
                self.assertEqual(out.tool_call_count, 0)
                self.assertEqual(out.effect_count, 0)
                batch += 1

            final = runtime.run_pulse(
                PulseSpecV5(
                    "final", basis_epoch=final_epoch, source_domains=("memory",),
                    max_candidates=16, max_focus=1, max_source_events=16,
                    reentry_mode="NO_REENTRY",
                ),
                now="final",
            )
            self.assertEqual(applied + final.source_event_count, 75)
            self.assertEqual(final.source_event_seq_after, event_seqs[-1])
            self.assertEqual(final.source_epoch_after, final_epoch)
            self.assertEqual(final.backlog_events_after, 0)
            self.assertEqual(runtime._pending_event_count(), 0)
            self.assertEqual(ledger.epoch, final_epoch)
        finally:
            ledger.close()

    def test_invocation_idempotency_does_not_create_second_pulse(self):
        ledger, runtime = seed()
        try:
            spec = PulseSpecV5(
                "same-id", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=3, max_focus=1, reentry_mode="NO_REENTRY",
            )
            first = runtime.run_pulse(spec, now="first")
            pulse_count = int(runtime._state()["pulse_count"])
            second = runtime.run_pulse(spec, now="retry")
            self.assertEqual(second.status, "ALREADY_RECORDED")
            self.assertEqual(second.receipt_hash, first.receipt_hash)
            self.assertEqual(second.pulse_id, first.pulse_id)
            self.assertEqual(second.pulse_index, first.pulse_index)
            self.assertEqual(int(runtime._state()["pulse_count"]), pulse_count)
        finally:
            ledger.close()

    def test_hash_graph_is_acyclic_state_binds_assembly_receipt_binds_post_state(self):
        ledger, runtime = seed()
        try:
            out = runtime.run_pulse(
                PulseSpecV5(
                    "acyclic", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=3, max_focus=1,
                ),
                now="acyclic",
            )
            state = runtime._state()
            state_body = runtime._decode_state_clay(state)
            receipt = runtime._existing_invocation("acyclic")
            self.assertEqual(state_body["last_cognitive_assembly_hash"], out.assembly_hash)
            self.assertNotIn("last_cognitive_receipt_hash", state_body)
            self.assertEqual(receipt["post_state_hash"], state["state_hash"])
            plain = dict(receipt); supplied = plain.pop("receipt_hash")
            from research_entity.harness.reference.state_ledger import h
            self.assertEqual(h(plain), supplied)
        finally:
            ledger.close()

    def test_focus_use_guard_catches_direct_selected_row_tamper_between_full_audits(self):
        ledger, runtime = seed()
        try:
            runtime.run_pulse(
                PulseSpecV5(
                    "p1", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=3, max_focus=1, full_audit_every=999,
                    reentry_mode="NO_REENTRY",
                ),
                now="p1",
            )
            ledger.conn.execute(
                "UPDATE state SET value_json=? WHERE domain='memory' AND k='zzzz-critical'",
                (json.dumps({
                    "priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0,
                    "tampered":True,
                }, sort_keys=True, separators=(",", ":")),),
            )
            ledger.conn.commit()
            pulse_count = int(runtime._state()["pulse_count"])
            with self.assertRaises(AuthShadowIntegrityError):
                runtime.run_pulse(
                    PulseSpecV5(
                        "p2", basis_epoch=ledger.epoch, source_domains=("memory",),
                        max_candidates=3, max_focus=1, full_audit_every=999,
                        reentry_mode="NO_REENTRY",
                    ),
                    now="p2",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), pulse_count)
        finally:
            ledger.close()

    def test_periodic_full_audit_catches_unselected_direct_state_tamper(self):
        ledger, runtime = seed()
        try:
            runtime.run_pulse(
                PulseSpecV5(
                    "p1", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=1, max_focus=1, full_audit_every=2,
                    reentry_mode="NO_REENTRY",
                ),
                now="p1",
            )
            ledger.conn.execute(
                "UPDATE state SET value_json='999' WHERE domain='memory' AND k='a'"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseIntegrityError):
                runtime.run_pulse(
                    PulseSpecV5(
                        "p2", basis_epoch=ledger.epoch, source_domains=("memory",),
                        max_candidates=1, max_focus=1, full_audit_every=2,
                        reentry_mode="NO_REENTRY",
                    ),
                    now="p2",
                )
        finally:
            ledger.close()

    def test_optional_model_output_remains_unknown_context_only(self):
        ledger, runtime = seed()
        try:
            before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            out = runtime.run_pulse(
                PulseSpecV5(
                    "model", basis_epoch=ledger.epoch, source_domains=("memory",),
                    max_candidates=3, max_focus=1,
                ),
                model_assistant=lambda ctx:{
                    "kind":"HYPOTHESIS","basis":ctx["assembly_hash"],"text":"candidate only"
                },
                now="model",
            )
            self.assertEqual(out.model_call_count, 1)
            self.assertEqual(out.tool_call_count, 0)
            self.assertEqual(out.effect_count, 0)
            receipt = runtime._existing_invocation("model")
            self.assertEqual(receipt["model_candidate"]["epistemic"], "UNKNOWN")
            self.assertEqual(
                receipt["model_candidate"]["authority"],
                "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
            )
            self.assertEqual(receipt["effect_authority"], "NONE")
            self.assertIsNone(ledger.get("pulse", "model_candidate"))
            self.assertEqual(before, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
        finally:
            ledger.close()

    def test_legacy_u12_delta_backlog_blocks_direct_event_mode_instead_of_mixing_clocks(self):
        ledger, runtime = seed()
        try:
            runtime.admit_delta(
                delta_id="legacy",
                changed_ref="memory:legacy",
                reason_class="LEGACY",
                payload={"legacy":True},
                source_epoch=ledger.epoch,
                graph_epoch=0,
                now="legacy",
            )
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    PulseSpecV5(
                        "blocked-legacy", basis_epoch=ledger.epoch, source_domains=("memory",)
                    ),
                    now="blocked-legacy",
                )
            with self.assertRaises(PulseStateError):
                runtime.drain_source_events(
                    invocation_id="blocked-catchup",
                    basis_epoch=ledger.epoch,
                    now="blocked-catchup",
                )
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
