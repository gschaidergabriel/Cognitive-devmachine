from __future__ import annotations

import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_execution_plane_v5 import (
    DatabasePulseExecutionPlaneV5,
    PulseSpecV5,
)
from research_entity.runtime.database_pulse_v0 import DatabasePulseV0


class DatabasePulseExecutionPlaneV5SourceBoundaryTests(unittest.TestCase):
    def test_partial_catchup_source_hash_equals_last_acknowledged_event_not_current_future_root(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=0, event_type="SEED", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"seed","value":0,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="seed",
        )
        runtime = DatabasePulseExecutionPlaneV5(ledger, now="bootstrap")
        event_hashes: list[str] = []
        event_epochs: list[int] = []
        for i in range(5):
            ledger.append_event(
                event_id=f"e{i}", idem=f"e{i}", base_epoch=ledger.epoch,
                event_type="DELTA", writer="test",
                ops=[{"op":"SET","domain":"memory","key":f"k{i}","value":i,"epistemic":"KNOWN","status":"CURRENT"}],
                committed_at=f"e{i}",
            )
            row = ledger.conn.execute(
                "SELECT semantic_state_hash FROM events WHERE event_id=?", (f"e{i}",)
            ).fetchone()
            event_hashes.append(str(row[0]))
            event_epochs.append(ledger.epoch)
        current_hash = ledger.semantic_state_hash
        current_epoch = ledger.epoch
        try:
            first = runtime.drain_source_events(
                invocation_id="catch-1", basis_epoch=current_epoch,
                max_source_events=2, now="catch-1",
            )
            self.assertEqual(first.source_event_count, 2)
            self.assertEqual(first.source_epoch_after, event_epochs[1])
            self.assertEqual(first.source_semantic_state_hash_after, event_hashes[1])
            self.assertNotEqual(first.source_semantic_state_hash_after, current_hash)
            state_body = runtime._decode_state_clay(runtime._state())
            self.assertEqual(state_body["source_semantic_state_hash"], event_hashes[1])
            self.assertEqual(int(runtime._state()["source_epoch"]), event_epochs[1])

            second = runtime.drain_source_events(
                invocation_id="catch-2", basis_epoch=current_epoch,
                max_source_events=2, now="catch-2",
            )
            self.assertEqual(second.source_epoch_after, event_epochs[3])
            self.assertEqual(second.source_semantic_state_hash_after, event_hashes[3])
            self.assertNotEqual(second.source_semantic_state_hash_after, current_hash)

            final = runtime.run_pulse(
                PulseSpecV5(
                    "final", basis_epoch=current_epoch, source_domains=("memory",),
                    max_candidates=8, max_focus=1, max_source_events=2,
                    reentry_mode="NO_REENTRY",
                ),
                now="final",
            )
            self.assertEqual(final.source_event_count, 1)
            self.assertEqual(final.source_epoch_after, current_epoch)
            self.assertEqual(final.source_semantic_state_hash_after, current_hash)
            self.assertEqual(final.backlog_events_after, 0)
        finally:
            ledger.close()

    def test_existing_lagging_u12_is_adopted_at_its_recorded_event_boundary(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="e1", idem="e1", base_epoch=0, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"a","value":1,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="e1",
        )
        e1_hash = ledger.semantic_state_hash
        e1_epoch = ledger.epoch
        u12_sql = __import__(
            "pathlib"
        ).Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(encoding="utf-8")
        ledger.conn.executescript(u12_sql)
        ledger.conn.commit()
        legacy = DatabasePulseV0(ledger.conn)
        legacy.bootstrap(
            entity_id="entity", lineage_id="lineage", source_epoch=e1_epoch,
            graph_epoch=0, now="legacy",
        )
        ledger.append_event(
            event_id="e2", idem="e2", base_epoch=ledger.epoch, event_type="TEST", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"b","value":2,"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="e2",
        )
        current_epoch = ledger.epoch
        current_hash = ledger.semantic_state_hash
        try:
            runtime = DatabasePulseExecutionPlaneV5(
                ledger, entity_id="entity", lineage_id="lineage", now="adopt"
            )
            state = runtime._state()
            body = runtime._decode_state_clay(state)
            self.assertEqual(int(state["source_epoch"]), e1_epoch)
            self.assertEqual(body["source_semantic_state_hash"], e1_hash)
            self.assertEqual(runtime._pending_event_count(), 1)
            out = runtime.run_pulse(
                PulseSpecV5(
                    "migrate-forward", basis_epoch=current_epoch, source_domains=("memory",),
                    max_candidates=8, max_focus=1, max_source_events=1,
                    reentry_mode="NO_REENTRY",
                ),
                now="migrate-forward",
            )
            self.assertEqual(out.source_event_count, 1)
            self.assertEqual(out.source_epoch_after, current_epoch)
            self.assertEqual(out.source_semantic_state_hash_after, current_hash)
        finally:
            ledger.close()

    def test_invocation_registry_is_bound_to_receipt_and_single_pulse_index(self):
        ledger = StateLedger()
        ledger.append_event(
            event_id="seed", idem="seed", base_epoch=0, event_type="SEED", writer="test",
            ops=[{"op":"SET","domain":"memory","key":"x","value":{"priority":1.0},"epistemic":"KNOWN","status":"CURRENT"}],
            committed_at="seed",
        )
        runtime = DatabasePulseExecutionPlaneV5(ledger, now="bootstrap")
        try:
            spec = PulseSpecV5(
                "idem", basis_epoch=ledger.epoch, source_domains=("memory",),
                max_candidates=4, max_focus=1,
            )
            first = runtime.run_pulse(spec, now="first")
            second = runtime.run_pulse(spec, now="second")
            self.assertEqual(second.status, "ALREADY_RECORDED")
            self.assertEqual(second.receipt_hash, first.receipt_hash)
            rows = runtime.con.execute(
                "SELECT * FROM frank_database_pulse_v5_invocations WHERE invocation_id='idem'"
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["pulse_id"], first.pulse_id)
            self.assertEqual(int(rows[0]["pulse_index"]), first.pulse_index)
            self.assertEqual(rows[0]["receipt_hash"], first.receipt_hash)
            self.assertEqual(int(runtime._state()["pulse_count"]), 1)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
