from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec
from research_entity.runtime.database_pulse_runtime_v3 import DatabasePulseRuntimeV3
from research_entity.runtime.database_pulse_v0 import PulseIntegrityError, PulseStateError


def seed(path=":memory:", *, many: int = 8):
    ledger = StateLedger(path)
    ops = []
    for i in range(many):
        ops.append({
            "op":"SET", "domain":"memory", "key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN", "status":"CURRENT",
        })
    ops.extend([
        {
            "op":"SET", "domain":"memory", "key":"zzzz-critical",
            "value":{"fact":"critical","priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
            "epistemic":"KNOWN", "status":"CURRENT",
        },
        {"op":"SET","domain":"memory","key":"unknown","value":{"u":1},"epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"c":1},"epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(
        event_id="seed-v3", idem="seed-v3", base_epoch=ledger.epoch,
        event_type="PULSE_V3_TEST_SEED", writer="test", ops=ops,
        committed_at="2026-08-10T01:00:00Z",
    )
    runtime = DatabasePulseRuntimeV3(ledger, now="2026-08-10T01:00:01Z")
    return ledger, runtime


class DatabasePulseRuntimeV3Tests(unittest.TestCase):
    def test_zero_model_pulse_advances_u12_clock_without_semantic_self_churn(self):
        ledger, runtime = seed()
        try:
            epoch = ledger.epoch
            state_hash = ledger.semantic_state_hash
            trace_hash = ledger.trace_root_hash
            receipt = runtime.run_pulse(
                basis_epoch=epoch,
                source_domains=("memory",),
                max_candidates=8,
                max_focus=2,
                now="2026-08-10T01:00:02Z",
            )
            self.assertEqual(receipt.pulse_index, 1)
            self.assertEqual(receipt.model_call_count, 0)
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
            self.assertEqual(receipt.semantic_state_transition_count, 0)
            self.assertEqual(ledger.epoch, epoch)
            self.assertEqual(ledger.semantic_state_hash, state_hash)
            self.assertEqual(ledger.trace_root_hash, trace_hash)
            state = runtime._state()
            self.assertEqual(int(state["pulse_count"]), 1)
            self.assertEqual(int(state["entity_epoch"]), 1)
        finally:
            ledger.close()

    def test_v3_directly_repairs_v1_query_receipt_self_invalidation(self):
        left, v1 = seed()
        try:
            # Use the StateLedger v1 runtime on the same semantic fixture only; its normal
            # scheduler lives in semantic state and therefore the Pulse itself advances epoch.
            v1_semantic = DatabasePulseRuntime(left)
            v1_semantic.set_scheduler(
                enabled=True, event_id="v1-scheduler", base_epoch=left.epoch,
                actor="test", reason="differential", committed_at="2026-08-10T01:00:02Z",
            )
            plane = UnifiedDBQueryPlane(left)
            prepared = plane.query(QuerySpec(
                "prepared-v1", domains=("memory",), basis_epoch=left.epoch
            ))
            v1_semantic.run_pulse(PulseSpec(
                "v1", basis_epoch=left.epoch, source_domains=("memory",), max_focus=1
            ), committed_at="2026-08-10T01:00:03Z")
            with self.assertRaises(StaleEpoch):
                plane.select_for_assembly(prepared)
        finally:
            left.close()

        right, v3 = seed()
        try:
            plane = UnifiedDBQueryPlane(right)
            prepared = plane.query(QuerySpec(
                "prepared-v3", domains=("memory",), basis_epoch=right.epoch
            ))
            epoch = right.epoch
            v3.run_pulse(
                basis_epoch=epoch, source_domains=("memory",), max_focus=1,
                now="2026-08-10T01:00:03Z",
            )
            selected = plane.select_for_assembly(prepared)
            self.assertEqual(right.epoch, epoch)
            self.assertTrue(selected["selected"])
        finally:
            right.close()

    def test_active_field_preselection_repairs_v1_lexicographic_starvation(self):
        ledger, runtime = seed(many=180)
        try:
            receipt = runtime.run_pulse(
                basis_epoch=ledger.epoch,
                source_domains=("memory",),
                max_candidates=64,
                max_focus=1,
                reentry_mode="NO_REENTRY",
                now="2026-08-10T01:00:02Z",
            )
            self.assertEqual(receipt.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(receipt.conflicts_present, 1)
            self.assertEqual(receipt.unknown_present, 1)
            body = json.loads(
                runtime.con.execute(
                    "SELECT receipt_clay FROM frank_database_pulse_receipts ORDER BY pulse_index DESC LIMIT 1"
                ).fetchone()[0]
            )
            self.assertEqual(body["candidate_generation"], "PULSE_ACTIVE_FIELD_V2")
            self.assertEqual(body["effect_authority"], "NONE")
        finally:
            ledger.close()

    def test_stateledger_events_bridge_to_u12_delta_queue_and_ack_atomically(self):
        ledger, runtime = seed()
        try:
            first = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=4096,
                now="2026-08-10T01:00:02Z",
            )
            self.assertGreater(first.applied_delta_count, 0)
            self.assertEqual(first.backlog_after, 0)
            ledger.append_event(
                event_id="memory-change", idem="memory-change", base_epoch=ledger.epoch,
                event_type="MEMORY_UPDATE", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"hot",
                    "value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T01:00:03Z",
            )
            second = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:00:04Z",
            )
            self.assertEqual(second.applied_delta_count, 1)
            self.assertEqual(second.memory_update_observed_count, 1)
            self.assertIn("memory:hot", second.candidate_refs)
            queue = runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue "
                "WHERE changed_ref='memory:hot' ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            self.assertEqual(queue[0], second.pulse_id)
        finally:
            ledger.close()

    def test_idle_pulses_do_not_rebridge_or_advance_semantic_epoch(self):
        ledger, runtime = seed()
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=4096,
                now="2026-08-10T01:00:02Z",
            )
            epoch = ledger.epoch
            semantic_hash = ledger.semantic_state_hash
            for i in range(5):
                r = runtime.run_pulse(
                    basis_epoch=epoch, source_domains=("memory",), max_deltas=32,
                    now=f"2026-08-10T01:00:{3+i:02d}Z",
                )
                self.assertEqual(r.applied_delta_count, 0)
                self.assertEqual(r.semantic_state_transition_count, 0)
            self.assertEqual(ledger.epoch, epoch)
            self.assertEqual(ledger.semantic_state_hash, semantic_hash)
            meta = runtime._bridge_meta()
            self.assertGreaterEqual(int(meta["bridge_count"]), 1)
        finally:
            ledger.close()

    def test_truthful_reentry_remains_causally_lesionable(self):
        def run_arm(mode: str):
            ledger = StateLedger()
            ledger.append_event(
                event_id="seed", idem="seed", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"a","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"b","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                ], committed_at="2026-08-10T01:00:00Z",
            )
            runtime = DatabasePulseRuntimeV3(ledger, now="2026-08-10T01:00:01Z")
            first = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=2, max_focus=1, reentry_mode="TRUTHFUL",
                max_deltas=32, now="2026-08-10T01:00:02Z",
            )
            self.assertEqual(first.focus_refs, ("memory:a",))
            ledger.append_event(
                event_id="challenge", idem="challenge", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"0-challenger",
                    "value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T01:00:03Z",
            )
            out = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=2, max_focus=1, reentry_mode=mode,
                max_deltas=32, now="2026-08-10T01:00:04Z",
            )
            return ledger, out

        truthful_ledger, truthful = run_arm("TRUTHFUL")
        lesion_ledger, lesion = run_arm("NO_REENTRY")
        try:
            self.assertEqual(truthful.focus_refs, ("memory:a",))
            self.assertEqual(truthful.reentry_count, 1)
            self.assertEqual(lesion.focus_refs, ("memory:0-challenger",))
            self.assertEqual(lesion.reentry_count, 0)
            self.assertNotEqual(truthful.assembly_hash, lesion.assembly_hash)
        finally:
            truthful_ledger.close(); lesion_ledger.close()

    def test_optional_model_output_is_unknown_context_only_and_zero_effect(self):
        ledger, runtime = seed()
        try:
            epoch = ledger.epoch
            receipt = runtime.run_pulse(
                basis_epoch=epoch, source_domains=("memory",), max_focus=1,
                model_assistant=lambda ctx:{
                    "kind":"HYPOTHESIS", "text":"candidate", "basis":ctx["selection_hash"]
                }, now="2026-08-10T01:00:02Z",
            )
            self.assertEqual(receipt.model_call_count, 1)
            self.assertEqual(receipt.hypothesis_count, 1)
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
            body = json.loads(runtime.con.execute(
                "SELECT receipt_clay FROM frank_database_pulse_receipts ORDER BY pulse_index DESC LIMIT 1"
            ).fetchone()[0])
            candidate = body["model_candidate"]
            self.assertEqual(candidate["epistemic"], "UNKNOWN")
            self.assertEqual(candidate["authority"], "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
            self.assertEqual(ledger.epoch, epoch)
            self.assertIsNone(ledger.get("pulse", "model_candidate"))
        finally:
            ledger.close()

    def test_fault_after_delta_ack_rolls_back_u12_state_receipt_checkpoint_and_ack(self):
        ledger, runtime = seed()
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=4096,
                now="2026-08-10T01:00:02Z",
            )
            ledger.append_event(
                event_id="fault-delta", idem="fault-delta", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"fault","value":1,
                    "epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T01:00:03Z",
            )
            before_state = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            receipt_count = int(runtime.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_receipts"
            ).fetchone()[0])
            with self.assertRaises(RuntimeError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                    fault_after_apply=True, now="2026-08-10T01:00:04Z",
                )
            after_state = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            self.assertEqual(after_state, before_state)
            self.assertEqual(int(runtime.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_receipts"
            ).fetchone()[0]), receipt_count)
            ack = runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue "
                "WHERE changed_ref='memory:fault' ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
            self.assertIsNone(ack)
            retry = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:00:05Z",
            )
            self.assertEqual(retry.applied_delta_count, 1)
        finally:
            ledger.close()

    def test_pause_resume_and_restart_preserve_u12_pulse_identity(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "v3.sqlite"
            ledger, runtime = seed(path)
            first = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=4096,
                now="2026-08-10T01:00:02Z",
            )
            runtime.set_status("PAUSED", now="2026-08-10T01:00:03Z")
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",),
                    now="2026-08-10T01:00:04Z",
                )
            epoch = ledger.epoch
            ledger.close()

            reopened = StateLedger(path)
            runtime2 = DatabasePulseRuntimeV3(reopened, now="2026-08-10T01:00:05Z")
            runtime2.set_status("PULSING", now="2026-08-10T01:00:06Z")
            second = runtime2.run_pulse(
                basis_epoch=reopened.epoch, source_domains=("memory",),
                now="2026-08-10T01:00:07Z",
            )
            self.assertEqual(first.pulse_index, 1)
            self.assertEqual(second.pulse_index, 2)
            self.assertEqual(reopened.epoch, epoch)
            reopened.close()

    def test_direct_state_corruption_is_detected_by_full_integrity_gate_before_pulse(self):
        ledger, runtime = seed()
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=4096,
                now="2026-08-10T01:00:02Z",
            )
            ledger.conn.execute(
                "UPDATE state SET value_json='999' WHERE domain='memory' AND k='k0000'"
            )
            ledger.conn.commit()
            pulse_count = int(runtime._state()["pulse_count"])
            with self.assertRaises(PulseIntegrityError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",),
                    now="2026-08-10T01:00:03Z",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), pulse_count)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
