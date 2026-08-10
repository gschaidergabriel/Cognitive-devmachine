from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane
from research_entity.runtime.database_pulse_candidate_v1 import DatabasePulseRuntime, PulseSpec
from research_entity.runtime.database_pulse_rank_index_v3 import INDEX_NAME
from research_entity.runtime.database_pulse_runtime_v4 import DatabasePulseRuntimeV4
from research_entity.runtime.database_pulse_v0 import DatabasePulseV0, PulseIntegrityError, PulseStateError


def seed(path=":memory:", *, many: int = 16):
    ledger = StateLedger(path)
    ops = [
        {
            "op":"SET","domain":"memory","key":f"k{i:04d}",
            "value":{"fact":i,"priority":0.0,"urgency":0.0,"salience":0.0,"novelty":0.0},
            "epistemic":"KNOWN","status":"CURRENT",
        }
        for i in range(many)
    ]
    ops.extend([
        {
            "op":"SET","domain":"memory","key":"zzzz-critical",
            "value":{"priority":1.0,"urgency":1.0,"salience":1.0,"novelty":1.0},
            "epistemic":"KNOWN","status":"CURRENT",
        },
        {"op":"SET","domain":"goal","key":"g","value":{"priority":0.4},"epistemic":"KNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"unknown","value":{"priority":1.0},"epistemic":"UNKNOWN","status":"CURRENT"},
        {"op":"SET","domain":"memory","key":"conflict","value":{"priority":1.0},"epistemic":"CONFLICT","status":"CURRENT"},
    ])
    ledger.append_event(
        event_id="seed-v4", idem="seed-v4", base_epoch=ledger.epoch,
        event_type="PULSE_V4_TEST_SEED", writer="test", ops=ops,
        committed_at="2026-08-10T01:40:00Z",
    )
    runtime = DatabasePulseRuntimeV4(ledger, now="2026-08-10T01:40:01Z")
    return ledger, runtime


class DatabasePulseRuntimeV4Tests(unittest.TestCase):
    def test_fresh_bootstrap_anchors_current_snapshot_without_historical_delta_storm(self):
        ledger, runtime = seed(many=200)
        try:
            state = runtime._state()
            meta = runtime._bridge_meta()
            self.assertEqual(int(state["source_epoch"]), ledger.epoch)
            self.assertEqual(int(meta["last_event_seq"]), runtime._max_event_seq())
            self.assertEqual(meta["bootstrap_mode"], "CURRENT_SNAPSHOT_BOOTSTRAP")
            self.assertEqual(runtime.backlog_count(), 0)
            out = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=64, max_focus=1, max_deltas=32,
                reentry_mode="NO_REENTRY", now="2026-08-10T01:40:02Z",
            )
            self.assertEqual(out.applied_delta_count, 0)
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertEqual(out.bridge_mode, "NO_CHANGE")
        finally:
            ledger.close()

    def test_rank_index_repairs_starvation_without_second_candidate_table_or_semantic_churn(self):
        ledger, runtime = seed(many=180)
        try:
            root_before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            out = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=64, max_focus=1, max_deltas=32,
                reentry_mode="NO_REENTRY", now="2026-08-10T01:40:02Z",
            )
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertTrue(out.query_truncated)
            self.assertEqual(out.candidate_universe_count, 181)
            self.assertEqual(out.unknown_present, 1)
            self.assertEqual(out.conflicts_present, 1)
            self.assertEqual(out.rank_index_name, INDEX_NAME)
            tables = {r[0] for r in ledger.conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )}
            self.assertNotIn("pulse_active_field", tables)
            self.assertEqual(root_before, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
        finally:
            ledger.close()

    def test_v4_preserves_prepared_query_receipt_while_semantic_pulse_v2_invalidates_it(self):
        left = StateLedger()
        left.append_event(
            event_id="seed", idem="seed", base_epoch=0, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"x","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:40:00Z",
        )
        try:
            old = DatabasePulseRuntime(left)
            old.set_scheduler(
                enabled=True, event_id="sched", base_epoch=left.epoch,
                actor="test", reason="differential", committed_at="2026-08-10T01:40:01Z",
            )
            plane = UnifiedDBQueryPlane(left)
            receipt = plane.query(QuerySpec("old", domains=("memory",), basis_epoch=left.epoch))
            old.run_pulse(PulseSpec(
                "old-pulse", basis_epoch=left.epoch, source_domains=("memory",), max_focus=1
            ), committed_at="2026-08-10T01:40:02Z")
            with self.assertRaises(StaleEpoch):
                plane.select_for_assembly(receipt)
        finally:
            left.close()

        right, runtime = seed(many=1)
        try:
            plane = UnifiedDBQueryPlane(right)
            receipt = plane.query(QuerySpec("v4", domains=("memory",), basis_epoch=right.epoch))
            epoch = right.epoch
            semantic_hash = right.semantic_state_hash
            runtime.run_pulse(
                basis_epoch=epoch, source_domains=("memory",),
                max_focus=1, max_deltas=32, now="2026-08-10T01:40:02Z",
            )
            selected = plane.select_for_assembly(receipt)
            self.assertTrue(selected["selected"])
            self.assertEqual(right.epoch, epoch)
            self.assertEqual(right.semantic_state_hash, semantic_hash)
        finally:
            right.close()

    def test_new_authoritative_event_is_bridged_and_acknowledged_in_same_cognitive_pulse(self):
        ledger, runtime = seed(many=2)
        try:
            ledger.append_event(
                event_id="hot", idem="hot", base_epoch=ledger.epoch,
                event_type="MEMORY_UPDATE", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"hot-new",
                    "value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T01:40:02Z",
            )
            semantic_epoch = ledger.epoch
            semantic_hash = ledger.semantic_state_hash
            out = runtime.run_pulse(
                basis_epoch=semantic_epoch, source_domains=("memory",),
                max_candidates=8, max_focus=2, max_deltas=32,
                reentry_mode="NO_REENTRY", now="2026-08-10T01:40:03Z",
            )
            self.assertEqual(out.applied_delta_count, 1)
            self.assertEqual(out.memory_update_observed_count, 1)
            self.assertIn("memory:hot-new", out.candidate_refs)
            self.assertEqual(runtime.backlog_count(), 0)
            q = runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue "
                "WHERE changed_ref='memory:hot-new' ORDER BY seq DESC LIMIT 1"
            ).fetchone()
            self.assertEqual(q[0], out.pulse_id)
            self.assertEqual(ledger.epoch, semantic_epoch)
            self.assertEqual(ledger.semantic_state_hash, semantic_hash)
        finally:
            ledger.close()

    def test_global_bridge_retains_other_domain_even_when_cognitive_view_is_narrow(self):
        ledger, runtime = seed(many=1)
        try:
            ledger.append_event(
                event_id="mixed", idem="mixed", base_epoch=ledger.epoch,
                event_type="MIXED", writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"m2","value":1,"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"goal","key":"g2","value":{"priority":0.9},"epistemic":"KNOWN","status":"CURRENT"},
                ], committed_at="2026-08-10T01:40:02Z",
            )
            out = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_deltas=32, now="2026-08-10T01:40:03Z",
            )
            self.assertEqual(out.applied_delta_count, 2)
            refs = {r[0] for r in runtime.con.execute(
                "SELECT changed_ref FROM frank_database_pulse_delta_queue "
                "WHERE delta_id LIKE 'stateledger:%'"
            )}
            self.assertIn("memory:m2", refs)
            self.assertIn("goal:g2", refs)
            goal = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("goal",),
                max_focus=1, max_deltas=32, now="2026-08-10T01:40:04Z",
            )
            self.assertEqual(goal.focus_refs, ("goal:g2",))
        finally:
            ledger.close()

    def test_large_post_boot_burst_is_backlog_gated_then_bounded_catchup_allows_cognition(self):
        ledger, runtime = seed(many=1)
        try:
            epoch_before = ledger.epoch
            ledger.append_event(
                event_id="burst", idem="burst", base_epoch=ledger.epoch,
                event_type="BURST", writer="test",
                ops=[
                    {
                        "op":"SET","domain":"memory","key":f"burst-{i:04d}",
                        "value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT",
                    }
                    for i in range(180)
                ], committed_at="2026-08-10T01:40:02Z",
            )
            epoch = ledger.epoch
            self.assertEqual(epoch, epoch_before + 1)
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    basis_epoch=epoch, source_domains=("memory",),
                    max_candidates=64, max_focus=1, max_deltas=32,
                    now="2026-08-10T01:40:03Z",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), 0)
            self.assertEqual(runtime.backlog_count(), 180)
            catchups = 0
            while runtime.backlog_count() > 32:
                r = runtime.drain_backlog(
                    basis_epoch=epoch, max_deltas=32, now=f"catchup-{catchups}"
                )
                self.assertEqual(r.model_call_count, 0)
                self.assertEqual(r.tool_call_count, 0)
                self.assertEqual(r.effect_count, 0)
                catchups += 1
            out = runtime.run_pulse(
                basis_epoch=epoch, source_domains=("memory",),
                max_candidates=64, max_focus=1, max_deltas=32,
                reentry_mode="NO_REENTRY", now="2026-08-10T01:40:04Z",
            )
            self.assertEqual(runtime.backlog_count(), 0)
            self.assertEqual(out.focus_refs, ("memory:zzzz-critical",))
            self.assertGreater(catchups, 0)
            self.assertEqual(ledger.epoch, epoch)
        finally:
            ledger.close()

    def test_truthful_reentry_is_lesionable_under_authoritative_rank_index(self):
        def arm(mode: str):
            ledger = StateLedger()
            ledger.append_event(
                event_id="seed", idem="seed", base_epoch=0, event_type="TEST", writer="test",
                ops=[
                    {"op":"SET","domain":"memory","key":"previous","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                    {"op":"SET","domain":"memory","key":"other","value":{"priority":0.0},"epistemic":"KNOWN","status":"CURRENT"},
                ], committed_at="2026-08-10T01:40:00Z",
            )
            runtime = DatabasePulseRuntimeV4(ledger, now="2026-08-10T01:40:01Z")
            first = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=1, max_focus=1, max_deltas=32,
                reentry_mode="TRUTHFUL", now="2026-08-10T01:40:02Z",
            )
            self.assertEqual(first.focus_refs, ("memory:other",))
            ledger.append_event(
                event_id="challenger", idem="challenger", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[{
                    "op":"SET","domain":"memory","key":"challenger",
                    "value":{"priority":0.5},"epistemic":"KNOWN","status":"CURRENT",
                }], committed_at="2026-08-10T01:40:03Z",
            )
            second = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=1, max_focus=1, max_deltas=32,
                reentry_mode=mode, now="2026-08-10T01:40:04Z",
            )
            return ledger, second

        truthful_ledger, truthful = arm("TRUTHFUL")
        lesion_ledger, lesion = arm("NO_REENTRY")
        try:
            self.assertEqual(truthful.focus_refs, ("memory:other",))
            self.assertEqual(truthful.reentry_count, 1)
            self.assertEqual(lesion.focus_refs, ("memory:challenger",))
            self.assertEqual(lesion.reentry_count, 0)
            self.assertNotEqual(truthful.assembly_hash, lesion.assembly_hash)
        finally:
            truthful_ledger.close(); lesion_ledger.close()

    def test_optional_model_candidate_is_unknown_context_only(self):
        ledger, runtime = seed(many=1)
        try:
            epoch = ledger.epoch
            semantic_hash = ledger.semantic_state_hash
            out = runtime.run_pulse(
                basis_epoch=epoch, source_domains=("memory",), max_focus=1, max_deltas=32,
                model_assistant=lambda ctx:{
                    "kind":"HYPOTHESIS", "basis":ctx["selection_hash"], "text":"candidate"
                }, now="2026-08-10T01:40:02Z",
            )
            self.assertEqual(out.model_call_count, 1)
            self.assertEqual(out.hypothesis_count, 1)
            self.assertEqual(out.tool_call_count, 0)
            self.assertEqual(out.effect_count, 0)
            body = json.loads(runtime.con.execute(
                "SELECT receipt_clay FROM frank_database_pulse_receipts ORDER BY pulse_index DESC LIMIT 1"
            ).fetchone()[0])
            self.assertEqual(body["model_candidate"]["epistemic"], "UNKNOWN")
            self.assertEqual(body["model_candidate"]["authority"], "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
            self.assertEqual(body["effect_authority"], "NONE")
            self.assertIsNone(ledger.get("pulse", "model_candidate"))
            self.assertEqual(ledger.epoch, epoch)
            self.assertEqual(ledger.semantic_state_hash, semantic_hash)
        finally:
            ledger.close()

    def test_fault_after_ack_rolls_back_u12_state_receipt_checkpoint_and_delta_ack(self):
        ledger, runtime = seed(many=1)
        try:
            ledger.append_event(
                event_id="fault", idem="fault", base_epoch=ledger.epoch,
                event_type="TEST", writer="test",
                ops=[{"op":"SET","domain":"memory","key":"fault","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
                committed_at="2026-08-10T01:40:02Z",
            )
            before = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            with self.assertRaises(RuntimeError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                    fault_after_apply=True, now="2026-08-10T01:40:03Z",
                )
            after = tuple(runtime.con.execute(
                "SELECT pulse_count,last_applied_delta_seq,state_hash FROM frank_database_pulse_state"
            ).fetchone())
            self.assertEqual(after, before)
            ack = runtime.con.execute(
                "SELECT applied_pulse_id FROM frank_database_pulse_delta_queue "
                "WHERE changed_ref='memory:fault' ORDER BY seq DESC LIMIT 1"
            ).fetchone()[0]
            self.assertIsNone(ack)
            retry = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:40:04Z",
            )
            self.assertEqual(retry.applied_delta_count, 1)
        finally:
            ledger.close()

    def test_pause_restart_resume_preserves_pulse_identity_and_semantic_epoch(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "v4.sqlite"
            ledger, runtime = seed(path, many=1)
            first = runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:40:02Z",
            )
            runtime.set_status("PAUSED", now="2026-08-10T01:40:03Z")
            with self.assertRaises(PulseStateError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                    now="2026-08-10T01:40:04Z",
                )
            epoch = ledger.epoch
            ledger.close()

            reopened = StateLedger(path)
            runtime2 = DatabasePulseRuntimeV4(reopened, now="2026-08-10T01:40:05Z")
            runtime2.set_status("PULSING", now="2026-08-10T01:40:06Z")
            second = runtime2.run_pulse(
                basis_epoch=reopened.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:40:07Z",
            )
            self.assertEqual(first.pulse_index, 1)
            self.assertEqual(second.pulse_index, 2)
            self.assertEqual(reopened.epoch, epoch)
            reopened.close()

    def test_existing_u12_lag_migrates_from_recorded_source_epoch_not_full_history(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="e1", idem="e1", base_epoch=0, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"a","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:40:00Z",
        )
        u12_sql = Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(encoding="utf-8")
        ledger.conn.executescript(u12_sql); ledger.conn.commit()
        old = DatabasePulseV0(ledger.conn)
        old.bootstrap(entity_id="e", lineage_id="l", source_epoch=ledger.epoch, now="old")
        ledger.append_event(
            event_id="e2", idem="e2", base_epoch=ledger.epoch, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"b","value":2,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="2026-08-10T01:40:01Z",
        )
        try:
            runtime = DatabasePulseRuntimeV4(ledger, entity_id="e", lineage_id="l", now="migrate")
            meta = runtime._bridge_meta()
            self.assertEqual(meta["bootstrap_mode"], "LAGGING_U12_MIGRATION")
            bridge = runtime.bridge_stateledger_events(now="bridge")
            self.assertEqual(bridge["events_consumed"], 1)
            self.assertEqual(bridge["changed_refs"], ["memory:b"])
            self.assertEqual(runtime.backlog_count(), 1)
        finally:
            ledger.close()

    def test_direct_valid_json_state_tamper_is_caught_by_full_root_before_next_pulse(self):
        ledger, runtime = seed(many=1)
        try:
            runtime.run_pulse(
                basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                now="2026-08-10T01:40:02Z",
            )
            ledger.conn.execute(
                "UPDATE state SET value_json='999' WHERE domain='memory' AND k='k0000'"
            )
            ledger.conn.commit()
            count = int(runtime._state()["pulse_count"])
            with self.assertRaises(PulseIntegrityError):
                runtime.run_pulse(
                    basis_epoch=ledger.epoch, source_domains=("memory",), max_deltas=32,
                    now="2026-08-10T01:40:03Z",
                )
            self.assertEqual(int(runtime._state()["pulse_count"]), count)
        finally:
            ledger.close()

    def test_rank_index_drop_and_rebuild_is_semantically_inert(self):
        ledger, runtime = seed(many=20)
        try:
            before = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            expected = runtime.rank_index.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=16, max_focus=2,
            ).focus_refs
            runtime.rank_index.drop_index()
            middle = (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash)
            runtime.rank_index.ensure_index()
            got = runtime.rank_index.select(
                source_domains=("memory",), basis_epoch=ledger.epoch,
                max_candidates=16, max_focus=2,
            ).focus_refs
            self.assertEqual(before, middle)
            self.assertEqual(before, (ledger.epoch, ledger.semantic_state_hash, ledger.trace_root_hash))
            self.assertEqual(got, expected)
            self.assertTrue(runtime.rank_index.verify_index_semantics(domains=("memory",))["pass"])
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
